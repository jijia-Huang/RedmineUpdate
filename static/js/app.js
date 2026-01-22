// Redmine 進度回報工具 - 前端 JavaScript

const API_BASE = '/api';

// 應用狀態
const state = {
  currentPage: 'issue-list',
  selectedIssue: null,
  selectedRepo: null,
  selectedBranch: null,
  timeRange: null,
  analysisResult: null,
  issues: [],
  repositories: [],
  repoViewMode: 'list', // 'list' | 'select'
};

// Toast（取代 alert，降低打斷感）
function showToast(message, type = 'info', timeoutMs = 3800) {
  const host = document.getElementById('toastHost');
  if (!host) {
    // fallback
    // eslint-disable-next-line no-alert
    alert(message);
    return;
  }

  const palette = {
    info:  { ring: 'ring-blue-200',  bg: 'bg-white', iconBg: 'bg-blue-50',  iconText: 'text-blue-700',  title: '提示' },
    success:{ ring: 'ring-green-200', bg: 'bg-white', iconBg: 'bg-green-50', iconText: 'text-green-700', title: '完成' },
    warning:{ ring: 'ring-yellow-200',bg: 'bg-white', iconBg: 'bg-yellow-50',iconText: 'text-yellow-700',title: '注意' },
    error:{ ring: 'ring-red-200',   bg: 'bg-white', iconBg: 'bg-red-50',   iconText: 'text-red-700',   title: '錯誤' },
  };
  const p = palette[type] || palette.info;

  const el = document.createElement('div');
  el.className = `rounded-xl border border-slate-200 ${p.bg} shadow-sm ring-1 ${p.ring} px-4 py-3`;
  el.innerHTML = `
    <div class="flex items-start gap-3">
      <div class="shrink-0 w-9 h-9 rounded-lg ${p.iconBg} flex items-center justify-center ${p.iconText} font-semibold">
        !
      </div>
      <div class="min-w-0 flex-1">
        <div class="text-sm font-semibold text-slate-900">${p.title}</div>
        <div class="text-sm text-slate-700 mt-0.5 break-words">${escapeHtml(message)}</div>
      </div>
      <button type="button" class="shrink-0 text-slate-400 hover:text-slate-600 px-2 -mt-1" aria-label="Close">✕</button>
    </div>
  `;

  el.querySelector('button')?.addEventListener('click', () => el.remove());
  host.appendChild(el);

  window.setTimeout(() => {
    el.classList.add('opacity-0', 'translate-y-1');
    el.style.transition = 'all 200ms ease';
    window.setTimeout(() => el.remove(), 220);
  }, timeoutMs);
}

function escapeHtml(s) {
  return (s ?? '')
    .toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function updateStepper(activeStep) {
  const stepper = document.getElementById('stepper');
  if (!stepper) return;
  stepper.querySelectorAll('[data-step]').forEach(el => {
    const isActive = el.dataset.step === activeStep;
    el.classList.toggle('bg-blue-600', isActive);
    el.classList.toggle('text-white', isActive);
    el.classList.toggle('border-blue-600', isActive);
    el.classList.toggle('bg-white', !isActive);
    el.classList.toggle('text-slate-700', !isActive);
    el.classList.toggle('border-slate-200', !isActive);
  });
}

function setRedmineBadge(status, detail = '') {
  const badge = document.getElementById('redmineStatusBadge');
  if (!badge) return;
  badge.classList.remove('hidden');
  const dot = badge.querySelector('span.inline-block');
  const text = badge.querySelector('span:last-child');
  if (!dot || !text) return;

  const map = {
    unknown: { dot: 'bg-slate-400', wrap: 'bg-slate-100 text-slate-700 border-slate-200', label: 'Redmine：未檢查' },
    ok:      { dot: 'bg-green-500', wrap: 'bg-green-50 text-green-800 border-green-200', label: 'Redmine：已連線' },
    error:   { dot: 'bg-red-500',   wrap: 'bg-red-50 text-red-800 border-red-200', label: 'Redmine：連線失敗' },
  };
  const m = map[status] || map.unknown;

  badge.className = `hidden sm:inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${m.wrap}`;
  dot.className = `inline-block w-2 h-2 rounded-full ${m.dot}`;
  text.textContent = detail ? `${m.label}（${detail}）` : m.label;
}

function normalizeText(s) {
  return (s || '').toString().toLowerCase();
}

function setRepoCount(n) {
  const el = document.getElementById('repoCount');
  if (el) el.textContent = String(n);
}

function renderRepoSelect(repos) {
  const repoSelect = document.getElementById('repoSelect');
  if (!repoSelect) return;

  repoSelect.innerHTML = '<option value="">請選擇儲存庫</option>';
  repos.forEach(repo => {
    const option = document.createElement('option');
    option.value = encodeURIComponent(repo.path);
    option.textContent = `${repo.name} (${repo.path})`;
    option.dataset.path = repo.path;
    repoSelect.appendChild(option);
  });

  if (state.selectedRepo) {
    repoSelect.value = encodeURIComponent(state.selectedRepo);
  }
}

function renderRepoList(repos, query = '') {
  const list = document.getElementById('repoList');
  if (!list) return;

  const q = normalizeText(query).trim();
  const filtered = q
    ? repos.filter(r =>
        normalizeText(r.name).includes(q) || normalizeText(r.path).includes(q)
      )
    : repos;

  setRepoCount(filtered.length);

  if (filtered.length === 0) {
    list.innerHTML = `
      <div class="col-span-full text-sm text-slate-500 py-6 text-center">
        找不到符合的儲存庫。可按「新增/選擇資料夾...」手動新增。
      </div>
    `;
    return;
  }

  list.innerHTML = filtered
    .map(repo => {
      const currentBranch = repo.current_branch ? `目前：${repo.current_branch}` : '目前：detached/未知';
      const isSelected = state.selectedRepo === repo.path;
      const safePath = (repo.path || '').replace(/"/g, '&quot;');
      return `
        <button
          type="button"
          class="text-left bg-white border ${isSelected ? 'border-blue-400 ring-1 ring-blue-200' : 'border-slate-200'} rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition"
          data-repo-path="${safePath}"
          title="${safePath}"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="font-semibold text-slate-900 truncate">${repo.name || '(未命名)'}</div>
              <div class="text-xs text-slate-500 truncate mt-1">${repo.path}</div>
              <div class="text-xs text-slate-600 mt-2">${currentBranch}</div>
            </div>
            <span class="text-xs ${isSelected ? 'text-blue-700' : 'text-slate-400'} whitespace-nowrap">${isSelected ? '已選取' : '選取'}</span>
          </div>
        </button>
      `;
    })
    .join('');

  list.querySelectorAll('button[data-repo-path]').forEach(btn => {
    btn.addEventListener('click', () => {
      const repoPath = btn.dataset.repoPath;
      selectRepository(repoPath);
    });
  });
}

function setRepoViewMode(mode) {
  state.repoViewMode = mode;
  const list = document.getElementById('repoList');
  const wrap = document.getElementById('repoSelectWrap');
  const toggle = document.getElementById('toggleRepoViewBtn');

  if (!list || !wrap || !toggle) return;

  if (mode === 'select') {
    list.classList.add('hidden');
    wrap.classList.remove('hidden');
    toggle.textContent = '切換到列表';
  } else {
    wrap.classList.add('hidden');
    list.classList.remove('hidden');
    toggle.textContent = '切換到下拉選單';
  }
}

function selectRepository(repoPath) {
  state.selectedRepo = repoPath;
  state.selectedBranch = null;
  updateNextButton();
  loadBranches(repoPath);

  const q = document.getElementById('repoSearchInput')?.value || '';
  renderRepoList(state.repositories, q);
  renderRepoSelect(state.repositories);
}

// 頁面切換
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(page => {
    page.classList.remove('active');
  });
  const page = document.getElementById(`page-${pageId}`);
  if (page) {
    page.classList.add('active');
    state.currentPage = pageId;
    updateStepper(pageId);
  }
}

// API 呼叫
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API 呼叫失敗:', error);
    throw error;
  }
}

// 載入工單列表
async function loadIssues(statusId = null, search = null) {
  const loadingState = document.getElementById('loadingState');
  const issueList = document.getElementById('issueList');
  const emptyState = document.getElementById('emptyState');
  
  loadingState.style.display = 'block';
  emptyState.classList.add('hidden');
  issueList.innerHTML = '';
  
  try {
    const params = new URLSearchParams();
    if (statusId) params.append('status_id', statusId);
    if (search) params.append('search', search);
    
    const data = await apiCall(`/issues?${params.toString()}`);
    state.issues = data.issues || [];
    
    loadingState.style.display = 'none';
    
    if (state.issues.length === 0) {
      emptyState.classList.remove('hidden');
      return;
    }
    
    state.issues.forEach(issue => {
      const card = createIssueCard(issue);
      issueList.appendChild(card);
    });
  } catch (error) {
    loadingState.style.display = 'none';
    showToast(`載入工單失敗：${error.message}`, 'error');
  }
}

// 建立工單卡片
function createIssueCard(issue) {
  const card = document.createElement('div');
  card.className = 'bg-white border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer';
  card.dataset.issueId = issue.id;
  
  const statusColors = {
    '進行中': 'bg-blue-100 text-blue-800',
    '待處理': 'bg-yellow-100 text-yellow-800',
    '已解決': 'bg-green-100 text-green-800',
    '已關閉': 'bg-slate-100 text-slate-800'
  };
  
  const statusName = issue.status?.name || '未知';
  const statusColor = statusColors[statusName] || 'bg-slate-100 text-slate-800';
  
  card.innerHTML = `
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-3 mb-2">
          <h3 class="text-lg font-semibold text-slate-900">#${issue.id} ${issue.subject}</h3>
          <span class="px-2 py-1 ${statusColor} rounded-full text-xs font-medium">${statusName}</span>
        </div>
        <div class="flex items-center space-x-4 text-sm text-slate-600">
          <span>進度：<span class="font-medium">${issue.done_ratio}%</span></span>
          <span>工時：<span class="font-medium">${issue.spent_hours || 0} 小時</span></span>
          ${issue.priority ? `<span>優先級：<span class="px-1.5 py-0.5 bg-red-100 text-red-800 rounded text-xs font-medium">${issue.priority.name}</span></span>` : ''}
          <span>最後更新：${new Date(issue.updated_on).toLocaleString('zh-TW')}</span>
        </div>
      </div>
      <button class="select-issue-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 cursor-pointer font-medium">
        選擇此工單
      </button>
    </div>
  `;
  
  card.querySelector('.select-issue-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    selectIssue(issue);
  });
  
  card.addEventListener('click', () => selectIssue(issue));
  
  return card;
}

// 選擇工單
function selectIssue(issue) {
  state.selectedIssue = issue;
  document.getElementById('selectedIssueTitle').textContent = `#${issue.id} ${issue.subject}`;
  loadRepositories();
  showPage('repo-select');
}

// 載入儲存庫列表
async function loadRepositories() {
  const repoSelect = document.getElementById('repoSelect');
  repoSelect.innerHTML = '<option value="">載入中...</option>';
  
  try {
    const data = await apiCall('/repositories');
    const repos = data.repositories || [];

    state.repositories = repos;
    renderRepoSelect(repos);
    renderRepoList(repos, document.getElementById('repoSearchInput')?.value || '');
  } catch (error) {
    showToast(`載入儲存庫失敗：${error.message}`, 'error');
    repoSelect.innerHTML = '<option value="">載入失敗</option>';
    const list = document.getElementById('repoList');
    if (list) list.innerHTML = `<div class="text-sm text-red-600 py-2">載入失敗：${error.message}</div>`;
  }
}

// 新增儲存庫
async function addRepository(repoPath) {
  try {
    // 先驗證儲存庫是否有效
    const data = await apiCall(`/repositories/${encodeURIComponent(repoPath)}/branches`);
    
    // 如果成功，將儲存庫加入設定檔
    const config = await apiCall('/config');
    const repos = config.repositories || [];
    
    // 檢查是否已存在
    if (repos.some(r => r.path === repoPath)) {
      showToast('此儲存庫已經在列表中', 'warning');
      loadRepositories();
      return;
    }
    
    // 新增到列表
    repos.push({
      name: repoPath.split(/[/\\]/).pop(),
      path: repoPath,
      last_used: new Date().toISOString().split('T')[0]
    });
    
    // 更新設定檔
    await apiCall('/config', {
      method: 'POST',
      body: JSON.stringify({ repositories: repos })
    });
    
    showToast('儲存庫已新增', 'success');
    loadRepositories();
    
    // 自動選擇剛新增的儲存庫
    selectRepository(repoPath);
  } catch (error) {
    showToast(`新增儲存庫失敗：${error.message}（請確認路徑正確且為 Git 儲存庫）`, 'error', 6000);
  }
}

// 載入分支列表
async function loadBranches(repoPath) {
  const branchList = document.getElementById('branchList');
  branchList.innerHTML = '<p class="text-slate-500">載入中...</p>';
  
  try {
    const data = await apiCall(`/repositories/${encodeURIComponent(repoPath)}/branches`);
    const branches = data.branches || [];
    
    branchList.innerHTML = '';
    branches.forEach(branch => {
      const label = document.createElement('label');
      label.className = 'flex items-center space-x-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50';
      
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'branch';
      radio.value = branch.name;
      radio.className = 'text-blue-600';
      if (branch.is_current) {
        radio.checked = true;
        state.selectedBranch = branch.name;
      }
      
      radio.addEventListener('change', () => {
        state.selectedBranch = branch.name;
        updateNextButton();
      });
      
      const span = document.createElement('span');
      span.textContent = branch.name + (branch.is_current ? ' (當前)' : '');
      
      label.appendChild(radio);
      label.appendChild(span);
      branchList.appendChild(label);
    });
    
    updateNextButton();
  } catch (error) {
    branchList.innerHTML = `<p class="text-red-600">載入分支失敗: ${error.message}</p>`;
  }
}

// 更新下一步按鈕狀態
function updateNextButton() {
  const btn = document.getElementById('nextToTimeRangeBtn');
  btn.disabled = !(state.selectedRepo && state.selectedBranch);
}

// 計算時間範圍
function getTimeRange(value) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  
  switch (value) {
    case 'today':
      return {
        start: today.toISOString().split('T')[0] + 'T00:00:00',
        end: new Date(today.getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0] + 'T23:59:59'
      };
    case 'yesterday':
      const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
      return {
        start: yesterday.toISOString().split('T')[0] + 'T00:00:00',
        end: today.toISOString().split('T')[0] + 'T23:59:59'
      };
    case 'thisWeek':
      const weekStart = new Date(today);
      weekStart.setDate(today.getDate() - today.getDay());
      return {
        start: weekStart.toISOString().split('T')[0] + 'T00:00:00',
        end: now.toISOString()
      };
    case 'lastWeek':
      const lastWeekStart = new Date(today);
      lastWeekStart.setDate(today.getDate() - today.getDay() - 7);
      const lastWeekEnd = new Date(today);
      lastWeekEnd.setDate(today.getDate() - today.getDay() - 1);
      return {
        start: lastWeekStart.toISOString().split('T')[0] + 'T00:00:00',
        end: lastWeekEnd.toISOString().split('T')[0] + 'T23:59:59'
      };
    case 'custom':
      const startDate = document.getElementById('customStartDate').value;
      const endDate = document.getElementById('customEndDate').value;
      if (!startDate || !endDate) return null;
      return {
        start: startDate + 'T00:00:00',
        end: endDate + 'T23:59:59'
      };
    default:
      return null;
  }
}

// 載入 Git 使用者資訊
async function loadGitUserInfo() {
  try {
    const config = await apiCall('/config');
    const gitUser = config.git?.user || {};
    const gitName = gitUser.name || '未知';
    const gitEmail = gitUser.email || '未知';
    
    const currentGitUserEl = document.getElementById('currentGitUser');
    if (currentGitUserEl) {
      currentGitUserEl.textContent = `${gitName} (${gitEmail})`;
    }
  } catch (error) {
    console.error('載入 Git 使用者資訊失敗:', error);
    const currentGitUserEl = document.getElementById('currentGitUser');
    if (currentGitUserEl) {
      currentGitUserEl.textContent = '載入失敗';
    }
  }
}

// 更新 commit 預覽
async function updateCommitPreview() {
  if (!state.selectedRepo || !state.selectedBranch) {
    return;
  }
  
  const timeRange = getTimeRange(state.timeRange);
  if (!timeRange) {
    const commitCountEl = document.getElementById('commitCount');
    if (commitCountEl) commitCountEl.textContent = '0';
    return;
  }
  
  try {
    const result = await apiCall(
      `/preview-commits?repository_path=${encodeURIComponent(state.selectedRepo)}&branch=${encodeURIComponent(state.selectedBranch)}&start_date=${timeRange.start}&end_date=${timeRange.end}`
    );
    
    const commitCountEl = document.getElementById('commitCount');
    if (commitCountEl) {
      commitCountEl.textContent = String(result.count || 0);
    }
    
    // 更新 Git 使用者資訊（如果 API 有返回）
    if (result.user) {
      const currentGitUserEl = document.getElementById('currentGitUser');
      if (currentGitUserEl) {
        currentGitUserEl.textContent = `${result.user.name} (${result.user.email})`;
      }
    }
  } catch (error) {
    console.error('預覽 commit 失敗:', error);
    const commitCountEl = document.getElementById('commitCount');
    if (commitCountEl) commitCountEl.textContent = '?';
  }
}

// 開始分析
async function startAnalysis() {
  const timeRange = getTimeRange(state.timeRange);
  if (!timeRange) {
    showToast('請選擇時間範圍', 'warning');
    return;
  }
  
  // 顯示分析頁面並更新狀態
  showPage('analyzing');
  const analyzingCommitCountEl = document.getElementById('analyzingCommitCount');
  if (analyzingCommitCountEl) {
    // 先顯示「載入中...」，實際數量會在 API 回應後更新
    analyzingCommitCountEl.textContent = '載入中...';
  }
  
  // 更新分析狀態文字
  const analyzingCommitsEl = document.getElementById('analyzingCommits');
  if (analyzingCommitsEl) {
    analyzingCommitsEl.innerHTML = '<span class="text-blue-600">正在呼叫 Claude CLI 分析 commit...</span>';
  }
  
  try {
    const result = await apiCall('/analyze', {
      method: 'POST',
      body: JSON.stringify({
        issue_id: state.selectedIssue.id,
        repository_path: state.selectedRepo,
        branch: state.selectedBranch,
        start_date: timeRange.start,
        end_date: timeRange.end
      })
    });
    
    state.analysisResult = result;
    displayAnalysisResult(result);
    showPage('review');
  } catch (error) {
    // 顯示更詳細的錯誤訊息
    let errorMessage = `分析失敗: ${error.message}`;
    
    // 如果錯誤訊息很長，顯示前 500 字元並提示可查看控制台
    if (error.message && error.message.length > 500) {
      errorMessage = `分析失敗: ${error.message.substring(0, 500)}...\n\n（完整錯誤訊息請查看瀏覽器控制台）`;
      console.error('完整錯誤訊息:', error);
    }
    
    showToast(errorMessage, 'error', 7000);
    showPage('time-range');
  }
}

// 顯示分析結果
function displayAnalysisResult(result) {
  // 組合回報內容
  let notes = result.summary || '';
  if (result.completed_items && result.completed_items.length > 0) {
    notes += '\n\n完成項目：\n' + result.completed_items.map(item => `• ${item}`).join('\n');
  }
  if (result.technical_details && result.technical_details.length > 0) {
    notes += '\n\n技術細節：\n' + result.technical_details.map(detail => `• ${detail}`).join('\n');
  }
  if (result.blockers && result.blockers.length > 0) {
    notes += '\n\n阻礙：\n' + result.blockers.map(blocker => `• ${blocker}`).join('\n');
  }
  if (result.next_steps && result.next_steps.length > 0) {
    notes += '\n\n下一步：\n' + result.next_steps.map(step => `• ${step}`).join('\n');
  }
  
  document.getElementById('notesInput').value = notes;
  document.getElementById('percentDoneInput').value = result.suggested_percent_done || 0;
  
  // 顯示相關 commit
  const commitsDiv = document.getElementById('commitsAnalyzed');
  if (result.commits_analyzed && result.commits_analyzed.length > 0) {
    commitsDiv.innerHTML = result.commits_analyzed.map(c => 
      `<div>• ${c.hash} - ${c.message.split('\n')[0]}</div>`
    ).join('');
  } else {
    commitsDiv.innerHTML = '<p class="text-slate-500">無相關 commit</p>';
  }
}

// 更新 Redmine
async function updateRedmine() {
  const notes = document.getElementById('notesInput').value;
  const percentDone = parseInt(document.getElementById('percentDoneInput').value) || 0;
  const statusId = parseInt(document.getElementById('statusInput').value) || null;
  
  showPage('analyzing');
  
  try {
    const result = await apiCall('/update-redmine', {
      method: 'POST',
      body: JSON.stringify({
        issue_id: state.selectedIssue.id,
        notes: notes,
        percent_done: percentDone,
        status_id: statusId
      })
    });
    
    if (result.success) {
      const successDiv = document.getElementById('successResult');
      const redmineLink = document.getElementById('redmineLink');
      // 這裡需要從設定檔取得 Redmine URL
      redmineLink.href = `#`; // TODO: 從設定檔取得
      successDiv.classList.remove('hidden');
      document.getElementById('errorResult').classList.add('hidden');
      showPage('result');
    } else {
      throw new Error(result.errors?.join(', ') || '更新失敗');
    }
  } catch (error) {
    const errorDiv = document.getElementById('errorResult');
    document.getElementById('errorMessage').textContent = error.message;
    errorDiv.classList.remove('hidden');
    document.getElementById('successResult').classList.add('hidden');
    showPage('result');
  }
}

// 載入設定
async function loadSettings() {
  try {
    const config = await apiCall('/config');
    
    // 更新 Redmine 設定
    document.getElementById('redmineUrlInput').value = config.redmine?.url || '';
    document.getElementById('redmineApiKeyInput').value = ''; // API Key 已隱藏
    
    // 更新 AI 服務設定
    const aiConfig = config.ai || {};
    // 向後相容：如果沒有新的 ai 設定，使用舊的 claude 設定
    const aiProvider = aiConfig.provider || (config.claude ? 'claude' : 'claude');
    document.getElementById('aiProviderSelect').value = aiProvider;
    
    // 更新 Claude 設定
    const claudeConfig = aiConfig.claude || config.claude || {};
    document.getElementById('claudeCliPathInput').value = claudeConfig.cli_path || 'claude';
    document.getElementById('claudeModelSelect').value = claudeConfig.model || 'haiku';
    
    // 更新 Gemini 設定
    const geminiConfig = aiConfig.gemini || {};
    document.getElementById('geminiCliPathInput').value = geminiConfig.cli_path || 'gemini';
    document.getElementById('geminiModelSelect').value = geminiConfig.model || 'gemini-2.0-flash-exp';
    
    // 更新 OpenCode 設定
    const opencodeConfig = aiConfig.opencode || {};
    const opencodeCliPathInput = document.getElementById('opencodeCliPathInput');
    if (opencodeCliPathInput) {
      opencodeCliPathInput.value = opencodeConfig.cli_path || 'opencode';
    }
    
    // 更新超時時間（使用當前 provider 的設定）
    let currentProviderConfig;
    if (aiProvider === 'claude') {
      currentProviderConfig = claudeConfig;
    } else if (aiProvider === 'gemini') {
      currentProviderConfig = geminiConfig;
    } else if (aiProvider === 'opencode') {
      currentProviderConfig = opencodeConfig;
    } else {
      currentProviderConfig = claudeConfig;
    }
    // Gemini 和 OpenCode 預設 120 秒，Claude 預設 60 秒
    const defaultTimeout = (aiProvider === 'gemini' || aiProvider === 'opencode') ? 120 : 60;
    document.getElementById('aiTimeoutInput').value = currentProviderConfig.timeout || defaultTimeout;
    
    // 顯示/隱藏對應的設定區塊
    updateAISettingsVisibility(aiProvider);
    
    // 更新 Git 設定
    document.getElementById('gitAutoDetectCheckbox').checked = config.git?.auto_detect !== false;
    document.getElementById('gitUserNameInput').value = config.git?.user?.name || '';
    document.getElementById('gitUserEmailInput').value = config.git?.user?.email || '';
    
    const autoDetect = document.getElementById('gitAutoDetectCheckbox').checked;
    document.getElementById('gitUserNameInput').disabled = autoDetect;
    document.getElementById('gitUserEmailInput').disabled = autoDetect;
    
    // 更新掃描資料夾列表
    displayScanPaths(config.scan_paths || []);
  } catch (error) {
    console.error('載入設定失敗:', error);
  }
}

// 更新 AI 設定區塊的可見性
function updateAISettingsVisibility(provider) {
  const claudeSettings = document.getElementById('claudeSettings');
  const geminiSettings = document.getElementById('geminiSettings');
  const opencodeSettings = document.getElementById('opencodeSettings');
  
  // 隱藏所有設定區塊
  if (claudeSettings) claudeSettings.classList.add('hidden');
  if (geminiSettings) geminiSettings.classList.add('hidden');
  if (opencodeSettings) opencodeSettings.classList.add('hidden');
  
  // 顯示對應的設定區塊
  if (provider === 'claude' && claudeSettings) {
    claudeSettings.classList.remove('hidden');
  } else if (provider === 'gemini' && geminiSettings) {
    geminiSettings.classList.remove('hidden');
  } else if (provider === 'opencode' && opencodeSettings) {
    opencodeSettings.classList.remove('hidden');
  }
}

// 顯示掃描資料夾列表
function displayScanPaths(paths) {
  const listDiv = document.getElementById('scanPathsList');
  if (paths.length === 0) {
    listDiv.innerHTML = '<p class="text-sm text-slate-500 text-center py-2">尚未設定掃描資料夾</p>';
    return;
  }
  
  listDiv.innerHTML = paths.map((path, index) => `
    <div class="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-200">
      <span class="text-sm text-slate-700 flex-1 truncate" title="${path}">${path}</span>
      <button class="remove-scan-path-btn ml-2 px-2 py-1 text-red-600 hover:bg-red-50 rounded text-sm" data-index="${index}">
        移除
      </button>
    </div>
  `).join('');
  
  // 綁定移除按鈕事件
  listDiv.querySelectorAll('.remove-scan-path-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const index = parseInt(btn.dataset.index);
      removeScanPath(index);
    });
  });
}

// 移除掃描資料夾
async function removeScanPath(index) {
  try {
    const config = await apiCall('/config');
    const scanPaths = config.scan_paths || [];
    scanPaths.splice(index, 1);
    
    await apiCall('/config', {
      method: 'POST',
      body: JSON.stringify({ scan_paths: scanPaths })
    });
    
    displayScanPaths(scanPaths);
  } catch (error) {
    showToast(`移除失敗：${error.message}`, 'error');
  }
}

// 新增掃描資料夾
async function addScanPath() {
  // 使用 File System Access API 或回退方案
  if ('showDirectoryPicker' in window) {
    try {
      const directoryHandle = await window.showDirectoryPicker({
        mode: 'read'
      });
      
      const folderName = directoryHandle.name;
      const repoPath = prompt(`已選擇資料夾：${folderName}\n\n請輸入該資料夾的完整路徑：\n\n例如：D:\\Projects\\${folderName}`);
      if (repoPath && repoPath.trim()) {
        await saveScanPath(repoPath.trim());
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('選擇資料夾失敗:', error);
        // 回退到 prompt
        const repoPath = prompt('請輸入要掃描的資料夾完整路徑：\n例如：D:\\Projects');
        if (repoPath && repoPath.trim()) {
          await saveScanPath(repoPath.trim());
        }
      }
    }
  } else {
    // 回退方案：直接輸入
    const repoPath = prompt('請輸入要掃描的資料夾完整路徑：\n例如：D:\\Projects');
    if (repoPath && repoPath.trim()) {
      await saveScanPath(repoPath.trim());
    }
  }
}

// 儲存掃描資料夾
async function saveScanPath(path) {
  try {
    const config = await apiCall('/config');
    const scanPaths = config.scan_paths || [];
    
    // 檢查是否已存在
    if (scanPaths.includes(path)) {
      showToast('此資料夾已經在掃描列表中', 'warning');
      return;
    }
    
    scanPaths.push(path);
    
    await apiCall('/config', {
      method: 'POST',
      body: JSON.stringify({ scan_paths: scanPaths })
    });
    
    displayScanPaths(scanPaths);
  } catch (error) {
    showToast(`新增失敗：${error.message}`, 'error');
  }
}

// 儲存設定
async function saveSettings() {
  try {
    const aiProvider = document.getElementById('aiProviderSelect').value;
    const timeout = parseInt(document.getElementById('aiTimeoutInput').value) || 60;
    
    const config = {
      redmine: {
        url: document.getElementById('redmineUrlInput').value,
        api_key: document.getElementById('redmineApiKeyInput').value || undefined
      },
      ai: {
        provider: aiProvider,
        claude: {
          cli_path: document.getElementById('claudeCliPathInput').value,
          model: document.getElementById('claudeModelSelect').value,
          timeout: timeout,
          system_prompt_file: 'prompts/redmine_analysis.txt'
        },
        gemini: {
          cli_path: document.getElementById('geminiCliPathInput').value,
          model: document.getElementById('geminiModelSelect').value,
          timeout: timeout,
          system_prompt_file: 'prompts/redmine_analysis.txt'
        },
        opencode: {
          cli_path: document.getElementById('opencodeCliPathInput')?.value || 'opencode',
          timeout: timeout,
          system_prompt_file: 'prompts/redmine_analysis.txt'
        }
      },
      git: {
        auto_detect: document.getElementById('gitAutoDetectCheckbox').checked,
        user: {
          name: document.getElementById('gitUserNameInput').value,
          email: document.getElementById('gitUserEmailInput').value
        }
      }
    };
    
    await apiCall('/config', {
      method: 'POST',
      body: JSON.stringify(config)
    });
    
    showToast('設定已儲存', 'success');
    showPage('issue-list');
    loadIssues();
  } catch (error) {
    showToast(`儲存設定失敗：${error.message}`, 'error');
  }
}

// 事件監聽器
document.addEventListener('DOMContentLoaded', () => {
  // 頁面載入時載入工單列表
  loadIssues();
  loadSettings();
  // 預設時間範圍：本週（避免「開始分析」時 state.timeRange 為 null）
  state.timeRange = 'thisWeek';
  
  // 重新整理按鈕
  document.getElementById('refreshBtn').addEventListener('click', async () => {
    // 保留當前的篩選和搜尋條件
    const statusId = document.getElementById('statusFilter').value === 'all' ? null : document.getElementById('statusFilter').value;
    const search = document.getElementById('searchInput').value || null;

    // 先主動重試 Redmine 連線，再載入工單（避免使用者以為「重新整理」沒動作）
    try {
      await apiCall('/redmine/ping');
      setRedmineBadge('ok');
      showToast('Redmine 連線正常，已重新整理工單。', 'success', 2200);
    } catch (error) {
      setRedmineBadge('error', error.message);
      showToast(`Redmine 連線失敗，請檢查設定或網路：${error.message}`, 'error', 6000);
      return;
    }

    loadIssues(statusId, search);
  });
  
  // 設定按鈕
  document.getElementById('settingsBtn').addEventListener('click', () => {
    loadSettings();
    showPage('settings');
  });
  
  // 篩選和搜尋
  document.getElementById('statusFilter').addEventListener('change', (e) => {
    const statusId = e.target.value === 'all' ? null : e.target.value;
    const search = document.getElementById('searchInput').value || null;
    loadIssues(statusId, search);
  });
  
  document.getElementById('searchInput').addEventListener('input', (e) => {
    const statusId = document.getElementById('statusFilter').value === 'all' ? null : document.getElementById('statusFilter').value;
    const search = e.target.value || null;
    loadIssues(statusId, search);
  });
  
  // 儲存庫選擇
  document.getElementById('repoSelect').addEventListener('change', (e) => {
    const selectedOption = e.target.options[e.target.selectedIndex];
    if (selectedOption.value) {
      selectRepository(selectedOption.dataset.path);
    }
  });

  // Repo search
  const repoSearchInput = document.getElementById('repoSearchInput');
  const clearRepoSearchBtn = document.getElementById('clearRepoSearchBtn');
  if (repoSearchInput && clearRepoSearchBtn) {
    repoSearchInput.addEventListener('input', (e) => {
      const q = e.target.value || '';
      clearRepoSearchBtn.classList.toggle('hidden', q.length === 0);
      renderRepoList(state.repositories, q);
    });
    clearRepoSearchBtn.addEventListener('click', () => {
      repoSearchInput.value = '';
      clearRepoSearchBtn.classList.add('hidden');
      renderRepoList(state.repositories, '');
      repoSearchInput.focus();
    });
  }

  // Toggle view
  const toggleRepoViewBtn = document.getElementById('toggleRepoViewBtn');
  if (toggleRepoViewBtn) {
    toggleRepoViewBtn.addEventListener('click', () => {
      setRepoViewMode(state.repoViewMode === 'list' ? 'select' : 'list');
    });
    setRepoViewMode('list');
  }
  
  // 新增儲存庫按鈕（使用 File System Access API 或回退方案）
  document.getElementById('addRepoBtn').addEventListener('click', async () => {
    // 嘗試使用 File System Access API（Chrome/Edge 支援，需要 HTTPS 或 localhost）
    if ('showDirectoryPicker' in window) {
      try {
        const directoryHandle = await window.showDirectoryPicker({
          mode: 'read'
        });
        
        // 從 directoryHandle 取得名稱（但無法取得完整路徑）
        // 所以我們需要提示用戶輸入完整路徑，或使用其他方式
        // 實際上，File System Access API 也無法直接取得完整路徑
        // 但我們可以讓用戶選擇資料夾後，提示輸入完整路徑
        const folderName = directoryHandle.name;
        showToast(`已選擇資料夾：${folderName}。請在下一個視窗輸入完整路徑（瀏覽器安全限制無法自動取得）。`, 'info', 5000);
        const repoPath = prompt(`請輸入資料夾的完整路徑：\n\n已選擇的資料夾名稱：${folderName}\n\n例如：D:\\Projects\\${folderName}`);
        if (repoPath && repoPath.trim()) {
          addRepository(repoPath.trim());
        }
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('選擇資料夾失敗:', error);
          // 回退到 prompt
          const repoPath = prompt('請輸入 Git 儲存庫的完整路徑：\n例如：D:\\Projects\\my-project');
          if (repoPath && repoPath.trim()) {
            addRepository(repoPath.trim());
          }
        }
      }
    } else {
      // 回退方案：使用傳統的 input file（選擇資料夾內的檔案）
      document.getElementById('folderPicker').click();
    }
  });
  
  // 資料夾選擇處理（回退方案）
  document.getElementById('folderPicker').addEventListener('change', (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      // 從 webkitRelativePath 推斷資料夾名稱
      const firstFile = files[0];
      let folderName = '';
      
      if (firstFile.webkitRelativePath) {
        // webkitRelativePath 格式：資料夾名稱/子資料夾/檔案名
        const parts = firstFile.webkitRelativePath.split(/[/\\]/);
        folderName = parts[0]; // 第一個部分是根資料夾名稱
      }
      
      // 提示用戶輸入完整路徑
      const message = folderName 
        ? `已選擇資料夾內的檔案。\n\n資料夾名稱：${folderName}\n\n請輸入該資料夾的完整路徑：`
        : '請輸入 Git 儲存庫的完整路徑：';
      
      const example = folderName 
        ? `例如：D:\\Projects\\${folderName}`
        : '例如：D:\\Projects\\my-project';
      
      const repoPath = prompt(`${message}\n\n${example}`);
      if (repoPath && repoPath.trim()) {
        addRepository(repoPath.trim());
      }
      
      // 清空選擇，以便下次可以再次選擇
      e.target.value = '';
    }
  });
  
  // 返回按鈕
  document.getElementById('backToIssuesBtn').addEventListener('click', () => {
    showPage('issue-list');
  });
  
  // 下一步：到時間範圍選擇
  document.getElementById('nextToTimeRangeBtn').addEventListener('click', () => {
    if (!state.selectedRepo || !state.selectedBranch) {
      showToast('請先選擇儲存庫與分支', 'warning');
      return;
    }
    showPage('time-range');
  });

  document.getElementById('backToRepoBtn').addEventListener('click', () => {
    showPage('repo-select');
  });
  
  document.getElementById('backToTimeRangeBtn').addEventListener('click', () => {
    showPage('time-range');
  });
  
  document.getElementById('backToIssuesFromResultBtn').addEventListener('click', () => {
    showPage('issue-list');
    loadIssues();
  });
  
  document.getElementById('backToReviewBtn').addEventListener('click', () => {
    showPage('review');
  });
  
  // 時間範圍選擇
  document.querySelectorAll('input[name="timeRange"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      state.timeRange = e.target.value;
      const customInputs = document.querySelectorAll('#customStartDate, #customEndDate');
      if (e.target.value === 'custom') {
        customInputs.forEach(input => input.disabled = false);
        // 自訂日期改變時也更新預覽
        customInputs.forEach(input => {
          input.addEventListener('change', updateCommitPreview);
        });
      } else {
        customInputs.forEach(input => input.disabled = true);
      }
      // 更新預覽
      updateCommitPreview();
    });
  });
  
  // 當進入時間範圍選擇頁面時，載入 Git 使用者資訊和預覽
  const timeRangePage = document.getElementById('page-time-range');
  if (timeRangePage) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          if (timeRangePage.classList.contains('active')) {
            loadGitUserInfo();
            updateCommitPreview();
          }
        }
      });
    });
    observer.observe(timeRangePage, { attributes: true, attributeFilter: ['class'] });
  }
  
  // 開始分析
  document.getElementById('startAnalysisBtn').addEventListener('click', startAnalysis);
  
  // 確認更新
  document.getElementById('confirmUpdateBtn').addEventListener('click', updateRedmine);
  
  // 設定頁面
  document.getElementById('gitAutoDetectCheckbox').addEventListener('change', (e) => {
    const disabled = e.target.checked;
    document.getElementById('gitUserNameInput').disabled = disabled;
    document.getElementById('gitUserEmailInput').disabled = disabled;
  });
  
  document.getElementById('cancelSettingsBtn').addEventListener('click', () => {
    showPage('issue-list');
  });
  
  document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
  
  // 新增掃描資料夾按鈕
  document.getElementById('addScanPathBtn').addEventListener('click', addScanPath);
  
  // AI 服務提供者選擇
  document.getElementById('aiProviderSelect').addEventListener('change', (e) => {
    const provider = e.target.value;
    updateAISettingsVisibility(provider);
    // 切換 provider 時，更新超時時間的預設值提示
    const defaultTimeout = (provider === 'gemini' || provider === 'opencode') ? 120 : 60;
    const timeoutInput = document.getElementById('aiTimeoutInput');
    // 如果當前值是預設值，則更新為新 provider 的預設值
    if (!timeoutInput.value || timeoutInput.value === '60' || timeoutInput.value === '120') {
      timeoutInput.value = defaultTimeout;
    }
  });
  
  // 重試更新
  document.getElementById('retryUpdateBtn').addEventListener('click', updateRedmine);
});
