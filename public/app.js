/* ── Config ──────────────────────────────────────────────────────────────── */
const BASE = '/scim/v2';
const HEADERS = {
  'Content-Type':  'application/scim+json',
  'Accept':        'application/scim+json',
  'Authorization': 'Bearer demo-token-abc123',
};

/* ── Quick-select presets ────────────────────────────────────────────────── */
const PRESETS = {
  listUsers: {
    method: 'GET',
    url:    '/scim/v2/Users',
    body:   '',
  },
  createUser: {
    method: 'POST',
    url:    '/scim/v2/Users',
    body: JSON.stringify({
      schemas:     ['urn:ietf:params:scim:schemas:core:2.0:User'],
      userName:    'alice.smith',
      displayName: 'Alice Smith',
      emails:      [{ value: 'alice@company.com', type: 'work', primary: true }],
      active:      true,
    }, null, 2),
  },
  listGroups: {
    method: 'GET',
    url:    '/scim/v2/Groups',
    body:   '',
  },
  createGroup: {
    method: 'POST',
    url:    '/scim/v2/Groups',
    body: JSON.stringify({
      schemas:     ['urn:ietf:params:scim:schemas:core:2.0:Group'],
      displayName: 'data-engineering',
      members:     [],
    }, null, 2),
  },
  spc: {
    method: 'GET',
    url:    '/scim/v2/ServiceProviderConfig',
    body:   '',
  },
};

function loadPreset(name) {
  const p = PRESETS[name];
  if (!p) return;
  document.getElementById('pg-method').value = p.method;
  document.getElementById('pg-url').value    = p.url;
  document.getElementById('pg-body').value   = p.body;
  toggleBodyField();
}

function toggleBodyField() {
  const method = document.getElementById('pg-method').value;
  const field  = document.getElementById('body-field');
  field.style.display = ['GET','DELETE'].includes(method) ? 'none' : '';
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('pg-method').addEventListener('change', toggleBodyField);
  toggleBodyField();
});

/* ── Playground send ─────────────────────────────────────────────────────── */
async function sendRequest() {
  const method   = document.getElementById('pg-method').value;
  const urlPath  = document.getElementById('pg-url').value.trim();
  const bodyText = document.getElementById('pg-body').value.trim();

  const url = urlPath.startsWith('http') ? urlPath : window.location.origin + urlPath;

  // UI: loading state
  const btn     = document.getElementById('send-btn');
  const label   = document.getElementById('send-label');
  const spinner = document.getElementById('send-spinner');
  btn.disabled  = true;
  label.classList.add('hidden');
  spinner.classList.remove('hidden');

  const statusEl = document.getElementById('status-badge');
  const timingEl = document.getElementById('timing-badge');
  const responseEl = document.getElementById('pg-response');
  statusEl.classList.add('hidden');
  timingEl.classList.add('hidden');
  responseEl.innerHTML = '<div class="pg-placeholder"><div class="log-loading">Sending request…</div></div>';

  const opts = { method, headers: HEADERS };
  if (!['GET','DELETE'].includes(method) && bodyText) {
    try { JSON.parse(bodyText); } catch { alert('Request body is not valid JSON'); resetBtn(); return; }
    opts.body = bodyText;
  }

  const t0 = performance.now();
  try {
    const res  = await fetch(url, opts);
    const ms   = Math.round(performance.now() - t0);
    let body;
    try { body = await res.json(); } catch { body = await res.text(); }

    const isOk = res.status < 300;
    statusEl.textContent = res.status + ' ' + res.statusText;
    statusEl.className   = 'status-badge ' + (isOk ? 'ok' : 'error');
    statusEl.classList.remove('hidden');
    timingEl.textContent = ms + ' ms';
    timingEl.classList.remove('hidden');

    const formatted = typeof body === 'string' ? body : JSON.stringify(body, null, 2);
    responseEl.textContent = formatted;
    colorizeJson(responseEl);

  } catch (err) {
    responseEl.textContent = 'Network error: ' + err.message;
  }
  resetBtn();
}

function resetBtn() {
  const btn = document.getElementById('send-btn');
  btn.disabled = false;
  document.getElementById('send-label').classList.remove('hidden');
  document.getElementById('send-spinner').classList.add('hidden');
}

/* ── Basic JSON colorizer ────────────────────────────────────────────────── */
function colorizeJson(el) {
  const raw = el.textContent;
  el.innerHTML = raw
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?)/g, m => {
      if (/:$/.test(m)) return `<span style="color:#60a5fa">${m}</span>`;
      return `<span style="color:#4ade80">${m}</span>`;
    })
    .replace(/\b(true|false)\b/g,  '<span style="color:#f97316">$1</span>')
    .replace(/\b(null)\b/g,        '<span style="color:#888899">$1</span>')
    .replace(/\b(-?\d+\.?\d*)\b/g, '<span style="color:#a78bfa">$1</span>');
}

/* ── Lifecycle scenario runner ───────────────────────────────────────────── */
async function runScenario(name) {
  const outputEl = document.getElementById('scenario-output');
  const logEl    = document.getElementById('scenario-log');
  const labelEl  = document.getElementById('scenario-output-label');

  const labels = {
    onboarding:      '🚀 Onboarding',
    offboarding:     '🔄 Offboarding',
    termination:     '🚪 Termination',
    recertification: '📋 Recertification',
    verification:    '🌙 Nightly Verification',
  };

  labelEl.textContent = labels[name] || name;
  logEl.innerHTML = '<div class="log-loading">Running scenario…</div>';
  outputEl.classList.remove('hidden');
  outputEl.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const steps = await buildScenario(name);
    logEl.innerHTML = '';
    for (const step of steps) {
      await executeStep(step, logEl);
    }
  } catch (err) {
    logEl.innerHTML = `<div style="color:#f87171">Error: ${err.message}</div>`;
  }
}

function closeScenarioOutput() {
  document.getElementById('scenario-output').classList.add('hidden');
}

/* ── Step executor ───────────────────────────────────────────────────────── */
async function executeStep(step, logEl) {
  // Resolve dynamic IDs
  const url    = resolvePath(step.url);
  const method = step.method;
  const body   = step.body ? JSON.stringify(resolveBody(step.body)) : undefined;

  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `
    <div class="log-entry-header">
      <span class="method ${method.toLowerCase()}">${method}</span>
      <code style="color:var(--text-dim);font-size:11px">${url}</code>
      <span class="log-step-label" style="margin-left:auto">${step.label}</span>
      <span class="log-loading">…</span>
    </div>
    <div class="log-entry-body">Sending…</div>`;
  logEl.appendChild(entry);

  const opts = { method, headers: HEADERS };
  if (body) opts.body = body;

  const t0 = performance.now();
  try {
    const res  = await fetch(window.location.origin + url, opts);
    const ms   = Math.round(performance.now() - t0);
    let respBody;
    try { respBody = await res.json(); } catch { respBody = {}; }

    // Store IDs for later steps
    if (step.saveAs && respBody.id) {
      _ids[step.saveAs] = respBody.id;
    }

    const isOk    = res.status < 300;
    const statusEl = entry.querySelector('.log-loading');
    statusEl.textContent  = res.status + ' · ' + ms + 'ms';
    statusEl.className    = isOk ? 'log-status-ok' : 'log-status-error';

    const bodyEl = entry.querySelector('.log-entry-body');
    if (res.status === 204) {
      bodyEl.textContent = '(204 No Content)';
    } else {
      bodyEl.textContent = JSON.stringify(respBody, null, 2);
    }
  } catch (err) {
    entry.querySelector('.log-entry-body').textContent = 'Error: ' + err.message;
  }

  await sleep(200); // small pause so output is readable
}

/* ── Dynamic ID store ────────────────────────────────────────────────────── */
const _ids = {};

function resolvePath(url) {
  return url.replace(/:([a-z_]+)/g, (_, key) => _ids[key] || (':'+key));
}

function resolveBody(body) {
  if (typeof body !== 'object') return body;
  const s = JSON.stringify(body).replace(/":(id:[a-z_]+)"/g, (_, key) => {
    return `":"${_ids[key] || key}"`;
  });
  try { return JSON.parse(s); } catch { return body; }
}

/* ── Scenario definitions ────────────────────────────────────────────────── */
async function buildScenario(name) {
  // Reset IDs before each scenario
  Object.keys(_ids).forEach(k => delete _ids[k]);

  const USER_SCHEMA  = 'urn:ietf:params:scim:schemas:core:2.0:User';
  const GROUP_SCHEMA = 'urn:ietf:params:scim:schemas:core:2.0:Group';
  const PATCH_SCHEMA = 'urn:ietf:params:scim:api:messages:2.0:PatchOp';

  if (name === 'onboarding') return [
    {
      label: 'Create AD group',
      method: 'POST', url: '/scim/v2/Groups', saveAs: 'group_id',
      body: { schemas:[GROUP_SCHEMA], displayName:'data-engineering', members:[] },
    },
    {
      label: 'Provision user',
      method: 'POST', url: '/scim/v2/Users', saveAs: 'user_id',
      body: { schemas:[USER_SCHEMA], userName:'sarah.chen', displayName:'Sarah Chen',
              emails:[{value:'sarah.chen@company.com',primary:true}], active:true },
    },
    {
      label: 'Grant workspace access',
      method: 'PATCH', url: '/scim/v2/Groups/:group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'add', path:'members', value:[{value:'__USER_ID__', display:'Sarah Chen'}]}] },
    },
    {
      label: 'Verify: list users',
      method: 'GET', url: '/scim/v2/Users',
    },
    {
      label: 'Verify: list groups',
      method: 'GET', url: '/scim/v2/Groups',
    },
  ];

  if (name === 'offboarding') return [
    {
      label: 'Create DE group',
      method: 'POST', url: '/scim/v2/Groups', saveAs: 'de_group_id',
      body: { schemas:[GROUP_SCHEMA], displayName:'data-engineering', members:[] },
    },
    {
      label: 'Create ML group',
      method: 'POST', url: '/scim/v2/Groups', saveAs: 'ml_group_id',
      body: { schemas:[GROUP_SCHEMA], displayName:'ml-platform', members:[] },
    },
    {
      label: 'Provision user',
      method: 'POST', url: '/scim/v2/Users', saveAs: 'user_id',
      body: { schemas:[USER_SCHEMA], userName:'sarah.chen', displayName:'Sarah Chen',
              emails:[{value:'sarah.chen@company.com',primary:true}], active:true },
    },
    {
      label: 'Add to DE group',
      method: 'PATCH', url: '/scim/v2/Groups/:de_group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'add',path:'members',value:[{value:'__USER_ID__',display:'Sarah Chen'}]}] },
    },
    {
      label: 'Remove from DE (transfer out)',
      method: 'PATCH', url: '/scim/v2/Groups/:de_group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'remove',path:'members[value eq "__USER_ID__"]'}] },
    },
    {
      label: 'Add to ML (transfer in)',
      method: 'PATCH', url: '/scim/v2/Groups/:ml_group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'add',path:'members',value:[{value:'__USER_ID__',display:'Sarah Chen'}]}] },
    },
    {
      label: 'Update department',
      method: 'PATCH', url: '/scim/v2/Users/:user_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'replace',path:'department',value:'ML Platform'}] },
    },
  ];

  if (name === 'termination') return [
    {
      label: 'Create group',
      method: 'POST', url: '/scim/v2/Groups', saveAs: 'group_id',
      body: { schemas:[GROUP_SCHEMA], displayName:'data-engineering', members:[] },
    },
    {
      label: 'Provision Marcus Webb',
      method: 'POST', url: '/scim/v2/Users', saveAs: 'user_id',
      body: { schemas:[USER_SCHEMA], userName:'marcus.webb', displayName:'Marcus Webb',
              emails:[{value:'marcus.webb@company.com',primary:true}], active:true },
    },
    {
      label: 'Add to group',
      method: 'PATCH', url: '/scim/v2/Groups/:group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'add',path:'members',value:[{value:'__USER_ID__',display:'Marcus Webb'}]}] },
    },
    {
      label: 'STEP 1: Immediate lockout (deactivate)',
      method: 'PATCH', url: '/scim/v2/Users/:user_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'replace',path:'active',value:false}] },
    },
    {
      label: 'STEP 2: Remove from all groups',
      method: 'PATCH', url: '/scim/v2/Groups/:group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'remove',path:'members[value eq "__USER_ID__"]'}] },
    },
    {
      label: 'STEP 3: Delete user permanently',
      method: 'DELETE', url: '/scim/v2/Users/:user_id',
    },
    {
      label: 'Verify: confirm user is gone',
      method: 'GET', url: '/scim/v2/Users',
    },
  ];

  if (name === 'recertification') return [
    {
      label: 'Create group',
      method: 'POST', url: '/scim/v2/Groups', saveAs: 'group_id',
      body: { schemas:[GROUP_SCHEMA], displayName:'data-engineering', members:[] },
    },
    {
      label: 'Provision Alice (45 days, approved)',
      method: 'POST', url: '/scim/v2/Users', saveAs: 'alice_id',
      body: { schemas:[USER_SCHEMA], userName:'alice.johnson', displayName:'Alice Johnson',
              emails:[{value:'alice@co.com',primary:true}], active:true },
    },
    {
      label: 'Provision Dan (95 days — STALE)',
      method: 'POST', url: '/scim/v2/Users', saveAs: 'dan_id',
      body: { schemas:[USER_SCHEMA], userName:'dan.old', displayName:'Dan Old',
              emails:[{value:'dan@co.com',primary:true}], active:true },
    },
    {
      label: 'Add both to group',
      method: 'PATCH', url: '/scim/v2/Groups/:group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'add',path:'members',value:[
        {value:'__ALICE_ID__',display:'Alice Johnson'},
        {value:'__DAN_ID__',display:'Dan Old'},
      ]}]},
    },
    {
      label: 'Review: list all users',
      method: 'GET', url: '/scim/v2/Users',
    },
    {
      label: 'REVOKE: deactivate Dan (stale, 95 days)',
      method: 'PATCH', url: '/scim/v2/Users/:dan_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'replace',path:'active',value:false}] },
    },
    {
      label: 'REVOKE: remove Dan from group',
      method: 'PATCH', url: '/scim/v2/Groups/:group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'remove',path:'members[value eq "__DAN_ID__"]'}] },
    },
    {
      label: 'Verify: final state',
      method: 'GET', url: '/scim/v2/Groups',
    },
  ];

  if (name === 'verification') return [
    {
      label: 'Setup: create group',
      method: 'POST', url: '/scim/v2/Groups', saveAs: 'group_id',
      body: { schemas:[GROUP_SCHEMA], displayName:'data-engineering', members:[] },
    },
    {
      label: 'Setup: provision Alice (AD source of truth)',
      method: 'POST', url: '/scim/v2/Users', saveAs: 'alice_id',
      body: { schemas:[USER_SCHEMA], userName:'alice.smith', displayName:'Alice Smith',
              emails:[{value:'alice@co.com',primary:true}], active:true },
    },
    {
      label: 'Setup: add Alice to group',
      method: 'PATCH', url: '/scim/v2/Groups/:group_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'add',path:'members',value:[{value:'__ALICE_ID__',display:'Alice Smith'}]}] },
    },
    {
      label: 'Verification: GET all users (actual state)',
      method: 'GET', url: '/scim/v2/Users',
    },
    {
      label: 'Verification: GET all groups (membership check)',
      method: 'GET', url: '/scim/v2/Groups',
    },
    {
      label: 'Simulate drift: deactivate Alice (out-of-band change)',
      method: 'PATCH', url: '/scim/v2/Users/:alice_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'replace',path:'active',value:false}] },
    },
    {
      label: 'Auto-remediate: re-activate Alice (AD says active=true)',
      method: 'PATCH', url: '/scim/v2/Users/:alice_id',
      body: { schemas:[PATCH_SCHEMA], Operations:[{op:'replace',path:'active',value:true}] },
    },
    {
      label: 'Verify: confirm clean state',
      method: 'GET', url: '/scim/v2/Users',
    },
  ];

  return [];
}

/* ── ID resolver for PATCH bodies (replaces __USER_ID__ etc.) ────────────── */
// We override executeStep's resolveBody to use actual saved IDs
const _origExecuteStep = executeStep;
async function executeStep(step, logEl) {
  // Patch body values that contain __KEY__ placeholders
  if (step.body) {
    let s = JSON.stringify(step.body);
    s = s.replace(/__USER_ID__/g,  _ids['user_id']  || '');
    s = s.replace(/__ALICE_ID__/g, _ids['alice_id'] || '');
    s = s.replace(/__DAN_ID__/g,   _ids['dan_id']   || '');
    // Also patch filter-path members[value eq "..."]
    s = s.replace(/members\[value eq ""\]/g, () =>
      _ids['user_id'] ? `members[value eq "${_ids['user_id']}"]` : 'members[value eq ""]'
    );
    step = { ...step, body: JSON.parse(s) };
  }

  const url    = resolvePath(step.url);
  const method = step.method;
  const body   = step.body ? JSON.stringify(step.body) : undefined;

  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `
    <div class="log-entry-header">
      <span class="method ${method.toLowerCase()}">${method}</span>
      <code style="color:var(--text-dim);font-size:11px">${url}</code>
      <span class="log-step-label" style="margin-left:auto;font-size:11px">${step.label}</span>
      <span class="log-loading">…</span>
    </div>
    <div class="log-entry-body">Sending…</div>`;
  logEl.appendChild(entry);
  logEl.scrollTop = logEl.scrollHeight;

  const opts = { method, headers: HEADERS };
  if (body) opts.body = body;

  const t0 = performance.now();
  try {
    const res  = await fetch(window.location.origin + url, opts);
    const ms   = Math.round(performance.now() - t0);
    let respBody;
    try { respBody = await res.json(); } catch { respBody = null; }

    if (step.saveAs && respBody && respBody.id) {
      _ids[step.saveAs] = respBody.id;
    }

    const statusSpan = entry.querySelector('.log-loading');
    const isOk = res.status < 300;
    statusSpan.textContent = res.status + ' · ' + ms + 'ms';
    statusSpan.className   = isOk ? 'log-status-ok' : 'log-status-error';

    const bodyEl = entry.querySelector('.log-entry-body');
    if (res.status === 204 || !respBody) {
      bodyEl.textContent = res.status === 204 ? '(204 No Content — success)' : '(empty response)';
    } else {
      bodyEl.textContent = JSON.stringify(respBody, null, 2);
    }
  } catch (err) {
    entry.querySelector('.log-entry-body').textContent = 'Network error: ' + err.message;
  }

  await sleep(250);
  logEl.scrollTop = logEl.scrollHeight;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
