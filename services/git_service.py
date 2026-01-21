"""
Git 整合服務
處理 Git 儲存庫操作、分支管理和 commit 過濾
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from git import Repo, InvalidGitRepositoryError, GitCommandError
from git.exc import NoSuchPathError
import logging

logger = logging.getLogger(__name__)


class GitService:
    """Git 操作服務類別"""
    
    def __init__(self, user_name: str, user_email: str):
        """
        初始化 Git 服務
        
        Args:
            user_name: 當前使用者名稱（用於過濾 commit）
            user_email: 當前使用者 Email（用於過濾 commit）
        """
        self.user_name = user_name
        self.user_email = user_email

    @staticmethod
    def _safe_current_branch(repo: Repo) -> Optional[str]:
        """
        安全取得目前分支名稱。
        detached HEAD 時，repo.active_branch 會丟例外，這裡回傳 None。
        """
        try:
            if repo.head.is_valid():
                return repo.active_branch.name
        except TypeError:
            # detached HEAD
            return None
        except Exception:
            return None
        return None
    
    def scan_repositories(self, common_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        掃描本地 Git 儲存庫
        
        Args:
            common_paths: 要掃描的常用路徑列表（可選）
        
        Returns:
            找到的 Git 儲存庫列表
        """
        if common_paths is None:
            # 預設常用路徑
            common_paths = [
                str(Path.home() / "Projects"),
                "D:/Projects",
                "C:/Projects",
                str(Path.home() / "Documents" / "Projects"),
            ]
        
        # 性能優先：掃描階段只找「有 .git 目錄的資料夾」即可。
        # 不在掃描時初始化 Repo（GitPython 會較慢），分支等資訊延後到選擇 repo 時再載入。
        repositories: List[Dict[str, Any]] = []
        seen_repo_paths: set[str] = set()

        def depth_ok(root: str, current: str, max_depth: int) -> bool:
            try:
                rel = os.path.relpath(current, root)
                if rel in (".", ""):
                    return True
                depth = len([p for p in rel.split(os.sep) if p and p != "."])
                return depth <= max_depth
            except Exception:
                return True

        MAX_DEPTH = 6  # 避免掃到太深（可視需要調整）

        for base_path in common_paths:
            if not base_path:
                continue
            if not os.path.exists(base_path):
                continue

            base_path_str = str(Path(base_path).resolve())

            try:
                for root, dirs, _files in os.walk(base_path_str):
                    # 限制掃描深度
                    if not depth_ok(base_path_str, root, MAX_DEPTH):
                        dirs[:] = []
                        continue

                    # 避免掃描一些常見大型資料夾
                    dirs[:] = [d for d in dirs if d not in ("node_modules", ".venv", "venv", "__pycache__", ".git")]

                    git_dir = os.path.join(root, ".git")
                    if os.path.isdir(git_dir):
                        repo_path = root
                        if repo_path not in seen_repo_paths:
                            repositories.append(
                                {
                                    "path": repo_path,
                                    "name": os.path.basename(repo_path),
                                    "current_branch": None,  # 延後到 get_branches 時再看
                                }
                            )
                            seen_repo_paths.add(repo_path)

                        # 找到 repo 後不需要再深入該 repo
                        dirs[:] = []
            except Exception as e:
                logger.warning(f"掃描路徑 {base_path_str} 時發生錯誤: {e}")
                continue

        return repositories
    
    def validate_repository(self, repo_path: str) -> bool:
        """
        驗證路徑是否為有效的 Git 儲存庫
        
        Args:
            repo_path: 儲存庫路徑
        
        Returns:
            是否為有效的 Git 儲存庫
        """
        try:
            repo = Repo(repo_path)
            return not repo.bare
        except (InvalidGitRepositoryError, NoSuchPathError, GitCommandError):
            return False
    
    def get_branches(self, repo_path: str) -> List[Dict[str, Any]]:
        """
        取得儲存庫的所有分支
        
        Args:
            repo_path: 儲存庫路徑
        
        Returns:
            分支列表，包含當前分支標記
        """
        try:
            repo = Repo(repo_path)
            branches = []
            current_branch = self._safe_current_branch(repo)
            
            for branch in repo.branches:
                branches.append({
                    'name': branch.name,
                    'is_current': branch.name == current_branch,
                    # 計算 commit_count 會很慢（會列舉整個分支歷史），先不做
                    'commit_count': None
                })
            
            return branches
        except InvalidGitRepositoryError:
            raise ValueError(f"無效的 Git 儲存庫: {repo_path}")
        except Exception as e:
            logger.error(f"取得分支列表失敗: {e}")
            raise ValueError(f"無法取得分支列表: {e}")
    
    def get_user_commits(
        self,
        repo_path: str,
        branch: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        取得指定時間範圍內當前使用者的 commit
        
        Args:
            repo_path: 儲存庫路徑
            branch: 分支名稱
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            過濾後的 commit 列表（僅包含當前使用者的 commit）
        
        Raises:
            ValueError: 如果沒有找到當前使用者的 commit 或發生其他錯誤
        """
        try:
            repo = Repo(repo_path)
            
            # 切換到指定分支
            try:
                repo.git.checkout(branch)
            except GitCommandError as e:
                raise ValueError(f"無法切換到分支 {branch}: {e}")
            
            # 取得該時間範圍內的所有 commit
            all_commits = list(repo.iter_commits(
                branch,
                since=start_date,
                until=end_date
            ))
            
            if not all_commits:
                raise ValueError(
                    f"在 {start_date.date()} 至 {end_date.date()} 的時間範圍內沒有找到任何 commit。\n"
                    f"請檢查時間範圍或分支選擇。"
                )
            
            # 過濾：只保留當前使用者的 commit
            user_commits = []
            for commit in all_commits:
                author_name = commit.author.name
                author_email = commit.author.email
                
                if (author_name == self.user_name or author_email == self.user_email):
                    # 計算檔案變更
                    files_changed = {
                        'added': 0,
                        'modified': 0,
                        'deleted': 0
                    }
                    
                    try:
                        if commit.parents:
                            diff = commit.diff(commit.parents[0])
                            for item in diff:
                                if item.new_file:
                                    files_changed['added'] += 1
                                elif item.deleted_file:
                                    files_changed['deleted'] += 1
                                else:
                                    files_changed['modified'] += 1
                    except Exception:
                        # 如果無法計算 diff，跳過
                        pass
                    
                    user_commits.append({
                        'hash': commit.hexsha[:8],
                        'full_hash': commit.hexsha,
                        'author': {
                            'name': author_name,
                            'email': author_email
                        },
                        'date': commit.committed_datetime.isoformat(),
                        'message': commit.message.strip(),
                        'files_changed': files_changed
                    })
            
            if not user_commits:
                total_count = len(all_commits)
                raise ValueError(
                    f"在 {start_date.date()} 至 {end_date.date()} 的時間範圍內沒有找到你的 commit。\n"
                    f"當前使用者：{self.user_name} ({self.user_email})\n"
                    f"該時間範圍內共有 {total_count} 個 commit（其他使用者的）\n"
                    f"請檢查：\n"
                    f"1. Git 使用者設定是否正確\n"
                    f"2. 是否選擇了正確的時間範圍\n"
                    f"3. 是否選擇了正確的分支"
                )
            
            return user_commits
            
        except InvalidGitRepositoryError:
            raise ValueError(f"無效的 Git 儲存庫: {repo_path}")
        except ValueError:
            # 重新拋出我們自己的 ValueError
            raise
        except Exception as e:
            logger.error(f"取得 commit 失敗: {e}")
            raise ValueError(f"無法取得 commit: {e}")
