from flask import Flask, jsonify, render_template_string
from position_tracker import positions, event_log
import bot_state

app = Flask(__name__)

HTML = """<!doctype html>
<html>
<head>
<title>Signal Bot Dashboard</title>
<style>
body { font-family: sans-serif; background:#111; color:#eee; padding:20px; }
table { width:100%; border-collapse: collapse; margin-bottom: 30px; }
th, td { border-bottom: 1px solid #333; padding: 8px; text-align:left; }
h2 { border-bottom: 2px solid #444; padding-bottom: 5px; }
.long { color: #4caf50; } .short { color: #f44336; }
button { padding: 10px 20px; font-size: 16px; border: none; border-radius: 6px; color: white; cursor: pointer; margin-bottom: 20px; }
</style>
</head>
<body>
<h1>Signal Bot Dashboard</h1>
<button id="toggleBtn" onclick="toggleBot()">Loading...</button>
<h2>Open Positions</h2>
<table id="positions"><thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Remaining Qty</th><th>Stop Loss</th><th>TP1 Hit</th></tr></thead><tbody></tbody></table>
<h2>Event Log</h2>
<table id="log"><thead><tr><th>Time</th><th>Type</th><th>Symbol</th><th>Details</th></tr></thead><tbody></tbody></table>
<script>
async function refresh() {
    const res = await fetch('/api/status');
    const data = await res.json();

    updateButton(data.bot_enabled);

    const posBody = document.querySelector('#positions tbody');
    posBody.innerHTML = '';
    for (const [symbol, pos] of Object.entries(data.positions)) {
        posBody.innerHTML += `<tr>
            <td>${symbol}</td><td class="${pos.side}">${pos.side}</td>
            <td>${pos.entry_price}</td><td>${pos.remaining_qty.toFixed(4)}</td>
            <td>${pos.stop_loss ?? '-'}</td><td>${pos.tp1_hit}</td></tr>`;
    }

    const logBody = document.querySelector('#log tbody');
    logBody.innerHTML = '';
    for (const entry of data.log.slice().reverse()) {
        logBody.innerHTML += `<tr>
            <td>${entry.time}</td><td>${entry.type}</td>
            <td>${entry.symbol}</td><td>${entry.details}</td></tr>`;
    }
}
function updateButton(enabled) {
    const btn = document.getElementById('toggleBtn');
    btn.textContent = enabled ? 'Bot: RUNNING (click to pause)' : 'Bot: PAUSED (click to resume)';
    btn.style.background = enabled ? '#4caf50' : '#f44336';
}
async function toggleBot() {
    const res = await fetch('/api/toggle', { method: 'POST' });
    const data = await res.json();
    updateButton(data.bot_enabled);
}
setInterval(refresh, 3000);
refresh();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/status")
def status():
    return jsonify({"positions": positions, "log": event_log, "bot_enabled": bot_state.bot_enabled})

@app.route("/api/toggle", methods=["POST"])
def toggle():
    bot_state.bot_enabled = not bot_state.bot_enabled
    return jsonify({"bot_enabled": bot_state.bot_enabled})

def run_dashboard():
    app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)