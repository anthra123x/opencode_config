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

  // Check URL hash for direct tab navigation
  if (window.location.hash === '#brain') {
    switchView('brain');
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
  }
}

// ─────────────────────────────────────────────────────────────
// REAL-TIME SSE & DATA FETCHING
// ─────────────────────────────────────────────────────────────
function initSSE() {
  const liveDot = document.querySelector('.pulse-dot');
  const liveText = document.getElementById('liveStatusText');

  try {
    const evtSource = new EventSource('/api/stream');

    evtSource.onopen = () => {
      liveText.textContent = 'LIVE SSE';
      liveText.style.color = '#34d399';
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
      liveText.textContent = 'RECONNECTING';
      liveText.style.color = '#fbbf24';
      if (liveDot) liveDot.style.background = '#f59e0b';
    };
  } catch (e) {
    console.warn('SSE unavailable, falling back to polling');
    setInterval(fetchInitialData, 3000);
  }
}

async function fetchInitialData() {
  try {
    const [resStatus, resTasks, resArtifacts, resMemories, resFeed] = await Promise.all([
      fetch('/api/status').then(r => r.json()),
      fetch('/api/tasks').then(r => r.json()),
      fetch('/api/artifacts').then(r => r.json()),
      fetch('/api/memories').then(r => r.json()),
      fetch('/api/feed').then(r => r.json())
    ]);

    updateSwarmUI({
      project: resStatus.project,
      project_dir: resStatus.project_dir,
      branch: resStatus.branch,
      clock: resStatus.clock,
      agents: resStatus.agents,
      tasks: resTasks.tasks,
      messages: resFeed.feed
    });

    renderArtifacts(resArtifacts.artifacts || []);
    renderMemories(resMemories.memories || []);
    fetchBrainGraph();
  } catch (err) {
    console.error('Error fetching initial data:', err);
  }
}

async function fetchBrainGraph() {
  try {
    const res = await fetch('/api/brain');
    const data = await res.json();
    state.brain = data;
    document.getElementById('brainNodesCount').textContent = data.nodes ? data.nodes.length : 0;
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
  document.getElementById('activeAgentsBadge').textContent = `${activeCount} Agente(s) en Ejecución`;
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

  document.getElementById('countTodo').textContent = counts.todo;
  document.getElementById('countInProgress').textContent = counts.in_progress;
  document.getElementById('countReview').textContent = counts.review;
  document.getElementById('countCompleted').textContent = counts.completed;

  Object.keys(cols).forEach(k => {
    cols[k].innerHTML = htmls[k] || '<div style="font-size:11px; color:#475569; padding:8px; text-align:center;">Sin tareas</div>';
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
  document.getElementById('artifactsCountBadge').textContent = `${artifacts.length} Contrato(s)`;
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
  document.getElementById('memoriesCountBadge').textContent = `${memories.length} Recuerdo(s)`;
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

  // 1. Draw Links
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
      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 2.5;
    } else {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
      ctx.lineWidth = 1;
    }
    ctx.stroke();

    // Animated particles on active links
    if (link.animated || isSelected) {
      const particleCount = 2;
      for (let p = 0; p < particleCount; p++) {
        const offset = ((timeNow + (p / particleCount)) % 1);
        const px = a.x + (b.x - a.x) * offset;
        const py = a.y + (b.y - a.y) * offset;

        ctx.beginPath();
        ctx.arc(px, py, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = '#a855f7';
        ctx.shadowColor = '#a855f7';
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }
  }

  // 2. Draw Nodes
  for (let i = 0; i < graphNodes.length; i++) {
    const n = graphNodes[i];
    if (!isNodeVisible(n)) continue;

    const isHovered = (hoveredNode === n);
    const isSelected = (state.selectedNode === n);
    const radius = n.radius * (isSelected ? 1.25 : (isHovered ? 1.15 : 1));

    // Glow aura
    ctx.beginPath();
    ctx.arc(n.x, n.y, radius + 4, 0, Math.PI * 2);
    ctx.fillStyle = n.color ? hexToRgba(n.color, isSelected ? 0.45 : 0.15) : 'rgba(255, 255, 255, 0.1)';
    ctx.fill();

    // Pulse ring for working agents
    if (n.status === 'working' || n.status === 'in_progress') {
      const pulseSize = radius + 6 + Math.sin(timeNow * 4) * 4;
      ctx.beginPath();
      ctx.arc(n.x, n.y, pulseSize, 0, Math.PI * 2);
      ctx.strokeStyle = n.color || '#10b981';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    // Node body
    ctx.beginPath();
    ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#161a28';
    ctx.fill();
    ctx.strokeStyle = n.color || '#8b5cf6';
    ctx.lineWidth = isSelected ? 3 : 2;
    ctx.stroke();

    // Node Glyph / Emoji
    const glyph = n.extra && n.extra.glyph ? n.extra.glyph : (n.type === 'hub' ? '⚡' : n.type === 'task' ? '📋' : n.type === 'artifact' ? '📦' : n.type === 'memory' ? '🧠' : '📄');
    ctx.font = `${Math.round(radius * 0.9)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(glyph, n.x, n.y);

    // Node Label
    ctx.font = `${isSelected ? '600 12px' : '500 11px'} Inter, sans-serif`;
    ctx.fillStyle = isSelected ? '#fff' : '#cbd5e1';
    ctx.fillText(n.label, n.x, n.y + radius + 14);
  }

  ctx.restore();
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

  inspector.classList.add('open');
}

function selectNodeById(id) {
  const n = graphNodes.find(node => node.id === id);
  if (n) selectNode(n);
}

function closeInspector() {
  state.selectedNode = null;
  const inspector = document.getElementById('nodeInspector');
  if (inspector) inspector.classList.remove('open');
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
  btn.textContent = simRunning ? '⏸️' : '▶️';
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

async function createMemoryCheckpoint() {
  const summary = prompt('Resumen del Checkpoint de Contexto Persistente:', 'Punto de control de arquitectura y avances del proyecto');
  if (!summary) return;
  try {
    const res = await fetch('/api/brain/checkpoint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary, decisions: 'Guardado manualmente desde GetBrain Cockpit' })
    });
    const data = await res.json();
    if (data.brain) {
      state.brain = data.brain;
      const countEl = document.getElementById('brainNodesCount');
      if (countEl) countEl.textContent = data.brain.nodes ? data.brain.nodes.length : 0;
      setupBrainSimulation(data.brain.nodes, data.brain.links);
    }
    alert('💾 Checkpoint de memoria persistente guardado exitosamente.\nContexto protegido en SQLite (zero-loss).');
  } catch (err) {
    console.error('Error creating memory checkpoint:', err);
    alert('Error al guardar checkpoint: ' + err.message);
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
