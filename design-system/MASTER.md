# Redmine 進度回報工具 - 設計系統

## 產品概述

**產品類型**：開發者工具（Developer Tool）  
**目標使用者**：工程師  
**使用場景**：快速生成 Redmine 進度回報，提升工作效率  
**技術棧**：FastAPI + HTML + Tailwind CSS

---

## 設計原則

### 核心價值
- **效率優先**：減少操作步驟，快速完成任務
- **清晰明確**：資訊層次分明，狀態一目了然
- **專業可靠**：符合工程師工作習慣，減少學習成本

### 設計風格
- **簡潔實用**：避免過度設計，專注功能
- **資訊密度適中**：重要資訊突出，次要資訊可折疊
- **響應式設計**：支援桌面和筆電螢幕（主要使用場景）

---

## 色彩系統

### 主色調
- **Primary（主要操作）**：`blue-600` (#2563EB) - 按鈕、連結、重要操作
- **Primary Hover**：`blue-700` (#1D4ED8)
- **Primary Light**：`blue-50` (#EFF6FF) - 背景、強調區塊

### 語意色彩
- **Success（成功）**：`green-600` (#16A34A) - 更新成功、完成狀態
- **Warning（警告）**：`yellow-600` (#CA8A04) - 需要確認的操作
- **Error（錯誤）**：`red-600` (#DC2626) - 錯誤訊息、失敗狀態
- **Info（資訊）**：`blue-500` (#3B82F6) - 提示訊息

### 中性色
- **Text Primary**：`slate-900` (#0F172A) - 主要文字
- **Text Secondary**：`slate-600` (#475569) - 次要文字
- **Text Muted**：`slate-400` (#94A3B8) - 輔助文字
- **Border**：`slate-200` (#E2E8F0) - 邊框
- **Background**：`white` (#FFFFFF) - 主背景
- **Background Secondary**：`slate-50` (#F8FAFC) - 次要背景

### 狀態色彩
- **進行中**：`blue-500` (#3B82F6)
- **待處理**：`yellow-500` (#EAB308)
- **已完成**：`green-500` (#22C55E)
- **已關閉**：`slate-400` (#94A3B8)

---

## 字體系統

### 字體家族
- **主要字體**：`Inter`（Google Fonts）- 現代、清晰、易讀
- **等寬字體**：`JetBrains Mono` 或 `Fira Code` - 程式碼、commit hash

### 字體大小
- **H1（頁面標題）**：`text-3xl` (30px) / `font-bold`
- **H2（區塊標題）**：`text-2xl` (24px) / `font-semibold`
- **H3（小標題）**：`text-xl` (20px) / `font-semibold`
- **Body（正文）**：`text-base` (16px) / `font-normal`
- **Small（輔助文字）**：`text-sm` (14px) / `font-normal`
- **Code（程式碼）**：`text-sm` (14px) / `font-mono`

### 行高
- **標題**：`leading-tight` (1.25)
- **正文**：`leading-normal` (1.5)
- **緊湊**：`leading-snug` (1.375)

---

## 間距系統

使用 Tailwind 標準間距：
- **xs**：`4px` (1)
- **sm**：`8px` (2)
- **md**：`16px` (4)
- **lg**：`24px` (6)
- **xl**：`32px` (8)
- **2xl**：`48px` (12)
- **3xl**：`64px` (16)

---

## 元件設計

### 按鈕（Button）

#### Primary Button
```html
<button class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 cursor-pointer font-medium">
  確認並更新
</button>
```

#### Secondary Button
```html
<button class="px-4 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors duration-200 cursor-pointer font-medium">
  取消
</button>
```

#### Text Button
```html
<button class="px-3 py-1.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors duration-200 cursor-pointer">
  上一步
</button>
```

### 卡片（Card）

#### 標準卡片
```html
<div class="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
  <!-- 內容 -->
</div>
```

#### 可點擊卡片（工單列表）
```html
<div class="bg-white border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer">
  <!-- 內容 -->
</div>
```

### 輸入框（Input）

```html
<input 
  type="text" 
  class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
  placeholder="請輸入..."
/>
```

### 文字區域（Textarea）

```html
<textarea 
  class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y min-h-[120px]"
  placeholder="請輸入..."
></textarea>
```

### 選擇器（Select）

```html
<select class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white">
  <option>選項 1</option>
</select>
```

### 單選按鈕（Radio）

```html
<label class="flex items-center space-x-2 cursor-pointer">
  <input type="radio" name="timeRange" class="w-4 h-4 text-blue-600 focus:ring-blue-500" />
  <span class="text-slate-700">本週</span>
</label>
```

### 進度條（Progress）

```html
<div class="w-full bg-slate-200 rounded-full h-2">
  <div class="bg-blue-600 h-2 rounded-full" style="width: 60%"></div>
</div>
```

### 徽章（Badge）

#### 狀態徽章
```html
<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
  進行中
</span>
```

#### 優先級徽章
```html
<span class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
  高
</span>
```

### 載入狀態（Loading）

#### Spinner
```html
<div class="flex items-center justify-center">
  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
</div>
```

#### Skeleton
```html
<div class="animate-pulse">
  <div class="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
  <div class="h-4 bg-slate-200 rounded w-1/2"></div>
</div>
```

### 提示訊息（Alert）

#### Success
```html
<div class="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
  <p>更新成功！</p>
</div>
```

#### Error
```html
<div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
  <p>更新失敗：錯誤訊息</p>
</div>
```

---

## 頁面佈局

### 整體結構

```
┌─────────────────────────────────────┐
│  Header (固定)                       │
│  - Logo/標題                        │
│  - 設定按鈕                         │
├─────────────────────────────────────┤
│                                     │
│  Main Content (可滾動)              │
│  - 最大寬度：max-w-6xl (1152px)     │
│  - 左右置中：mx-auto                │
│  - 上下間距：py-8                    │
│                                     │
└─────────────────────────────────────┘
```

### Header

```html
<header class="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
  <div class="max-w-6xl mx-auto px-6 py-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Redmine 進度回報工具</h1>
      <button class="px-3 py-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors cursor-pointer">
        設定
      </button>
    </div>
  </div>
</header>
```

### 頁面容器

```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <!-- 頁面內容 -->
</main>
```

---

## 互動設計

### 過渡動畫
- **標準過渡**：`transition-colors duration-200`（顏色變化）
- **快速過渡**：`transition-all duration-150`（複雜變化）
- **平滑過渡**：`transition-all duration-300`（重要操作）

### Hover 狀態
- **按鈕**：顏色加深 + 輕微陰影
- **卡片**：邊框顏色變化 + 陰影加深
- **連結**：顏色變化 + 底線（可選）

### Focus 狀態
- **輸入框**：`focus:ring-2 focus:ring-blue-500`
- **按鈕**：`focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`

### 載入狀態
- **按鈕載入**：顯示 spinner + 禁用按鈕
- **頁面載入**：顯示 skeleton 或 spinner
- **分析中**：進度條 + 狀態文字

---

## 響應式設計

### 斷點
- **Mobile**：`< 640px`（sm）
- **Tablet**：`640px - 1024px`（md-lg）
- **Desktop**：`> 1024px`（xl+）

### 主要使用場景
- **桌面優先**：主要使用場景是桌面/筆電
- **平板適配**：確保平板可用
- **手機基本支援**：基本功能可用即可

---

## 無障礙設計（A11y）

### 基本要求
- 所有互動元素有明確的 focus 狀態
- 按鈕和連結有清晰的文字標籤
- 表單輸入有對應的 label
- 顏色對比度符合 WCAG AA 標準（4.5:1）

### 鍵盤導航
- Tab 鍵可遍歷所有互動元素
- Enter/Space 可觸發按鈕
- Esc 可關閉模態框

---

## 反模式（避免事項）

### ❌ 不要做
1. **不要使用 emoji 作為圖示**：使用 SVG 圖示（Heroicons、Lucide）
2. **不要使用過度動畫**：避免分散注意力的動畫
3. **不要使用低對比度文字**：確保文字清晰可讀
4. **不要忽略 hover 狀態**：所有可點擊元素都要有視覺回饋
5. **不要使用預設游標**：可點擊元素使用 `cursor-pointer`

### ✅ 應該做
1. **使用一致的間距**：遵循間距系統
2. **提供載入狀態**：長時間操作要有回饋
3. **錯誤處理明確**：錯誤訊息要清楚易懂
4. **狀態視覺化**：不同狀態用顏色區分
5. **操作可撤銷**：重要操作提供取消/確認機制

---

## 圖示系統

### 圖示庫
- **主要使用**：Heroicons（Solid/Outline）
- **備選**：Lucide Icons

### 常用圖示
- **設定**：`CogIcon`
- **重新整理**：`ArrowPathIcon`
- **下一步**：`ArrowRightIcon`
- **上一步**：`ArrowLeftIcon`
- **成功**：`CheckCircleIcon`
- **錯誤**：`XCircleIcon`
- **載入**：`ArrowPathIcon`（旋轉動畫）
- **Git**：`CodeBracketIcon`
- **時間**：`ClockIcon`

### 圖示使用規範
- **大小**：統一使用 `w-5 h-5` 或 `w-6 h-6`
- **顏色**：使用語意色彩（如 `text-blue-600`）
- **間距**：與文字間距 `space-x-2` 或 `space-x-3`

---

## 範例頁面結構

### 工單列表頁
```html
<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="flex items-center justify-between mb-6">
    <h2 class="text-2xl font-bold text-slate-900">我的工單</h2>
    <button class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
      重新整理
    </button>
  </div>
  
  <div class="space-y-4">
    <!-- 工單卡片 -->
    <div class="bg-white border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-slate-900">#1234 實作使用者登入功能</h3>
          <div class="flex items-center space-x-4 mt-2 text-sm text-slate-600">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">進行中</span>
            <span>進度：60%</span>
            <span>工時：8 小時</span>
          </div>
        </div>
        <button class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer">
          選擇
        </button>
      </div>
    </div>
  </div>
</main>
```

---

## 設計系統版本

- **版本**：1.0.0
- **建立日期**：2026-01-21
- **最後更新**：2026-01-21
