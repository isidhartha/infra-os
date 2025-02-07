const API = 'http://localhost:8000';
let ws = null;
let cpuChart, memChart, nsChart;
let cpuData = [], memData = [], timeLabels = [];
let allPods = [], allDeployments = [];
const MAX_POINTS = 60;

// ---- NAVIGATION ----
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.infra-nav').forEach(b => b.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
  const titles = { overview: 'Overview', pods: 'Pods', deployments: 'Deployments', metrics: 'Metrics', alerts: 'Alerts', analysis: 'AI Analysis', events: 'Events' };
  document.getElementById('pageTitle').textContent = titles[name] || name;
  if (name === 'pods') loadPods();
  if (name === 'deployments') loadDeployments();
  if (name === 'alerts') loadAlerts();
  if (name === 'events') loadEvents();
  if (name === 'metrics') initCharts();
}

// ---- HEALTH ----
async function checkHealth() {
  try {
    const r = await fetch(`${API}/health`);
    if (r.ok) document.getElementById('wsLabel').textContent = 'backend online';
    else throw new Error();
  } catch { document.getElementById('wsLabel').textContent = 'backend offline'; }
}

// ---- OVERVIEW ----
async function loadOverview() {
  try {
    const r = await fetch(`${API}/api/v1/k8s/cluster`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    animateCounter('stat-nodes', data.node_count || data.nodes?.total || 3);
    animateCounter('stat-pods', data.pod_count || data.pods?.running || 12);
    animateCounter('stat-deploys', data.deployment_count || data.deployments?.total || 5);
    renderNodeGrid(data.nodes || mockNodes());
    setHealthScore(data.health_score || 87);
  } catch {
    animateCounter('stat-nodes', 3);
    animateCounter('stat-pods', 12);
    animateCounter('stat-deploys', 5);
    renderNodeGrid(mockNodes());
    setHealthScore(87);
  }
  loadAlertCount();
}

function mockNodes() {
  return [
    { name: 'node-master-1', status: 'Ready', cpu_usage: 45, memory_usage: 62 },
    { name: 'node-worker-1', status: 'Ready', cpu_usage: 28, memory_usage: 71 },
    { name: 'node-worker-2', status: 'Ready', cpu_usage: 65, memory_usage: 48 },
  ];
}

function renderNodeGrid(nodes) {
  const container = document.getElementById('nodeGrid');
  container.innerHTML = '';
  const nodeArr = Array.isArray(nodes) ? nodes : nodes?.items || [];
  nodeArr.forEach(node => {
    const cpu = node.cpu_usage || Math.floor(Math.random() * 70 + 10);
    const mem = node.memory_usage || Math.floor(Math.random() * 60 + 20);
    const ready = (node.status || 'Ready').toLowerCase() === 'ready';
    const card = document.createElement('div');
    card.className = 'node-card';
    card.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-mono text-slate-300">${node.name || node.metadata?.name || 'node'}</span>
        <span class="status-badge status-${ready ? 'running' : 'failed'}">${ready ? 'Ready' : 'NotReady'}</span>
      </div>
      <div class="text-xs text-slate-500 mb-1">CPU: <span style="color:#6366f1">${cpu}%</span></div>
      <div class="node-bar"><div class="node-bar-fill" style="width:${cpu}%;background:linear-gradient(90deg,#6366f1,#7c3aed)"></div></div>
      <div class="text-xs text-slate-500 mb-1 mt-2">Memory: <span style="color:#22d3ee">${mem}%</span></div>
      <div class="node-bar"><div class="node-bar-fill" style="width:${mem}%;background:linear-gradient(90deg,#22d3ee,#06b6d4)"></div></div>
    `;
    container.appendChild(card);
  });
}

function setHealthScore(score) {
  const ring = document.getElementById('healthRing');
  const scoreEl = document.getElementById('healthScore');
  const descEl = document.getElementById('healthDesc');
  const circumference = 213.6;
  ring.style.strokeDashoffset = circumference * (1 - score / 100);
  ring.style.stroke = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
  scoreEl.textContent = score + '%';
  descEl.textContent = score >= 80 ? 'All systems operational' : score >= 60 ? 'Minor issues detected' : 'Critical issues present';
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const step = Math.max(1, Math.floor(target / 30));
  const interval = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current;
    if (current >= target) clearInterval(interval);
  }, 30);
}

async function loadAlertCount() {
  try {
    const r = await fetch(`${API}/api/v1/alerts`);
    if (!r.ok) return;
    const data = await r.json();
    const alerts = Array.isArray(data) ? data : data.alerts || [];
    animateCounter('stat-alerts', alerts.length);
    document.getElementById('alertCount').textContent = alerts.length;
    if (alerts.length > 0) {
      document.getElementById('alertCount').classList.remove('hidden');
      const critical = alerts.filter(a => a.severity === 'critical');
      if (critical.length > 0) {
        const strip = document.getElementById('alertStrip');
        strip.classList.remove('hidden');
        document.getElementById('alertStripText').textContent = `${critical.length} critical alert(s): ${critical[0].summary || critical[0].name}`;
      }
    }
  } catch { animateCounter('stat-alerts', 0); }
}

// ---- PODS ----
async function loadPods() {
  const ns = document.getElementById('nsFilter')?.value || '';
  const url = ns ? `${API}/api/v1/k8s/pods?namespace=${ns}` : `${API}/api/v1/k8s/pods`;
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error();
    const data = await r.json();
    allPods = Array.isArray(data) ? data : data.items || data.pods || mockPods();
  } catch { allPods = mockPods(); }
  renderPods(allPods);
  document.getElementById('podsCount').textContent = allPods.length;
}

function mockPods() {
  return [
    { name: 'api-server-abc123', namespace: 'default', status: 'Running', restart_count: 0, age: '2d' },
    { name: 'frontend-xyz789', namespace: 'default', status: 'Running', restart_count: 1, age: '1d' },
    { name: 'database-pod-1', namespace: 'default', status: 'Running', restart_count: 0, age: '5d' },
    { name: 'cache-pod-2', namespace: 'default', status: 'Pending', restart_count: 3, age: '1h' },
    { name: 'worker-pod-1', namespace: 'kube-system', status: 'Running', restart_count: 0, age: '7d' },
    { name: 'monitor-abc', namespace: 'monitoring', status: 'Running', restart_count: 0, age: '3d' },
  ];
}

function filterPods() {
  const q = document.getElementById('podSearch')?.value?.toLowerCase() || '';
  renderPods(allPods.filter(p => (p.name || '').toLowerCase().includes(q)));
}

function renderPods(pods) {
  const tbody = document.getElementById('podsTable');
  tbody.innerHTML = '';
  pods.forEach(pod => {
    const status = pod.status || pod.phase || 'Unknown';
    const sClass = status.toLowerCase() === 'running' ? 'status-running' : status.toLowerCase() === 'pending' ? 'status-pending' : status.toLowerCase() === 'failed' ? 'status-failed' : 'status-unknown';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="px-4 py-3 font-mono text-xs">${pod.name || pod.metadata?.name}</td>
      <td class="px-4 py-3 text-slate-400 text-xs hidden md:table-cell">${pod.namespace || pod.metadata?.namespace || 'default'}</td>
      <td class="px-4 py-3"><span class="status-badge ${sClass}">${status}</span></td>
      <td class="px-4 py-3 text-slate-400 text-xs hidden sm:table-cell">${pod.restart_count ?? pod.restartCount ?? 0}</td>
      <td class="px-4 py-3 text-slate-400 text-xs hidden lg:table-cell">${pod.age || pod.creationTimestamp || '—'}</td>
    `;
    tbody.appendChild(tr);
  });
  if (pods.length === 0) tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-slate-600 text-sm italic">No pods found</td></tr>';
}

// ---- DEPLOYMENTS ----
async function loadDeployments() {
  try {
    const r = await fetch(`${API}/api/v1/k8s/deployments`);
    if (!r.ok) throw new Error();
    const data = await r.json();
    allDeployments = Array.isArray(data) ? data : data.items || data.deployments || mockDeployments();
  } catch { allDeployments = mockDeployments(); }
  renderDeployments(allDeployments);
}

function mockDeployments() {
  return [
    { name: 'api-server', namespace: 'default', ready_replicas: 3, available_replicas: 3, total_replicas: 3 },
    { name: 'frontend', namespace: 'default', ready_replicas: 2, available_replicas: 2, total_replicas: 2 },
    { name: 'worker', namespace: 'default', ready_replicas: 1, available_replicas: 1, total_replicas: 2 },
  ];
}

function filterDeployments() {
  const q = document.getElementById('depSearch')?.value?.toLowerCase() || '';
  renderDeployments(allDeployments.filter(d => (d.name || '').toLowerCase().includes(q)));
}

function renderDeployments(deps) {
  const tbody = document.getElementById('deploymentsTable');
  tbody.innerHTML = '';
  deps.forEach(dep => {
    const ready = dep.ready_replicas ?? 0;
    const total = dep.total_replicas ?? dep.replicas ?? 0;
    const allReady = ready === total && total > 0;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="px-4 py-3 font-mono text-xs">${dep.name || dep.metadata?.name}</td>
      <td class="px-4 py-3 text-slate-400 text-xs hidden md:table-cell">${dep.namespace || 'default'}</td>
      <td class="px-4 py-3 text-xs"><span class="status-badge ${allReady ? 'status-running' : 'status-pending'}">${ready}/${total}</span></td>
      <td class="px-4 py-3 text-slate-400 text-xs hidden sm:table-cell">${dep.available_replicas ?? ready}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ---- METRICS / CHARTS ----
function initCharts() {
  const chartOpts = (label, color) => ({
    type: 'line',
    data: { labels: timeLabels, datasets: [{ label, data: [], borderColor: color, backgroundColor: color + '20', borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0 }] },
    options: { responsive: true, maintainAspectRatio: false, animation: false, scales: { x: { display: false }, y: { min: 0, max: 100, ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.03)' } } }, plugins: { legend: { display: false } } }
  });

  if (!cpuChart) {
    cpuChart = new Chart(document.getElementById('cpuChart').getContext('2d'), chartOpts('CPU %', '#6366f1'));
    memChart = new Chart(document.getElementById('memChart').getContext('2d'), chartOpts('Memory %', '#22d3ee'));
  }
  loadNsChart();
}

function updateCharts(cpu, mem) {
  const now = new Date().toLocaleTimeString('en-US', { hour12: false });
  if (timeLabels.length >= MAX_POINTS) {
    timeLabels.shift(); cpuData.shift(); memData.shift();
  }
  timeLabels.push(now);
  cpuData.push(cpu);
  memData.push(mem);

  if (cpuChart) {
    cpuChart.data.labels = [...timeLabels];
    cpuChart.data.datasets[0].data = [...cpuData];
    cpuChart.update('none');
    document.getElementById('cpuCurrent').textContent = cpu.toFixed(1) + '%';
  }
  if (memChart) {
    memChart.data.labels = [...timeLabels];
    memChart.data.datasets[0].data = [...memData];
    memChart.update('none');
    document.getElementById('memCurrent').textContent = mem.toFixed(1) + '%';
  }
  document.getElementById('lastUpdate').textContent = 'Updated ' + now;
}

async function loadNsChart() {
  try {
    const r = await fetch(`${API}/api/v1/metrics/resources`);
    if (!r.ok) throw new Error();
    const data = await r.json();
    const ns = data.namespaces || data;
    const labels = Object.keys(ns);
    const vals = Object.values(ns).map(v => v.cpu_usage || v.cpu || Math.random() * 80 + 10);
    if (!nsChart) {
      nsChart = new Chart(document.getElementById('nsChart').getContext('2d'), {
        type: 'bar',
        data: { labels, datasets: [{ label: 'CPU %', data: vals, backgroundColor: '#6366f130', borderColor: '#6366f1', borderWidth: 1, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { display: false } }, y: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.03)' } } }, plugins: { legend: { display: false } } }
      });
    }
  } catch {
    if (!nsChart) {
      nsChart = new Chart(document.getElementById('nsChart').getContext('2d'), {
        type: 'bar',
        data: { labels: ['default', 'kube-system', 'monitoring'], datasets: [{ label: 'CPU %', data: [45, 28, 15], backgroundColor: '#6366f130', borderColor: '#6366f1', borderWidth: 1, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { display: false } }, y: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.03)' } } }, plugins: { legend: { display: false } } }
      });
    }
  }
}

// ---- WEBSOCKET METRICS ----
function connectMetricsWS() {
  try {
    ws = new WebSocket('ws://localhost:8000/ws/metrics');
    ws.onopen = () => {
      document.getElementById('wsIndicator').className = 'w-2 h-2 rounded-full bg-green-400 live-pulse';
      document.getElementById('wsLabel').textContent = 'live stream';
    };
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        const cpu = msg.cpu_usage || msg.cpu || (30 + Math.random() * 40);
        const mem = msg.memory_usage || msg.memory || (40 + Math.random() * 30);
        updateCharts(cpu, mem);
      } catch {}
    };
    ws.onerror = () => document.getElementById('wsIndicator').className = 'w-2 h-2 rounded-full bg-red-400';
    ws.onclose = () => {
      document.getElementById('wsIndicator').className = 'w-2 h-2 rounded-full bg-slate-600';
      document.getElementById('wsLabel').textContent = 'reconnecting…';
      setTimeout(connectMetricsWS, 5000);
    };
  } catch { simulateMetrics(); }
}

function simulateMetrics() {
  setInterval(() => {
    const cpu = 30 + Math.random() * 40 + Math.sin(Date.now() / 10000) * 15;
    const mem = 45 + Math.random() * 20 + Math.sin(Date.now() / 8000) * 10;
    updateCharts(Math.min(100, Math.max(0, cpu)), Math.min(100, Math.max(0, mem)));
  }, 3000);
}

// ---- ALERTS ----
async function loadAlerts() {
  const container = document.getElementById('alertsList');
  try {
    const r = await fetch(`${API}/api/v1/alerts`);
    if (!r.ok) throw new Error();
    const data = await r.json();
    const alerts = Array.isArray(data) ? data : data.alerts || [];
    container.innerHTML = '';
    if (alerts.length === 0) {
      container.innerHTML = '<div class="infra-card rounded-xl p-4 text-sm" style="color:#10b981">✓ No active alerts</div>';
      return;
    }
    alerts.forEach(alert => {
      const sev = (alert.severity || 'info').toLowerCase();
      const card = document.createElement('div');
      card.className = `alert-card alert-${sev === 'critical' ? 'critical' : sev === 'warning' ? 'warning' : 'info'}`;
      card.innerHTML = `
        <div class="flex items-start justify-between gap-3 mb-2">
          <span class="font-semibold text-sm">${alert.name || alert.summary || 'Alert'}</span>
          <span class="status-badge status-${sev === 'critical' ? 'failed' : 'pending'}">${sev}</span>
        </div>
        <div class="text-xs text-slate-400">${alert.message || alert.description || ''}</div>
        ${alert.firing_since ? `<div class="text-xs text-slate-600 mt-1">Since: ${alert.firing_since}</div>` : ''}
        <button onclick="acknowledgeAlert(this)" class="mt-2 text-xs px-3 py-1 rounded border border-white/10 text-slate-400 hover:bg-white/5 transition">
          Acknowledge
        </button>
      `;
      container.appendChild(card);
    });
  } catch {
    container.innerHTML = `
      <div class="alert-card alert-warning"><div class="font-semibold text-sm">High Memory Usage</div><div class="text-xs text-slate-400 mt-1">Node worker-2 memory at 85%</div><button onclick="acknowledgeAlert(this)" class="mt-2 text-xs px-3 py-1 rounded border border-white/10 text-slate-400 hover:bg-white/5">Acknowledge</button></div>
      <div class="alert-card alert-info"><div class="font-semibold text-sm">Pod Restart Loop</div><div class="text-xs text-slate-400 mt-1">cache-pod-2 restarted 3 times in 1 hour</div><button onclick="acknowledgeAlert(this)" class="mt-2 text-xs px-3 py-1 rounded border border-white/10 text-slate-400 hover:bg-white/5">Acknowledge</button></div>
    `;
  }
}

function acknowledgeAlert(btn) {
  const card = btn.closest('.alert-card');
  card.style.opacity = '0.4';
  btn.textContent = '✓ Acknowledged';
  btn.disabled = true;
  showToast('Alert acknowledged', 'success');
}

// ---- AI ANALYSIS ----
async function analyzeCluster() {
  const result = document.getElementById('analysisResult');
  result.classList.remove('hidden');
  document.getElementById('analysisText').innerHTML = '<div class="animate-pulse text-slate-500">Analyzing cluster with AI…</div>';
  try {
    const r = await fetch(`${API}/api/v1/k8s/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    const text = data.analysis || data.recommendations || data.result || JSON.stringify(data, null, 2);
    document.getElementById('analysisText').innerHTML = formatAnalysis(text);
    showToast('Analysis complete', 'success');
  } catch (e) {
    document.getElementById('analysisText').textContent = 'Backend unavailable. Check docker-compose logs.';
  }
}

async function nlQuery_() {
  const query = document.getElementById('nlQuery').value.trim();
  if (!query) return showToast('Enter a query', 'error');
  const result = document.getElementById('analysisResult');
  result.classList.remove('hidden');
  document.getElementById('analysisText').innerHTML = '<div class="animate-pulse text-slate-500">Querying…</div>';
  try {
    const r = await fetch(`${API}/api/v1/k8s/nl-query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) });
    if (!r.ok) throw new Error();
    const data = await r.json();
    document.getElementById('analysisText').innerHTML = formatAnalysis(data.result || data.answer || JSON.stringify(data));
  } catch (e) { document.getElementById('analysisText').textContent = `Error: ${e.message}`; }
}

function formatAnalysis(text) {
  if (typeof text !== 'string') text = JSON.stringify(text, null, 2);
  return text.replace(/\n/g, '<br/>').replace(/## (.+)/g, '<strong style="color:#6366f1">$1</strong>').replace(/- (.+)/g, '• $1');
}

// ---- EVENTS ----
async function loadEvents() {
  const container = document.getElementById('eventsList');
  try {
    const r = await fetch(`${API}/api/v1/k8s/events`);
    if (!r.ok) throw new Error();
    const data = await r.json();
    const events = Array.isArray(data) ? data : data.events || data.items || mockEvents();
    container.innerHTML = '';
    events.slice(0, 100).forEach(ev => {
      const type = (ev.type || ev.reason || 'Normal').toLowerCase();
      const item = document.createElement('div');
      item.className = `event-log-item event-${type.includes('warning') || type.includes('error') ? 'warning' : type.includes('fail') ? 'error' : 'normal'}`;
      item.innerHTML = `<span style="color:inherit">[${ev.reason || type}]</span> <span style="color:rgba(255,255,255,0.5)">${ev.message || ev.object?.name || ''}</span> <span style="color:#475569;float:right">${ev.timestamp || ev.lastTimestamp || ''}</span>`;
      container.appendChild(item);
    });
    if (container.children.length === 0) container.innerHTML = '<div class="event-log-item event-normal">No events</div>';
  } catch {
    container.innerHTML = mockEvents().map(e => `<div class="event-log-item event-${e.type === 'Warning' ? 'warning' : 'normal'}">[${e.reason}] ${e.message}</div>`).join('');
  }
}

function mockEvents() {
  return [
    { type: 'Normal', reason: 'Pulled', message: 'Successfully pulled image "nginx:latest"' },
    { type: 'Normal', reason: 'Started', message: 'Started container frontend' },
    { type: 'Warning', reason: 'BackOff', message: 'Back-off restarting failed container' },
    { type: 'Normal', reason: 'Scheduled', message: 'Successfully assigned pod to node-worker-1' },
  ];
}

// ---- REFRESH ----
async function refreshAll() {
  loadOverview();
  showToast('Refreshed', 'success');
}

// ---- SIDEBAR TOGGLE ----
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('mobileOverlay').classList.toggle('hidden');
}

// ---- TOAST ----
function showToast(msg, type = 'info') {
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ---- INIT ----
checkHealth();
loadOverview();
connectMetricsWS();
setInterval(loadOverview, 30000);
