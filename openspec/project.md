# Project Context

## Purpose
Redmine 進度回報自動化工具，讓工程師可以：
- 快速查看 Redmine 上指派給自己的工單
- 選擇本地 Git 儲存庫和分支
- 自動分析指定時段的 commit 記錄（僅限當前使用者的 commit）
- 使用 AI（Claude Code CLI）分析 commit 內容並生成進度回報
- 確認後自動更新到 Redmine

核心價值：節省時間、減少遺漏、提升回報品質。

## Tech Stack
- **後端**：
  - Python 3.9+（使用 Conda 環境 `GPTAction`）
  - FastAPI（Web 框架）
  - GitPython（Git 操作）
  - python-redmine（Redmine API 整合）
  - Claude Code CLI（透過 subprocess 執行，分析 commit）
- **前端**：
  - HTML/JavaScript（純前端，無框架）
  - Tailwind CSS（樣式框架，透過 CDN）
- **資料儲存**：
  - JSON/YAML（設定檔：Redmine URL、API Key、儲存庫書籤等）
  - SQLite（可選，記錄歷史操作）

## Project Conventions

### Code Style
- **語言**：Python 3.9+，使用 Conda 環境 `GPTAction`
- **命名**：使用 snake_case（Python）、camelCase（JavaScript）
- **註解與文件**：使用繁體中文撰寫註解、文件、UI 文字
- **格式化**：遵循 PEP 8（Python）、使用標準 JavaScript 風格
- **字串**：UI 和文件使用繁體中文

### Architecture Patterns
- **前後端分離**：FastAPI 提供 RESTful API，前端透過 AJAX 呼叫
- **服務層架構**：
  - `services/redmine_service.py` - Redmine API 操作
  - `services/git_service.py` - Git 操作與 commit 過濾
  - `services/analyze_service.py` - AI 分析服務
- **設定管理**：使用 JSON 設定檔（`config.json`），支援自動偵測 Git 使用者設定
- **錯誤處理**：明確的錯誤訊息，提供重試機制

### Testing Strategy
- **測試範圍**：重點測試 commit 過濾邏輯（確保只分析當前使用者的 commit）
- **邊界情況**：
  - 該時間範圍內沒有 commit
  - 該時間範圍內沒有當前使用者的 commit
  - Git 使用者設定不存在
  - Redmine API 連線失敗
  - Claude CLI 執行失敗

### Git Workflow
- **Commit 訊息**：建議包含 issue ID（如 `#1234`），方便關聯
- **分支策略**：功能開發使用 feature 分支
- **重要**：只分析當前使用者的 commit（透過 `author.name` 或 `author.email` 過濾）

## Domain Context
- **Redmine**：專案管理系統，使用 REST API 進行操作
- **Git Commit 分析**：只分析指定時間範圍內「當前使用者」的 commit，過濾其他作者的 commit
- **使用者識別**：從 Git 設定檔（`git config --global user.name` 和 `user.email`）或設定檔讀取
- **AI 分析流程**：
  1. 收集當前使用者的 commit（訊息、檔案變更摘要）
  2. 透過 Claude Code CLI 分析（使用 stdin pipe + JSON 輸出）
  3. 生成結構化的進度回報（summary、completed_items、technical_details、blockers、next_steps、estimated_hours、suggested_percent_done）
  4. 使用者確認/編輯後更新到 Redmine

## Important Constraints
- **Python 環境**：必須使用 Conda 環境 `GPTAction`
- **Commit 過濾**：核心需求是只分析當前使用者的 commit，不是該時間範圍內所有的 commit
- **Claude CLI**：需要已安裝並登入 Claude Code CLI
- **Redmine API**：需要有效的 API Key 和適當的權限
- **Git 設定**：需要正確的 Git 使用者設定（name 和 email）才能正確過濾 commit

## External Dependencies
- **Redmine API**：透過 `python-redmine` 套件整合
  - 端點：取得工單列表、更新 issue（Notes、% Done、Spent Time、Status）
  - 認證：API Key
- **Claude Code CLI**：透過 subprocess 執行
  - 使用方式：`echo "{commit_data_json}" | claude -p "..." --output-format json --system-prompt-file prompts/redmine_analysis.txt`
  - 系統提示詞：儲存在 `prompts/redmine_analysis.txt`
  - 輸出格式：JSON
- **本地 Git 儲存庫**：透過 GitPython 操作
  - 支援本地分支和遠端分支（需先 fetch）
  - 自動掃描常用位置（如 `~/Projects`, `D:/Projects`）
  - 支援書籤功能（儲存常用儲存庫路徑）
