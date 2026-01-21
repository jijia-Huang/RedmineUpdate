# 使用 Claude Code CLI 進行分析 - 討論文件

## 方案概述

將原本的 **Claude API** 方案改為使用 **Claude Code CLI** 來分析 commit 記錄。

---

## Claude Code CLI 使用方式

根據官方文件，關鍵命令：

### 非互動式模式（適合自動化）
```bash
# 基本用法
claude -p "請分析這些 commit..."

# 使用 JSON 輸出格式
claude -p "請分析..." --output-format json

# 透過 stdin 傳入資料
echo "commit data" | claude -p "請分析這些 commit 記錄"

# 使用系統提示詞檔案
claude -p "請分析..." --system-prompt-file prompt.txt

# 組合使用：傳入檔案內容 + JSON 輸出
cat commits.txt | claude -p "請分析這些 commit" --output-format json
```

---

## 方案優點

### ✅ 優點
1. **不需要 API Key**：使用 CLI 登入後即可使用，不需要管理 API key
2. **更簡單的設定**：只需要安裝 CLI 並登入一次
3. **本地執行**：所有分析在本地完成，資料不會上傳到外部服務（除了 Claude 本身）
4. **可能更穩定**：不依賴 API 的 rate limit 或配額問題

### ⚠️ 需要考慮的點
1. **輸出解析**：需要確保 CLI 輸出格式穩定，方便解析
2. **錯誤處理**：CLI 執行失敗時的處理機制
3. **登入狀態**：需要確認 CLI 是否已登入
4. **效能**：CLI 可能比直接 API 呼叫稍慢（但對這個使用場景應該可接受）

---

## 實作方式討論

### 方案 A：透過 stdin 傳入 commit 資料

**流程**：
1. 將 commit 資料整理成文字格式（JSON 或 Markdown）
2. 透過 `subprocess` 執行 CLI，將資料 pipe 進去
3. 解析 CLI 的 JSON 輸出

**範例程式碼概念**：
```python
import subprocess
import json

# 準備 commit 資料
commit_data = {
    "issue_id": 1234,
    "commits": [...]
}

# 轉換成文字格式
commit_text = format_commits(commit_data)

# 執行 CLI
process = subprocess.run(
    [
        "claude", "-p",
        "請分析這些 commit 記錄並生成 Redmine 進度回報，以 JSON 格式輸出",
        "--output-format", "json",
        "--system-prompt-file", "prompt.txt"
    ],
    input=commit_text.encode(),
    capture_output=True,
    text=True
)

# 解析輸出
result = json.loads(process.stdout)
```

**優點**：
- 簡單直接
- 可以傳入大量資料

**缺點**：
- 需要處理 CLI 的錯誤輸出
- 需要確認 CLI 是否已安裝並登入

---

### 方案 B：先寫入暫存檔案，再讓 CLI 讀取

**流程**：
1. 將 commit 資料寫入暫存檔案（JSON 或 Markdown）
2. 執行 CLI 命令，讓它讀取檔案
3. 解析輸出

**範例程式碼概念**：
```python
import tempfile
import subprocess
import json

# 寫入暫存檔案
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(commit_data, f, ensure_ascii=False, indent=2)
    temp_file = f.name

# 執行 CLI
process = subprocess.run(
    [
        "claude", "-p",
        f"請讀取 {temp_file} 並分析這些 commit 記錄，以 JSON 格式輸出",
        "--output-format", "json"
    ],
    capture_output=True,
    text=True
)

# 清理暫存檔
os.unlink(temp_file)
```

**優點**：
- 可以處理更大的資料量
- 檔案可以保留供除錯用（可選）

**缺點**：
- 需要管理暫存檔案
- 需要處理檔案路徑（Windows 路徑格式）

---

### 方案 C：使用系統提示詞檔案 + 直接傳入查詢

**流程**：
1. 預先準備系統提示詞檔案（定義分析格式、輸出格式等）
2. 將 commit 資料格式化後作為查詢內容
3. 執行 CLI 並解析輸出

**優點**：
- 提示詞可以版本控制
- 更容易調整和維護
- 可以定義更複雜的分析邏輯

---

## 需要討論的技術細節

### 1. 資料傳遞方式
**問題**：如何將 commit 資料傳給 CLI？

**選項**：
- [ ] **A. stdin pipe**：`echo data | claude -p "query"`
- [ ] **B. 暫存檔案**：先寫檔案，再讓 CLI 讀取
- [ ] **C. 直接嵌入查詢**：將資料直接放在查詢字串中（適合少量資料）

**建議**：**方案 A（stdin pipe）**，因為：
- 不需要管理暫存檔案
- 資料不會殘留在磁碟上
- 適合自動化流程

---

### 2. 輸出格式
**問題**：如何確保 CLI 輸出可被程式解析？

**選項**：
- [ ] **A. JSON 格式**：使用 `--output-format json`，要求 AI 輸出 JSON
- [ ] **B. Markdown 格式**：輸出 Markdown，再用 regex 解析
- [ ] **C. 結構化文字**：定義特定格式（如 YAML），再解析

**建議**：**方案 A（JSON）**，因為：
- 最穩定、最容易解析
- 可以在系統提示詞中明確要求 JSON 格式
- 錯誤處理較簡單

**注意**：需要測試 CLI 的 JSON 輸出是否穩定，可能需要加上錯誤處理（如果輸出不是有效 JSON）

---

### 3. 系統提示詞設計
**問題**：如何設計提示詞讓 CLI 產生我們需要的格式？

**建議結構**：
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

請分析並輸出 JSON。
```

**儲存位置**：`prompts/redmine_analysis.txt` 或 `prompts/system_prompt.txt`

---

### 4. 錯誤處理
**問題**：如何處理 CLI 執行失敗的情況？

**需要處理的情況**：
1. **CLI 未安裝**：提示使用者安裝
2. **CLI 未登入**：提示使用者登入
3. **執行超時**：設定 timeout，避免卡住
4. **輸出格式錯誤**：如果 JSON 解析失敗，顯示原始輸出讓使用者手動處理
5. **網路問題**：CLI 可能需要連線，處理連線失敗

**實作建議**：
```python
try:
    process = subprocess.run(
        [...],
        timeout=60,  # 60 秒超時
        capture_output=True,
        text=True
    )
    
    if process.returncode != 0:
        # 處理錯誤
        error_msg = process.stderr
        if "not logged in" in error_msg:
            raise NotLoggedInError("請先執行 'claude' 登入")
        elif "command not found" in error_msg:
            raise CLINotFoundError("請先安裝 Claude Code CLI")
        else:
            raise CLIExecutionError(f"CLI 執行失敗: {error_msg}")
    
    # 解析 JSON
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError:
        # 如果輸出不是 JSON，顯示原始輸出
        raise InvalidOutputError(f"CLI 輸出格式錯誤: {process.stdout}")
        
except subprocess.TimeoutExpired:
    raise CLITimeoutError("分析超時，請稍後再試")
```

---

### 5. CLI 登入狀態檢查
**問題**：如何確認 CLI 是否已登入？

**檢查方式**：
- 執行一個簡單的 CLI 命令（如 `claude -p "test"`），檢查是否成功
- 或者直接執行主要命令，從錯誤訊息判斷

**建議**：在應用啟動時檢查，或在第一次使用時檢查。

---

### 6. 效能考量
**問題**：CLI 執行速度如何？需要顯示進度嗎？

**考量**：
- CLI 可能需要幾秒到幾十秒來分析
- 建議顯示「分析中...」的進度提示
- 可以考慮加上進度條或載入動畫

---

## 與原規格的差異

### 需要修改的部分

1. **設定檔**（config.json）：
   ```json
   {
     "claude": {
       "use_cli": true,  // 新增：使用 CLI 而非 API
       "cli_path": "claude",  // CLI 命令路徑（預設 "claude"）
       "timeout": 60,  // CLI 執行超時時間（秒）
       "output_format": "json"  // 輸出格式
     }
   }
   ```
   
   移除：
   - `claude.api_key`
   - `claude.model`（CLI 可以透過參數指定，但可能不需要）

2. **依賴套件**：
   - 移除：`anthropic` SDK
   - 新增：可能需要 `subprocess`（Python 內建，不需要額外套件）

3. **實作模組**：
   - 將 `ClaudeAPIService` 改為 `ClaudeCLIService`
   - 使用 `subprocess` 執行 CLI 命令
   - 解析 CLI 輸出而非 API 回應

---

## 待確認的問題

### 問題 1：你已經安裝 Claude Code CLI 了嗎？
- [ ] 已安裝
- [ ] 未安裝（需要安裝步驟）

### 問題 2：你偏好哪種資料傳遞方式？
- [ ] stdin pipe（建議）
- [ ] 暫存檔案
- [ ] 其他

### 問題 3：輸出格式偏好？
- [ ] JSON（建議）
- [ ] Markdown
- [ ] 其他

### 問題 4：是否需要處理 CLI 的登入狀態檢查？
- [ ] 需要（在啟動時檢查）
- [ ] 不需要（假設已登入）

### 問題 5：分析超時時間？
- [ ] 30 秒
- [ ] 60 秒（建議）
- [ ] 120 秒
- [ ] 其他

---

## 建議的實作順序

1. **先做簡單測試**：手動執行 CLI 命令，確認可以正常分析 commit 資料
2. **實作 CLI 服務模組**：封裝 CLI 執行邏輯
3. **整合到主流程**：將 CLI 服務整合到分析流程中
4. **錯誤處理**：加上完整的錯誤處理機制
5. **優化與測試**：測試各種邊界情況

---

## 下一步

請確認以上討論事項，特別是：
1. 資料傳遞方式（建議 stdin pipe）
2. 輸出格式（建議 JSON）
3. 錯誤處理的需求
4. 是否需要登入狀態檢查

確認後，我會更新規格文件，然後等你說「開始」再開始實作。
