"""
web_viewer.py — Flask log görüntüleyici ve durum paneli
"""

from flask import Flask, jsonify
from config import LOG_FILE
from state import agent_state

app = Flask(__name__)


@app.route("/")
def home():
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            logs = f.read()[-4000:]
    except FileNotFoundError:
        logs = "(henüz log yok)"

    state = agent_state.state
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>AI Agent — Log Viewer</title>
  <style>
    body {{ font-family: monospace; background: #111; color: #0f0; padding: 20px; }}
    pre  {{ white-space: pre-wrap; word-wrap: break-word; }}
    .status {{ background: #1a1a1a; border: 1px solid #333; padding: 12px; margin-bottom: 16px; border-radius: 6px; }}
    h2   {{ color: #4af; }}
  </style>
  <meta http-equiv="refresh" content="10">
</head>
<body>
  <h2>🤖 AI Agent Dashboard</h2>
  <div class="status">
    <b>Durum:</b> {state.status.name}<br>
    <b>Hedef:</b> {state.goal or '—'}<br>
    <b>Aktif Görev:</b> {state.current_task or '—'}<br>
    <b>Adım:</b> {state.step_count}<br>
    <b>Tamamlanan:</b> {len(state.completed_tasks)} görev
  </div>
  <h2>📜 Son Loglar</h2>
  <pre>{logs}</pre>
</body>
</html>"""
    return html


@app.route("/api/status")
def api_status():
    s = agent_state.state
    return jsonify({
        "status":           s.status.name,
        "goal":             s.goal,
        "current_task":     s.current_task,
        "step_count":       s.step_count,
        "completed_tasks":  s.completed_tasks,
        "pending_tasks":    s.task_queue,
    })


def start_web(port: int = 5000):
    """Flask sunucusunu başlatır (blocking — ayrı thread'de çalıştır)."""
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
