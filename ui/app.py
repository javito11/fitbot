"""
FitBot Config Manager — UI local para editar config.json y el cron de scheduled.yml
Uso: uv run python ui/app.py
Luego abre http://localhost:5001 en el navegador.
"""

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "scheduled.yml"

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FitBot Config</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0f0f13;
    --surface: #1a1a23;
    --surface2: #22222e;
    --border: #2e2e3e;
    --accent: #6c63ff;
    --accent-hover: #8079ff;
    --accent-dim: #6c63ff22;
    --danger: #ff5a5a;
    --danger-dim: #ff5a5a22;
    --success: #4caf7d;
    --text: #e8e8f0;
    --text-muted: #7a7a9a;
    --radius: 10px;
    --day-size: 42px;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 14px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 24px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 16px;
    letter-spacing: 0.5px;
  }

  .logo-icon {
    width: 32px; height: 32px;
    background: var(--accent);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
  }

  .header-actions { display: flex; gap: 10px; align-items: center; }

  #status {
    font-size: 12px;
    color: var(--text-muted);
    padding: 4px 10px;
    border-radius: 20px;
    transition: all 0.3s;
  }
  #status.ok { background: #4caf7d22; color: var(--success); }
  #status.err { background: var(--danger-dim); color: var(--danger); }

  .btn {
    padding: 8px 18px;
    border-radius: var(--radius);
    border: none;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    transition: all 0.15s;
  }
  .btn-primary {
    background: var(--accent);
    color: #fff;
  }
  .btn-primary:hover { background: var(--accent-hover); transform: translateY(-1px); }
  .btn-primary:active { transform: translateY(0); }

  main {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 24px;
    max-width: 960px;
    width: 100%;
    margin: 0 auto;
  }

  @media (max-width: 700px) {
    main { grid-template-columns: 1fr; }
  }

  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .panel-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  /* ─── Day toggles ─── */
  .day-row {
    display: flex;
    gap: 6px;
  }

  .day-btn {
    width: var(--day-size);
    height: var(--day-size);
    border-radius: 50%;
    border: 2px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s;
    display: flex; align-items: center; justify-content: center;
  }
  .day-btn:hover { border-color: var(--accent); color: var(--text); }
  .day-btn.active {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }

  /* ─── Booking goals list ─── */
  #goals-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .goal-row {
    display: grid;
    grid-template-columns: auto 1fr 1fr auto;
    align-items: center;
    gap: 8px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 12px;
  }

  .goal-day-badge {
    background: var(--accent-dim);
    color: var(--accent);
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    white-space: nowrap;
  }

  .goal-input {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    padding: 6px 8px;
    font-size: 13px;
    width: 100%;
    outline: none;
    transition: border-color 0.15s;
  }
  .goal-input:focus { border-color: var(--accent); }

  .btn-remove {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    width: 28px; height: 28px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.15s;
    flex-shrink: 0;
  }
  .btn-remove:hover { background: var(--danger-dim); border-color: var(--danger); color: var(--danger); }

  .add-row {
    display: flex;
    gap: 8px;
  }

  /* ─── Schedule panel ─── */
  .label {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 6px;
    font-weight: 600;
  }

  .hour-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .hour-input {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    padding: 10px 14px;
    font-size: 22px;
    font-weight: 700;
    width: 110px;
    text-align: center;
    outline: none;
    transition: border-color 0.15s;
  }
  .hour-input:focus { border-color: var(--accent); }

  .utc-note {
    font-size: 11px;
    color: var(--text-muted);
  }

  .preview-box {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 14px;
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.6;
  }

  .preview-box strong { color: var(--text); }

  .divider {
    border: none;
    border-top: 1px solid var(--border);
  }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">🤖</div>
    FitBot Config
  </div>
  <div class="header-actions">
    <span id="status"></span>
    <button class="btn btn-primary" onclick="saveAll()">Guardar cambios</button>
  </div>
</header>

<main>
  <!-- ─── Panel izquierdo: Clases ─── -->
  <div class="panel">
    <span class="panel-title">Clases a reservar</span>

    <div>
      <div class="label">Selecciona el día y añade la clase</div>
      <div class="day-row" id="booking-days">
        <!-- JS los rellena -->
      </div>
    </div>

    <hr class="divider">

    <div id="goals-list">
      <!-- goal-rows generados por JS -->
    </div>

    <div class="add-row">
      <select id="new-day-select" class="goal-input" style="flex:1"></select>
      <input id="new-time" type="time" class="goal-input" style="width:110px" value="18:00">
      <input id="new-name" type="text" class="goal-input" placeholder="Nombre clase" style="flex:1.5">
      <button class="btn btn-primary" onclick="addGoal()" style="padding:6px 14px">+</button>
    </div>
  </div>

  <!-- ─── Panel derecho: Cron ─── -->
  <div class="panel">
    <span class="panel-title">Programación del bot</span>

    <div>
      <div class="label">Días de ejecución</div>
      <div class="day-row" id="cron-days">
        <!-- JS los rellena -->
      </div>
    </div>

    <hr class="divider">

    <div>
      <div class="label">Hora de ejecución (UTC)</div>
      <div class="hour-row">
        <input id="cron-hour" type="time" class="hour-input" value="05:00" oninput="updatePreview()">
        <span class="utc-note">UTC<br>España = UTC+1/+2</span>
      </div>
    </div>

    <hr class="divider">

    <div class="preview-box" id="cron-preview">
      <!-- rellenado por JS -->
    </div>

    <div class="preview-box" style="margin-top:-8px">
      <span style="font-size:11px; color: var(--text-muted)">Expresión cron:</span><br>
      <code id="cron-expr" style="color: var(--accent); font-size:13px"></code>
    </div>
  </div>
</main>

<script>
const DAY_NAMES = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];
const DAY_NAMES_FULL = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
// cron weekday: 1=Mon,2=Tue,3=Wed,4=Thu,5=Fri,6=Sat,0=Sun
// python weekday: 0=Mon,1=Tue,2=Wed,3=Thu,4=Fri,5=Sat,6=Sun
const PY_TO_CRON = [1,2,3,4,5,6,0];
const CRON_TO_PY = {1:0,2:1,3:2,4:3,5:4,6:5,0:6};

let goals = {};       // { pyDay: { time: "1800", name: "HYROX" } }
let cronDays = new Set(); // python weekdays

// ─── Init ───────────────────────────────────────────────
async function init() {
  const res = await fetch('/api/config');
  const data = await res.json();
  goals = data.goals || {};
  const cronInfo = data.cron || {};
  cronDays = new Set((cronInfo.days || []).map(Number));

  const [h, m] = (cronInfo.time || '05:00').split(':');
  document.getElementById('cron-hour').value = `${h.padStart(2,'0')}:${(m||'00').padStart(2,'0')}`;

  renderBookingDays();
  renderGoalsList();
  renderCronDays();
  updatePreview();
  populateDaySelect();
}

// ─── Booking day badges ──────────────────────────────────
function renderBookingDays() {
  const container = document.getElementById('booking-days');
  container.innerHTML = '';
  DAY_NAMES.forEach((name, pyDay) => {
    const btn = document.createElement('button');
    btn.className = 'day-btn' + (goals[pyDay] ? ' active' : '');
    btn.textContent = name;
    btn.title = DAY_NAMES_FULL[pyDay];
    btn.onclick = () => toggleBookingDay(pyDay);
    container.appendChild(btn);
  });
}

function toggleBookingDay(pyDay) {
  if (goals[pyDay]) {
    delete goals[pyDay];
  } else {
    goals[pyDay] = { time: '1800', name: 'HYROX' };
  }
  renderBookingDays();
  renderGoalsList();
}

// ─── Goals list ──────────────────────────────────────────
function renderGoalsList() {
  const list = document.getElementById('goals-list');
  list.innerHTML = '';
  const sorted = Object.keys(goals).map(Number).sort();
  if (sorted.length === 0) {
    list.innerHTML = '<div style="color:var(--text-muted);font-size:13px;text-align:center;padding:12px">Sin clases configuradas. Pulsa un día o usa el formulario.</div>';
    return;
  }
  sorted.forEach(pyDay => {
    const g = goals[pyDay];
    const row = document.createElement('div');
    row.className = 'goal-row';

    const badge = document.createElement('span');
    badge.className = 'goal-day-badge';
    badge.textContent = DAY_NAMES_FULL[pyDay];

    const timeVal = g.time.length === 4
      ? `${g.time.slice(0,2)}:${g.time.slice(2)}`
      : g.time;

    const timeInput = document.createElement('input');
    timeInput.type = 'time';
    timeInput.className = 'goal-input';
    timeInput.value = timeVal;
    timeInput.oninput = (e) => {
      goals[pyDay].time = e.target.value.replace(':', '');
    };

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'goal-input';
    nameInput.placeholder = 'Nombre clase';
    nameInput.value = g.name;
    nameInput.oninput = (e) => { goals[pyDay].name = e.target.value; };

    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn-remove';
    removeBtn.innerHTML = '✕';
    removeBtn.onclick = () => {
      delete goals[pyDay];
      renderBookingDays();
      renderGoalsList();
    };

    row.append(badge, timeInput, nameInput, removeBtn);
    list.appendChild(row);
  });
}

function populateDaySelect() {
  const sel = document.getElementById('new-day-select');
  sel.innerHTML = '';
  DAY_NAMES_FULL.forEach((name, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = name;
    sel.appendChild(opt);
  });
}

function addGoal() {
  const pyDay = parseInt(document.getElementById('new-day-select').value);
  const rawTime = document.getElementById('new-time').value;
  const name = document.getElementById('new-name').value.trim() || 'HYROX';
  goals[pyDay] = { time: rawTime.replace(':', ''), name };
  renderBookingDays();
  renderGoalsList();
}

// ─── Cron days ───────────────────────────────────────────
function renderCronDays() {
  const container = document.getElementById('cron-days');
  container.innerHTML = '';
  DAY_NAMES.forEach((name, pyDay) => {
    const btn = document.createElement('button');
    btn.className = 'day-btn' + (cronDays.has(pyDay) ? ' active' : '');
    btn.textContent = name;
    btn.title = DAY_NAMES_FULL[pyDay];
    btn.onclick = () => {
      cronDays.has(pyDay) ? cronDays.delete(pyDay) : cronDays.add(pyDay);
      renderCronDays();
      updatePreview();
    };
    container.appendChild(btn);
  });
}

// ─── Cron preview ────────────────────────────────────────
function updatePreview() {
  const timeVal = document.getElementById('cron-hour').value || '05:00';
  const [hStr, mStr] = timeVal.split(':');
  const h = parseInt(hStr), m = parseInt(mStr || '0');

  const sorted = [...cronDays].sort();
  const dayNames = sorted.length
    ? sorted.map(d => DAY_NAMES_FULL[d]).join(', ')
    : '<em>ningún día seleccionado</em>';

  // Spain offset: UTC+1 winter, UTC+2 summer — show both
  const spainH1 = ((h + 1) % 24).toString().padStart(2, '0');
  const spainH2 = ((h + 2) % 24).toString().padStart(2, '0');

  document.getElementById('cron-preview').innerHTML =
    `El bot se ejecutará los <strong>${dayNames}</strong> a las <strong>${hStr.padStart(2,'0')}:${mStr||'00'} UTC</strong>`+
    `<br><small>${spainH1}:${mStr||'00'} hora española (invierno) · ${spainH2}:${mStr||'00'} (verano)</small>`;

  document.getElementById('cron-expr').textContent = buildCron(m, h, sorted);
}

function buildCron(minute, hour, pyDays) {
  if (!pyDays.length) return '— sin días —';
  const cronD = pyDays.map(d => PY_TO_CRON[d]).sort((a,b)=>a-b);
  // try to compress to range
  let dayStr;
  if (cronD.length === 5 && cronD.every((v,i) => v === i+1)) {
    dayStr = '1-5';
  } else {
    dayStr = cronD.join(',');
  }
  return `${minute} ${hour} * * ${dayStr}`;
}

// ─── Save ─────────────────────────────────────────────────
async function saveAll() {
  const timeVal = document.getElementById('cron-hour').value || '05:00';
  const [h, m] = timeVal.split(':');
  const sorted = [...cronDays].sort();
  const cronDaysCron = sorted.map(d => PY_TO_CRON[d]).sort((a,b)=>a-b);

  if (!sorted.length) {
    const el = document.getElementById('status');
    el.textContent = 'Selecciona al menos un día de ejecución';
    el.className = 'err';
    setTimeout(() => { el.textContent = ''; el.className = ''; }, 3000);
    return;
  }

  const payload = {
    goals,
    cron: buildCron(parseInt(m||0), parseInt(h), sorted),
  };

  const res = await fetch('/api/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await res.json();
  const el = document.getElementById('status');
  if (result.ok) {
    el.textContent = 'Guardado correctamente';
    el.className = 'ok';
  } else {
    el.textContent = 'Error: ' + result.error;
    el.className = 'err';
  }
  setTimeout(() => { el.textContent = ''; el.className = ''; }, 3000);
}

init();
</script>
</body>
</html>
"""


# ─── Helpers ───────────────────────────────────────────────────────────────────

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def parse_cron_days(cron_expr: str) -> list[int]:
    """Return python weekday indices from a cron expression's day-of-week field.
    Cron: 0=Sun,1=Mon,...,6=Sat  →  Python: 0=Mon,...,6=Sun
    """
    CRON_TO_PY = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
    parts = cron_expr.strip().split()
    if len(parts) < 5:
        return []
    dow = parts[4]
    cron_days = set()
    for token in dow.split(","):
        if "-" in token:
            start, end = token.split("-")
            cron_days.update(range(int(start), int(end) + 1))
        elif token.isdigit():
            cron_days.add(int(token))
    return sorted(CRON_TO_PY[d] for d in cron_days if d in CRON_TO_PY)


def parse_cron_time(cron_expr: str) -> str:
    """Return HH:MM from a cron expression."""
    parts = cron_expr.strip().split()
    if len(parts) < 2:
        return "05:00"
    minute = parts[0].zfill(2)
    hour = parts[1].zfill(2)
    return f"{hour}:{minute}"


def read_workflow_cron() -> str:
    """Extract the cron expression from the workflow file."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    m = re.search(r"cron:\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else "0 5 * * 1-5"


def update_workflow_cron(new_cron: str):
    """Replace the cron expression in the workflow file."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    updated = re.sub(
        r"(cron:\s*['\"])[^'\"]+(['\"])",
        lambda m: f"{m.group(1)}{new_cron}{m.group(2)}",
        text,
    )
    WORKFLOW_PATH.write_text(updated, encoding="utf-8")


# ─── HTTP Handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silencia el log de cada request

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/" or path == "":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/config":
            cfg = load_config()
            cron_expr = read_workflow_cron()
            self.send_json({
                "goals": cfg.get("booking-goals", {}),
                "cron": {
                    "days": parse_cron_days(cron_expr),
                    "time": parse_cron_time(cron_expr),
                },
            })
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/save":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            try:
                # Actualizar config.json
                cfg = load_config()
                cfg["booking-goals"] = {
                    str(k): v for k, v in body["goals"].items()
                }
                save_config(cfg)

                # Actualizar scheduled.yml
                update_workflow_cron(body["cron"])

                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, status=500)
        else:
            self.send_response(404)
            self.end_headers()


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = 5001
    server = HTTPServer(("localhost", port), Handler)
    print(f"FitBot Config UI →  http://localhost:{port}")
    print("Ctrl+C para detener.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        sys.exit(0)
