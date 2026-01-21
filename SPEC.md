# Redmine 進度回報自動化工具 - 規格文件

## 1. 專案概述

### 1.1 目標
建立一個工具，讓工程師可以：
- 快速查看 Redmine 上指派給自己的工單
- 選擇本地 Git 儲存庫和分支
- 自動分析指定時段的 commit 記錄
- 使用 AI（Claude Code）分析 commit 內容並生成進度回報
- 確認後自動更新到 Redmine

### 1.2 核心價值
- **節省時間**：從手動整理 commit → 自動分析生成回報
- **減少遺漏**：系統化追蹤，不會漏掉該回報的工單
- **提升品質**：AI 分析讓回報內容更完整、結構化

---

## 2. 功能需求

### 2.1 功能模組

#### 模組 A：Redmine 工單列表
**功能描述**：
- 從 Redmine API 取得「指派給當前使用者」的工單
- 顯示工單基本資訊（編號、標題、狀態、優先級、到期日等）
- 支援篩選（進行中、待處理、已解決等）
- 支援搜尋

**顯示欄位**：
- Issue ID（可點擊）
- 標題
- 狀態（Status）
- 優先級（Priority）
- 指派日期
- 最後更新時間
- 進度百分比（% Done）
- 已記錄工時（Spent Time）

**操作**：
- 點擊工單 → 進入「Commit 分析流程」

---

#### 模組 B：Git 儲存庫選擇
**功能描述**：
- 顯示本地可用的 Git 儲存庫列表
- 可手動新增/移除儲存庫路徑（支援書籤功能）
- 選擇儲存庫後，顯示該儲存庫的所有分支
- 可選擇要分析的分支

**儲存庫管理**：
- 掃描常用位置（如 `~/Projects`, `D:/Projects` 等）
- 手動新增路徑
- 儲存書籤（下次開啟自動載入）

**分支選擇**：
- 顯示所有本地分支
- 顯示當前分支（標記）
- 可選擇遠端分支（需先 fetch）

---

#### 模組 C：時間範圍選擇
**功能描述**：
- 選擇要分析的 commit 時間範圍
- 預設選項：
  - 今天
  - 昨天
  - 本週
  - 上週
  - 自訂日期範圍
- 顯示該時間範圍內的 commit 數量預覽

---

#### 模組 D：Commit 分析（AI 分析）
**功能描述**：
- **重要**：只取得指定時間範圍內「當前使用者」的 commit 列表（過濾其他作者的 commit）
- 將 commit 訊息、檔案變更、diff 等資訊整理後
- 呼叫 Claude Code CLI 進行分析
- 生成結構化的進度回報內容

**使用者識別方式**：
- 從 Git 設定檔讀取 `user.name` 和 `user.email`
- 或從 Redmine 使用者資訊取得對應的 Git 身份
- 過濾條件：commit 的 `author.name` 或 `author.email` 匹配當前使用者

**分析輸入**：
- Commit 列表（hash, author, date, message）- **僅包含當前使用者的 commit**
- 檔案變更摘要（新增/修改/刪除的檔案數）
- 關鍵檔案路徑（可選）
- 相關的 Redmine issue ID（從 commit message 中提取）

**過濾邏輯**：
```python
# 取得當前使用者的 Git 身份
current_user_name = git_config.get('user.name')
current_user_email = git_config.get('user.email')

# 過濾 commit：只保留當前使用者的
filtered_commits = [
    commit for commit in all_commits
    if (commit.author.name == current_user_name or 
        commit.author.email == current_user_email)
]
```

**AI 分析方式**：
使用 Claude Code CLI 進行分析，透過 stdin pipe 傳入 commit 資料。

**系統提示詞（System Prompt）**：
儲存在 `prompts/redmine_analysis.txt`，內容如下：
```
你是一位專業的工程師，請分析以下 commit 記錄，並生成一份 Redmine 進度回報。

**重要**：請以 JSON 格式輸出，格式如下：
{
  "summary": "摘要",
  "completed_items": ["項目1", "項目2"],
  "technical_details": ["細節1"],
  "blockers": [],
  "next_steps": ["下一步1"],
  "estimated_hours": 8.5,
  "suggested_percent_done": 75
}

工單資訊：
- Issue ID: #{issue_id}
- 標題: {issue_title}

Commit 記錄（{start_date} 至 {end_date}）：
{commit_list}

請分析並輸出 JSON。回報語言：繁體中文，風格：專業、簡潔、技術導向。
```

**CLI 執行方式**：
```bash
echo "{commit_data_json}" | claude -p "請分析這些 commit 記錄並生成 Redmine 進度回報" --output-format json --system-prompt-file prompts/redmine_analysis.txt
```

**分析輸出格式**：
```json
{
  "summary": "本週完成的主要工作摘要",
  "completed_items": [
    "完成功能 A 的實作",
    "修復 bug #123",
    "重構模組 X 的程式碼"
  ],
  "technical_details": [
    "使用新的 API 架構",
    "優化資料庫查詢效能"
  ],
  "blockers": [
    "等待第三方 API 回應"
  ],
  "next_steps": [
    "進行單元測試",
    "準備 code review"
  ],
  "estimated_hours": 8.5,
  "suggested_percent_done": 75
}
```

---

#### 模組 E：回報確認與編輯
**功能描述**：
- 顯示 AI 生成的進度回報內容
- 提供編輯介面讓使用者微調
- 顯示建議的 Redmine 欄位更新值

**顯示內容**：
- **Notes（回報內容）**：可編輯的文字區塊
- **% Done**：進度百分比（可調整）
- **Spent Time**：建議工時（可調整）
- **Status**：建議狀態（可選擇：進行中、待測試、待審核等）
- **相關 Commit 列表**：顯示被分析的 commit（僅供參考）

**操作**：
- 編輯回報內容
- 調整數值欄位
- 預覽更新後的 Redmine 內容
- 確認送出 / 取消

---

#### 模組 F：Redmine 自動更新
**功能描述**：
- 將確認後的內容透過 Redmine API 更新到對應的 issue
- 更新欄位：
  - Notes（新增一筆記錄）
  - % Done
  - Spent Time（新增一筆工時記錄）
  - Status（可選）
- 顯示更新結果（成功/失敗）

**錯誤處理**：
- API 連線失敗 → 提示重試
- 權限不足 → 提示錯誤訊息
- 部分欄位更新失敗 → 顯示哪些成功、哪些失敗

---

## 3. 技術架構

### 3.1 技術棧建議

**前端（UI）**：
- **選項 A**：Web 應用（Flask/FastAPI + HTML/JS）
  - 優點：跨平台、易於部署、UI 彈性大
  - 缺點：需要瀏覽器
  
- **選項 B**：桌面應用（Tkinter/PyQt/Electron）
  - 優點：原生體驗、可整合系統功能
  - 缺點：開發複雜度較高

- **選項 C**：CLI + 互動式選單（Rich/Terminal UI）
  - 優點：輕量、快速、適合工程師
  - 缺點：UI 較簡陋

**建議**：先做 **Web 應用（FastAPI）**，之後可考慮打包成桌面應用。

**後端（核心邏輯）**：
- Python 3.9+（使用 Conda 環境 `GPTAction`）
- FastAPI（Web 框架）
- GitPython（Git 操作）
- python-redmine（Redmine API）
- Claude Code CLI（透過 subprocess 執行，分析 commit）

**資料儲存**：
- 設定檔：JSON/YAML（儲存 Redmine URL、API Key、儲存庫書籤等）
- 暫存資料：SQLite（可選，記錄歷史操作）

---

### 3.2 系統架構圖

```
┌─────────────────────────────────────────┐
│          使用者介面（Web UI）            │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ 工單列表 │  │ 儲存庫選  │  │ 確認 │ │
│  │          │  │ 擇/分支  │  │ 編輯 │ │
│  └──────────┘  └──────────┘  └──────┘ │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         FastAPI 後端服務                │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Redmine  │  │   Git    │  │  AI  │ │
│  │  Service │  │  Service │  │Analyzer││
│  └──────────┘  └──────────┘  └──────┘ │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Redmine │ │  Local  │ │ Claude  │
   │   API   │ │   Git   │ │   CLI   │
   └─────────┘ └─────────┘ └─────────┘
```

---

## 4. UI/UX 流程

### 4.1 主要流程

```
1. 啟動應用
   ↓
2. 顯示「我的工單列表」
   - 從 Redmine 載入
   - 顯示載入中狀態
   ↓
3. 使用者點擊某個工單
   ↓
4. 顯示「選擇儲存庫」頁面
   - 選擇本地 Git 儲存庫
   - 選擇分支
   ↓
5. 顯示「選擇時間範圍」頁面
   - 選擇要分析的 commit 時間範圍
   ↓
6. 顯示「分析中...」頁面
   - 進度條
   - 顯示正在分析的 commit 數量
   ↓
7. 顯示「AI 分析結果」頁面
   - 顯示生成的回報內容
   - 可編輯欄位
   - 顯示相關 commit 列表
   ↓
8. 使用者確認/微調
   ↓
9. 顯示「更新中...」狀態
   ↓
10. 顯示「更新成功/失敗」結果
    - 成功：顯示更新後的 Redmine issue 連結
    - 失敗：顯示錯誤訊息，提供重試選項
```

### 4.2 頁面設計（Mockup 概念）

**頁面 1：工單列表**
```
┌─────────────────────────────────────────┐
│  Redmine 進度回報工具                    │
├─────────────────────────────────────────┤
│  [重新整理]  [設定]                      │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ #1234 實作使用者登入功能            │ │
│  │ 狀態：進行中 | 進度：60% | 8小時   │ │
│  │ [選擇此工單]                       │ │
│  └───────────────────────────────────┘ │
│  ┌───────────────────────────────────┐ │
│  │ #1235 修復 API 回應錯誤            │ │
│  │ 狀態：待處理 | 進度：0% | 0小時   │ │
│  │ [選擇此工單]                       │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**頁面 2：儲存庫選擇**
```
┌─────────────────────────────────────────┐
│  選擇 Git 儲存庫和分支                   │
├─────────────────────────────────────────┤
│  儲存庫：                                │
│  [▼] D:/Projects/my-project             │
│      [新增儲存庫...]                     │
│                                         │
│  分支：                                  │
│  ○ main (當前)                          │
│  ○ feature/user-login                   │
│  ○ bugfix/api-error                     │
│                                         │
│  [上一步]  [下一步：選擇時間範圍]        │
└─────────────────────────────────────────┘
```

**頁面 3：時間範圍選擇**
```
┌─────────────────────────────────────────┐
│  選擇要分析的 Commit 時間範圍            │
├─────────────────────────────────────────┤
│  ○ 今天                                 │
│  ○ 昨天                                 │
│  ● 本週                                 │
│  ○ 上週                                 │
│  ○ 自訂：2026-01-15 至 2026-01-21      │
│                                         │
│  預覽：找到 12 個 commit                │
│                                         │
│  [上一步]  [開始分析]                    │
└─────────────────────────────────────────┘
```

**頁面 4：分析結果確認**
```
┌─────────────────────────────────────────┐
│  AI 分析結果 - 請確認並微調              │
├─────────────────────────────────────────┤
│  回報內容（Notes）：                     │
│  ┌───────────────────────────────────┐ │
│  │ 本週完成的主要工作：                │ │
│  │ • 完成使用者登入功能的後端 API      │ │
│  │ • 實作 JWT token 驗證機制          │ │
│  │ • 修復密碼加密的 bug               │ │
│  │                                    │ │
│  │ 技術細節：                          │ │
│  │ • 使用 bcrypt 進行密碼雜湊         │ │
│  │ • 整合 Redis 做 session 管理       │ │
│  └───────────────────────────────────┘ │
│                                         │
│  進度百分比： [75] %                     │
│  工時： [8.5] 小時                       │
│  狀態： [進行中 ▼]                      │
│                                         │
│  相關 Commit（12 個）：                 │
│  • abc123 - feat: 實作登入 API          │
│  • def456 - fix: 修復密碼加密問題       │
│  • ...                                  │
│                                         │
│  [上一步]  [確認並更新到 Redmine]        │
└─────────────────────────────────────────┘
```

---

## 5. 資料流設計

### 5.1 API 端點設計

```
GET  /api/issues                    # 取得我的工單列表
GET  /api/repositories              # 取得本地儲存庫列表
GET  /api/repositories/{path}/branches  # 取得分支列表
POST /api/analyze                   # 分析 commit 並生成回報
POST /api/update-redmine            # 更新 Redmine issue
GET  /api/config                    # 取得設定
POST /api/config                    # 更新設定
```

### 5.2 資料結構

**Issue 資料**：
```python
{
  "id": 1234,
  "subject": "實作使用者登入功能",
  "status": {"id": 2, "name": "進行中"},
  "priority": {"id": 3, "name": "高"},
  "assigned_to": {"id": 10, "name": "使用者名稱"},
  "done_ratio": 60,
  "spent_hours": 8.0,
  "created_on": "2026-01-15T10:00:00Z",
  "updated_on": "2026-01-21T15:30:00Z"
}
```

**Commit 資料**：
```python
{
  "hash": "abc123def456",
  "author": "使用者名稱",
  "date": "2026-01-21T14:30:00Z",
  "message": "feat: 實作使用者登入 API\n\n- 新增 /api/login 端點\n- 整合 JWT token",
  "files_changed": {
    "added": 2,
    "modified": 1,
    "deleted": 0
  },
  "related_issues": [1234]  # 從 commit message 提取
}
```

**分析請求**：
```python
{
  "issue_id": 1234,
  "repository_path": "D:/Projects/my-project",
  "branch": "feature/user-login",
  "start_date": "2026-01-15",
  "end_date": "2026-01-21",
  "user_filter": {
    "name": "使用者名稱",  # 從 Git config 或 Redmine 取得
    "email": "user@example.com"
  }
}
```

**注意**：後端會自動過濾，只分析符合 `user_filter` 的 commit。

**分析回應**：
```python
{
  "notes": "本週完成的主要工作：\n• ...",
  "percent_done": 75,
  "spent_time": 8.5,
  "suggested_status": "進行中",
  "commits_analyzed": [
    {"hash": "abc123", "message": "..."},
    ...
  ]
}
```

---

## 6. 設定檔設計

### 6.1 設定檔結構（config.json）

```json
{
  "redmine": {
    "url": "https://redmine.example.com",
    "api_key": "your_api_key_here",
    "user_id": 10
  },
  "git": {
    "user": {
      "name": "使用者名稱",
      "email": "user@example.com"
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
  "repositories": [
    {
      "name": "主專案",
      "path": "D:/Projects/my-project",
      "last_used": "2026-01-21"
    }
  ],
  "default_time_range": "本週",
  "ui": {
    "theme": "light",
    "language": "zh-TW"
  }
}
```

**Git 使用者設定說明**：
- `git.user.name` 和 `git.user.email`：用於過濾 commit，只分析當前使用者的 commit
- `git.auto_detect`：如果為 `true`，自動從 Git 全域設定檔讀取（`git config --global user.name` 和 `user.email`）
- 如果 `auto_detect` 為 `false`，則使用設定檔中的 `git.user` 值

---

## 7. 錯誤處理與邊界情況

### 7.1 錯誤情境

1. **Redmine 連線失敗**
   - 顯示錯誤訊息
   - 提供「重試」按鈕
   - 檢查網路連線和 API key

2. **Git 儲存庫無效**
   - 驗證路徑是否存在
   - 驗證是否為有效的 Git 儲存庫
   - 提示使用者選擇其他儲存庫

3. **指定時間範圍內無 commit**
   - **情況 A**：該時間範圍內完全沒有 commit
     - 提示「該時間範圍內沒有 commit」
     - 建議選擇其他時間範圍或分支
   - **情況 B**：該時間範圍內有其他使用者的 commit，但沒有當前使用者的 commit
     - 提示「該時間範圍內沒有你的 commit（當前使用者：{user.name} / {user.email}）」
     - 顯示該時間範圍內的其他 commit 數量（僅供參考）
     - 建議選擇其他時間範圍或分支
     - 提示檢查 Git 使用者設定是否正確

4. **Claude CLI 執行失敗**
   - 檢查 CLI 是否已安裝（提示安裝步驟）
   - 檢查 CLI 是否已登入（提示登入步驟）
   - 執行超時處理（預設 60 秒）
   - JSON 解析失敗（顯示原始輸出供手動處理）
   - 記錄錯誤日誌

5. **Redmine 更新權限不足**
   - 顯示權限錯誤
   - 提示聯絡管理員

6. **Commit message 中找不到 issue ID**
   - 仍可分析，但提示「未找到相關 issue ID」
   - 建議在 commit message 中加入 `#issue_id`

---

## 8. 實作階段規劃

### Phase 1：MVP（最小可行產品）
- [ ] Redmine API 連線與工單列表
- [ ] 本地 Git 儲存庫掃描與分支選擇
- [ ] Commit 時間範圍選擇
- [ ] 基本的 commit 列表取得
- [ ] Claude CLI 整合與分析
- [ ] 簡單的文字編輯介面
- [ ] Redmine 更新功能

**預估時間**：2-3 天

### Phase 2：優化與增強
- [ ] 儲存庫書籤功能
- [ ] 歷史記錄（記錄每次更新）
- [ ] 批次處理（一次處理多個工單）
- [ ] 更豐富的 AI 分析提示詞
- [ ] 錯誤處理與重試機制

**預估時間**：1-2 天

### Phase 3：進階功能
- [ ] 自動偵測 commit message 中的 issue ID
- [ ] 支援多個 Redmine 專案
- [ ] 匯出/匯入設定
- [ ] 統計報表（工時統計、進度追蹤）
- [ ] 桌面應用打包（可選）

**預估時間**：2-3 天

---

## 9. 待討論事項

### 9.1 技術選項
- [x] **前端框架**：純 HTML/JS + Tailwind CSS（已決定）
- [x] **Git 操作**：GitPython（已決定）
- [x] **Redmine 套件**：python-redmine（已決定）
- [x] **AI 分析**：Claude Code CLI（已決定，使用 stdin pipe + JSON 輸出）

### 9.2 功能細節
- [ ] **Commit 分析範圍**：只分析 commit message？還是也要分析 diff？（建議先做 message，之後可選做 diff）
- [ ] **工時計算**：AI 估算 vs 手動輸入 vs 從 commit 時間推算？（建議 AI 估算 + 可手動調整）
- [ ] **批次處理**：一次處理多個工單？（Phase 2 再考慮）
- [ ] **歷史記錄**：要不要記錄每次更新的內容？（建議做，方便追蹤）

### 9.3 部署方式
- [ ] **本機執行**：直接跑 Python 腳本？
- [ ] **打包成執行檔**：PyInstaller？
- [ ] **Docker 容器**：可選，但對本機工具可能過度設計

---

## 10. 下一步行動

1. **確認規格**：請檢視以上規格，確認是否符合需求
2. **技術選項確認**：已確認使用 Claude Code CLI、GitPython、python-redmine
3. **設定檔準備**：準備 Redmine API key，確認 Claude CLI 已安裝並登入
4. **UI 設計系統**：使用 ui-ux-pro-max 生成設計系統
5. **開始實作**：從 Phase 1 MVP 開始

---

## 附錄：相關資源

- Redmine REST API 文件：https://www.redmine.org/projects/redmine/wiki/Rest_api
- python-redmine 文件：https://python-redmine.com/
- GitPython 文件：https://gitpython.readthedocs.io/
- Anthropic Claude API：https://docs.anthropic.com/
