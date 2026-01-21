# Redmine 進度回報自動化工具

自動化 Redmine 進度回報流程的工具，透過分析 Git commit 記錄並使用 AI 生成結構化的進度回報。

## 功能特色

- 🔍 **自動取得工單列表**：從 Redmine 取得指派給你的工單
- 📦 **Git 儲存庫整合**：自動掃描本地 Git 儲存庫並選擇分支
- 🎯 **智能 Commit 過濾**：只分析當前使用者的 commit（核心功能）
- 🤖 **AI 分析**：使用 Claude Code CLI 分析 commit 並生成進度回報
- ✏️ **可編輯回報**：在更新到 Redmine 前可編輯 AI 生成的內容
- 🔄 **自動更新**：一鍵更新 Redmine issue（Notes、% Done、Spent Time、Status）

## 技術堆疊

- **後端**：Python 3.9+、FastAPI
- **前端**：HTML、JavaScript、Tailwind CSS
- **依賴**：
  - `python-redmine`：Redmine API 整合
  - `GitPython`：Git 操作
  - `Claude Code CLI`：AI 分析

## 安裝步驟

### 1. 環境準備

確保已安裝：
- Python 3.9+
- Conda（用於管理 `GPTAction` 環境）
- Git
- Claude Code CLI（已安裝並登入）

### 2. 設定 Conda 環境

```bash
# 啟動 Conda 環境 GPTAction
conda activate GPTAction
```

### 3. 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

### 4. 設定 Redmine

編輯 `config.json`，設定 Redmine 連線資訊：

```json
{
  "redmine": {
    "url": "https://your-redmine.example.com",
    "api_key": "your_api_key_here",
    "user_id": null
  }
}
```

### 5. 設定 Git 使用者（可選）

如果未啟用自動偵測，在 `config.json` 中設定：

```json
{
  "git": {
    "user": {
      "name": "你的名稱",
      "email": "your.email@example.com"
    },
    "auto_detect": false
  }
}
```

或使用 Git 全域設定（推薦）：

```bash
git config --global user.name "你的名稱"
git config --global user.email "your.email@example.com"
```

## 使用方式

### 啟動應用

```bash
# 在 Conda 環境 GPTAction 中執行
python app.py
```

或使用 uvicorn：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 開啟瀏覽器

訪問 `http://localhost:8000`

### 使用流程

1. **選擇工單**：從列表選擇要回報的 Redmine issue
2. **選擇儲存庫**：選擇本地 Git 儲存庫和分支
3. **選擇時間範圍**：選擇要分析的 commit 時間範圍（今天、昨天、本週、上週或自訂）
4. **AI 分析**：系統會自動分析你的 commit 並生成進度回報
5. **確認編輯**：檢視並編輯 AI 生成的內容
6. **更新 Redmine**：確認後自動更新到 Redmine

## 重要說明

### Commit 過濾

**核心功能**：系統只會分析**當前使用者**的 commit，不會包含其他使用者的 commit。

過濾條件：
- 使用 Git 設定檔中的 `user.name` 或 `user.email` 進行匹配
- 如果設定檔中沒有，會使用 `config.json` 中的設定

### Claude CLI 需求

- 必須已安裝 Claude Code CLI
- 必須已登入 Claude CLI
- CLI 必須在系統 PATH 中（或設定 `config.json` 中的 `claude.cli_path`）

## 設定檔說明

`config.json` 結構：

```json
{
  "redmine": {
    "url": "Redmine 伺服器 URL",
    "api_key": "Redmine API Key",
    "user_id": null
  },
  "git": {
    "user": {
      "name": "Git 使用者名稱",
      "email": "Git Email"
    },
    "auto_detect": true
  },
  "claude": {
    "use_cli": true,
    "cli_path": "claude",
    "timeout": 60,
    "output_format": "json",
    "system_prompt_file": "prompts/redmine_analysis.txt"
  },
  "repositories": [],
  "default_time_range": "本週",
  "ui": {
    "theme": "light",
    "language": "zh-TW"
  }
}
```

## 故障排除

### Redmine 連線失敗

- 檢查 Redmine URL 是否正確
- 確認 API Key 是否有效
- 檢查網路連線

### Git 儲存庫無法找到

- 確認儲存庫路徑正確
- 確認該路徑是有效的 Git 儲存庫
- 可以在設定頁面手動新增儲存庫路徑

### 沒有找到你的 commit

- 檢查 Git 使用者設定是否正確（`git config --global user.name` 和 `user.email`）
- 確認選擇的時間範圍內確實有你的 commit
- 確認選擇了正確的分支

### Claude CLI 執行失敗

- 確認 Claude CLI 已安裝：`claude --version`
- 確認已登入：`claude auth status`
- 檢查 `config.json` 中的 `claude.cli_path` 設定

## 開發

### 專案結構

```
.
├── app.py                 # FastAPI 主應用
├── config.json            # 設定檔
├── requirements.txt       # Python 依賴
├── services/              # 服務層
│   ├── redmine_service.py
│   ├── git_service.py
│   └── analyze_service.py
├── utils/                  # 工具函數
│   └── config.py
├── templates/              # HTML 模板
│   └── index.html
├── static/                 # 靜態檔案
│   ├── css/
│   └── js/
│       └── app.js
└── prompts/                # AI 提示詞
    └── redmine_analysis.txt
```

## 授權

MIT License

## 相關資源

- [Redmine REST API 文件](https://www.redmine.org/projects/redmine/wiki/Rest_api)
- [python-redmine 文件](https://python-redmine.com/)
- [GitPython 文件](https://gitpython.readthedocs.io/)
