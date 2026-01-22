"""
Redmine 進度回報自動化工具 - FastAPI 主應用
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import os

from utils.config import load_config, save_config, validate_config, get_git_user
from services.redmine_service import RedmineService
from services.git_service import GitService
from services.analyze_service import AnalyzeService

# 設定日誌 - 輸出到控制台，格式清楚易讀
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True  # 強制重新設定（避免被其他模組覆蓋）
)
logger = logging.getLogger(__name__)

# 確保所有模組的日誌都會顯示
logging.getLogger('services').setLevel(logging.INFO)
logging.getLogger('utils').setLevel(logging.INFO)

# 儲存庫掃描快取（避免每次都全盤掃描）
_REPO_SCAN_CACHE: dict = {
    "key": None,
    "ts": 0.0,
    "repos": [],
}
_REPO_SCAN_CACHE_TTL_SECONDS = 30

# 建立 FastAPI 應用
app = FastAPI(title="Redmine 進度回報工具", version="1.0.0")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發環境允許所有來源，生產環境應限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態檔案服務
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")


# Pydantic 模型
class AnalyzeRequest(BaseModel):
    issue_id: int
    repository_path: str
    branch: str
    start_date: str  # ISO 格式日期字串
    end_date: str    # ISO 格式日期字串


class UpdateRedmineRequest(BaseModel):
    issue_id: int
    notes: Optional[str] = None
    percent_done: Optional[int] = Field(None, ge=0, le=100)
    spent_time: Optional[float] = Field(None, ge=0)
    status_id: Optional[int] = None


class ConfigUpdateRequest(BaseModel):
    redmine: Optional[Dict[str, Any]] = None
    git: Optional[Dict[str, Any]] = None
    ai: Optional[Dict[str, Any]] = None
    claude: Optional[Dict[str, Any]] = None  # 向後相容
    repositories: Optional[List[Dict[str, Any]]] = None
    scan_paths: Optional[List[str]] = None
    default_time_range: Optional[str] = None
    ui: Optional[Dict[str, Any]] = None


# 錯誤處理中介軟體
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未處理的錯誤: {exc}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail=f"內部伺服器錯誤: {str(exc)}"
    )


# API 端點

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """主頁面"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"載入主頁面失敗: {e}")
        return HTMLResponse("<h1>Redmine 進度回報工具</h1><p>前端檔案載入失敗</p>")


@app.get("/api/issues")
async def get_issues(status_id: Optional[int] = None, search: Optional[str] = None):
    """取得指派給當前使用者的工單列表"""
    logger.info(f"[API] GET /api/issues (status_id={status_id}, search={search})")
    try:
        config = load_config()
        redmine_config = config.get('redmine', {})
        
        if not redmine_config.get('url') or not redmine_config.get('api_key'):
            raise HTTPException(
                status_code=400,
                detail="請先在設定頁面設定 Redmine URL 和 API Key"
            )
        
        service = RedmineService(
            url=redmine_config['url'],
            api_key=redmine_config['api_key'],
            user_id=redmine_config.get('user_id')
        )
        
        issues = service.get_assigned_issues(status_id=status_id, search=search)
        logger.info(f"[API] 成功取得 {len(issues)} 個工單")
        return {"issues": issues}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取得工單列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法取得工單列表: {e}")


@app.get("/api/redmine/ping")
async def redmine_ping():
    """測試並重試 Redmine 連線（前端可用於「重新整理」時主動重連）"""
    logger.info("[API] GET /api/redmine/ping")
    try:
        config = load_config()
        redmine_config = config.get("redmine", {})

        if not redmine_config.get("url") or not redmine_config.get("api_key"):
            raise HTTPException(
                status_code=400,
                detail="請先在設定頁面設定 Redmine URL 和 API Key",
            )

        # 只要成功建立 service 並通過 auth()（在 RedmineService._connect 內）就代表連線可用
        RedmineService(
            url=redmine_config["url"],
            api_key=redmine_config["api_key"],
            user_id=redmine_config.get("user_id"),
        )

        return {"ok": True}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Redmine 連線測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"Redmine 連線測試失敗: {e}")


@app.get("/api/repositories")
async def get_repositories():
    """取得本地 Git 儲存庫列表"""
    logger.info("[API] GET /api/repositories")
    try:
        config = load_config()
        git_user = get_git_user(config)
        
        if not git_user:
            raise HTTPException(
                status_code=400,
                detail="無法取得 Git 使用者資訊，請先設定"
            )
        
        service = GitService(
            user_name=git_user['name'],
            user_email=git_user['email']
        )
        
        # 從設定檔取得已儲存的儲存庫
        saved_repos = config.get('repositories', [])
        saved_paths = {repo['path'] for repo in saved_repos}
        
        # 從設定檔取得自訂掃描路徑，如果沒有則使用預設
        scan_paths = config.get('scan_paths', None)

        # 快取 key（scan_paths + saved_repos）
        import time
        cache_key = (
            tuple(scan_paths) if isinstance(scan_paths, list) else None,
            tuple(sorted([r.get("path", "") for r in saved_repos])),
        )

        now = time.time()
        if (
            _REPO_SCAN_CACHE["key"] == cache_key
            and (now - _REPO_SCAN_CACHE["ts"]) < _REPO_SCAN_CACHE_TTL_SECONDS
        ):
            scanned_repos = _REPO_SCAN_CACHE["repos"]
        else:
            scanned_repos = service.scan_repositories(common_paths=scan_paths)
            _REPO_SCAN_CACHE["key"] = cache_key
            _REPO_SCAN_CACHE["ts"] = now
            _REPO_SCAN_CACHE["repos"] = scanned_repos
        
        # 合併結果（避免重複）
        all_repos = {}
        for repo in saved_repos:
            all_repos[repo['path']] = repo
        
        for repo in scanned_repos:
            if repo['path'] not in all_repos:
                all_repos[repo['path']] = repo
        
        repos_list = list(all_repos.values())
        logger.info(f"[API] 成功掃描到 {len(repos_list)} 個儲存庫")
        return {"repositories": repos_list}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 取得儲存庫列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法取得儲存庫列表: {e}")


@app.get("/api/repositories/{path:path}/branches")
async def get_branches(path: str):
    """取得指定儲存庫的分支列表"""
    import urllib.parse
    repo_path = urllib.parse.unquote(path)
    logger.info(f"[API] GET /api/repositories/.../branches (repo: {repo_path})")
    try:
        config = load_config()
        git_user = get_git_user(config)
        
        if not git_user:
            raise HTTPException(
                status_code=400,
                detail="無法取得 Git 使用者資訊，請先設定"
            )
        
        service = GitService(
            user_name=git_user['name'],
            user_email=git_user['email']
        )
        
        if not service.validate_repository(repo_path):
            raise HTTPException(
                status_code=400,
                detail=f"無效的 Git 儲存庫: {repo_path}"
            )
        
        branches = service.get_branches(repo_path)
        logger.info(f"[API] 成功取得 {len(branches)} 個分支")
        return {"branches": branches}
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] 取得分支列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法取得分支列表: {e}")


@app.get("/api/preview-commits")
async def preview_commits(
    repository_path: str,
    branch: str,
    start_date: str,
    end_date: str
):
    """預覽指定時間範圍內的 commit 數量（僅計算，不返回詳細內容）"""
    import urllib.parse
    repo_path = urllib.parse.unquote(repository_path)
    logger.info(f"[API] GET /api/preview-commits (repo: {repo_path}, branch: {branch}, {start_date} ~ {end_date})")
    try:
        config = load_config()
        git_user = get_git_user(config)
        
        if not git_user:
            raise HTTPException(
                status_code=400,
                detail="無法取得 Git 使用者資訊，請先設定"
            )
        
        # 解析日期
        try:
            start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"日期格式錯誤: {e}"
            )
        
        service = GitService(
            user_name=git_user['name'],
            user_email=git_user['email']
        )
        
        # 取得當前使用者的 commit（只計算數量，不返回詳細內容）
        commits = service.get_user_commits(
            repo_path=repo_path,
            branch=branch,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        commit_count = len(commits)
        logger.info(f"[API] 預覽完成：找到 {commit_count} 個 commit")
        return {
            "count": commit_count,
            "user": {
                "name": git_user['name'],
                "email": git_user['email']
            }
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        # 如果是「沒有 commit」的錯誤，回傳 0 而不是錯誤
        if "沒有找到" in str(e) or "沒有找到任何 commit" in str(e):
            config = load_config()
            git_user = get_git_user(config)
            return {
                "count": 0,
                "user": {
                    "name": git_user['name'] if git_user else "未知",
                    "email": git_user['email'] if git_user else "未知"
                },
                "message": str(e)
            }
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"預覽 commit 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法預覽 commit: {e}")


@app.post("/api/analyze")
async def analyze_commits(request: AnalyzeRequest):
    """分析 commit 並生成進度回報"""
    import urllib.parse
    repo_path = urllib.parse.unquote(request.repository_path)
    logger.info(f"[API] POST /api/analyze (Issue #{request.issue_id}, repo: {repo_path}, branch: {request.branch}, {request.start_date} ~ {request.end_date})")
    try:
        config = load_config()
        git_user = get_git_user(config)
        
        if not git_user:
            raise HTTPException(
                status_code=400,
                detail="無法取得 Git 使用者資訊，請先設定"
            )
        
        # 解析日期
        try:
            start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"日期格式錯誤: {e}"
            )
        
        # 取得 Git 服務
        git_service = GitService(
            user_name=git_user['name'],
            user_email=git_user['email']
        )
        
        # 取得當前使用者的 commit
        logger.info(f"[API] 開始取得 commit 記錄...")
        commits = git_service.get_user_commits(
            repo_path=repo_path,
            branch=request.branch,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"[API] 取得 {len(commits)} 個 commit，開始 AI 分析...")
        
        # 取得 Issue 資訊
        redmine_config = config.get('redmine', {})
        redmine_service = RedmineService(
            url=redmine_config['url'],
            api_key=redmine_config['api_key']
        )
        
        # 取得 issue 標題（這裡簡化處理，實際可能需要更好的錯誤處理）
        issue_title = f"Issue #{request.issue_id}"
        try:
            issues = redmine_service.get_assigned_issues()
            for issue in issues:
                if issue['id'] == request.issue_id:
                    issue_title = issue['subject']
                    break
        except Exception:
            pass  # 如果無法取得，使用預設標題
        
        # AI 分析
        # 優先使用新的 ai 設定，向後相容舊的 claude 設定
        ai_config = config.get('ai', {})
        if not ai_config or 'provider' not in ai_config:
            # 向後相容：使用舊的 claude 設定
            claude_config = config.get('claude', {})
            provider = 'claude'
            provider_config = claude_config
        else:
            provider = ai_config.get('provider', 'claude')
            provider_config = ai_config.get(provider, {})
        
        # Gemini CLI 和 OpenCode CLI 通常需要更長的超時時間，特別是處理大量 commit 時
        default_timeout = 120 if provider in ('gemini', 'opencode') else 60
        # OpenCode 不使用 model 參數，其他 provider 需要
        default_model = 'haiku' if provider == 'claude' else ('gemini-2.0-flash-exp' if provider == 'gemini' else '')
        analyze_service = AnalyzeService(
            provider=provider,
            cli_path=provider_config.get('cli_path', provider),
            model=provider_config.get('model', default_model) if provider != 'opencode' else '',
            timeout=provider_config.get('timeout', default_timeout),
            system_prompt_file=provider_config.get('system_prompt_file', 'prompts/redmine_analysis.txt')
        )
        
        result = analyze_service.analyze_commits(
            commits=commits,
            issue_id=request.issue_id,
            issue_title=issue_title,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        logger.info(f"[API] AI 分析完成！建議進度: {result.get('suggested_percent_done', 'N/A')}%, 預估工時: {result.get('estimated_hours', 'N/A')} 小時")
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"[API] 分析失敗 (ValueError): {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] 分析失敗 (Exception): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析失敗: {e}")


@app.post("/api/update-redmine")
async def update_redmine(request: UpdateRedmineRequest):
    """更新 Redmine issue"""
    try:
        config = load_config()
        redmine_config = config.get('redmine', {})
        
        if not redmine_config.get('url') or not redmine_config.get('api_key'):
            raise HTTPException(
                status_code=400,
                detail="請先在設定頁面設定 Redmine URL 和 API Key"
            )
        
        service = RedmineService(
            url=redmine_config['url'],
            api_key=redmine_config['api_key']
        )
        
        result = service.update_issue(
            issue_id=request.issue_id,
            notes=request.notes,
            percent_done=request.percent_done,
            spent_time=request.spent_time,
            status_id=request.status_id
        )
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 Redmine 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新失敗: {e}")


@app.get("/api/config")
async def get_config():
    """取得設定（排除敏感資訊）"""
    try:
        config = load_config()
        
        # 隱藏 API Key
        safe_config = config.copy()
        if 'redmine' in safe_config and 'api_key' in safe_config['redmine']:
            api_key = safe_config['redmine']['api_key']
            if api_key and api_key != 'your_api_key_here':
                # 只顯示前後各 4 個字元
                safe_config['redmine']['api_key'] = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        
        return safe_config
    
    except Exception as e:
        logger.error(f"取得設定失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法取得設定: {e}")


@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """更新設定"""
    try:
        config = load_config()
        
        # 更新各區塊
        if request.redmine is not None:
            if 'redmine' not in config:
                config['redmine'] = {}
            config['redmine'].update(request.redmine)
        
        if request.git is not None:
            if 'git' not in config:
                config['git'] = {}
            config['git'].update(request.git)
        
        if request.ai is not None:
            if 'ai' not in config:
                config['ai'] = {}
            config['ai'].update(request.ai)
        
        if request.claude is not None:
            # 向後相容：如果更新了舊的 claude 設定，也更新到新的 ai 結構
            if 'claude' not in config:
                config['claude'] = {}
            config['claude'].update(request.claude)
            
            # 同步到新的 ai 結構
            if 'ai' not in config:
                config['ai'] = {'provider': 'claude', 'claude': {}, 'gemini': {}}
            if 'claude' not in config['ai']:
                config['ai']['claude'] = {}
            config['ai']['claude'].update(request.claude)
        
        if request.repositories is not None:
            config['repositories'] = request.repositories
        
        if request.scan_paths is not None:
            config['scan_paths'] = request.scan_paths
        
        if request.default_time_range is not None:
            config['default_time_range'] = request.default_time_range
        
        if request.ui is not None:
            if 'ui' not in config:
                config['ui'] = {}
            config['ui'].update(request.ui)
        
        # 驗證設定
        is_valid, error_msg = validate_config(config)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 儲存設定
        save_config(config)
        
        return {"success": True, "message": "設定已更新"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新設定失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法更新設定: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
