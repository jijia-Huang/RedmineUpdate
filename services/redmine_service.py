"""
Redmine API 整合服務
處理 Redmine 連線、工單查詢和更新
"""
from typing import List, Dict, Any, Optional
from redminelib import Redmine
from redminelib.exceptions import ResourceNotFoundError, ValidationError, AuthError
import logging

logger = logging.getLogger(__name__)


class RedmineService:
    """Redmine API 服務類別"""
    
    def __init__(self, url: str, api_key: str, user_id: Optional[int] = None):
        """
        初始化 Redmine 服務
        
        Args:
            url: Redmine 伺服器 URL
            api_key: Redmine API Key
            user_id: 當前使用者 ID（可選，用於過濾指派工單）
        """
        self.url = url
        self.api_key = api_key
        self.user_id = user_id
        self.redmine = None
        self._connect()
    
    def _connect(self) -> None:
        """連線到 Redmine API"""
        try:
            self.redmine = Redmine(self.url, key=self.api_key)
            # 測試連線：取得當前使用者資訊
            self.redmine.auth()
            logger.info(f"成功連線到 Redmine: {self.url}")
        except AuthError as e:
            raise ValueError(f"Redmine 認證失敗: {e}")
        except Exception as e:
            raise ValueError(f"無法連線到 Redmine: {e}")
    
    def get_assigned_issues(self, status_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        取得指派給當前使用者的工單列表
        
        Args:
            status_id: 狀態 ID 過濾（可選）
            search: 搜尋關鍵字（可選）
        
        Returns:
            工單列表
        """
        try:
            # 建立查詢條件
            filters = {'assigned_to_id': 'me'}
            if status_id:
                filters['status_id'] = status_id
            
            issues = self.redmine.issue.filter(**filters)
            
            # 如果提供搜尋關鍵字，進行過濾
            if search:
                search_lower = search.lower()
                issues = [
                    issue for issue in issues
                    if search_lower in str(issue.subject).lower() or
                       search_lower in str(issue.id)
                ]
            
            # 格式化工單資料
            result = []
            for issue in issues:
                result.append({
                    'id': issue.id,
                    'subject': issue.subject,
                    'status': {
                        'id': issue.status.id,
                        'name': issue.status.name
                    },
                    'priority': {
                        'id': issue.priority.id,
                        'name': issue.priority.name
                    } if hasattr(issue, 'priority') and issue.priority else None,
                    'assigned_to': {
                        'id': issue.assigned_to.id,
                        'name': issue.assigned_to.name
                    } if hasattr(issue, 'assigned_to') and issue.assigned_to else None,
                    'done_ratio': issue.done_ratio,
                    'spent_hours': getattr(issue, 'spent_hours', 0.0),
                    'created_on': issue.created_on.isoformat() if hasattr(issue.created_on, 'isoformat') else str(issue.created_on),
                    'updated_on': issue.updated_on.isoformat() if hasattr(issue.updated_on, 'isoformat') else str(issue.updated_on),
                })
            
            return result
        except Exception as e:
            logger.error(f"取得工單列表失敗: {e}")
            raise ValueError(f"無法取得工單列表: {e}")
    
    def update_issue(
        self,
        issue_id: int,
        notes: Optional[str] = None,
        percent_done: Optional[int] = None,
        spent_time: Optional[float] = None,
        status_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        更新 Redmine issue
        
        Args:
            issue_id: Issue ID
            notes: 備註內容
            percent_done: 完成百分比 (0-100)
            spent_time: 已花費工時（小時）
            status_id: 狀態 ID
        
        Returns:
            更新結果，包含成功/失敗的欄位資訊
        """
        result = {
            'success': True,
            'updated_fields': [],
            'failed_fields': [],
            'errors': []
        }
        
        try:
            issue = self.redmine.issue.get(issue_id)
            update_data = {}
            
            # 更新備註
            if notes:
                try:
                    # 將換行符號轉換為 HTML <br> 標籤，以便在 Redmine 中正確顯示換行
                    notes_html = notes.replace('\r\n', '<br>').replace('\n', '<br>').replace('\r', '<br>')
                    issue.notes = notes_html
                    update_data['notes'] = notes_html
                    result['updated_fields'].append('notes')
                except Exception as e:
                    result['failed_fields'].append('notes')
                    result['errors'].append(f"更新備註失敗: {e}")
            
            # 更新完成百分比
            if percent_done is not None:
                try:
                    issue.done_ratio = percent_done
                    update_data['done_ratio'] = percent_done
                    result['updated_fields'].append('percent_done')
                except Exception as e:
                    result['failed_fields'].append('percent_done')
                    result['errors'].append(f"更新完成百分比失敗: {e}")
            
            # 更新狀態
            if status_id is not None:
                try:
                    issue.status_id = status_id
                    update_data['status_id'] = status_id
                    result['updated_fields'].append('status')
                except Exception as e:
                    result['failed_fields'].append('status')
                    result['errors'].append(f"更新狀態失敗: {e}")
            
            # 儲存更新
            if update_data:
                issue.save()
            
            # 更新工時
            if spent_time is not None and spent_time > 0:
                try:
                    time_entry = self.redmine.time_entry.create(
                        issue_id=issue_id,
                        hours=spent_time,
                        activity_id=9  # 預設活動 ID，可能需要根據實際情況調整
                    )
                    result['updated_fields'].append('spent_time')
                except Exception as e:
                    result['failed_fields'].append('spent_time')
                    result['errors'].append(f"更新工時失敗: {e}")
            
            # 如果有任何失敗的欄位，標記為部分成功
            if result['failed_fields']:
                result['success'] = False
            
            return result
            
        except ResourceNotFoundError:
            raise ValueError(f"Issue #{issue_id} 不存在")
        except ValidationError as e:
            raise ValueError(f"更新驗證失敗: {e}")
        except Exception as e:
            logger.error(f"更新 Issue #{issue_id} 失敗: {e}")
            raise ValueError(f"無法更新 Issue: {e}")
