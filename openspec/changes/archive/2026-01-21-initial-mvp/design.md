# Technical Design: Initial MVP

## Context
建立 Redmine 進度回報自動化工具，整合 Redmine API、Git 操作和 Claude Code CLI，提供 Web 介面讓工程師自動化進度回報流程。

## Goals / Non-Goals

### Goals
- 提供完整的 MVP 功能，涵蓋從工單選擇到 Redmine 更新的完整流程
- 確保只分析當前使用者的 commit（核心需求）
- 提供清晰的錯誤訊息和處理機制
- 使用簡單、可維護的架構

### Non-Goals
- 批次處理多個工單（Phase 2）
- 歷史記錄功能（Phase 2）
- 統計報表（Phase 3）
- 桌面應用打包（Phase 3）

## Decisions

### Decision: 前後端分離架構
**選擇**：FastAPI 後端 + 純 HTML/JavaScript 前端

**理由**：
- 簡單直接，無需複雜的前端框架
- 易於部署和維護
- 符合專案規模（單人工具）

**替代方案考慮**：
- 桌面應用（Tkinter/PyQt）：開發複雜度較高，不符合快速迭代需求
- CLI 工具：UI 體驗較差，不符合需求

### Decision: 服務層架構
**選擇**：將功能拆分為獨立的服務模組（redmine_service、git_service、analyze_service）

**理由**：
- 關注點分離，易於測試和維護
- 每個服務職責單一明確
- 未來擴展容易

### Decision: Commit 過濾策略
**選擇**：在 Git 服務層過濾 commit，只保留當前使用者的 commit（透過 author.name 或 author.email 匹配）

**理由**：
- 這是核心需求，必須嚴格執行
- 在服務層過濾可以確保所有使用該服務的地方都遵循此規則
- 錯誤訊息可以明確指出過濾條件

**實作細節**：
- 從 Git 設定檔或設定檔讀取當前使用者資訊
- 在 `get_user_commits()` 方法中過濾
- 如果沒有找到當前使用者的 commit，提供明確的錯誤訊息

### Decision: Claude CLI 整合方式
**選擇**：透過 subprocess 執行 Claude CLI，使用 stdin pipe 傳入資料，JSON 格式輸出

**理由**：
- 符合 SPEC.md 中的技術選項決定
- 簡單直接，無需額外的 API 整合
- 使用系統提示詞檔案，易於調整

**實作細節**：
- 系統提示詞儲存在 `prompts/redmine_analysis.txt`
- 執行命令：`echo "{commit_data_json}" | claude -p "..." --output-format json --system-prompt-file prompts/redmine_analysis.txt`
- 設定超時（預設 60 秒）
- 解析 JSON 輸出，處理解析失敗的情況

### Decision: 設定檔格式
**選擇**：JSON 格式（`config.json`）

**理由**：
- 簡單易讀
- Python 原生支援
- 符合 SPEC.md 中的設計

### Decision: 錯誤處理策略
**選擇**：在每個服務層提供明確的錯誤訊息，API 層統一處理並回傳適當的 HTTP 狀態碼

**理由**：
- 使用者需要知道具體的錯誤原因（例如：沒有當前使用者的 commit、Claude CLI 未安裝等）
- 統一的錯誤格式便於前端處理

## Risks / Trade-offs

### Risk: Claude CLI 依賴
**風險**：使用者可能未安裝或未登入 Claude CLI

**緩解**：
- 在設定頁面提供檢查功能
- 明確的錯誤訊息，提示安裝/登入步驟
- 在 `analyze_service.py` 中檢查 CLI 是否可用

### Risk: Commit 過濾邏輯錯誤
**風險**：如果過濾邏輯有誤，可能分析到其他使用者的 commit

**緩解**：
- 重點測試多使用者情境
- 在 UI 中顯示當前使用的 Git 使用者身份
- 在分析前顯示將要分析的 commit 列表（僅供確認）

### Risk: Redmine API 權限
**風險**：API Key 可能權限不足，無法更新某些欄位

**緩解**：
- 明確的錯誤訊息
- 部分更新失敗時，顯示哪些成功、哪些失敗
- 提供重試機制

### Trade-off: 簡化 vs 功能完整性
**選擇**：先實現核心功能，優化和增強功能留到 Phase 2

**理由**：
- 快速驗證核心價值
- 根據實際使用情況調整 Phase 2 的優先順序

## Migration Plan
不適用（新專案，無需遷移）。

## Open Questions
- [ ] Commit 分析範圍：目前只分析 commit message，是否需要在 Phase 2 加入 diff 分析？
- [ ] 工時計算：目前使用 AI 估算，是否需要從 commit 時間推算作為備選？
- [ ] 部署方式：本機執行 vs 打包成執行檔（待 Phase 3 決定）
