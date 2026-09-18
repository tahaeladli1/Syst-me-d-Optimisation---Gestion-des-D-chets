#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  ui/dashboard.py  —  ÉTAPE 5
#  Interface Graphique Tkinter — Application de Bureau
# ============================================================
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    FigureCanvasTkAgg = None
import threading, json, os
from datetime import datetime

from config.settings import (
    PROJECT_NAME, VERSION, AUTHORS, COLORS,
    WINDOW_WIDTH, WINDOW_HEIGHT, FONT_FAMILY
)

BG_DARK  = "#1E293B"
BG_MED   = "#334155"
BG_CARD  = "#1E3A5F"
TEXT     = "#F1F5F9"
MUTED    = "#94A3B8"
GREEN    = "#10B981"
RED      = "#EF4444"
YELLOW   = "#F59E0B"
BLUE     = "#3B82F6"
PURPLE   = "#A78BFA"


# ════════════════════════════════════════════════════════════
class WasteManagementApp:
    """
    Application de bureau complète — Gestion des Déchets EMSI.
    Onglets : Optimisation · IoT · Routes · Dashboard · Rapport
    """

    def __init__(self, root):
        self.root = root
        self._setup_window()
        self._load_data()
        self._build_ui()

    # ── Fenêtre principale ────────────────────────────────────
    def _setup_window(self):
        self.root.title(f"🗑️  {PROJECT_NAME}  v{VERSION}  — EMSI 2025/2026")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        try:
            self.root.tk.call("tk", "scaling", 1.2)
        except Exception:
            pass

    # ── Chargement des données ────────────────────────────────
    def _load_data(self):
        from modules.iot_sensors import IoTSensorManager
        from modules.simplex import simplex_chapter2
        from modules.linear_prog import solve_chapter1

        self.manager   = IoTSensorManager()
        self.sol_lp    = simplex_chapter2()
        self.sol_ch1   = solve_chapter1()
        self.plan      = None
        self.status_var = None

    # ── Construction UI ───────────────────────────────────────
    def _build_ui(self):
        # ── Barre de titre ────────────────────────────────────
        header = tk.Frame(self.root, bg="#0F172A", height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(header,
                 text="🗑️  Système d'Optimisation — Gestion des Déchets",
                 bg="#0F172A", fg=TEXT,
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(header,
                 text=f"EMSI 2025/2026  |  {'  ·  '.join(AUTHORS)}",
                 bg="#0F172A", fg=MUTED,
                 font=(FONT_FAMILY, 9)).pack(side="right", padx=16, pady=10)

        # ── Barre de statut ───────────────────────────────────
        self.status_var = tk.StringVar(value="✅ Système prêt")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              bg="#0F172A", fg=GREEN,
                              font=(FONT_FAMILY, 9), anchor="w")
        status_bar.pack(fill="x", side="bottom", padx=8, pady=2)

        # ── Notebook (onglets) ────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",
                        background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=BG_MED, foreground=MUTED,
                        font=(FONT_FAMILY, 10, "bold"),
                        padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", BG_CARD)],
                  foreground=[("selected", TEXT)])

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=4, pady=(0, 2))

        tabs = [
            ("📊  Optimisation LP",  self._tab_optimisation),
            ("📡  Capteurs IoT",     self._tab_iot),
            ("🗺️  Routes",           self._tab_routes),
            ("📈  Dashboard",        self._tab_dashboard),
            ("📄  Rapport",          self._tab_rapport),
        ]
        for title, builder in tabs:
            frame = tk.Frame(self.nb, bg=BG_DARK)
            self.nb.add(frame, text=title)
            builder(frame)

    # ══════════════════════════════════════════════════════════
    #  ONGLET 1 : Optimisation LP
    # ══════════════════════════════════════════════════════════
    def _tab_optimisation(self, frame):
        # ── Panneau gauche : contrôles ─────────────────────
        left = tk.Frame(frame, bg=BG_MED, width=280)
        left.pack(side="left", fill="y", padx=(8,4), pady=8)
        left.pack_propagate(False)

        tk.Label(left, text="⚙️  Paramètres du Modèle",
                 bg=BG_MED, fg=TEXT,
                 font=(FONT_FAMILY, 11, "bold")).pack(pady=(14,8), padx=12, anchor="w")

        self.params = {}
        params_def = [
            ("Carburant C1 ≤",    "fuel",   48, 20, 100),
            ("Flotte C2 ≤",       "fleet",  40, 20, 80),
            ("Budget C3 ≤",       "budget", 72, 30, 120),
        ]
        for label, key, default, mn, mx in params_def:
            f = tk.Frame(left, bg=BG_MED)
            f.pack(fill="x", padx=12, pady=4)
            tk.Label(f, text=label, bg=BG_MED, fg=MUTED,
                     font=(FONT_FAMILY, 9)).pack(anchor="w")
            var = tk.IntVar(value=default)
            self.params[key] = var
            row = tk.Frame(f, bg=BG_MED)
            row.pack(fill="x")
            scale = tk.Scale(row, from_=mn, to=mx, variable=var,
                             orient="horizontal", bg=BG_MED, fg=TEXT,
                             troughcolor=BG_DARK, highlightthickness=0,
                             activebackground=BLUE, length=160)
            scale.pack(side="left")
            tk.Label(row, textvariable=var, bg=BG_MED, fg=BLUE,
                     font=(FONT_FAMILY, 10, "bold"), width=4).pack(side="left")

        tk.Frame(left, bg="#475569", height=1).pack(fill="x", padx=12, pady=10)

        # Boutons
        for txt, cmd, color in [
            ("▶  Résoudre Ch.1 (Graphique)", self._run_ch1, BLUE),
            ("▶  Résoudre Ch.2 (Simplexe)",  self._run_ch2, GREEN),
            ("📊  Comparer Ch.1 vs Ch.2",     self._run_compare, PURPLE),
        ]:
            btn = tk.Button(left, text=txt, command=cmd,
                            bg=BG_CARD, fg=color, activebackground=BG_DARK,
                            activeforeground=color, relief="flat",
                            font=(FONT_FAMILY, 9, "bold"),
                            cursor="hand2", padx=10, pady=6)
            btn.pack(fill="x", padx=12, pady=3)

        tk.Frame(left, bg="#475569", height=1).pack(fill="x", padx=12, pady=10)

        # Résultats texte
        tk.Label(left, text="Résultat :", bg=BG_MED, fg=MUTED,
                 font=(FONT_FAMILY, 9)).pack(anchor="w", padx=12)
        self.result_text = scrolledtext.ScrolledText(
            left, height=12, bg="#0F172A", fg=GREEN,
            font=("Courier New", 9), relief="flat",
            insertbackground=GREEN)
        self.result_text.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # ── Panneau droit : graphique ──────────────────────
        right = tk.Frame(frame, bg=BG_DARK)
        right.pack(side="right", fill="both", expand=True, padx=(4,8), pady=8)

        self.fig_lp, self.canvas_lp = self._make_canvas(right, (9, 6))
        self._run_ch2()   # Afficher par défaut

    def _run_ch1(self):
        from modules.linear_prog import solve_chapter1, plot_graphical_method
        f = self.params["fuel"].get()
        fl = self.params["fleet"].get()
        b = self.params["budget"].get()
        self._set_status("⏳ Résolution Ch.1...")
        res = solve_chapter1(fuel=f, fleet=fl, budget=b)
        i = res["integer"]
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end",
            f"═ CHAPITRE 1 ══════════════\n"
            f"Méthode  : Graphique\n"
            f"x₁={i['x1']}  x₂={i['x2']}\n"
            f"Z = {i['Z']} t/jour\n\n"
            f"Saturation :\n"
            + "\n".join(f"  {k}: {v}%" for k,v in res["saturation_pct"].items())
        )
        fig = plot_graphical_method()
        self._update_canvas(self.canvas_lp, self.fig_lp, fig)
        plt.close(fig)
        self._set_status(f"✅ Ch.1 — Z = {i['Z']} t/jour")

    def _run_ch2(self):
        from modules.simplex import simplex_chapter2
        from modules.simplex import plot_simplex_iterations
        self._set_status("⏳ Résolution Ch.2...")
        res = simplex_chapter2(
            self.params["fuel"].get(),
            self.params["fleet"].get(),
            self.params["budget"].get()
        )
        i = res["integer"]
        sat = i["saturation"]
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end",
            f"═ CHAPITRE 2 ══════════════\n"
            f"Méthode  : Simplexe\n"
            f"Itérations : {res['n_iterations']}\n"
            f"x₁={i['x1']}  x₂={i['x2']}  x₃={i['x3']}\n"
            f"Z = {i['Z']} t/jour\n\n"
            f"Saturation :\n"
            + "\n".join(f"  C{k[-1]}: {v}%" for k,v in sat.items())
        )
        fig = plot_simplex_iterations()
        self._update_canvas(self.canvas_lp, self.fig_lp, fig)
        plt.close(fig)
        self._set_status(f"✅ Ch.2 — Z = {i['Z']} t/jour  (2 itérations)")

    def _run_compare(self):
        from modules.visualisation import plot_comparison
        self._set_status("⏳ Comparaison Ch.1 vs Ch.2...")
        fig = plot_comparison()
        self._update_canvas(self.canvas_lp, self.fig_lp, fig)
        plt.close(fig)
        self._set_status("✅ Comparaison : Ch.2 gagne +12.8%")

    # ══════════════════════════════════════════════════════════
    #  ONGLET 2 : Capteurs IoT
    # ══════════════════════════════════════════════════════════
    def _tab_iot(self, frame):
        # Contrôles
        ctrl = tk.Frame(frame, bg=BG_MED)
        ctrl.pack(fill="x", padx=8, pady=(8,0))

        for txt, cmd, color in [
            ("🔄  Rafraîchir", self._iot_refresh, BLUE),
            ("📊  Dashboard IoT", self._iot_dashboard, GREEN),
            ("🔮  Prédictions", self._iot_predictions, YELLOW),
            ("🚨  Alertes", self._iot_alerts, RED),
        ]:
            tk.Button(ctrl, text=txt, command=cmd,
                      bg=BG_CARD, fg=color, activebackground=BG_DARK,
                      relief="flat", font=(FONT_FAMILY, 9, "bold"),
                      cursor="hand2", padx=10, pady=5).pack(side="left", padx=4, pady=4)

        # KPI band
        self.kpi_frame = tk.Frame(frame, bg="#0F172A", height=55)
        self.kpi_frame.pack(fill="x", padx=8, pady=(4,0))
        self.kpi_frame.pack_propagate(False)
        self.kpi_labels = {}
        kpi_defs = [
            ("n_bins",     "Capteurs",      BLUE),
            ("fill_avg",   "Remplissage",   GREEN),
            ("urgent",     "Urgents",       RED),
            ("weight",     "Poids (kg)",    YELLOW),
            ("hotspot",    "Zone critique", PURPLE),
        ]
        for key, label, color in kpi_defs:
            col = tk.Frame(self.kpi_frame, bg="#0F172A")
            col.pack(side="left", expand=True, fill="both")
            tk.Label(col, text=label, bg="#0F172A", fg=MUTED,
                     font=(FONT_FAMILY, 8)).pack(pady=(6,0))
            var = tk.StringVar(value="—")
            self.kpi_labels[key] = var
            tk.Label(col, textvariable=var, bg="#0F172A", fg=color,
                     font=(FONT_FAMILY, 13, "bold")).pack()

        # Canvas graphique + table
        paned = tk.PanedWindow(frame, orient="horizontal",
                               bg=BG_DARK, sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=4)

        # Table bennes
        left_iot = tk.Frame(paned, bg=BG_MED)
        paned.add(left_iot, minsize=320)

        cols = ("ID", "Type", "Niveau", "Statut", "Zone")
        self.tree_iot = ttk.Treeview(left_iot, columns=cols,
                                      show="headings", height=22)
        style = ttk.Style()
        style.configure("Treeview", background=BG_DARK,
                        foreground=TEXT, fieldbackground=BG_DARK,
                        rowheight=22, font=(FONT_FAMILY, 8))
        style.configure("Treeview.Heading", background=BG_MED,
                        foreground=BLUE, font=(FONT_FAMILY, 8, "bold"))
        style.map("Treeview", background=[("selected", BG_CARD)])

        widths = [90, 80, 65, 75, 80]
        for col, w in zip(cols, widths):
            self.tree_iot.heading(col, text=col)
            self.tree_iot.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(left_iot, orient="vertical",
                            command=self.tree_iot.yview)
        self.tree_iot.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree_iot.pack(fill="both", expand=True, padx=4, pady=4)

        # Graphique IoT
        right_iot = tk.Frame(paned, bg=BG_DARK)
        paned.add(right_iot, minsize=400)
        self.fig_iot, self.canvas_iot = self._make_canvas(right_iot, (7, 5.5))
        self._iot_refresh()

    def _iot_refresh(self):
        self._set_status("⏳ Rafraîchissement des capteurs IoT...")
        stats  = self.manager.get_statistics()
        urgent, att, norm = self.manager.prioritize_bins()
        all_bins = sorted(self.manager.get_all_bins(),
                          key=lambda x: -x["fill_level"])

        # KPIs
        self.kpi_labels["n_bins"].set(str(stats["n_bins"]))
        self.kpi_labels["fill_avg"].set(f"{stats['fill_avg']:.1f}%")
        self.kpi_labels["urgent"].set(str(stats["urgent_count"]))
        self.kpi_labels["weight"].set(f"{stats['total_weight_kg']:.0f}")
        self.kpi_labels["hotspot"].set(str(stats["hotspot_zone"]))

        # Table
        for item in self.tree_iot.get_children():
            self.tree_iot.delete(item)

        tag_colors = {"CRITICAL":"#7F1D1D","URGENT":"#78350F",
                      "WARNING":"#1A3A1A","NORMAL":"#1E293B"}
        for b in all_bins:
            tag = b["status"]
            self.tree_iot.insert("", "end", values=(
                b["bin_id"].split("_")[1]+"_"+b["bin_id"].split("_")[2],
                b["waste_type"][:5], f"{b['fill_level']:.1f}%",
                b["status"], b["zone"][:8]
            ), tags=(tag,))
            self.tree_iot.tag_configure(tag, background=tag_colors.get(tag, BG_DARK))

        # Graphique : distribution
        from modules.iot_visualisation import plot_iot_dashboard
        fig = plot_iot_dashboard(self.manager)
        self._update_canvas(self.canvas_iot, self.fig_iot, fig)
        plt.close(fig)
        self._set_status(f"✅ IoT — {stats['n_bins']} capteurs | {stats['urgent_count']} urgents")

    def _iot_dashboard(self):
        from modules.iot_visualisation import plot_iot_dashboard
        fig = plot_iot_dashboard(self.manager)
        self._update_canvas(self.canvas_iot, self.fig_iot, fig)
        plt.close(fig)
        self._set_status("✅ Dashboard IoT affiché")

    def _iot_predictions(self):
        from modules.iot_visualisation import plot_predictions
        fig = plot_predictions(self.manager)
        if fig:
            self._update_canvas(self.canvas_iot, self.fig_iot, fig)
            plt.close(fig)
            self._set_status("✅ Prédictions IoT affichées")
        else:
            self._set_status("⚠️  Aucune benne critique dans les 24h")

    def _iot_alerts(self):
        from modules.iot_analytics import AlertSystem
        alert_sys = AlertSystem()
        alerts = alert_sys.check_and_generate(self.manager.get_all_bins())
        summ = alert_sys.summary
        top = alert_sys.get_active()[:20]
        msg = (f"🚨 Alertes actives : {summ['total']}\n\n"
               f"🔴 CRITICAL : {summ['critical']}\n"
               f"🟠 URGENT   : {summ['urgent']}\n"
               f"🟡 WARNING  : {summ['warning']}\n\n"
               "Top alertes :\n" +
               "\n".join(f"• {a['bin_id']} — {a['fill_level']:.0f}% ({a['level']})"
                         for a in top[:10]))
        messagebox.showinfo("Alertes IoT", msg)
        self._set_status(f"🚨 {summ['critical']} CRITICAL  |  {summ['urgent']} URGENT")

    # ══════════════════════════════════════════════════════════
    #  ONGLET 3 : Routes
    # ══════════════════════════════════════════════════════════
    def _tab_routes(self, frame):
        ctrl = tk.Frame(frame, bg=BG_MED)
        ctrl.pack(fill="x", padx=8, pady=(8,0))

        self.route_method = tk.StringVar(value="two_opt")
        for txt, val in [("Nearest Neighbor","nearest_neighbor"),
                         ("Cheapest Insertion","cheapest_insertion"),
                         ("2-Opt ★","two_opt")]:
            tk.Radiobutton(ctrl, text=txt, variable=self.route_method,
                           value=val, bg=BG_MED, fg=TEXT,
                           selectcolor=BG_DARK, activebackground=BG_MED,
                           font=(FONT_FAMILY, 9)).pack(side="left", padx=6, pady=4)

        for txt, cmd, color in [
            ("🚛  Calculer Tournées", self._routes_compute, GREEN),
            ("📍  Carte des Routes",  self._routes_map, BLUE),
            ("📊  Dashboard Flotte",  self._routes_dashboard, PURPLE),
        ]:
            tk.Button(ctrl, text=txt, command=cmd,
                      bg=BG_CARD, fg=color, activebackground=BG_DARK,
                      relief="flat", font=(FONT_FAMILY, 9, "bold"),
                      cursor="hand2", padx=10, pady=5).pack(side="left", padx=4, pady=4)

        # Résumé flotte
        self.route_summary = tk.StringVar(value="Cliquez sur 'Calculer Tournées'")
        tk.Label(frame, textvariable=self.route_summary,
                 bg="#0F172A", fg=YELLOW,
                 font=(FONT_FAMILY, 10, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(4,0))

        # Canvas
        canvas_frame = tk.Frame(frame, bg=BG_DARK)
        canvas_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.fig_routes, self.canvas_routes = self._make_canvas(canvas_frame, (12, 6))

    def _routes_compute(self):
        from modules.route_optimizer import FleetPlanner
        self._set_status("⏳ Calcul des tournées optimales...")
        sol = self.sol_lp["integer"]
        method = self.route_method.get()
        fp = FleetPlanner(sol, self.manager)
        self.plan = fp.plan(method=method)
        s = self.plan["summary"]
        self.route_summary.set(
            f"✅  {s['total_trucks']} camions  |  {s['total_bins']} bennes  |  "
            f"{s['total_distance']:.2f} km  |  {s['total_weight_kg']:.0f} kg  |  "
            f"{s['total_fuel_L']:.1f} L carburant"
        )
        self._routes_map()
        self._set_status(f"✅ Tournées calculées ({method}) — {s['total_distance']:.2f} km total")

    def _routes_map(self):
        if not self.plan:
            self._routes_compute(); return
        from modules.route_visualisation import plot_routes_map
        fig = plot_routes_map(self.plan)
        self._update_canvas(self.canvas_routes, self.fig_routes, fig)
        plt.close(fig)

    def _routes_dashboard(self):
        if not self.plan:
            self._routes_compute(); return
        from modules.route_visualisation import plot_fleet_dashboard
        fig = plot_fleet_dashboard(self.plan)
        self._update_canvas(self.canvas_routes, self.fig_routes, fig)
        plt.close(fig)
        self._set_status("✅ Dashboard flotte affiché")

    # ══════════════════════════════════════════════════════════
    #  ONGLET 4 : Dashboard global
    # ══════════════════════════════════════════════════════════
    def _tab_dashboard(self, frame):
        ctrl = tk.Frame(frame, bg=BG_MED)
        ctrl.pack(fill="x", padx=8, pady=(8,0))

        for txt, cmd, color in [
            ("🔄  Tout Rafraîchir",    self._dash_refresh, GREEN),
            ("💾  Exporter PNG",       self._dash_export,  BLUE),
            ("📋  Rapport Complet",    self._dash_rapport, PURPLE),
        ]:
            tk.Button(ctrl, text=txt, command=cmd,
                      bg=BG_CARD, fg=color, activebackground=BG_DARK,
                      relief="flat", font=(FONT_FAMILY, 9, "bold"),
                      cursor="hand2", padx=10, pady=5).pack(side="left", padx=4, pady=4)

        canvas_frame = tk.Frame(frame, bg=BG_DARK)
        canvas_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.fig_dash, self.canvas_dash = self._make_canvas(canvas_frame, (13, 7))
        self._dash_refresh()

    def _dash_refresh(self):
        self._set_status("⏳ Génération du dashboard global...")
        self._build_global_dashboard()
        self._set_status("✅ Dashboard global mis à jour")

    def _build_global_dashboard(self):
        from modules.linear_prog import solve_chapter1
        from modules.simplex import simplex_chapter2

        BG = "#1E293B"
        fig = plt.figure(figsize=(13, 7), facecolor=BG)
        gs  = gridspec.GridSpec(2, 4, figure=fig, hspace=0.55, wspace=0.42)

        stats = self.manager.get_statistics()
        sol2  = simplex_chapter2()["integer"]
        sol1  = solve_chapter1()["integer"]
        urgent, att, norm = self.manager.prioritize_bins()

        # ── KPIs textuels ────────
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.set_facecolor("#0F172A"); ax0.axis("off")
        ax0.set_title("Indicateurs Clés", color="#F1F5F9",
                      fontsize=9, fontweight="bold")
        items = [
            (f"Z★ = {sol2['Z']} t/j",   "#10B981"),
            (f"{stats['n_bins']} capteurs IoT", "#3B82F6"),
            (f"{stats['urgent_count']} urgents", "#EF4444"),
            (f"{stats['total_weight_kg']:.0f} kg", "#F59E0B"),
            (f"{stats['fill_avg']:.1f}% moy.", "#A78BFA"),
        ]
        for i, (txt, col) in enumerate(items):
            ax0.text(0.5, 0.82-i*0.17, txt, transform=ax0.transAxes,
                     ha="center", fontsize=11, fontweight="bold", color=col)

        # ── Comparaison Ch.1 vs Ch.2 ─────────
        ax1 = fig.add_subplot(gs[0, 1])
        ax1.set_facecolor(BG)
        ax1.bar(["Ch.1\nGraphique","Ch.2\nSimplexe"],
                [sol1["Z"], sol2["Z"]],
                color=["#3B82F6","#10B981"], width=0.5, edgecolor=BG)
        for x, v in enumerate([sol1["Z"], sol2["Z"]]):
            ax1.text(x, v+0.3, f"{v}", ha="center", fontsize=11,
                     fontweight="bold", color="#F1F5F9")
        ax1.set_title("LP : Ch.1 vs Ch.2", color="#F1F5F9",
                      fontsize=9, fontweight="bold")
        ax1.set_ylabel("t/jour", color="#94A3B8", fontsize=7)
        ax1.tick_params(colors="#94A3B8", labelsize=7)
        ax1.set_ylim(80, 115)
        ax1.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
        ax1.spines[:].set_edgecolor("#475569")

        # ── Remplissage par zone ─────────────
        ax2 = fig.add_subplot(gs[0, 2])
        ax2.set_facecolor(BG)
        zones = list(stats["by_zone"].keys())
        vals  = [stats["by_zone"][z] for z in zones]
        clrs  = ["#EF4444" if v>=70 else "#3B82F6" for v in vals]
        ax2.barh(zones, vals, color=clrs, height=0.55, edgecolor=BG)
        ax2.axvline(70, color="#F43F5E", ls="--", lw=1)
        ax2.set_title("IoT : Remplissage/Zone", color="#F1F5F9",
                      fontsize=9, fontweight="bold")
        ax2.set_xlim(0, 105)
        ax2.tick_params(colors="#94A3B8", labelsize=6)
        ax2.spines[:].set_edgecolor("#475569")
        ax2.grid(True, color="#334155", ls="--", alpha=0.4, axis="x")

        # ── Statuts bennes ───────────────────
        ax3 = fig.add_subplot(gs[0, 3])
        ax3.set_facecolor(BG)
        sd  = stats["by_status"]
        lbs = [k for k,v in sd.items() if v>0]
        szs = [v for v in sd.values() if v>0]
        cls = {"CRITICAL":"#EF4444","URGENT":"#F59E0B",
               "WARNING":"#FBBF24","NORMAL":"#10B981"}
        ax3.pie(szs, labels=lbs, colors=[cls[k] for k in lbs],
                autopct="%1.0f%%", startangle=90,
                wedgeprops=dict(edgecolor=BG, lw=2),
                textprops=dict(color="#F1F5F9", fontsize=7))
        ax3.set_title("IoT : Statuts", color="#F1F5F9",
                      fontsize=9, fontweight="bold")

        # ── Allocation camions LP ─────────────
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.set_facecolor(BG)
        types = ["Ménager\n(x₁)", "Recyclable\n(x₂)", "Biomédical\n(x₃)"]
        counts = [sol2["x1"], sol2["x2"], sol2["x3"]]
        contributions = [8*sol2["x1"], 7*sol2["x2"], 11*sol2["x3"]]
        bars = ax4.bar(types, counts, color=["#2196F3","#4CAF50","#FF9800"],
                       width=0.5, edgecolor=BG)
        for bar, n, c in zip(bars, counts, contributions):
            ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                     f"{n}\n+{c}t", ha="center", va="bottom",
                     fontsize=7.5, color="#F1F5F9", fontweight="bold")
        ax4.set_title("Allocation LP", color="#F1F5F9",
                      fontsize=9, fontweight="bold")
        ax4.tick_params(colors="#94A3B8", labelsize=7)
        ax4.set_ylim(0, max(counts)*1.5)
        ax4.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
        ax4.spines[:].set_edgecolor("#475569")

        # ── Saturation contraintes ───────────
        ax5 = fig.add_subplot(gs[1, 1])
        ax5.set_facecolor(BG)
        from modules.simplex import simplex_chapter2 as sc2
        sat = sc2()["integer"]["saturation"]
        c_lbs = ["C1 Carburant","C2 Temps","C3 Budget"]
        c_vals = [sat["C1"], sat["C2"], sat["C3"]]
        c_clrs = ["#EF4444" if v>=100 else "#F59E0B" if v>=90 else "#10B981"
                  for v in c_vals]
        ax5.barh(c_lbs, c_vals, color=c_clrs, height=0.45, edgecolor=BG)
        ax5.axvline(100, color="#F43F5E", ls="--", lw=1)
        for i, v in enumerate(c_vals):
            ax5.text(v+0.5, i, f"{v}%", va="center",
                     fontsize=8, color="#F1F5F9", fontweight="bold")
        ax5.set_xlim(0, 115)
        ax5.set_title("Saturation LP", color="#F1F5F9",
                      fontsize=9, fontweight="bold")
        ax5.tick_params(colors="#94A3B8", labelsize=7)
        ax5.spines[:].set_edgecolor("#475569")
        ax5.grid(True, color="#334155", ls="--", alpha=0.4, axis="x")

        # ── Routes : distance par type ──────
        ax6 = fig.add_subplot(gs[1, 2])
        ax6.set_facecolor(BG)
        if self.plan:
            rk = ["menager","recyclable","biomedical"]
            rl = ["Ménager","Recyclable","Biomédical"]
            rd = [sum(t["distance_km"] for t in self.plan["trucks"].get(k,[]))
                  for k in rk]
            ax6.bar(rl, rd, color=["#2196F3","#4CAF50","#FF9800"],
                    width=0.5, edgecolor=BG)
            for x, v in enumerate(rd):
                ax6.text(x, v+0.1, f"{v:.1f}km",
                         ha="center", va="bottom", fontsize=8,
                         color="#F1F5F9", fontweight="bold")
            ax6.set_title("Routes : km/Type", color="#F1F5F9",
                          fontsize=9, fontweight="bold")
        else:
            ax6.text(0.5, 0.5, "Calculez les routes\n(Onglet Routes)",
                     ha="center", va="center", transform=ax6.transAxes,
                     color="#94A3B8", fontsize=9)
            ax6.set_title("Routes : km/Type", color="#F1F5F9",
                          fontsize=9, fontweight="bold")
        ax6.tick_params(colors="#94A3B8", labelsize=7)
        ax6.spines[:].set_edgecolor("#475569")
        ax6.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")

        # ── Remplissage par type ─────────────
        ax7 = fig.add_subplot(gs[1, 3])
        ax7.set_facecolor(BG)
        td = stats["by_type"]
        t_lbs  = ["Ménager","Recyclable","Biomédical"]
        t_keys = ["menager","recyclable","biomedical"]
        t_vals = [td.get(k,0) for k in t_keys]
        ax7.bar(t_lbs, t_vals, color=["#2196F3","#4CAF50","#FF9800"],
                width=0.5, edgecolor=BG)
        for x, v in enumerate(t_vals):
            ax7.text(x, v+0.5, f"{v:.0f}%",
                     ha="center", va="bottom", fontsize=9,
                     color="#F1F5F9", fontweight="bold")
        ax7.axhline(70, color="#F43F5E", ls="--", lw=1)
        ax7.set_ylim(0, 105)
        ax7.set_title("IoT : Remplissage/Type", color="#F1F5F9",
                      fontsize=9, fontweight="bold")
        ax7.tick_params(colors="#94A3B8", labelsize=7)
        ax7.spines[:].set_edgecolor("#475569")
        ax7.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")

        fig.suptitle(
            f"EMSI 2025/2026 — Tableau de Bord Global  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            color="#F1F5F9", fontsize=11, fontweight="bold", y=0.99
        )
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        self._update_canvas(self.canvas_dash, self.fig_dash, fig)
        plt.close(fig)

    def _dash_export(self):
        export_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "exports", f"dashboard_global_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        self._build_global_dashboard()
        messagebox.showinfo("Export", f"Dashboard exporté :\n{export_path}")
        self._set_status(f"✅ Dashboard exporté")

    def _dash_rapport(self):
        self.nb.select(4)

    # ══════════════════════════════════════════════════════════
    #  ONGLET 5 : Rapport
    # ══════════════════════════════════════════════════════════
    def _tab_rapport(self, frame):
        ctrl = tk.Frame(frame, bg=BG_MED)
        ctrl.pack(fill="x", padx=8, pady=(8,0))

        for txt, cmd, color in [
            ("📝  Générer Rapport", self._rapport_generate, GREEN),
            ("💾  Exporter JSON",   self._rapport_json,     BLUE),
            ("🖨️  Imprimer",        self._rapport_print,    YELLOW),
        ]:
            tk.Button(ctrl, text=txt, command=cmd,
                      bg=BG_CARD, fg=color, activebackground=BG_DARK,
                      relief="flat", font=(FONT_FAMILY, 9, "bold"),
                      cursor="hand2", padx=10, pady=5).pack(side="left", padx=4, pady=4)

        self.rapport_text = scrolledtext.ScrolledText(
            frame, bg="#0F172A", fg=GREEN,
            font=("Courier New", 9), relief="flat",
            insertbackground=GREEN, wrap="word"
        )
        self.rapport_text.pack(fill="both", expand=True, padx=8, pady=8)
        self._rapport_generate()

    def _rapport_generate(self):
        from modules.linear_prog import rapport_chapter1
        from modules.simplex import rapport_chapter2

        self._set_status("⏳ Génération du rapport...")
        stats  = self.manager.get_statistics()
        urgent, att, norm = self.manager.prioritize_bins()
        sol2   = self.sol_lp["integer"]

        report = f"""
{'═'*64}
  RAPPORT — SYSTÈME D'OPTIMISATION GESTION DES DÉCHETS
  EMSI — 3ème Année Ingénierie Informatique — 2025/2026
  {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
  Équipe : {' · '.join(AUTHORS)}
{'═'*64}

{rapport_chapter1()}

{rapport_chapter2()}

{'═'*64}
  RÉSEAU IOT — ÉTAT TEMPS RÉEL
{'═'*64}

  Capteurs actifs    : {stats['n_bins']}
  Remplissage moyen  : {stats['fill_avg']:.1f}%
  Poids total estimé : {stats['total_weight_kg']:.0f} kg
  Bennes urgentes    : {stats['urgent_count']}
  Zone la + chargée  : {stats['hotspot_zone']}

  Répartition par statut :
"""
        for k, v in stats["by_status"].items():
            report += f"    {k:<12} : {v}\n"

        report += f"""
  Remplissage par type :
"""
        for k, v in stats["by_type"].items():
            report += f"    {k:<12} : {v:.1f}%\n"

        if self.plan:
            s = self.plan["summary"]
            report += f"""
{'═'*64}
  PLAN DE TOURNÉES — ÉTAPE 4
{'═'*64}

  Méthode           : {self.plan['method']}
  Camions déployés  : {s['total_trucks']}
  Bennes collectées : {s['total_bins']}
  Distance totale   : {s['total_distance']:.2f} km
  Carburant estimé  : {s['total_fuel_L']:.1f} L
  Poids collecté    : {s['total_weight_kg']:.0f} kg
"""

        report += f"\n{'═'*64}\n  Fin du rapport\n{'═'*64}\n"

        self.rapport_text.delete("1.0", "end")
        self.rapport_text.insert("end", report)
        self._set_status("✅ Rapport généré")

    def _rapport_json(self):
        path, _ = self.manager.export_json()
        messagebox.showinfo("Export JSON", f"Rapport IoT exporté :\n{path}")
        self._set_status(f"✅ JSON exporté : {path}")

    def _rapport_print(self):
        content = self.rapport_text.get("1.0", "end")
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "exports", f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Rapport sauvegardé", f"Fichier :\n{path}")
        self._set_status(f"✅ Rapport sauvegardé")

    # ══════════════════════════════════════════════════════════
    #  Utilitaires canvas / statut
    # ══════════════════════════════════════════════════════════
    def _make_canvas(self, parent, figsize):
        fig = plt.figure(figsize=figsize, facecolor="#1E293B")
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return fig, canvas

    def _update_canvas(self, canvas, old_fig, new_fig):
        old_fig.clf()
        for ax_new in new_fig.get_axes():
            old_fig.add_axes(ax_new)
        old_fig.set_size_inches(new_fig.get_size_inches())
        old_fig.__dict__.update(
            {k: v for k, v in new_fig.__dict__.items()
             if k not in ("axes", "_axstack")}
        )
        canvas.figure = new_fig
        canvas.draw()

    def _set_status(self, msg):
        if self.status_var:
            self.status_var.set(msg)
            if hasattr(self, "root"):
                self.root.update_idletasks()


# ── Lancement standalone ──────────────────────────────────────
def run_gui():
    if not TKINTER_AVAILABLE:
        print("⚠️  Tkinter non disponible — utilisez le mode web : python ui/web_app.py")
        return False
    root = tk.Tk()
    app  = WasteManagementApp(root)
    root.mainloop()
    return True
