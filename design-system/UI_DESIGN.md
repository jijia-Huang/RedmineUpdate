# Redmine 進度回報工具 - UI 設計詳細規格

## 頁面列表

1. **工單列表頁**（Issue List）
2. **儲存庫選擇頁**（Repository Selection）
3. **時間範圍選擇頁**（Time Range Selection）
4. **分析中頁**（Analyzing）
5. **結果確認頁**（Review & Edit）
6. **更新結果頁**（Update Result）
7. **設定頁**（Settings）

---

## 頁面 1：工單列表頁

### 功能
顯示 Redmine 上指派給當前使用者的所有工單，點擊後進入分析流程。

### 佈局結構

```
┌─────────────────────────────────────────────────────┐
│  Header (固定)                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ Redmine 進度回報工具              [設定]      │  │
│  └───────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│  Main Content                                        │
│  ┌───────────────────────────────────────────────┐  │
│  │ 我的工單                          [重新整理]   │  │
│  ├───────────────────────────────────────────────┤  │
│  │ 篩選：[全部 ▼]  搜尋：[___________]           │  │
│  ├───────────────────────────────────────────────┤  │
│  │ ┌───────────────────────────────────────────┐ │  │
│  │ │ #1234 實作使用者登入功能                   │ │  │
│  │ │ 狀態：進行中 | 進度：60% | 工時：8小時    │ │  │
│  │ │ 優先級：高 | 更新：2026-01-21 15:30       │ │  │
│  │ │                              [選擇此工單]  │ │  │
│  │ └───────────────────────────────────────────┘ │  │
│  │ ┌───────────────────────────────────────────┐ │  │
│  │ │ #1235 修復 API 回應錯誤                   │ │  │
│  │ │ 狀態：待處理 | 進度：0% | 工時：0小時     │ │  │
│  │ │ 優先級：中 | 更新：2026-01-20 10:15       │ │  │
│  │ │                              [選擇此工單]  │ │  │
│  │ └───────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### HTML 結構

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Redmine 進度回報工具</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
  <style>
    body { font-family: 'Inter', sans-serif; }
  </style>
</head>
<body class="bg-slate-50">
  <!-- Header -->
  <header class="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
    <div class="max-w-6xl mx-auto px-6 py-4">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-slate-900">Redmine 進度回報工具</h1>
        <button id="settingsBtn" class="px-3 py-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors cursor-pointer">
          設定
        </button>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-6xl mx-auto px-6 py-8">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-slate-900">我的工單</h2>
      <button id="refreshBtn" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 cursor-pointer font-medium flex items-center space-x-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>重新整理</span>
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white border border-slate-200 rounded-lg p-4 mb-6">
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-slate-700">篩選：</label>
          <select id="statusFilter" class="px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
            <option value="all">全部</option>
            <option value="open">進行中</option>
            <option value="pending">待處理</option>
            <option value="closed">已關閉</option>
          </select>
        </div>
        <div class="flex-1">
          <input 
            type="text" 
            id="searchInput"
            placeholder="搜尋工單標題或編號..." 
            class="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>
      </div>
    </div>

    <!-- Issue List -->
    <div id="issueList" class="space-y-4">
      <!-- Loading State -->
      <div id="loadingState" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-4 text-slate-600">載入中...</p>
      </div>

      <!-- Issue Cards (動態生成) -->
      <!-- 範例卡片 -->
      <div class="issue-card bg-white border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer" data-issue-id="1234">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center space-x-3 mb-2">
              <h3 class="text-lg font-semibold text-slate-900">#1234 實作使用者登入功能</h3>
              <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">進行中</span>
            </div>
            <div class="flex items-center space-x-4 text-sm text-slate-600">
              <span>進度：<span class="font-medium">60%</span></span>
              <span>工時：<span class="font-medium">8 小時</span></span>
              <span>優先級：<span class="px-1.5 py-0.5 bg-red-100 text-red-800 rounded text-xs font-medium">高</span></span>
              <span>最後更新：2026-01-21 15:30</span>
            </div>
          </div>
          <button class="select-issue-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 cursor-pointer font-medium">
            選擇此工單
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div id="emptyState" class="hidden text-center py-12">
      <svg class="mx-auto h-12 w-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-slate-900">沒有工單</h3>
      <p class="mt-1 text-sm text-slate-500">目前沒有指派給你的工單</p>
    </div>
  </main>
</body>
</html>
```

### 互動行為
- **點擊工單卡片**：進入儲存庫選擇頁
- **點擊「選擇此工單」按鈕**：進入儲存庫選擇頁
- **重新整理按鈕**：重新載入工單列表
- **篩選下拉選單**：即時篩選工單
- **搜尋輸入框**：即時搜尋工單標題和編號

---

## 頁面 2：儲存庫選擇頁

### 功能
選擇本地 Git 儲存庫和要分析的分支。

### 佈局結構

```
┌─────────────────────────────────────────────────────┐
│  Header (固定)                                       │
├─────────────────────────────────────────────────────┤
│  Main Content                                        │
│  ┌───────────────────────────────────────────────┐  │
│  │ 選擇 Git 儲存庫和分支                          │  │
│  │ 工單：#1234 實作使用者登入功能                 │  │
│  ├───────────────────────────────────────────────┤  │
│  │ 儲存庫：                                       │  │
│  │ [▼] D:/Projects/my-project        [新增...]   │  │
│  │                                               │  │
│  │ 分支：                                         │  │
│  │ ○ main (當前)                                 │  │
│  │ ○ feature/user-login                          │  │
│  │ ○ bugfix/api-error                            │  │
│  │                                               │  │
│  │ [上一步]              [下一步：選擇時間範圍]   │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### HTML 結構（關鍵部分）

```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="max-w-2xl mx-auto">
    <!-- Page Header -->
    <div class="mb-8">
      <h2 class="text-2xl font-bold text-slate-900 mb-2">選擇 Git 儲存庫和分支</h2>
      <p class="text-slate-600">工單：<span class="font-medium">#1234 實作使用者登入功能</span></p>
    </div>

    <!-- Repository Selection -->
    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <label class="block text-sm font-medium text-slate-700 mb-2">儲存庫：</label>
      <div class="flex items-center space-x-2">
        <select id="repositorySelect" class="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
          <option value="">請選擇儲存庫...</option>
          <option value="D:/Projects/my-project">D:/Projects/my-project</option>
        </select>
        <button id="addRepoBtn" class="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer">
          新增...
        </button>
      </div>
    </div>

    <!-- Branch Selection -->
    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <label class="block text-sm font-medium text-slate-700 mb-4">分支：</label>
      <div id="branchList" class="space-y-2">
        <!-- Loading -->
        <div class="text-center py-4">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="flex items-center justify-between">
      <button id="backBtn" class="px-4 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
        上一步
      </button>
      <button id="nextBtn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer font-medium disabled:opacity-50 disabled:cursor-not-allowed" disabled>
        下一步：選擇時間範圍
      </button>
    </div>
  </div>
</main>
```

---

## 頁面 3：時間範圍選擇頁

### 功能
選擇要分析的 commit 時間範圍。**重要**：系統會自動過濾，只分析當前使用者的 commit（根據 Git 設定檔的 `user.name` 和 `user.email`）。

### HTML 結構（關鍵部分）

```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="max-w-2xl mx-auto">
    <div class="mb-8">
      <h2 class="text-2xl font-bold text-slate-900 mb-2">選擇要分析的 Commit 時間範圍</h2>
      <p class="text-slate-600">儲存庫：<span class="font-medium">D:/Projects/my-project</span> | 分支：<span class="font-medium">feature/user-login</span></p>
    </div>

    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <div class="space-y-3">
        <label class="flex items-center space-x-3 cursor-pointer">
          <input type="radio" name="timeRange" value="today" class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
          <span class="text-slate-700">今天</span>
        </label>
        <label class="flex items-center space-x-3 cursor-pointer">
          <input type="radio" name="timeRange" value="yesterday" class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
          <span class="text-slate-700">昨天</span>
        </label>
        <label class="flex items-center space-x-3 cursor-pointer">
          <input type="radio" name="timeRange" value="thisWeek" checked class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
          <span class="text-slate-700">本週</span>
        </label>
        <label class="flex items-center space-x-3 cursor-pointer">
          <input type="radio" name="timeRange" value="lastWeek" class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
          <span class="text-slate-700">上週</span>
        </label>
        <label class="flex items-center space-x-3 cursor-pointer">
          <input type="radio" name="timeRange" value="custom" class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
          <span class="text-slate-700">自訂：</span>
          <input type="date" id="startDate" class="px-2 py-1 border border-slate-300 rounded text-sm" disabled />
          <span class="text-slate-500">至</span>
          <input type="date" id="endDate" class="px-2 py-1 border border-slate-300 rounded text-sm" disabled />
        </label>
      </div>
    </div>

    <!-- Commit Preview -->
    <div id="commitPreview" class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
      <p class="text-sm text-blue-800">
        <span class="font-medium">預覽：</span>找到 <span id="commitCount" class="font-bold">12</span> 個 <span class="font-medium">你的</span> commit
      </p>
      <p class="text-xs text-blue-700 mt-1">
        （僅分析當前使用者的 commit：<span id="currentUser" class="font-mono">user@example.com</span>）
      </p>
    </div>

    <div class="flex items-center justify-between">
      <button id="backBtn" class="px-4 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
        上一步
      </button>
      <button id="analyzeBtn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer font-medium">
        開始分析
      </button>
    </div>
  </div>
</main>
```

---

## 頁面 4：分析中頁

### 功能
顯示分析進度，使用 WebSocket 或輪詢更新狀態。

### HTML 結構

```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="max-w-2xl mx-auto text-center">
    <div class="mb-8">
      <div class="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
      <h2 class="text-2xl font-bold text-slate-900 mb-2">正在分析 Commit...</h2>
      <p class="text-slate-600" id="analyzeStatus">正在收集 commit 記錄...</p>
    </div>

    <!-- Progress Bar -->
    <div class="w-full bg-slate-200 rounded-full h-2 mb-4">
      <div id="progressBar" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
    </div>

    <!-- Commit List (可選，顯示正在分析的 commit) -->
    <div id="analyzingCommits" class="bg-white border border-slate-200 rounded-lg p-4 text-left mt-6">
      <p class="text-sm font-medium text-slate-700 mb-2">正在分析的 Commit：</p>
      <div class="space-y-1 text-sm text-slate-600 font-mono">
        <div>abc123 - feat: 實作登入 API</div>
        <div>def456 - fix: 修復密碼加密問題</div>
        <!-- ... -->
      </div>
    </div>
  </div>
</main>
```

---

## 頁面 5：結果確認頁

### 功能
顯示 AI 分析結果，允許使用者編輯和調整。

### HTML 結構（關鍵部分）

```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="max-w-3xl mx-auto">
    <div class="mb-8">
      <h2 class="text-2xl font-bold text-slate-900 mb-2">AI 分析結果 - 請確認並微調</h2>
      <p class="text-slate-600">工單：<span class="font-medium">#1234 實作使用者登入功能</span></p>
    </div>

    <!-- Notes Editor -->
    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <label class="block text-sm font-medium text-slate-700 mb-2">回報內容（Notes）：</label>
      <textarea 
        id="notesEditor"
        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y min-h-[200px] font-mono text-sm"
      >本週完成的主要工作：
• 完成使用者登入功能的後端 API
• 實作 JWT token 驗證機制
• 修復密碼加密的 bug

技術細節：
• 使用 bcrypt 進行密碼雜湊
• 整合 Redis 做 session 管理</textarea>
    </div>

    <!-- Fields -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="bg-white border border-slate-200 rounded-lg p-4">
        <label class="block text-sm font-medium text-slate-700 mb-2">進度百分比：</label>
        <input 
          type="number" 
          id="percentDone"
          min="0" 
          max="100" 
          value="75"
          class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div class="bg-white border border-slate-200 rounded-lg p-4">
        <label class="block text-sm font-medium text-slate-700 mb-2">工時（小時）：</label>
        <input 
          type="number" 
          id="spentTime"
          min="0" 
          step="0.5"
          value="8.5"
          class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div class="bg-white border border-slate-200 rounded-lg p-4">
        <label class="block text-sm font-medium text-slate-700 mb-2">狀態：</label>
        <select 
          id="statusSelect"
          class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        >
          <option value="2">進行中</option>
          <option value="3">待測試</option>
          <option value="4">待審核</option>
        </select>
      </div>
    </div>

    <!-- Related Commits -->
    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <h3 class="text-sm font-medium text-slate-700 mb-3">相關 Commit（12 個）：</h3>
      <div class="space-y-1 text-sm font-mono text-slate-600 max-h-48 overflow-y-auto">
        <div>• abc123 - feat: 實作登入 API</div>
        <div>• def456 - fix: 修復密碼加密問題</div>
        <!-- ... -->
      </div>
    </div>

    <!-- Navigation -->
    <div class="flex items-center justify-between">
      <button id="backBtn" class="px-4 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
        上一步
      </button>
      <button id="submitBtn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer font-medium">
        確認並更新到 Redmine
      </button>
    </div>
  </div>
</main>
```

---

## 頁面 6：更新結果頁

### 功能
顯示更新成功或失敗的結果。

### HTML 結構

```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="max-w-2xl mx-auto">
    <!-- Success State -->
    <div id="successState" class="text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
        <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 class="text-2xl font-bold text-slate-900 mb-2">更新成功！</h2>
      <p class="text-slate-600 mb-6">Redmine 工單已成功更新</p>
      <a 
        href="https://redmine.example.com/issues/1234" 
        target="_blank"
        class="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
      >
        查看 Redmine 工單
      </a>
    </div>

    <!-- Error State -->
    <div id="errorState" class="hidden text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
        <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
      <h2 class="text-2xl font-bold text-slate-900 mb-2">更新失敗</h2>
      <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
        <p class="text-sm text-red-800" id="errorMessage">錯誤訊息...</p>
      </div>
      <div class="flex items-center justify-center space-x-4">
        <button id="retryBtn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
          重試
        </button>
        <button id="backBtn" class="px-6 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
          返回
        </button>
      </div>
    </div>
  </div>
</main>
```

---

## 頁面 7：設定頁

### 功能
設定 Redmine URL、API Key、Claude CLI 路徑等。

### HTML 結構（關鍵部分）

```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="max-w-2xl mx-auto">
    <h2 class="text-2xl font-bold text-slate-900 mb-6">設定</h2>

    <!-- Redmine Settings -->
    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <h3 class="text-lg font-semibold text-slate-900 mb-4">Redmine 設定</h3>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Redmine URL：</label>
          <input type="url" id="redmineUrl" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">API Key：</label>
          <input type="password" id="redmineApiKey" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>
    </div>

    <!-- Git User Settings -->
    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <h3 class="text-lg font-semibold text-slate-900 mb-4">Git 使用者設定</h3>
      <p class="text-sm text-slate-600 mb-4">用於過濾 commit，只分析當前使用者的 commit</p>
      <div class="space-y-4">
        <div class="flex items-center space-x-2">
          <input type="checkbox" id="autoDetectGit" checked class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
          <label for="autoDetectGit" class="text-sm font-medium text-slate-700">自動偵測（從 Git 全域設定檔讀取）</label>
        </div>
        <div id="gitUserFields" class="space-y-4 hidden">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">使用者名稱：</label>
            <input type="text" id="gitUserName" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Email：</label>
            <input type="email" id="gitUserEmail" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
        <div class="text-sm text-slate-500">
          <p>當前偵測到的使用者：</p>
          <p class="font-mono text-xs mt-1" id="detectedGitUser">載入中...</p>
        </div>
      </div>
    </div>

    <!-- Claude CLI Settings -->
    <div class="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      <h3 class="text-lg font-semibold text-slate-900 mb-4">Claude CLI 設定</h3>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">CLI 路徑：</label>
          <input type="text" id="claudeCliPath" value="claude" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">執行超時（秒）：</label>
          <input type="number" id="claudeTimeout" value="60" min="30" max="300" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div class="flex items-center space-x-2">
          <button id="testClaudeBtn" class="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer">
            測試連線
          </button>
          <span id="claudeStatus" class="text-sm text-slate-600"></span>
        </div>
      </div>
    </div>

    <!-- Save Button -->
    <div class="flex items-center justify-end space-x-4">
      <button id="cancelBtn" class="px-4 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
        取消
      </button>
      <button id="saveBtn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer font-medium">
        儲存設定
      </button>
    </div>
  </div>
</main>
```

---

## 通用元件

### 模態框（Modal）

```html
<div id="modal" class="hidden fixed inset-0 z-50 overflow-y-auto">
  <div class="flex items-center justify-center min-h-screen px-4">
    <div class="fixed inset-0 bg-black opacity-50" onclick="closeModal()"></div>
    <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
      <h3 class="text-lg font-semibold text-slate-900 mb-4">標題</h3>
      <p class="text-slate-600 mb-6">內容...</p>
      <div class="flex items-center justify-end space-x-4">
        <button onclick="closeModal()" class="px-4 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
          取消
        </button>
        <button class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
          確認
        </button>
      </div>
    </div>
  </div>
</div>
```

---

## 響應式設計

### 斷點調整
- **Mobile (< 640px)**：
  - 卡片改為全寬
  - 按鈕改為全寬或堆疊
  - 文字大小適當縮小

- **Tablet (640px - 1024px)**：
  - 保持桌面佈局
  - 適當調整間距

- **Desktop (> 1024px)**：
  - 使用完整設計

---

## 動畫與過渡

### 頁面轉場
- 使用淡入效果：`transition-opacity duration-300`
- 載入狀態：spinner 動畫

### 互動回饋
- 按鈕 hover：顏色變化 + 輕微陰影
- 卡片 hover：邊框顏色 + 陰影加深
- 輸入框 focus：ring 效果

---

## 無障礙設計

### 鍵盤導航
- Tab 鍵遍歷所有互動元素
- Enter/Space 觸發按鈕
- Esc 關閉模態框

### ARIA 標籤
- 按鈕有明確的 `aria-label`
- 載入狀態使用 `aria-live="polite"`
- 表單輸入有對應的 `aria-describedby`

---

## 設計系統版本

- **版本**：1.0.0
- **建立日期**：2026-01-21
- **最後更新**：2026-01-21
