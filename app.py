"""
app.py — Self-Healing Agentic Compiler
Flask web application that orchestrates all compiler modules.
"""

from flask import Flask, request, jsonify, render_template_string
import traceback
import os

from agent import Agent

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Self-Healing Agentic Compiler</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg:       #0a0c10;
    --surface:  #111318;
    --panel:    #161b22;
    --border:   #21262d;
    --accent:   #00ffa3;
    --accent2:  #00c8ff;
    --warn:     #ffb347;
    --danger:   #ff4f4f;
    --muted:    #484f58;
    --text:     #e6edf3;
    --subtext:  #8b949e;
    --mono:     'JetBrains Mono', monospace;
    --sans:     'Syne', sans-serif;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ── Animated background grid ── */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(0,255,163,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,163,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  /* ── Glow blob ── */
  body::after {
    content: '';
    position: fixed;
    top: -200px; right: -200px;
    width: 600px; height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,255,163,0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
    animation: drift 12s ease-in-out infinite alternate;
  }

  @keyframes drift {
    from { transform: translate(0, 0); }
    to   { transform: translate(-80px, 80px); }
  }

  /* ── Header ── */
  header {
    position: relative; z-index: 10;
    border-bottom: 1px solid var(--border);
    padding: 18px 32px;
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(17,19,24,0.8);
    backdrop-filter: blur(12px);
  }

  .logo-icon {
    width: 36px; height: 36px;
    border: 2px solid var(--accent);
    border-radius: 8px;
    display: grid;
    place-items: center;
    font-size: 18px;
    box-shadow: 0 0 16px rgba(0,255,163,0.3);
  }

  .logo-text {
    font-family: var(--sans);
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.5px;
  }

  .logo-text span { color: var(--accent); }

  .badge {
    margin-left: auto;
    padding: 4px 10px;
    border-radius: 20px;
    background: rgba(0,255,163,0.08);
    border: 1px solid rgba(0,255,163,0.2);
    font-size: 11px;
    color: var(--accent);
    letter-spacing: 0.5px;
  }

  /* ── Layout ── */
  .workspace {
    position: relative; z-index: 10;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr auto;
    gap: 0;
    height: calc(100vh - 61px);
  }

  /* ── Config bar ── */
  .config-bar {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 24px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }

  .config-bar label {
    font-size: 11px;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .config-bar input[type="text"],
  .config-bar input[type="password"],
  .config-bar input[type="number"] {
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: var(--mono);
    font-size: 12px;
    padding: 7px 12px;
    border-radius: 6px;
    outline: none;
    transition: border-color .2s;
  }

  .config-bar input:focus { border-color: var(--accent); }
  .config-bar input[type="text"] { width: 420px; }
  .config-bar input[type="number"] { width: 70px; }

  .btn-run {
    margin-left: auto;
    padding: 8px 24px;
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: 6px;
    font-family: var(--sans);
    font-weight: 700;
    font-size: 13px;
    cursor: pointer;
    letter-spacing: 0.5px;
    transition: all .2s;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 0 20px rgba(0,255,163,0.25);
  }

  .btn-run:hover { background: #00e591; box-shadow: 0 0 30px rgba(0,255,163,0.4); }
  .btn-run:disabled { opacity: .45; cursor: not-allowed; box-shadow: none; }

  .btn-clear {
    padding: 8px 14px;
    background: transparent;
    color: var(--subtext);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: var(--mono);
    font-size: 12px;
    cursor: pointer;
    transition: all .2s;
  }

  .btn-clear:hover { border-color: var(--muted); color: var(--text); }

  /* ── Editor panes ── */
  .pane {
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border);
    overflow: hidden;
  }

  .pane:last-of-type { border-right: none; }

  .pane-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    font-size: 11px;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    flex-shrink: 0;
  }

  .pane-header .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
  }

  .dot-red    { background: #ff5f57; }
  .dot-yellow { background: #febc2e; }
  .dot-green  { background: var(--accent); }
  .dot-blue   { background: var(--accent2); }

  .pane-header span:last-child { margin-left: auto; }

  textarea, .output-code {
    flex: 1;
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    line-height: 1.7;
    padding: 20px;
    border: none;
    outline: none;
    resize: none;
    overflow-y: auto;
    white-space: pre;
    tab-size: 4;
  }

  .output-code {
    overflow-x: auto;
  }

  .placeholder-text {
    color: var(--muted);
    font-style: italic;
    font-size: 13px;
    padding: 20px;
    line-height: 1.8;
  }

  /* ── Bottom panel: logs + analysis ── */
  .bottom-panel {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    border-top: 1px solid var(--border);
    max-height: 260px;
    background: var(--surface);
  }

  .log-panel {
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border);
    overflow: hidden;
  }

  .panel-title {
    padding: 8px 16px;
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
    flex-shrink: 0;
  }

  .log-entries {
    flex: 1;
    overflow-y: auto;
    padding: 12px 16px;
    font-size: 12px;
    line-height: 1.8;
  }

  .log-entry { display: flex; gap: 10px; }
  .log-entry .ts { color: var(--muted); flex-shrink: 0; }
  .log-entry.info    .msg { color: var(--text); }
  .log-entry.success .msg { color: var(--accent); }
  .log-entry.warn    .msg { color: var(--warn); }
  .log-entry.error   .msg { color: var(--danger); }

  /* ── Stats panel ── */
  .stats-panel { overflow-y: auto; }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--border);
    height: 100%;
  }

  .stat-card {
    background: var(--surface);
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .stat-label {
    font-size: 10px;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }

  .stat-value {
    font-size: 22px;
    font-family: var(--sans);
    font-weight: 800;
    color: var(--text);
  }

  .stat-value.ok     { color: var(--accent); }
  .stat-value.warn   { color: var(--warn); }
  .stat-value.danger { color: var(--danger); }

  /* ── Vuln tags ── */
  .vuln-tags {
    padding: 12px 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-content: flex-start;
    overflow-y: auto;
  }

  .vtag {
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-family: var(--mono);
    border: 1px solid;
  }

  .vtag.CRITICAL { background: rgba(255,79,79,.1);   color: var(--danger); border-color: rgba(255,79,79,.3); }
  .vtag.HIGH     { background: rgba(255,140,0,.1);   color: #ff8c00;       border-color: rgba(255,140,0,.3); }
  .vtag.MEDIUM   { background: rgba(255,179,71,.1);  color: var(--warn);   border-color: rgba(255,179,71,.3); }
  .vtag.LOW      { background: rgba(0,200,255,.08);  color: var(--accent2);border-color: rgba(0,200,255,.2); }

  /* ── Spinner ── */
  .spinner-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(10,12,16,0.7);
    backdrop-filter: blur(4px);
    z-index: 100;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 20px;
  }

  .spinner-overlay.active { display: flex; }

  .spinner {
    width: 48px; height: 48px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .spinner-label {
    font-family: var(--sans);
    font-size: 14px;
    color: var(--subtext);
    animation: pulse 1.4s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: .4; }
    50%       { opacity: 1; }
  }

  /* ── Verification badges ── */
  .verify-row {
    display: flex;
    gap: 8px;
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }

  .vbadge {
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }

  .vbadge.pass { background: rgba(0,255,163,.12); color: var(--accent);  border: 1px solid rgba(0,255,163,.25); }
  .vbadge.fail { background: rgba(255,79,79,.1);  color: var(--danger);  border: 1px solid rgba(255,79,79,.25); }

  /* ── Scrollbars ── */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  /* ── Copy button ── */
  .btn-copy {
    padding: 3px 10px;
    background: transparent;
    color: var(--subtext);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 10px;
    cursor: pointer;
    transition: all .15s;
  }

  .btn-copy:hover { color: var(--accent); border-color: rgba(0,255,163,.3); }

  .iter-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    background: rgba(0,200,255,.1);
    color: var(--accent2);
    font-size: 11px;
    border: 1px solid rgba(0,200,255,.2);
  }
</style>
</head>
<body>

<!-- ── Header ── -->
<header>
  <div class="logo-icon">⚙</div>
  <div class="logo-text">Self<span>Heal</span>Compiler</div>
  <div class="badge">Gemini-Powered · Agentic Loop</div>
</header>

<!-- ── Spinner overlay ── -->
<div class="spinner-overlay" id="spinnerOverlay">
  <div class="spinner"></div>
  <div class="spinner-label" id="spinnerLabel">Initializing agent...</div>
</div>

<!-- ── Main workspace ── -->
<div class="workspace">

  <!-- Config bar -->
  <div class="config-bar">
    <label>API KEY</label>
    <input type="password" id="apiKey" placeholder="AIza...your Gemini API key"/>
    <label>MAX ITERATIONS</label>
    <input type="number" id="maxIter" value="5" min="1" max="10"/>
    <button class="btn-clear" onclick="clearAll()">Clear</button>
    <button class="btn-run" id="runBtn" onclick="runCompiler()">
      <span>▶</span> Run Compiler
    </button>
  </div>

  <!-- Input pane -->
  <div class="pane">
    <div class="pane-header">
      <span class="dot dot-red"></span>
      <span class="dot dot-yellow"></span>
      <span class="dot dot-green"></span>
      &nbsp; input.py — your code
    </div>
    <textarea id="inputCode" spellcheck="false" placeholder="# Paste your Python code here...
# Example with vulnerabilities:

user_input = input('Enter expression: ')
result = eval(user_input)   # dangerous!
os.system('ls ' + user_input)  # also dangerous!
print(result)
"></textarea>
  </div>

  <!-- Output pane -->
  <div class="pane">
    <div class="pane-header">
      <span class="dot dot-blue"></span>
      &nbsp; healed_output.py — fixed code
      <span id="verifyBadges" style="margin-left:auto;display:flex;gap:6px;"></span>
      <button class="btn-copy" onclick="copyOutput()" id="copyBtn" style="display:none">Copy</button>
    </div>
    <div id="outputArea">
      <div class="placeholder-text">
        ← Paste your Python code, enter your Gemini API key,<br>
        then click <strong style="color:var(--accent)">Run Compiler</strong>.<br><br>
        The agent will detect vulnerabilities, apply fixes,<br>
        and loop until your code is clean and verified.
      </div>
    </div>
  </div>

  <!-- Bottom panel -->
  <div class="bottom-panel">

    <!-- Agent logs -->
    <div class="log-panel">
      <div class="panel-title">Agent Loop · Live Logs</div>
      <div class="log-entries" id="logEntries">
        <div class="log-entry info">
          <span class="ts">--:--:--</span>
          <span class="msg">Waiting for code submission...</span>
        </div>
      </div>
    </div>

    <!-- Stats + Vulnerabilities -->
    <div class="stats-panel">
      <div class="panel-title">Analysis · Stats &amp; Vulnerabilities</div>
      <div id="statsArea">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Iterations</div>
            <div class="stat-value" id="statIter">—</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Fixes Applied</div>
            <div class="stat-value" id="statFixes">—</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Vulnerabilities</div>
            <div class="stat-value" id="statVulns">—</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Status</div>
            <div class="stat-value" id="statStatus">—</div>
          </div>
        </div>
      </div>
      <div id="vulnTags" class="vuln-tags" style="display:none"></div>
    </div>

  </div>
</div>

<script>
  const spinnerLabels = [
    'Scanning for vulnerabilities...',
    'Consulting Gemini agent...',
    'Applying safe transformations...',
    'Running verification engine...',
    'Iterating healing loop...'
  ];

  let spinnerTimer = null;

  function startSpinner() {
    const overlay = document.getElementById('spinnerOverlay');
    const label   = document.getElementById('spinnerLabel');
    overlay.classList.add('active');
    let i = 0;
    label.textContent = spinnerLabels[0];
    spinnerTimer = setInterval(() => {
      i = (i + 1) % spinnerLabels.length;
      label.textContent = spinnerLabels[i];
    }, 1800);
  }

  function stopSpinner() {
    clearInterval(spinnerTimer);
    document.getElementById('spinnerOverlay').classList.remove('active');
  }

  function ts() {
    return new Date().toLocaleTimeString('en-US', {hour12: false});
  }

  function addLog(msg, level = 'info') {
    const container = document.getElementById('logEntries');
    const div = document.createElement('div');
    div.className = `log-entry ${level}`;
    div.innerHTML = `<span class="ts">${ts()}</span><span class="msg">${msg}</span>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function clearLogs() {
    document.getElementById('logEntries').innerHTML = '';
  }

  function setStats(iterations, fixes, vulns, status) {
    document.getElementById('statIter').textContent  = iterations;
    document.getElementById('statFixes').textContent = fixes;

    const vEl = document.getElementById('statVulns');
    vEl.textContent = vulns;
    vEl.className   = 'stat-value ' + (vulns === 0 ? 'ok' : 'danger');

    const sEl = document.getElementById('statStatus');
    sEl.textContent = status ? 'HEALED' : 'PARTIAL';
    sEl.className   = 'stat-value ' + (status ? 'ok' : 'warn');
  }

  function renderVulnTags(decisions) {
    const container = document.getElementById('vulnTags');
    container.innerHTML = '';
    if (!decisions || decisions.length === 0) {
      container.style.display = 'none';
      return;
    }
    container.style.display = 'flex';
    decisions.forEach(d => {
      const tag = document.createElement('div');
      // try to get severity from strategy
      const sev = d.severity || 'MEDIUM';
      tag.className = `vtag ${sev}`;
      tag.title = d.explanation || '';
      tag.textContent = `L${d.line} ${d.vulnerability} → ${d.strategy}`;
      container.appendChild(tag);
    });
  }

  function renderVerifyBadges(verification) {
    const container = document.getElementById('verifyBadges');
    container.innerHTML = '';
    if (!verification) return;
    const checks = [
      ['syntax',          'Syntax'],
      ['vulnerabilities', 'Vulns'],
      ['compilable',      'Compile']
    ];
    checks.forEach(([key, label]) => {
      if (!verification[key]) return;
      const b = document.createElement('div');
      b.className = `vbadge ${verification[key].passed ? 'pass' : 'fail'}`;
      b.textContent = `${verification[key].passed ? '✓' : '✗'} ${label}`;
      container.appendChild(b);
    });
  }

  async function runCompiler() {
    const code   = document.getElementById('inputCode').value.trim();
    const apiKey = document.getElementById('apiKey').value.trim();
    const maxIter = parseInt(document.getElementById('maxIter').value) || 5;

    if (!code) { addLog('No code provided.', 'warn'); return; }
    if (!apiKey) { addLog('Gemini API key is required.', 'error'); return; }

    document.getElementById('runBtn').disabled = true;
    document.getElementById('outputArea').innerHTML = '';
    document.getElementById('verifyBadges').innerHTML = '';
    document.getElementById('copyBtn').style.display = 'none';
    document.getElementById('vulnTags').style.display = 'none';
    clearLogs();
    setStats('—', '—', '—', null);
    startSpinner();

    addLog('Submitting code to self-healing compiler...', 'info');

    try {
      const resp = await fetch('/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, api_key: apiKey, max_iterations: maxIter })
      });

      const data = await resp.json();

      if (!resp.ok || data.error) {
        addLog(`Server error: ${data.error || resp.statusText}`, 'error');
        stopSpinner();
        document.getElementById('runBtn').disabled = false;
        return;
      }

      // Render iteration logs from backend
      if (data.iteration_logs) {
        data.iteration_logs.forEach(entry => {
          addLog(entry.message, entry.level || 'info');
        });
      }

      // Render healed code
      const pre = document.createElement('pre');
      pre.className = 'output-code';
      pre.textContent = data.healed_code || '';
      document.getElementById('outputArea').appendChild(pre);

      // Stats
      const vulnsRemaining = (data.vulnerabilities_remaining || []).length;
      setStats(
        data.iterations,
        (data.fixes_applied || []).length,
        vulnsRemaining,
        data.fully_healed
      );

      // Verification badges
      renderVerifyBadges(data.verification);

      // Vuln decision tags
      renderVulnTags(data.agent_decisions);

      // Copy button
      document.getElementById('copyBtn').style.display = 'block';

      // Summary log
      if (data.fully_healed) {
        addLog(`✅ Fully healed in ${data.iterations} iteration(s). All checks passed.`, 'success');
      } else {
        addLog(`⚠ Healing complete with ${vulnsRemaining} issue(s) remaining after ${data.iterations} iteration(s).`, 'warn');
      }

    } catch (err) {
      addLog(`Fetch error: ${err.message}`, 'error');
    } finally {
      stopSpinner();
      document.getElementById('runBtn').disabled = false;
    }
  }

  function copyOutput() {
    const pre = document.querySelector('.output-code');
    if (pre) {
      navigator.clipboard.writeText(pre.textContent);
      const btn = document.getElementById('copyBtn');
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = 'Copy', 1800);
    }
  }

  function clearAll() {
    document.getElementById('inputCode').value = '';
    document.getElementById('outputArea').innerHTML = `
      <div class="placeholder-text">
        ← Paste your Python code, enter your Gemini API key,<br>
        then click <strong style="color:var(--accent)">Run Compiler</strong>.
      </div>`;
    document.getElementById('verifyBadges').innerHTML = '';
    document.getElementById('copyBtn').style.display = 'none';
    document.getElementById('vulnTags').style.display = 'none';
    clearLogs();
    setStats('—', '—', '—', null);
    addLog('Workspace cleared.', 'info');
  }

  // Allow Tab key in textarea
  document.addEventListener('DOMContentLoaded', () => {
    const ta = document.getElementById('inputCode');
    ta.addEventListener('keydown', e => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const s = ta.selectionStart;
        ta.value = ta.value.substring(0, s) + '    ' + ta.value.substring(ta.selectionEnd);
        ta.selectionStart = ta.selectionEnd = s + 4;
      }
    });
  });
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/compile', methods=['POST'])
def compile_code():
    data = request.get_json(force=True)

    code          = data.get('code', '').strip()
    api_key       = data.get('api_key', '').strip() or os.environ.get('GEMINI_API_KEY', '')
    max_iterations = int(data.get('max_iterations', 5))

    if not code:
        return jsonify({'error': 'No code provided'}), 400
    if not api_key:
        return jsonify({'error': 'Gemini API key is required'}), 400

    try:
        agent  = Agent(api_key=api_key)
        result = agent.agentic_healing_loop(code, max_iterations=max_iterations)
        return jsonify(result)

    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({'error': str(e), 'traceback': tb}), 500


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n🚀 Self-Healing Agentic Compiler running at http://localhost:{port}")
    print("   Press Ctrl+C to stop.\n")
    app.run(debug=True, host='0.0.0.0', port=port)