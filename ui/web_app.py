#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  ui/web_app.py  —  ÉTAPE 5
#  Dashboard Web Flask — Interface navigateur complète
#  Accès : http://localhost:5000
# ============================================================
import sys, os, json, base64, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, render_template_string, send_file
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from modules.iot_sensors import IoTSensorManager
from modules.simplex import simplex_chapter2
from modules.linear_prog import solve_chapter1
from modules.route_optimizer import FleetPlanner

app     = Flask(__name__)
manager = None
plan    = None

def get_manager():
    global manager
    if manager is None:
        manager = IoTSensorManager()
    return manager

def get_plan():
    global plan
    if plan is None:
        sol = simplex_chapter2()["integer"]
        plan = FleetPlanner(sol, get_manager()).plan()
    return plan


# ════════════════════════════════════════════════════════════
#  Template HTML principal
# ════════════════════════════════════════════════════════════
HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EMSI — Gestion des Déchets 2025/2026</title>
<style>
  :root {
    --bg:     #1E293B; --bg2: #0F172A; --card: #1E3A5F;
    --text:   #F1F5F9; --muted: #94A3B8;
    --green:  #10B981; --red: #EF4444;
    --yellow: #F59E0B; --blue: #3B82F6; --purple: #A78BFA;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:var(--bg2); color:var(--text); }

  header {
    background:var(--bg); padding:14px 24px;
    display:flex; justify-content:space-between; align-items:center;
    border-bottom:2px solid var(--card);
  }
  header h1 { font-size:1.2rem; color:var(--text); }
  header span { font-size:.8rem; color:var(--muted); }

  nav {
    background:var(--bg); display:flex; gap:4px;
    padding:8px 16px; border-bottom:1px solid #334155;
  }
  nav button {
    background:transparent; border:none; color:var(--muted);
    padding:8px 18px; border-radius:6px; cursor:pointer;
    font-size:.9rem; font-weight:600; transition:.2s;
  }
  nav button:hover, nav button.active {
    background:var(--card); color:var(--text);
  }

  .tab-content { display:none; padding:16px; }
  .tab-content.active { display:block; }

  .kpi-grid {
    display:grid; grid-template-columns:repeat(6,1fr);
    gap:10px; margin-bottom:16px;
  }
  .kpi-card {
    background:var(--card); border-radius:10px;
    padding:14px; text-align:center; border:1px solid #334155;
  }
  .kpi-card .val  { font-size:1.6rem; font-weight:800; }
  .kpi-card .lbl  { font-size:.75rem; color:var(--muted); margin-top:4px; }

  .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .grid-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
  .grid-4 { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }

  .card {
    background:var(--card); border-radius:10px;
    padding:16px; border:1px solid #334155;
  }
  .card h3 { font-size:.9rem; color:var(--muted); margin-bottom:10px; }

  table { width:100%; border-collapse:collapse; font-size:.82rem; }
  th { background:var(--bg); color:var(--blue);
       padding:8px; text-align:left; position:sticky; top:0; }
  td { padding:7px 8px; border-bottom:1px solid #334155; }
  tr:hover td { background:rgba(59,130,246,.08); }

  .badge {
    display:inline-block; padding:2px 8px; border-radius:12px;
    font-size:.75rem; font-weight:700;
  }
  .badge.CRITICAL { background:#7F1D1D; color:#FCA5A5; }
  .badge.URGENT   { background:#78350F; color:#FCD34D; }
  .badge.WARNING  { background:#3B2D00; color:#FDE68A; }
  .badge.NORMAL   { background:#064E3B; color:#6EE7B7; }

  .bar-fill {
    height:8px; border-radius:4px; background:var(--green);
    transition:width .4s;
  }
  .bar-fill.warn  { background:var(--yellow); }
  .bar-fill.crit  { background:var(--red);    }

  img.chart { width:100%; border-radius:8px; margin-top:8px; }

  .btn {
    display:inline-block; padding:8px 18px; border-radius:8px;
    border:none; cursor:pointer; font-weight:700; font-size:.85rem;
    transition:.15s; margin:4px;
  }
  .btn-green  { background:var(--green);  color:#fff; }
  .btn-blue   { background:var(--blue);   color:#fff; }
  .btn-yellow { background:var(--yellow); color:#000; }
  .btn-purple { background:var(--purple); color:#fff; }
  .btn:hover  { filter:brightness(1.15); }

  .scrollbox { max-height:320px; overflow-y:auto; }
  footer {
    text-align:center; padding:10px; color:var(--muted);
    font-size:.78rem; border-top:1px solid #334155; margin-top:20px;
  }
  .loading { color:var(--yellow); font-style:italic; font-size:.85rem; }
  pre { background:var(--bg2); padding:12px; border-radius:8px;
        font-size:.8rem; color:var(--green); overflow-x:auto; }
</style>
</head>
<body>

<header>
  <h1>🗑️ Système d'Optimisation — Gestion des Déchets</h1>
  <span>EMSI 2025/2026 &nbsp;|&nbsp; Yahya Zaizi · Taki M.I. · Yasser D. · Youssef E. · Taha A.</span>
</header>

<nav id="nav">
  <button class="active" onclick="showTab('overview')">📊 Vue d'ensemble</button>
  <button onclick="showTab('lp')">🔢 Optimisation LP</button>
  <button onclick="showTab('iot')">📡 Capteurs IoT</button>
  <button onclick="showTab('routes')">🗺️ Routes</button>
  <button onclick="showTab('rapport')">📄 Rapport</button>
</nav>

<!-- ═══ TAB 1 : Vue d'ensemble ═══ -->
<div class="tab-content active" id="tab-overview">
  <div class="kpi-grid" id="kpi-grid">
    <div class="kpi-card"><div class="val" style="color:var(--blue)" id="k-bins">—</div><div class="lbl">Capteurs IoT</div></div>
    <div class="kpi-card"><div class="val" style="color:var(--green)" id="k-fill">—</div><div class="lbl">Remplissage moyen</div></div>
    <div class="kpi-card"><div class="val" style="color:var(--red)" id="k-urgent">—</div><div class="lbl">Bennes urgentes</div></div>
    <div class="kpi-card"><div class="val" style="color:var(--yellow)" id="k-weight">—</div><div class="lbl">Poids total (kg)</div></div>
    <div class="kpi-card"><div class="val" style="color:var(--green)" id="k-z">106</div><div class="lbl">Z★ optimal (t/j)</div></div>
    <div class="kpi-card"><div class="val" style="color:var(--purple)" id="k-zone">—</div><div class="lbl">Zone critique</div></div>
  </div>

  <div class="grid-2">
    <div class="card">
      <h3>📊 Solution LP — Simplexe (Ch.2)</h3>
      <div class="grid-3" id="lp-cards" style="margin-top:8px">
        <div style="text-align:center; padding:10px; background:rgba(33,150,243,.15); border-radius:8px">
          <div style="font-size:1.8rem; font-weight:800; color:#2196F3">2</div>
          <div style="font-size:.75rem; color:var(--muted)">Ménagers (x₁)</div>
          <div style="font-size:.8rem; color:#2196F3">+16 t/j</div>
        </div>
        <div style="text-align:center; padding:10px; background:rgba(76,175,80,.15); border-radius:8px">
          <div style="font-size:1.8rem; font-weight:800; color:#4CAF50">5</div>
          <div style="font-size:.75rem; color:var(--muted)">Recyclables (x₂)</div>
          <div style="font-size:.8rem; color:#4CAF50">+35 t/j</div>
        </div>
        <div style="text-align:center; padding:10px; background:rgba(255,152,0,.15); border-radius:8px">
          <div style="font-size:1.8rem; font-weight:800; color:#FF9800">5</div>
          <div style="font-size:.75rem; color:var(--muted)">Biomédicaux (x₃)</div>
          <div style="font-size:.8rem; color:#FF9800">+55 t/j</div>
        </div>
      </div>
    </div>
    <div class="card">
      <h3>📡 Top 8 Bennes Urgentes</h3>
      <div class="scrollbox">
        <table id="top-bins-table">
          <thead><tr><th>ID</th><th>Type</th><th>Niveau</th><th>Statut</th><th>Zone</th></tr></thead>
          <tbody id="top-bins-body"><tr><td colspan="5" class="loading">Chargement…</td></tr></tbody>
        </table>
      </div>
    </div>
  </div>

  <div style="margin-top:12px">
    <div class="card">
      <h3>📈 Dashboard Graphique Global</h3>
      <img id="img-overview" class="chart" src="/chart/dashboard" alt="Dashboard">
    </div>
  </div>
</div>

<!-- ═══ TAB 2 : LP ═══ -->
<div class="tab-content" id="tab-lp">
  <div class="grid-2" style="margin-bottom:12px">
    <div class="card">
      <h3>⚙️ Contrôles Modèle</h3>
      <div style="margin:8px 0">
        <label style="color:var(--muted); font-size:.85rem">Carburant C1 ≤</label>
        <input type="range" id="fuel" min="30" max="100" value="48"
               oninput="document.getElementById('fuel-val').innerText=this.value"
               style="width:100%; accent-color:var(--blue)">
        <span style="color:var(--blue); font-weight:700" id="fuel-val">48</span>
      </div>
      <div style="margin:8px 0">
        <label style="color:var(--muted); font-size:.85rem">Flotte C2 ≤</label>
        <input type="range" id="fleet" min="20" max="80" value="40"
               oninput="document.getElementById('fleet-val').innerText=this.value"
               style="width:100%; accent-color:var(--green)">
        <span style="color:var(--green); font-weight:700" id="fleet-val">40</span>
      </div>
      <div style="margin:8px 0">
        <label style="color:var(--muted); font-size:.85rem">Budget C3 ≤</label>
        <input type="range" id="budget" min="30" max="120" value="72"
               oninput="document.getElementById('budget-val').innerText=this.value"
               style="width:100%; accent-color:var(--yellow)">
        <span style="color:var(--yellow); font-weight:700" id="budget-val">72</span>
      </div>
      <div style="margin-top:12px">
        <button class="btn btn-blue"   onclick="solveCh1()">▶ Résoudre Ch.1</button>
        <button class="btn btn-green"  onclick="solveCh2()">▶ Résoudre Ch.2</button>
      </div>
      <pre id="lp-result" style="margin-top:10px; min-height:80px">Cliquez sur Résoudre…</pre>
    </div>
    <div class="card">
      <h3>📊 Graphique Optimisation</h3>
      <img id="img-lp" class="chart" src="/chart/simplex" alt="Simplexe">
    </div>
  </div>
</div>

<!-- ═══ TAB 3 : IoT ═══ -->
<div class="tab-content" id="tab-iot">
  <div style="margin-bottom:10px">
    <button class="btn btn-blue"   onclick="refreshIoT()">🔄 Rafraîchir</button>
    <button class="btn btn-yellow" onclick="showAlerts()">🚨 Alertes</button>
  </div>
  <div class="grid-2">
    <div class="card">
      <h3>📋 État de toutes les Bennes</h3>
      <div class="scrollbox" style="max-height:380px">
        <table id="all-bins-table">
          <thead><tr><th>ID</th><th>Type</th><th>Niveau</th><th>Remplissage</th><th>Statut</th><th>Zone</th></tr></thead>
          <tbody id="all-bins-body"><tr><td colspan="6" class="loading">Chargement…</td></tr></tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <h3>📡 Dashboard IoT</h3>
      <img id="img-iot" class="chart" src="/chart/iot" alt="IoT Dashboard">
    </div>
  </div>
</div>

<!-- ═══ TAB 4 : Routes ═══ -->
<div class="tab-content" id="tab-routes">
  <div style="margin-bottom:10px">
    <button class="btn btn-green"  onclick="computeRoutes('two_opt')">🚛 2-Opt</button>
    <button class="btn btn-blue"   onclick="computeRoutes('nearest_neighbor')">🚛 Nearest Neighbor</button>
    <button class="btn btn-purple" onclick="loadRoutesDashboard()">📊 Dashboard Flotte</button>
  </div>
  <div id="routes-summary" class="card" style="margin-bottom:12px; color:var(--yellow)">
    Cliquez sur 'Calculer Tournées' pour lancer l'optimisation des routes.
  </div>
  <div class="card">
    <h3>🗺️ Carte des Tournées</h3>
    <img id="img-routes" class="chart" src="/chart/routes" alt="Routes">
  </div>
</div>

<!-- ═══ TAB 5 : Rapport ═══ -->
<div class="tab-content" id="tab-rapport">
  <div style="margin-bottom:10px">
    <button class="btn btn-green"  onclick="generateReport()">📝 Générer Rapport</button>
    <button class="btn btn-blue"   onclick="exportJSON()">💾 Export JSON IoT</button>
  </div>
  <pre id="rapport-content" style="min-height:400px; max-height:600px; overflow-y:auto">
Cliquez sur 'Générer Rapport'…
  </pre>
</div>

<footer>EMSI 2025/2026 — Système d'Optimisation Gestion des Déchets — Étape 5</footer>

<script>
// ── Navigation ────────────────────────────────────────────
function showTab(id) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  event.target.classList.add('active');
  if (id === 'iot') loadIoT();
  if (id === 'routes') loadRouteMap();
}

// ── KPIs & Bennes ─────────────────────────────────────────
async function loadOverview() {
  const r = await fetch('/api/stats');
  const d = await r.json();
  document.getElementById('k-bins').innerText    = d.n_bins;
  document.getElementById('k-fill').innerText    = d.fill_avg + '%';
  document.getElementById('k-urgent').innerText  = d.urgent_count;
  document.getElementById('k-weight').innerText  = Math.round(d.total_weight_kg);
  document.getElementById('k-zone').innerText    = d.hotspot_zone;

  const r2 = await fetch('/api/bins?limit=8');
  const bins = await r2.json();
  let rows = '';
  bins.forEach(b => {
    const pct = b.fill_level.toFixed(1);
    rows += `<tr>
      <td>${b.bin_id}</td>
      <td>${b.waste_type}</td>
      <td>${pct}%</td>
      <td><span class="badge ${b.status}">${b.status}</span></td>
      <td>${b.zone}</td>
    </tr>`;
  });
  document.getElementById('top-bins-body').innerHTML = rows;
}

// ── IoT ───────────────────────────────────────────────────
async function loadIoT() {
  const r = await fetch('/api/bins');
  const bins = await r.json();
  const sorted = bins.sort((a,b) => b.fill_level - a.fill_level);
  let rows = '';
  sorted.forEach(b => {
    const pct   = b.fill_level.toFixed(1);
    const width = Math.round(b.fill_level);
    const cls   = b.fill_level >= 80 ? 'crit' : b.fill_level >= 60 ? 'warn' : '';
    rows += `<tr>
      <td>${b.bin_id}</td>
      <td>${b.waste_type}</td>
      <td>${pct}%</td>
      <td style="width:120px"><div class="bar-fill ${cls}" style="width:${width}%"></div></td>
      <td><span class="badge ${b.status}">${b.status}</span></td>
      <td>${b.zone}</td>
    </tr>`;
  });
  document.getElementById('all-bins-body').innerHTML = rows;
  document.getElementById('img-iot').src = '/chart/iot?t='+Date.now();
}

function refreshIoT() { loadIoT(); }

async function showAlerts() {
  const r = await fetch('/api/alerts');
  const d = await r.json();
  alert(`🚨 Alertes actives : ${d.total}\\n\\n🔴 CRITICAL: ${d.critical}\\n🟠 URGENT: ${d.urgent}\\n🟡 WARNING: ${d.warning}`);
}

// ── LP ────────────────────────────────────────────────────
async function solveCh1() {
  const f=document.getElementById('fuel').value;
  const fl=document.getElementById('fleet').value;
  const b=document.getElementById('budget').value;
  const r = await fetch(`/api/solve/ch1?fuel=${f}&fleet=${fl}&budget=${b}`);
  const d = await r.json();
  const i = d.integer;
  document.getElementById('lp-result').innerText =
    `CHAPITRE 1 — Méthode Graphique\\nx₁=${i.x1}  x₂=${i.x2}\\nZ = ${i.Z} t/jour\\n\\nSaturation:\\n` +
    Object.entries(d.saturation_pct).map(([k,v])=>`  ${k}: ${v}%`).join('\\n');
  document.getElementById('img-lp').src = '/chart/ch1?t='+Date.now();
}

async function solveCh2() {
  const f=document.getElementById('fuel').value;
  const fl=document.getElementById('fleet').value;
  const b=document.getElementById('budget').value;
  const r = await fetch(`/api/solve/ch2?fuel=${f}&fleet=${fl}&budget=${b}`);
  const d = await r.json();
  const i = d.integer;
  const sat = i.saturation;
  document.getElementById('lp-result').innerText =
    `CHAPITRE 2 — Simplexe (${d.n_iterations} itérations)\\n` +
    `x₁=${i.x1}  x₂=${i.x2}  x₃=${i.x3}\\nZ = ${i.Z} t/jour\\n\\nSaturation:\\n` +
    `  C1: ${sat.C1}%\\n  C2: ${sat.C2}%\\n  C3: ${sat.C3}%`;
  document.getElementById('img-lp').src = '/chart/simplex?t='+Date.now();
}

// ── Routes ────────────────────────────────────────────────
async function computeRoutes(method='two_opt') {
  document.getElementById('routes-summary').innerText = '⏳ Calcul en cours…';
  const r = await fetch('/api/routes?method='+method);
  const d = await r.json();
  const s = d.summary;
  document.getElementById('routes-summary').innerHTML =
    `✅ <b>${s.total_trucks}</b> camions &nbsp;|&nbsp; `+
    `<b>${s.total_bins}</b> bennes &nbsp;|&nbsp; `+
    `<b>${s.total_distance.toFixed(2)} km</b> &nbsp;|&nbsp; `+
    `<b>${s.total_weight_kg.toFixed(0)} kg</b> &nbsp;|&nbsp; `+
    `<b>${s.total_fuel_L.toFixed(1)} L</b>`;
  document.getElementById('img-routes').src = '/chart/routes?t='+Date.now();
}

function loadRouteMap() {
  document.getElementById('img-routes').src = '/chart/routes?t='+Date.now();
}

async function loadRoutesDashboard() {
  document.getElementById('img-routes').src = '/chart/routes_dashboard?t='+Date.now();
}

// ── Rapport ───────────────────────────────────────────────
async function generateReport() {
  const r = await fetch('/api/report');
  const d = await r.json();
  document.getElementById('rapport-content').innerText = d.content;
}

async function exportJSON() {
  window.open('/api/export/json', '_blank');
}

// ── Init ──────────────────────────────────────────────────
loadOverview();
</script>
</body>
</html>"""


# ════════════════════════════════════════════════════════════
#  Routes Flask
# ════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/stats")
def api_stats():
    return jsonify(get_manager().get_statistics())

@app.route("/api/bins")
def api_bins():
    from flask import request
    limit = int(request.args.get("limit", 999))
    all_bins = sorted(get_manager().get_all_bins(),
                      key=lambda x: -x["fill_level"])[:limit]
    for b in all_bins:
        b["bin_id"] = b["bin_id"].split("_")[1]+"_"+b["bin_id"].split("_")[2]
    return jsonify(all_bins)

@app.route("/api/alerts")
def api_alerts():
    from modules.iot_analytics import AlertSystem
    a = AlertSystem()
    a.check_and_generate(get_manager().get_all_bins())
    return jsonify(a.summary)

@app.route("/api/solve/ch1")
def api_solve_ch1():
    from flask import request
    from modules.linear_prog import solve_chapter1
    fuel   = int(request.args.get("fuel",   48))
    fleet  = int(request.args.get("fleet",  40))
    budget = int(request.args.get("budget", 72))
    return jsonify(solve_chapter1(fuel, fleet, budget))

@app.route("/api/solve/ch2")
def api_solve_ch2():
    from flask import request
    from modules.simplex import simplex_chapter2
    fuel   = int(request.args.get("fuel",   48))
    fleet  = int(request.args.get("fleet",  40))
    budget = int(request.args.get("budget", 72))
    return jsonify(simplex_chapter2(fuel, fleet, budget))

@app.route("/api/routes")
def api_routes():
    from flask import request
    from modules.route_optimizer import FleetPlanner
    global plan
    method = request.args.get("method", "two_opt")
    sol    = simplex_chapter2()["integer"]
    plan   = FleetPlanner(sol, get_manager()).plan(method=method)
    # Convertir pour JSON
    result = {
        "summary": plan["summary"],
        "method":  plan["method"],
        "trucks": {
            wtype: [{"truck_id": t["truck_id"], "n_bins": t["n_bins"],
                     "distance_km": t["distance_km"], "weight_kg": t["weight_kg"],
                     "fuel_L": t["fuel_L"], "load_pct": t.get("load_pct",0)}
                    for t in trucks]
            for wtype, trucks in plan["trucks"].items()
        }
    }
    return jsonify(result)

@app.route("/api/report")
def api_report():
    from modules.linear_prog import rapport_chapter1
    from modules.simplex import rapport_chapter2
    stats  = get_manager().get_statistics()
    urgent, _, _ = get_manager().prioritize_bins()
    content = (
        rapport_chapter1() + "\n\n" + rapport_chapter2() +
        f"\n\n{'═'*58}\n  RÉSEAU IOT\n{'═'*58}\n"
        f"  Capteurs    : {stats['n_bins']}\n"
        f"  Remplissage : {stats['fill_avg']:.1f}%\n"
        f"  Urgents     : {stats['urgent_count']}\n"
        f"  Poids total : {stats['total_weight_kg']:.0f} kg\n"
        f"  Généré le   : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    )
    return jsonify({"content": content})

@app.route("/api/export/json")
def api_export_json():
    path, _ = get_manager().export_json()
    return send_file(path, as_attachment=True,
                     download_name="iot_report.json")


# ── Génération des graphiques ─────────────────────────────
def _fig_to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130,
                bbox_inches="tight", facecolor="#1E293B")
    buf.seek(0)
    plt.close(fig)
    return send_file(buf, mimetype="image/png")

@app.route("/chart/dashboard")
def chart_dashboard():
    from modules.visualisation import plot_dashboard_etape2
    return _fig_to_png(plot_dashboard_etape2())

@app.route("/chart/simplex")
def chart_simplex():
    from modules.simplex import plot_simplex_iterations
    return _fig_to_png(plot_simplex_iterations())

@app.route("/chart/ch1")
def chart_ch1():
    from modules.linear_prog import plot_graphical_method
    return _fig_to_png(plot_graphical_method())

@app.route("/chart/iot")
def chart_iot():
    from modules.iot_visualisation import plot_iot_dashboard
    return _fig_to_png(plot_iot_dashboard(get_manager()))

@app.route("/chart/routes")
def chart_routes():
    from modules.route_visualisation import plot_routes_map
    p = get_plan()
    return _fig_to_png(plot_routes_map(p))

@app.route("/chart/routes_dashboard")
def chart_routes_dashboard():
    from modules.route_visualisation import plot_fleet_dashboard
    p = get_plan()
    return _fig_to_png(plot_fleet_dashboard(p))


def run_web(host="127.0.0.1", port=5000, debug=False):
    print(f"\n  🌐  Dashboard Web disponible sur : http://{host}:{port}")
    print(f"  Ctrl+C pour arrêter\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web()
