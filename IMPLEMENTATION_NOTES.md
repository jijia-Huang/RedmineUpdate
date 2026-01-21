# 實作注意事項

## 重要：Commit 過濾邏輯

### 核心需求
**只分析當前使用者的 commit，而不是該時間範圍內所有的 commit。**

### 實作方式

#### 1. 取得當前使用者身份

**方式 A：從 Git 設定檔讀取（推薦）**
```python
import subprocess

def get_git_user():
    """從 Git 全域設定檔讀取使用者資訊"""
    try:
        name = subprocess.check_output(
            ['git', 'config', '--global', 'user.name'],
            text=True
        ).strip()
        email = subprocess.check_output(
            ['git', 'config', '--global', 'user.email'],
            text=True
        ).strip()
        return {'name': name, 'email': email}
    except subprocess.CalledProcessError:
        # 如果全域設定沒有，嘗試讀取本地設定
        try:
            name = subprocess.check_output(
                ['git', 'config', 'user.name'],
                text=True
            ).strip()
            email = subprocess.check_output(
                ['git', 'config', 'user.email'],
                text=True
            ).strip()
            return {'name': name, 'email': email}
        except subprocess.CalledProcessError:
            return None
```

**方式 B：從設定檔讀取**
```python
# 從 config.json 讀取
config = load_config()
git_user = config.get('git', {}).get('user', {})
if config.get('git', {}).get('auto_detect', True):
    git_user = get_git_user()  # 優先使用 Git 設定檔
```

#### 2. 過濾 Commit

使用 GitPython 取得 commit 後，過濾出當前使用者的：

```python
from git import Repo
from datetime import datetime

def get_user_commits(repo_path, branch, start_date, end_date, user_name, user_email):
    """取得指定時間範圍內當前使用者的 commit"""
    repo = Repo(repo_path)
    repo.git.checkout(branch)
    
    # 取得該時間範圍內的所有 commit
    commits = list(repo.iter_commits(
        branch,
        since=start_date,
        until=end_date
    ))
    
    # 過濾：只保留當前使用者的 commit
    user_commits = [
        commit for commit in commits
        if (commit.author.name == user_name or 
            commit.author.email == user_email)
    ]
    
    return user_commits
```

#### 3. 錯誤處理

**情況 1：找不到 Git 使用者設定**
```python
if not git_user:
    raise ValueError(
        "無法取得 Git 使用者資訊。請在設定頁設定，或執行：\n"
        "git config --global user.name '你的名稱'\n"
        "git config --global user.email '你的email'"
    )
```

**情況 2：該時間範圍內沒有當前使用者的 commit**
```python
if not user_commits:
    total_commits = len(commits)
    raise ValueError(
        f"該時間範圍內沒有你的 commit。\n"
        f"當前使用者：{user_name} ({user_email})\n"
        f"該時間範圍內共有 {total_commits} 個 commit（其他使用者的）\n"
        f"請檢查：\n"
        f"1. Git 使用者設定是否正確\n"
        f"2. 是否選擇了正確的時間範圍\n"
        f"3. 是否選擇了正確的分支"
    )
```

#### 4. API 端點實作

```python
@app.post("/api/analyze")
async def analyze_commits(request: AnalyzeRequest):
    # 取得當前使用者身份
    git_user = get_git_user()
    if not git_user:
        raise HTTPException(
            status_code=400,
            detail="無法取得 Git 使用者資訊，請先設定"
        )
    
    # 取得並過濾 commit
    user_commits = get_user_commits(
        repo_path=request.repository_path,
        branch=request.branch,
        start_date=request.start_date,
        end_date=request.end_date,
        user_name=git_user['name'],
        user_email=git_user['email']
    )
    
    if not user_commits:
        raise HTTPException(
            status_code=404,
            detail=f"該時間範圍內沒有你的 commit（{git_user['name']} / {git_user['email']}）"
        )
    
    # 繼續分析流程...
```

### 測試建議

1. **測試多使用者情境**：
   - 建立一個測試儲存庫
   - 用不同使用者身份建立多個 commit
   - 確認只會分析當前使用者的 commit

2. **測試邊界情況**：
   - 該時間範圍內完全沒有 commit
   - 該時間範圍內有其他使用者的 commit，但沒有當前使用者的
   - Git 使用者設定不存在

3. **測試使用者識別**：
   - 使用 name 匹配
   - 使用 email 匹配
   - name 和 email 都匹配

---

## 其他實作注意事項

### 1. 設定檔初始化

首次啟動時，如果 `git.auto_detect` 為 `true`，自動從 Git 設定檔讀取並儲存到 `config.json`。

### 2. UI 提示

在時間範圍選擇頁面，顯示：
- 當前使用的 Git 使用者身份
- 預覽時顯示「找到 X 個你的 commit」

### 3. 設定頁

提供：
- 開關「自動偵測 Git 使用者」
- 手動設定 Git 使用者名稱和 Email
- 顯示當前偵測到的使用者資訊

---

## 相關檔案

- `SPEC.md` - 規格文件（已更新）
- `design-system/UI_DESIGN.md` - UI 設計（已更新）
- `services/git_service.py` - Git 服務實作（待建立）
- `services/analyze_service.py` - 分析服務實作（待建立）
