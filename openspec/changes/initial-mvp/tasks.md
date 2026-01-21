# Implementation Tasks

## 1. 設定管理基礎設施
- [x] 1.1 建立 `config.json` 設定檔範本
- [x] 1.2 實作設定檔讀取/寫入功能（`utils/config.py`）
- [x] 1.3 實作 Git 使用者設定自動偵測功能
- [x] 1.4 建立設定驗證邏輯（檢查必要欄位）

## 2. Redmine 整合服務
- [x] 2.1 安裝並設定 `python-redmine` 套件（已加入 requirements.txt）
- [x] 2.2 實作 `services/redmine_service.py`：連線 Redmine API
- [x] 2.3 實作取得指派工單列表功能
- [x] 2.4 實作更新 issue 功能（Notes、% Done、Spent Time、Status）
- [x] 2.5 實作錯誤處理（連線失敗、權限不足等）

## 3. Git 整合服務
- [x] 3.1 安裝並設定 `GitPython` 套件（已加入 requirements.txt）
- [x] 3.2 實作 `services/git_service.py`：Git 儲存庫操作
- [x] 3.3 實作掃描本地 Git 儲存庫功能
- [x] 3.4 實作取得分支列表功能
- [x] 3.5 實作取得指定時間範圍內 commit 的功能
- [x] 3.6 實作 commit 過濾邏輯（只保留當前使用者的 commit）
- [x] 3.7 實作錯誤處理（無效儲存庫、無 commit 等）

## 4. AI 分析服務
- [x] 4.1 建立 `prompts/redmine_analysis.txt` 系統提示詞檔案
- [x] 4.2 實作 `services/analyze_service.py`：Claude CLI 整合
- [x] 4.3 實作 commit 資料格式化（準備給 Claude CLI 的輸入）
- [x] 4.4 實作透過 subprocess 執行 Claude CLI
- [x] 4.5 實作 JSON 輸出解析
- [x] 4.6 實作錯誤處理（CLI 未安裝、執行失敗、超時等）

## 5. FastAPI 後端
- [x] 5.1 建立 `app.py`（FastAPI 主應用）
- [x] 5.2 實作 API 端點：`GET /api/issues`（取得工單列表）
- [x] 5.3 實作 API 端點：`GET /api/repositories`（取得儲存庫列表）
- [x] 5.4 實作 API 端點：`GET /api/repositories/{path}/branches`（取得分支列表）
- [x] 5.5 實作 API 端點：`POST /api/analyze`（分析 commit）
- [x] 5.6 實作 API 端點：`POST /api/update-redmine`（更新 Redmine）
- [x] 5.7 實作 API 端點：`GET /api/config` 和 `POST /api/config`（設定管理）
- [x] 5.8 實作 CORS 設定（允許前端跨域請求）
- [x] 5.9 實作錯誤處理中介軟體

## 6. Web 前端
- [x] 6.1 建立 `templates/index.html`（主頁面）
- [x] 6.2 建立 `static/css/` 和 `static/js/` 目錄
- [x] 6.3 實作工單列表頁面（顯示、篩選、搜尋）
- [x] 6.4 實作儲存庫選擇頁面（選擇儲存庫和分支）
- [x] 6.5 實作時間範圍選擇頁面（預設選項、自訂範圍）
- [x] 6.6 實作分析中頁面（進度顯示）
- [x] 6.7 實作結果確認頁面（顯示 AI 分析結果、可編輯欄位）
- [x] 6.8 實作更新結果頁面（成功/失敗訊息）
- [x] 6.9 實作設定頁面（Redmine 設定、Git 設定）
- [x] 6.10 整合 Tailwind CSS（透過 CDN）
- [x] 6.11 實作前端 JavaScript（API 呼叫、狀態管理、錯誤處理）

## 7. 測試與驗證
- [ ] 7.1 測試 commit 過濾邏輯（多使用者情境）
- [ ] 7.2 測試邊界情況（無 commit、無當前使用者 commit、Git 設定不存在）
- [ ] 7.3 測試 Redmine API 連線與錯誤處理
- [ ] 7.4 測試 Claude CLI 整合與錯誤處理
- [ ] 7.5 端對端測試完整流程（從工單選擇到 Redmine 更新）

## 8. 文件與部署
- [x] 8.1 建立 `requirements.txt`（Python 依賴）
- [x] 8.2 建立 `README.md`（使用說明、安裝步驟）
- [x] 8.3 建立 `.gitignore`（排除設定檔、暫存檔案）
- [ ] 8.4 驗證 Conda 環境 `GPTAction` 設定
