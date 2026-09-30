/**
 * ⚡ OpenCode Swarm Cockpit & GetBrain Web Application
 * Pure Vanilla JavaScript (ES6+)
 * Features:
 *   - Real-Time Server-Sent Events (SSE) stream listener
 *   - Cockpit UI renderer (Agents, Kanban, Live Feed, Artifacts, Memories)
 *   - Interactive 2D Physics Canvas Engine for GetBrain Knowledge Graph
 *   - Drag, Pan, Zoom, Filtering, Node Inspector
 */

// Application State
const state = {
  currentView: 'cockpit',
  project: 'default',
  branch: 'main',
  agents: [],
  tasks: [],
  messages: [],
  artifacts: [],
  memories: [],
  brain: { nodes: [], links: [] },
  activeFilter: 'all', // kanban filter
  brainFilters: {
    agent: true,
    task: true,
    artifact: true,
    memory: true,
    module: true
  },
  searchQuery: '',
  selectedNode: null
};

// ─────────────────────────────────────────────────────────────
// INITIALIZATION
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSSE();
  fetchInitialData();
  initBrainCanvas();
  closeInspector();
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeInspector();
  });

  // Check URL hash for direct tab navigation
  if (window.location.hash === '#brain') {
    switchView('brain');
  } else if (window.location.hash === '#tester') {
    switchView('tester');
  }
});

function switchView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

  if (viewName === 'cockpit') {
    const panel = document.getElementById('viewCockpit');
    const tab = document.getElementById('tabCockpit');
    if (panel) panel.classList.add('active');
    if (tab) tab.classList.add('active');
    try { history.replaceState(null, null, window.location.pathname); } catch (e) {}
  } else if (viewName === 'brain') {
    const panel = document.getElementById('viewBrain');
    const tab = document.getElementById('tabBrain');
    if (panel) panel.classList.add('active');
    if (tab) tab.classList.add('active');
    try { history.replaceState(null, null, '#brain'); } catch (e) {}
    requestAnimationFrame(() => {
      resizeCanvas();
      if (state.brain && state.brain.nodes && (!graphNodes || graphNodes.length === 0)) {
        setupBrainSimulation(state.brain.nodes, state.brain.links);
      } else {
        drawGraph();
      }
    });
    fetchBrainGraph();
  } else if (viewName === 'tester') {
    const panel = document.getElementById('viewTester');
    const tab = document.getElementById('tabTester');
    if (panel) panel.classList.add('active');
    if (tab) tab.classList.add('active');
    try { history.replaceState(null, null, '#tester'); } catch (e) {}
    fetchTesterData();
  }
}

// ─────────────────────────────────────────────────────────────
// REAL-TIME SSE & DATA FETCHING
// ─────────────────────────────────────────────────────────────
let sseFallbackTimer = null;

function initSSE() {
  const liveDot = document.querySelector('.pulse-dot');
  const liveText = document.getElementById('liveStatusText');

  function startFallbackPolling() {
    if (!sseFallbackTimer) {
      sseFallbackTimer = setInterval(fetchInitialData, 2500);
    }
  }

  function stopFallbackPolling() {
    if (sseFallbackTimer) {
      clearInterval(sseFallbackTimer);
      sseFallbackTimer = null;
    }
  }

  try {
    const evtSource = new EventSource('/api/stream');

    evtSource.onopen = () => {
      stopFallbackPolling();
      if (liveText) {
        liveText.textContent = 'LIVE SSE';
        liveText.style.color = '#34d399';
      }
      if (liveDot) liveDot.style.background = '#10b981';
    };

    evtSource.onmessage = (event) => {
      try {
        const data = jsonParseSafe(event.data);
        if (data) {
          updateSwarmUI(data);
        }
      } catch (err) {
        console.error('SSE data parse error:', err);
      }
    };

    evtSource.onerror = () => {
      if (liveText) {
        liveText.textContent = 'RECONNECTING (POLLING)';
        liveText.style.color = '#fbbf24';
      }
      if (liveDot) liveDot.style.background = '#f59e0b';
      startFallbackPolling();
    };
  } catch (e) {
    console.warn('SSE unavailable, falling back to polling');
    startFallbackPolling();
  }
}

async function safeFetchJson(url, fallback = {}) {
  try {
    const res = await fetch(url);
    if (!res.ok) return fallback;
    return await res.json();
  } catch (e) {
    return fallback;
  }
}

async function fetchInitialData() {
  try {
    const [resStatus, resTasks, resArtifacts, resMemories, resFeed, resSentinel, resTester] = await Promise.all([
      safeFetchJson('/api/status', { project: 'default', agents: [] }),
      safeFetchJson('/api/tasks', { tasks: [] }),
      safeFetchJson('/api/artifacts', { artifacts: [] }),
      safeFetchJson('/api/memories', { memories: [] }),
      safeFetchJson('/api/feed', { feed: [] }),
      safeFetchJson('/api/sentinel', { status: 'COMPLIANT', score: 100 }),
      safeFetchJson('/api/tester', { health: 'MONITORING', runs: [], probes: [], components: [] })
    ]);

    updateSwarmUI({
      project: resStatus.project,
      project_dir: resStatus.project_dir,
      branch: resStatus.branch,
      clock: resStatus.clock,
      agents: resStatus.agents || [],
      tasks: resTasks.tasks || [],
      messages: resFeed.feed || []
    });

    renderArtifacts(resArtifacts.artifacts || []);
    renderMemories(resMemories.memories || []);
    updateSentinelUI(resSentinel);
    updateTesterUI(resTester);
    fetchBrainGraph();
  } catch (err) {
    console.error('Error fetching initial data:', err);
  }
}

function updateSentinelUI(sentinel) {
  const textEl = document.getElementById('sentinelStatusText');
  const pillEl = document.getElementById('sentinelPill');
  if (!textEl || !sentinel) return;

  const score = sentinel.score !== undefined ? sentinel.score : 100;
  const status = sentinel.status || (score >= 80 ? 'COMPLIANT' : 'NON-COMPLIANT');

  textEl.textContent = `SENTINEL: ${status} (${score}%)`;
  if (pillEl) {
    if (status === 'COMPLIANT') {
      pillEl.style.background = 'rgba(16, 185, 129, 0.15)';
      pillEl.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      pillEl.style.color = '#34d399';
    } else {
      pillEl.style.background = 'rgba(239, 68, 68, 0.15)';
      pillEl.style.borderColor = 'rgba(239, 68, 68, 0.3)';
      pillEl.style.color = '#f87171';
    }
  }

  const mValSentinel = document.getElementById('mValSentinel');
  if (mValSentinel) {
    mValSentinel.textContent = `${score}% ${status}`;
    mValSentinel.className = status === 'COMPLIANT' ? 'm-val val-blue' : 'm-val val-red';
  }
  const mSubSentinel = document.getElementById('mSubSentinel');
  if (mSubSentinel) {
    mSubSentinel.textContent = `${sentinel.rules ? sentinel.rules.length : 7} reglas activas enforcadas`;
  }

  renderSentinelRules(sentinel.rules || []);
}

function renderSentinelRules(rules) {
  const container = document.getElementById('sentinelRulesList');
  if (!container) return;

  if (!rules || rules.length === 0) {
    container.innerHTML = '<div class="empty-state">[ sin reglas de ingeniería registradas ]</div>';
    return;
  }

  const countEl = document.getElementById('sentinelRulesCount');
  if (countEl) countEl.textContent = `${rules.length} reglas`;

  container.innerHTML = rules.map(r => {
    const sevColor = r.severity === 'critical' ? 'var(--term-amber)' : 'var(--term-blue)';
    return `
      <div class="rule-card">
        <div class="rule-card-header">
          <span class="rule-code" style="color: ${sevColor}">[${escapeHtml(r.rule_code)}]</span>
          <span class="rule-title">${escapeHtml(r.title)}</span>
          <span class="rule-agent">@${escapeHtml(r.target_agent)}</span>
        </div>
        <div class="rule-desc">${escapeHtml(r.description)}</div>
      </div>
    `;
  }).join('');
}

async function fetchTesterData() {
  const [dataTester, dataSentinel] = await Promise.all([
    safeFetchJson('/api/tester', { health: 'MONITORING', runs: [], probes: [], components: [] }),
    safeFetchJson('/api/sentinel', { status: 'COMPLIANT', score: 100, rules: [] })
  ]);
  updateTesterUI(dataTester);
  updateSentinelUI(dataSentinel);
}

function updateTesterUI(tester) {
  if (!tester) return;
  const pillEl = document.getElementById('testerPill');
  const textEl = document.getElementById('testerStatusText');
  const badgeEl = document.getElementById('testerHealthBadge');
  const countEl = document.getElementById('testPassCount');
  const runsCountEl = document.getElementById('testRunsCount');
  const runnerBadge = document.getElementById('testRunnerBadge');

  const health = tester.health || 'MONITORING';
  if (textEl) textEl.textContent = `TESTER: ${health}`;
  if (badgeEl) {
    badgeEl.textContent = health;
    if (health === 'HEALTHY') {
      badgeEl.className = 'health-badge healthy';
      badgeEl.style.background = 'rgba(16, 185, 129, 0.15)';
      badgeEl.style.color = 'var(--term-green)';
      badgeEl.style.borderColor = 'rgba(16, 185, 129, 0.3)';
    } else if (health === 'DEGRADED') {
      badgeEl.className = 'health-badge degraded';
      badgeEl.style.background = 'rgba(245, 158, 11, 0.15)';
      badgeEl.style.color = 'var(--term-amber)';
      badgeEl.style.borderColor = 'rgba(245, 158, 11, 0.3)';
    } else {
      badgeEl.className = 'health-badge failing';
      badgeEl.style.background = 'rgba(239, 68, 68, 0.15)';
      badgeEl.style.color = 'var(--term-red)';
      badgeEl.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    }
  }

  if (runnerBadge && tester.detected_runner) {
    runnerBadge.textContent = `runner: ${tester.detected_runner}`;
  }

  const runs = tester.runs || [];
  const latestRun = runs[0];
  const passed = latestRun ? latestRun.passed : 0;
  if (countEl) countEl.textContent = passed;
  if (runsCountEl) runsCountEl.textContent = runs.length;

  const failedRuns = runs.filter(r => r.status === 'FAIL').length;
  const passedRuns = runs.filter(r => r.status === 'PASS').length;

  const mValAssertions = document.getElementById('mValAssertions');
  const mSubAssertions = document.getElementById('mSubAssertions');
  if (mValAssertions) {
    if (failedRuns > 0) {
      mValAssertions.textContent = `${failedRuns} FALLOS`;
      mValAssertions.className = 'm-val val-red';
    } else {
      mValAssertions.textContent = '100% GREEN';
      mValAssertions.className = 'm-val val-green';
    }
  }
  if (mSubAssertions) {
    mSubAssertions.textContent = runs.length > 0
      ? `${passedRuns} pasadas · ${failedRuns} fallos`
      : 'cero fallos de regresión';
  }

  // Render runs or diagnostic fallback
  const runsList = document.getElementById('testRunsList');
  if (runsList) {
    if (runs.length === 0) {
      const runnerName = (tester.detected_runner && tester.detected_runner !== 'none') ? tester.detected_runner : 'python unittest';
      const testFilesList = (tester.test_files && tester.test_files.length) ? tester.test_files.slice(0, 3).join(', ') : 'tests/';
      runsList.innerHTML = `
        <div class="diagnostic-box">
          <div class="diag-header">[ DIAGNÓSTICO DEL ENTORNO DE PRUEBAS ]</div>
          <div class="diag-row">
            <span class="diag-label">Framework detectado:</span>
            <span class="diag-val">${escapeHtml(runnerName)}</span>
          </div>
          <div class="diag-row">
            <span class="diag-label">Suites en workspace:</span>
            <span class="diag-val">${escapeHtml(testFilesList)}</span>
          </div>
          <div class="diag-row">
            <span class="diag-label">Vigilancia Sentinel:</span>
            <span class="diag-val" style="color: var(--term-green);">TDD-001 Activo (Aserciones requeridas)</span>
          </div>
          <div class="diag-row">
            <span class="diag-label">Modo de disparo:</span>
            <span class="diag-val">Autónomo en handoffs / CLI ('ecc test')</span>
          </div>
          <div style="font-size: 10px; color: var(--text-dim); margin-top: 4px; line-height: 1.4;">
            ℹ Los subagentes ejecutan las suites en segundo plano y los resultados se transmiten en vivo aquí.
          </div>
        </div>
      `;
    } else {
      runsList.innerHTML = runs.map(r => {
        const isPass = r.status === 'PASS';
        const color = isPass ? 'var(--term-green)' : 'var(--term-red)';
        const bg = isPass ? 'rgba(63, 185, 80, 0.05)' : 'rgba(248, 81, 73, 0.08)';
        const border = isPass ? 'rgba(63, 185, 80, 0.25)' : 'rgba(248, 81, 73, 0.3)';
        return `
          <div style="background: ${bg}; border: 1px solid ${border}; border-radius: var(--radius-xs); padding: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 700; color: ${color}; font-size: 11px;">[${r.status}]</span>
                <span style="font-size: 12px; font-weight: 600; color: var(--text-title);">${escapeHtml(r.runner || 'runner')}</span>
                ${r.target_path ? `<span style="font-size: 10px; color: var(--text-dim); font-family: var(--font-mono);">${escapeHtml(r.target_path)}</span>` : ''}
              </div>
              <span style="font-size: 10px; color: var(--text-dim);">${escapeHtml(r.duration_ms || 0)}ms</span>
            </div>
            <div style="display: flex; gap: 12px; font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">
              <span>✓ ${r.passed || 0} pasados</span>
              <span>✗ ${r.failed || 0} fallados</span>
              <span>⏭ ${r.skipped || 0} omitidos</span>
              ${r.coverage_percent > 0 ? `<span style="font-weight: 600; color: var(--term-blue);">Cobertura: ${r.coverage_percent}%</span>` : ''}
            </div>
            <details style="font-size: 10px; color: var(--text-dim); cursor: pointer;">
              <summary>Ver salida de consola</summary>
              <pre style="margin-top: 6px; padding: 8px; background: var(--bg-base); border: 1px solid var(--border); border-radius: var(--radius-xs); overflow-x: auto; color: var(--text-main); font-family: var(--font-mono); font-size: 10px; max-height: 160px;">${escapeHtml(r.output || 'Sin salida')}</pre>
            </details>
          </div>
        `;
      }).join('');
    }
  }

  // Render probes
  const probesList = document.getElementById('endpointProbesList');
  if (probesList) {
    const probes = tester.probes || [];
    if (probes.length === 0) {
      probesList.innerHTML = '<div class="empty-state">[ sin sondeos recientes ]</div>';
    } else {
      probesList.innerHTML = probes.map(p => {
        const isPass = p.status === 'PASS';
        const color = isPass ? 'var(--term-green)' : 'var(--term-red)';
        return `
          <div style="background: var(--bg-base); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 6px 8px; font-size: 11px; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              <span style="font-weight: 700; color: var(--term-blue);">${escapeHtml(p.method || 'GET')}</span>
              <span style="color: var(--text-main); font-family: var(--font-mono); font-size: 10px;">${escapeHtml(p.url)}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 10px; color: var(--text-dim);">${p.latency_ms || 0}ms</span>
              <span style="font-weight: 600; color: ${color}; font-size: 10px;">${p.actual_status || 'ERR'}</span>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  // Render component checks
  const compsList = document.getElementById('componentChecksList');
  if (compsList) {
    const comps = tester.components || [];
    if (comps.length === 0) {
      compsList.innerHTML = '<div class="empty-state">[ sin verificaciones de componentes ]</div>';
    } else {
      compsList.innerHTML = comps.map(c => {
        const isPass = c.status === 'PASS';
        const isWarn = c.status === 'WARN';
        const color = isPass ? 'var(--term-green)' : (isWarn ? 'var(--term-amber)' : 'var(--term-red)');
        return `
          <div style="background: var(--bg-base); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 6px 8px; font-size: 11px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
              <span style="font-weight: 600; color: var(--text-title); font-family: var(--font-mono); font-size: 10px;">${escapeHtml(c.file_path)}</span>
              <span style="font-weight: 700; color: ${color}; font-size: 10px;">[${c.status}]</span>
            </div>
            <div style="font-size: 10px; color: var(--text-dim); white-space: pre-wrap; font-family: var(--font-mono);">${escapeHtml(c.details || '')}</div>
          </div>
        `;
      }).join('');
    }
  }
}

async function triggerRunTests() {
  const btn = document.getElementById('btnRunTests');
  const input = document.getElementById('testPathInput');
  const path = input ? input.value.trim() : '';

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span><span>Ejecutando...</span>';
  }

  try {
    const res = await fetch('/api/tester/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    });
    await res.json();
    await fetchTesterData();
  } catch (e) {
    console.error('Error running tests:', e);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>▶</span><span>Ejecutar Tests Ahora</span>';
    }
  }
}

async function triggerProbeEndpoint() {
  const input = document.getElementById('probeUrlInput');
  const url = input ? input.value.trim() : '';
  if (!url) return;

  try {
    await fetch('/api/tester/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, method: 'GET' })
    });
    await fetchTesterData();
  } catch (e) {
    console.error('Error probing endpoint:', e);
  }
}

async function fetchBrainGraph() {
  try {
    const res = await fetch('/api/brain');
    const data = await res.json();
    const bnc = document.getElementById('brainNodesCount');
    if (bnc) bnc.textContent = data.nodes ? data.nodes.length : 0;
    setupBrainSimulation(data.nodes, data.links);
  } catch (err) {
    console.error('Error fetching brain graph:', err);
  }
}

// ─────────────────────────────────────────────────────────────
// COCKPIT RENDERING
// ─────────────────────────────────────────────────────────────
function updateSwarmUI(data) {
  if (data.project) {
    state.project = data.project;
    const nameEl = document.getElementById('projectName');
    if (nameEl) nameEl.textContent = data.project;
    document.title = `⚡ OpenCode Swarm [${data.project}]`;
  }
  if (data.project_dir) {
    state.projectDir = data.project_dir;
    const pill = document.getElementById('projectPill');
    if (pill) {
      pill.title = `Directorio del Proyecto: ${data.project_dir}`;
    }
  }
  if (data.branch) {
    const branchEl = document.getElementById('projectBranch');
    if (branchEl) branchEl.textContent = data.branch;
  }
  if (data.clock) {
    const clockEl = document.getElementById('liveClock');
    if (clockEl) clockEl.textContent = data.clock;
  }

  if (data.agents) {
    state.agents = data.agents;
    renderAgents(data.agents);
  }

  if (data.tasks) {
    state.tasks = data.tasks;
    renderKanban(data.tasks);
  }

  if (data.messages) {
    state.messages = data.messages;
    renderFeed(data.messages);
  }
}

const ROSTER_CONFIG = {
  orchestrator: { glyph: '👑', color: '#8B5CF6', title: 'Lead Architect' },
  backend:      { glyph: '⚡', color: '#3B82F6', title: 'Backend Specialist' },
  frontend:     { glyph: '🎨', color: '#EC4899', title: 'Frontend Specialist' },
  'git-flow':   { glyph: '🌿', color: '#10B981', title: 'Git Flow Manager' },
  'qa-auditor': { glyph: '🛡️', color: '#F59E0B', title: 'QA & Security Auditor' },
  devops:       { glyph: '🐳', color: '#06B6D4', title: 'DevOps & Containers' }
};

function renderAgents(agentsList) {
  const container = document.getElementById('agentsGrid');
  if (!container) return;

  const agentMap = {};
  agentsList.forEach(a => { agentMap[a.agent_name] = a; });

  let activeCount = 0;
  let html = '';

  Object.keys(ROSTER_CONFIG).forEach(role => {
    const cfg = ROSTER_CONFIG[role];
    const ag = agentMap[role] || {
      agent_name: role,
      status: 'idle',
      current_task: '',
      window_id: '',
      relative_time: 'esperando'
    };

    const isWorking = ag.status === 'working';
    if (isWorking) activeCount++;

    const statusClass = ag.status || 'idle';
    const statusLabel = isWorking ? 'WORKING' : (ag.status ? ag.status.toUpperCase() : 'IDLE');
    const windowTag = ag.window_id ? `<span class="window-tag">🖥️ ${ag.window_id}</span>` : `<span class="window-tag">session</span>`;
    const taskSnippet = ag.current_task ? ag.current_task : 'Listo para asignación de tareas...';

    html += `
      <div class="agent-card" style="--agent-color: ${cfg.color};">
        <div class="agent-header">
          <div class="agent-id">
            <div class="agent-avatar">${cfg.glyph}</div>
            <div class="agent-name-title">
              <span class="agent-name">@${role}</span>
              <span class="agent-role">${cfg.title}</span>
            </div>
          </div>
          <span class="status-pill ${statusClass}">
            ${isWorking ? '<span class="pulse-dot"></span>' : ''}
            ${statusLabel}
          </span>
        </div>

        <div class="agent-task-box">
          <div class="task-label">Tarea Actual:</div>
          <div class="task-text">${escapeHtml(taskSnippet)}</div>
        </div>

        <div class="agent-footer">
          ${windowTag}
          <span>${ag.relative_time || 'reciente'}</span>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  const aab = document.getElementById('activeAgentsBadge');
  if (aab) aab.textContent = `${activeCount} Agente(s) en Ejecución`;
}

function renderKanban(tasksList) {
  const cols = {
    todo: document.getElementById('cardsTodo'),
    in_progress: document.getElementById('cardsInProgress'),
    review: document.getElementById('cardsReview'),
    completed: document.getElementById('cardsCompleted')
  };

  const counts = { todo: 0, in_progress: 0, review: 0, completed: 0 };
  const htmls = { todo: '', in_progress: '', review: '', completed: '' };

  tasksList.forEach(t => {
    let st = t.status || 'todo';
    if (!cols[st]) st = 'todo';
    counts[st]++;

    // Filter check
    if (state.activeFilter !== 'all' && state.activeFilter !== st) {
      return;
    }

    const priorityClass = t.priority ? t.priority.toLowerCase() : 'normal';
    const assigneeStr = t.assigned_to ? `@${t.assigned_to}` : 'Sin Asignar';
    const notesStr = t.notes ? `<div style="font-size:10px; color:#94a3b8; margin-top:4px;">↳ ${escapeHtml(t.notes)}</div>` : '';

    htmls[st] += `
      <div class="task-item-card" onclick="inspectTask(${t.id})">
        <div class="task-item-top">
          <span class="task-id">#${t.id}</span>
          <span class="priority-tag ${priorityClass}">${t.priority || 'normal'}</span>
        </div>
        <div class="task-item-title">${escapeHtml(t.title)}</div>
        ${notesStr}
        <div class="task-item-footer">
          <span class="assignee-badge">${assigneeStr}</span>
          <span>${t.relative_time || ''}</span>
        </div>
      </div>
    `;
  });

  const cTodo = document.getElementById('countTodo');
  if (cTodo) cTodo.textContent = counts.todo;
  const cInProg = document.getElementById('countInProgress');
  if (cInProg) cInProg.textContent = counts.in_progress;
  const cRev = document.getElementById('countReview');
  if (cRev) cRev.textContent = counts.review;
  const cComp = document.getElementById('countCompleted');
  if (cComp) cComp.textContent = counts.completed;

  Object.keys(cols).forEach(k => {
    if (cols[k]) {
      cols[k].innerHTML = htmls[k] || '<div style="font-size:11px; color:#475569; padding:8px; text-align:center;">Sin tareas</div>';
    }
  });
}

function renderFeed(messages) {
  const container = document.getElementById('feedStream');
  if (!container) return;

  if (!messages || messages.length === 0) {
    container.innerHTML = '<div class="feed-empty">No hay mensajes recientes en el bus.</div>';
    return;
  }

  let html = '';
  messages.forEach(m => {
    const cat = m.category || 'status';
    html += `
      <div class="feed-item">
        <div class="feed-item-header">
          <span class="feed-sender">@${escapeHtml(m.sender)}</span>
          <span class="category-badge ${cat}">${cat.toUpperCase()}</span>
        </div>
        <div class="feed-msg">${escapeHtml(m.message)}</div>
        <div class="feed-time">${m.relative_time || m.created_at || ''}</div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderArtifacts(artifacts) {
  const container = document.getElementById('artifactsList');
  const acb = document.getElementById('artifactsCountBadge');
  const count = artifacts ? artifacts.length : 0;
  if (acb) acb.textContent = `${count} Contrato(s)`;
  if (!container) return;

  if (!artifacts || artifacts.length === 0) {
    container.innerHTML = '<div class="empty-state">No hay contratos compartidos aún.</div>';
    return;
  }

  let html = '';
  artifacts.forEach(art => {
    html += `
      <div class="art-card" onclick="openArtifactModal('${art.artifact_key}')">
        <div class="art-left">
          <div class="art-title">${escapeHtml(art.title)}</div>
          <div class="art-key">🔑 ${escapeHtml(art.artifact_key)} • por @${escapeHtml(art.creator)}</div>
        </div>
        <span class="art-type-tag">${art.artifact_type || 'contract'}</span>
      </div>
    `;
  });
  container.innerHTML = html;
}

function renderMemories(memories) {
  const container = document.getElementById('memoriesList');
  const mcb = document.getElementById('memoriesCountBadge');
  const count = memories ? memories.length : 0;
  if (mcb) mcb.textContent = `${count} Recuerdo(s)`;
  if (!container) return;

  if (!memories || memories.length === 0) {
    container.innerHTML = '<div class="empty-state">No hay recuerdos almacenados aún.</div>';
    return;
  }

  let html = '';
  memories.forEach(mem => {
    html += `
      <div class="mem-card" onclick="inspectMemory('${mem.key}')">
        <div class="mem-left">
          <div class="mem-title">${escapeHtml(mem.key)}</div>
          <div class="mem-meta">Alcance: ${mem.project || 'global'}</div>
        </div>
        <span class="mem-cat-tag">${mem.category || 'general'}</span>
      </div>
    `;
  });
  container.innerHTML = html;
}

function filterTasks(status) {
  state.activeFilter = status;
  document.querySelectorAll('#kanbanFilters .pill').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  renderKanban(state.tasks);
}

// ─────────────────────────────────────────────────────────────
// GETBRAIN CANVAS PHYSICS & KNOWLEDGE GRAPH ENGINE
// ─────────────────────────────────────────────────────────────
let canvas, ctx;
let graphNodes = [];
let graphLinks = [];
let simRunning = true;
let transform = { x: 0, y: 0, k: 1 };
let isDragging = false;
let draggedNode = null;
let lastMousePos = { x: 0, y: 0 };
let hoveredNode = null;
let animFrameId = null;

function initBrainCanvas() {
  canvas = document.getElementById('brainCanvas');
  if (!canvas) return;
  ctx = canvas.getContext('2d');

  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Mouse event listeners for Pan, Zoom & Drag
  canvas.addEventListener('mousedown', onMouseDown);
  canvas.addEventListener('mousemove', onMouseMove);
  canvas.addEventListener('mouseup', onMouseUp);
  canvas.addEventListener('wheel', onWheel, { passive: false });
  canvas.addEventListener('click', onClickCanvas);
}

function resizeCanvas() {
  if (!canvas) return;
  const parent = canvas.parentElement;
  const rect = parent ? parent.getBoundingClientRect() : null;
  const w = (rect && rect.width > 0) ? rect.width : (window.innerWidth || 800);
  const h = (rect && rect.height > 0) ? rect.height : (Math.max(window.innerHeight - 100, 500));
  canvas.width = Math.floor(w);
  canvas.height = Math.floor(h);
}

function setupBrainSimulation(nodes, links) {
  if (!nodes || !canvas) return;

  const width = canvas.width || 800;
  const height = canvas.height || 600;

  // Initialize node positions in a circle/galaxy distribution around center
  const existingPos = {};
  graphNodes.forEach(n => { existingPos[n.id] = { x: n.x, y: n.y, vx: n.vx, vy: n.vy }; });

  graphNodes = nodes.map((n, i) => {
    const angle = (i / nodes.length) * Math.PI * 2;
    const radius = 100 + (Math.random() * 220);
    const prev = existingPos[n.id];

    return {
      ...n,
      x: prev ? prev.x : width / 2 + Math.cos(angle) * radius,
      y: prev ? prev.y : height / 2 + Math.sin(angle) * radius,
      vx: prev ? prev.vx : (Math.random() - 0.5) * 2,
      vy: prev ? prev.vy : (Math.random() - 0.5) * 2,
      radius: n.type === 'hub' ? 28 : (n.type === 'agent' ? 22 : 16)
    };
  });

  // Map link source/target to node objects
  const nodeMap = {};
  graphNodes.forEach(n => { nodeMap[n.id] = n; });

  graphLinks = (links || []).map(l => ({
    ...l,
    sourceNode: nodeMap[l.source],
    targetNode: nodeMap[l.target]
  })).filter(l => l.sourceNode && l.targetNode);

  if (!animFrameId) {
    animFrameId = requestAnimationFrame(renderLoop);
  }
}

// Physics & Render Loop
function renderLoop() {
  if (state.currentView === 'brain') {
    if (simRunning) {
      updatePhysics();
    }
    drawGraph();
  }
  animFrameId = requestAnimationFrame(renderLoop);
}

function updatePhysics() {
  const kRepulsion = 1400;
  const kSpring = 0.04;
  const targetDist = 90;
  const damping = 0.88;
  const centerGravity = 0.015;
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;

  // 1. Repulsion between all node pairs
  for (let i = 0; i < graphNodes.length; i++) {
    const a = graphNodes[i];
    if (!isNodeVisible(a)) continue;

    for (let j = i + 1; j < graphNodes.length; j++) {
      const b = graphNodes[j];
      if (!isNodeVisible(b)) continue;

      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const distSq = dx * dx + dy * dy || 1;
      const dist = Math.sqrt(distSq);

      if (dist < 350) {
        const force = kRepulsion / distSq;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        if (a !== draggedNode) { a.vx -= fx; a.vy -= fy; }
        if (b !== draggedNode) { b.vx += fx; b.vy += fy; }
      }
    }
  }

  // 2. Spring attraction along links
  for (let i = 0; i < graphLinks.length; i++) {
    const link = graphLinks[i];
    const a = link.sourceNode;
    const b = link.targetNode;
    if (!isNodeVisible(a) || !isNodeVisible(b)) continue;

    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    const displacement = dist - targetDist;
    const force = displacement * kSpring;

    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;

    if (a !== draggedNode) { a.vx += fx; a.vy += fy; }
    if (b !== draggedNode) { b.vx -= fx; b.vy -= fy; }
  }

  // 3. Center gravity & velocity integration
  for (let i = 0; i < graphNodes.length; i++) {
    const n = graphNodes[i];
    if (n === draggedNode) continue;

    n.vx += (cx - n.x) * centerGravity;
    n.vy += (cy - n.y) * centerGravity;

    n.vx *= damping;
    n.vy *= damping;

    n.x += n.vx;
    n.y += n.vy;
  }
}

function isNodeVisible(n) {
  if (n.type === 'hub') return true;
  if (!state.brainFilters[n.type]) return false;
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    const match = n.label.toLowerCase().includes(q) || (n.category && n.category.toLowerCase().includes(q));
    if (!match) return false;
  }
  return true;
}

function drawGraph() {
  ctx.save();
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Apply pan & zoom transform
  ctx.translate(transform.x, transform.y);
  ctx.scale(transform.k, transform.k);

  const timeNow = Date.now() * 0.002;

  // 1. Draw Links (Subtle terminal wireframe)
  for (let i = 0; i < graphLinks.length; i++) {
    const link = graphLinks[i];
    const a = link.sourceNode;
    const b = link.targetNode;
    if (!isNodeVisible(a) || !isNodeVisible(b)) continue;

    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);

    const isHovered = (hoveredNode && (hoveredNode === a || hoveredNode === b));
    const isSelected = (state.selectedNode && (state.selectedNode === a || state.selectedNode === b));

    if (isSelected || isHovered) {
      ctx.strokeStyle = '#58a6ff';
      ctx.lineWidth = 1.5;
    } else {
      ctx.strokeStyle = '#21262d';
      ctx.lineWidth = 1;
    }
    ctx.stroke();

    // Subtle single packet dot on active links
    if (link.animated || isSelected) {
      const offset = (timeNow % 1);
      const px = a.x + (b.x - a.x) * offset;
      const py = a.y + (b.y - a.y) * offset;

      ctx.beginPath();
      ctx.arc(px, py, 2, 0, Math.PI * 2);
      ctx.fillStyle = '#58a6ff';
      ctx.fill();
    }
  }

  // 2. Draw Nodes (Minimalist Linux Terminal circles)
  for (let i = 0; i < graphNodes.length; i++) {
    const n = graphNodes[i];
    if (!isNodeVisible(n)) continue;

    const isHovered = (hoveredNode === n);
    const isSelected = (state.selectedNode === n);
    const radius = n.radius * (isSelected ? 1.15 : (isHovered ? 1.08 : 1));

    // Outer indicator ring when selected or hovered
    if (isSelected || isHovered) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, radius + 3, 0, Math.PI * 2);
      ctx.strokeStyle = isSelected ? '#58a6ff' : '#3b485c';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Pulse ring for working agents
    if (n.status === 'working' || n.status === 'in_progress') {
      const pulseSize = radius + 4 + Math.sin(timeNow * 3) * 3;
      ctx.beginPath();
      ctx.arc(n.x, n.y, pulseSize, 0, Math.PI * 2);
      ctx.strokeStyle = '#3fb950';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Node body (Neutral terminal dark background)
    ctx.beginPath();
    ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#0e131a';
    ctx.fill();
    ctx.strokeStyle = isSelected ? '#58a6ff' : (n.color || '#30363d');
    ctx.lineWidth = isSelected ? 2 : 1.5;
    ctx.stroke();

    // Node Glyph / Emoji
    const glyph = n.extra && n.extra.glyph ? n.extra.glyph : (n.type === 'hub' ? '⚡' : n.type === 'task' ? '📋' : n.type === 'artifact' ? '📦' : n.type === 'memory' ? '🧠' : '📄');
    ctx.font = `${Math.round(radius * 0.85)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(glyph, n.x, n.y);

    // Node Label (Monospaced, clean and high-contrast)
    ctx.font = `${isSelected ? '700 11px' : '500 10px'} "JetBrains Mono", monospace`;
    ctx.fillStyle = isSelected ? '#f0f6fc' : '#8b949e';
    ctx.fillText(n.label, n.x, n.y + radius + 13);
  }

  ctx.restore();
}
}

// ─────────────────────────────────────────────────────────────
// CANVAS INTERACTION (PAN, ZOOM, DRAG, INSPECT)
// ─────────────────────────────────────────────────────────────
function getMouseGraphPos(e) {
  const rect = canvas.getBoundingClientRect();
  const screenX = e.clientX - rect.left;
  const screenY = e.clientY - rect.top;
  return {
    screenX,
    screenY,
    x: (screenX - transform.x) / transform.k,
    y: (screenY - transform.y) / transform.k
  };
}

function findNodeAt(x, y) {
  for (let i = graphNodes.length - 1; i >= 0; i--) {
    const n = graphNodes[i];
    if (!isNodeVisible(n)) continue;
    const dx = n.x - x;
    const dy = n.y - y;
    if (dx * dx + dy * dy <= n.radius * n.radius * 1.5) {
      return n;
    }
  }
  return null;
}

function onMouseDown(e) {
  const pos = getMouseGraphPos(e);
  const node = findNodeAt(pos.x, pos.y);

  if (node) {
    draggedNode = node;
    node.vx = 0;
    node.vy = 0;
  } else {
    isDragging = true;
    lastMousePos = { x: e.clientX, y: e.clientY };
  }
}

function onMouseMove(e) {
  const pos = getMouseGraphPos(e);

  if (draggedNode) {
    draggedNode.x = pos.x;
    draggedNode.y = pos.y;
    draggedNode.vx = 0;
    draggedNode.vy = 0;
    return;
  }

  if (isDragging) {
    const dx = e.clientX - lastMousePos.x;
    const dy = e.clientY - lastMousePos.y;
    transform.x += dx;
    transform.y += dy;
    lastMousePos = { x: e.clientX, y: e.clientY };
    return;
  }

  // Hover detection
  const node = findNodeAt(pos.x, pos.y);
  hoveredNode = node;
  canvas.style.cursor = node ? 'pointer' : 'default';
}

function onMouseUp() {
  draggedNode = null;
  isDragging = false;
}

function onWheel(e) {
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 1.12 : 0.88;
  const pos = getMouseGraphPos(e);

  const newK = Math.max(0.2, Math.min(3.5, transform.k * zoomFactor));
  transform.x = pos.screenX - (pos.screenX - transform.x) * (newK / transform.k);
  transform.y = pos.screenY - (pos.screenY - transform.y) * (newK / transform.k);
  transform.k = newK;
}

function onClickCanvas(e) {
  const pos = getMouseGraphPos(e);
  const node = findNodeAt(pos.x, pos.y);

  if (node) {
    selectNode(node);
  } else {
    closeInspector();
  }
}

function selectNode(node) {
  state.selectedNode = node;
  openInspector(node);
}

function openInspector(node) {
  const inspector = document.getElementById('nodeInspector');
  if (!inspector) return;

  document.getElementById('inspBadge').textContent = (node.type || 'NODE').toUpperCase();
  document.getElementById('inspTitle').textContent = node.label;
  document.getElementById('inspMeta').textContent = `Categoría: ${node.category || 'general'} • Estado: ${node.status || 'activo'}`;

  // Content
  const contentEl = document.getElementById('inspContent');
  if (node.extra && node.extra.full_content) {
    contentEl.textContent = node.extra.full_content;
  } else if (node.details) {
    contentEl.textContent = node.details;
  } else {
    contentEl.textContent = 'Sin especificación detallada.';
  }

  // Connected links
  const connEl = document.getElementById('inspConnections');
  const connected = graphLinks.filter(l => l.source === node.id || l.target === node.id);

  if (connected.length === 0) {
    connEl.innerHTML = '<div style="font-size:11px; color:#64748b;">Sin enlaces directos.</div>';
  } else {
    let connHtml = '';
    connected.forEach(l => {
      const otherNode = l.source === node.id ? l.targetNode : l.sourceNode;
      if (otherNode) {
        connHtml += `
          <div class="conn-pill" onclick="selectNodeById('${otherNode.id}')">
            <span><strong>${l.label || 'enlace'}</strong> → ${otherNode.label}</span>
            <span>↗</span>
          </div>
        `;
      }
    });
    connEl.innerHTML = connHtml;
  }

  inspector.style.display = 'flex';
  inspector.classList.add('open');
}

function selectNodeById(id) {
  const n = graphNodes.find(node => node.id === id);
  if (n) selectNode(n);
}

function closeInspector() {
  state.selectedNode = null;
  const inspector = document.getElementById('nodeInspector');
  if (inspector) {
    inspector.classList.remove('open');
    inspector.style.display = 'none';
  }
}

// Graph Toolbar Actions
function zoomIn() { transform.k = Math.min(3.5, transform.k * 1.25); }
function zoomOut() { transform.k = Math.max(0.2, transform.k * 0.8); }
function resetZoom() {
  transform.k = 1;
  transform.x = 0;
  transform.y = 0;
}
function togglePhysics() {
  simRunning = !simRunning;
  const btn = document.getElementById('physicsToggle');
  if (btn) btn.textContent = simRunning ? '⏸️' : '▶️';
}

function toggleFilter(type) {
  state.brainFilters[type] = !state.brainFilters[type];
  const btn = document.querySelector(`.filter-btn[data-type="${type}"]`);
  if (btn) {
    btn.classList.toggle('active', state.brainFilters[type]);
  }
}

function onBrainSearch(val) {
  state.searchQuery = val.trim();
}

async function scanCodebase() {
  try {
    const res = await fetch('/api/brain/scan', { method: 'POST' });
    const data = await res.json();
    state.brain = data;
    const countEl = document.getElementById('brainNodesCount');
    if (countEl) countEl.textContent = data.nodes ? data.nodes.length : 0;
    setupBrainSimulation(data.nodes, data.links);
  } catch (err) {
    console.error('Scan codebase error:', err);
  }
}

// ─────────────────────────────────────────────────────────────
// MODALS & ACTIONS
// ─────────────────────────────────────────────────────────────
function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

function inspectTask(id) {
  const task = state.tasks.find(t => t.id === id);
  if (task) {
    alert(`[Tarea #${task.id}] ${task.title}\n\nEstado: ${task.status.toUpperCase()}\nAsignado a: @${task.assigned_to || 'nadie'}\nPrioridad: ${task.priority}\n\nNotas: ${task.notes || 'Ninguna'}`);
  }
}

function inspectMemory(key) {
  const mem = state.memories.find(m => m.key === key);
  if (mem) {
    alert(`[Memoria: ${mem.key}]\nCategoría: ${mem.category}\nAlcance: ${mem.project}\n\n${mem.content}`);
  }
}

function openArtifactModal(key) {
  const art = state.artifacts.find(a => a.artifact_key === key);
  if (art) {
    alert(`[Contrato: ${art.artifact_key}]\nTítulo: ${art.title}\nCreador: @${art.creator}\nTipo: ${art.artifact_type}\n\n${art.content}`);
  }
}

// Helpers
function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[m]);
}

function jsonParseSafe(str) {
  try { return JSON.parse(str); } catch { return null; }
}

function hexToRgba(hex, alpha = 1) {
  if (!hex || hex[0] !== '#') return `rgba(139, 92, 246, ${alpha})`;
  let c = hex.substring(1);
  if (c.length === 3) c = c.split('').map(x => x + x).join('');
  const num = parseInt(c, 16);
  return `rgba(${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}, ${alpha})`;
}
