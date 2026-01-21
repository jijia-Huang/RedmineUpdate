# Initial MVP Proposal

## Why
建立 Redmine 進度回報自動化工具的核心功能，讓工程師能夠自動化從 Git commit 分析到 Redmine 更新的完整流程，節省手動整理和回報的時間。

## What Changes
- **Redmine 整合**：連線 Redmine API，取得指派給當前使用者的工單列表，並支援更新 issue（Notes、% Done、Spent Time、Status）
- **Git 整合**：掃描本地 Git 儲存庫，選擇分支，取得指定時間範圍內的 commit（僅限當前使用者的 commit）
- **AI 分析**：整合 Claude Code CLI，分析 commit 內容並生成結構化的進度回報
- **Web 介面**：提供完整的 Web UI，包含工單列表、儲存庫選擇、時間範圍選擇、分析結果確認等頁面
- **設定管理**：支援 JSON 設定檔，管理 Redmine 連線資訊、Git 使用者設定、儲存庫書籤等

## Impact
- **新增能力**：建立 5 個核心能力模組（redmine-integration、git-integration、ai-analysis、web-ui、config-management）
- **受影響的程式碼**：
  - 新建 `services/` 目錄（redmine_service.py、git_service.py、analyze_service.py）
  - 新建 `app.py`（FastAPI 主應用）
  - 新建 `static/` 和 `templates/` 目錄（前端檔案）
  - 新建 `config.json`（設定檔範本）
  - 新建 `prompts/redmine_analysis.txt`（AI 分析系統提示詞）
