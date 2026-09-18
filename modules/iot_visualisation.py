#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  modules/iot_visualisation.py  —  ÉTAPE 3
#  Visualisations IoT : carte, jauges, graphiques temps réel
# ============================================================

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Wedge
import numpy as np
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import IOT_THRESHOLD
from modules.iot_sensors import WASTE_TYPES, CITY_ZONES

BG   = "#1E293B"
BG2  = "#0F172A"
CARD = "#1E3A5F"
TEXT = "#F1F5F9"
MUTED= "#94A3B8"

STATUS_COLORS = {
    "CRITICAL": "#EF4444",
    "URGENT"  : "#F59E0B",
    "WARNING" : "#FBBF24",
    "NORMAL"  : "#10B981",
}


# ════════════════════════════════════════════════════════════
#  Dashboard IoT — Vue globale
# ════════════════════════════════════════════════════════════
def plot_iot_dashboard(manager, save_path=None):
    """
    Dashboard 3×2 :
      [1] Carte des bennes (scatter géo)
      [2] Distribution des niveaux de remplissage
      [3] Remplissage moyen par zone (barres)
      [4] Répartition par statut (camembert)
      [5] Remplissage moyen par type de déchet
      [6] Top 10 bennes les plus urgentes
    """
    from modules.iot_analytics import IoTAnalytics

    analytics = IoTAnalytics(manager)
    kpis      = analytics.compute_kpis()
    all_bins  = manager.get_all_bins()
    stats     = manager.get_statistics()

    fig = plt.figure(figsize=(18, 12), facecolor=BG)
    gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.38)

    # ── [0] KPI Header ────────────────────────────────────────
    ax_kpi = fig.add_subplot(gs[0, :])
    ax_kpi.set_facecolor(BG)
    ax_kpi.axis("off")

    kpi_items = [
        (f"{kpis['taux_remplissage_moyen']}%",   "Remplissage Moyen",  "#3B82F6"),
        (f"{stats['urgent_count']}",              "Bennes Urgentes",    "#EF4444"),
        (f"{stats['n_bins']}",                    "Capteurs Actifs",    "#10B981"),
        (f"{stats['total_weight_kg']:.0f} kg",    "Poids Total",        "#F59E0B"),
        (f"{kpis['zone_critique']}",              "Zone Critique",      "#A78BFA"),
        (f"{kpis['taux_urgence_pct']}%",          "Taux d'Urgence",     "#F97316"),
    ]

    for i, (val, label, color) in enumerate(kpi_items):
        x = 0.08 + i * 0.155
        ax_kpi.add_patch(FancyBboxPatch((x-0.06, 0.05), 0.12, 0.85,
                                        boxstyle="round,pad=0.02",
                                        facecolor="#1E3A5F", edgecolor=color,
                                        linewidth=2, transform=ax_kpi.transAxes))
        ax_kpi.text(x, 0.62, val, ha="center", va="center",
                    transform=ax_kpi.transAxes,
                    fontsize=18, fontweight="bold", color=color)
        ax_kpi.text(x, 0.25, label, ha="center", va="center",
                    transform=ax_kpi.transAxes,
                    fontsize=8, color=MUTED)

    ax_kpi.set_title("🗑️  EMSI — Tableau de Bord IoT — Gestion des Déchets en Temps Réel",
                     color=TEXT, fontsize=14, fontweight="bold",
                     loc="center", pad=8)

    # ── [1] Carte géographique ────────────────────────────────
    ax1 = fig.add_subplot(gs[1, 0])
    ax1.set_facecolor(BG2)
    for b in all_bins:
        color = STATUS_COLORS.get(b["status"], "#10B981")
        size  = 20 + b["fill_level"] * 0.8
        ax1.scatter(b["location"][1], b["location"][0],
                    c=color, s=size, alpha=0.75, edgecolors="white",
                    linewidths=0.3, zorder=3)

    # Dépôt
    ax1.scatter([CITY_ZONES["Gueliz"]["lng"]], [CITY_ZONES["Gueliz"]["lat"]],
                marker="*", c="#FBBF24", s=220, zorder=5, label="Dépôt")

    for name, info in CITY_ZONES.items():
        ax1.annotate(name[:6], (info["lng"], info["lat"]),
                     fontsize=6.5, color=MUTED, ha="center",
                     xytext=(0, 8), textcoords="offset points")

    legend_elems = [mpatches.Patch(facecolor=c, label=k)
                    for k, c in STATUS_COLORS.items()]
    ax1.legend(handles=legend_elems, fontsize=7, facecolor=BG,
               edgecolor="#475569", labelcolor=TEXT, loc="lower right")
    ax1.set_title("Carte des Bennes", color=TEXT, fontsize=10, fontweight="bold")
    ax1.set_xlabel("Longitude", color=MUTED, fontsize=8)
    ax1.set_ylabel("Latitude",  color=MUTED, fontsize=8)
    ax1.tick_params(colors=MUTED, labelsize=7)
    ax1.grid(True, color="#334155", ls="--", alpha=0.3)
    ax1.spines[:].set_edgecolor("#475569")

    # ── [2] Histogramme des niveaux ───────────────────────────
    ax2 = fig.add_subplot(gs[1, 1])
    ax2.set_facecolor(BG)
    fill_vals = [b["fill_level"] for b in all_bins]
    bins_edges = range(0, 105, 10)
    colors_hist = []
    for edge in range(0, 100, 10):
        if edge >= 90: colors_hist.append("#EF4444")
        elif edge >= 70: colors_hist.append("#F59E0B")
        elif edge >= 50: colors_hist.append("#FBBF24")
        else: colors_hist.append("#10B981")

    n_hist, _, patches = ax2.hist(fill_vals, bins=list(bins_edges),
                                  edgecolor=BG, linewidth=0.8)
    for patch, color in zip(patches, colors_hist):
        patch.set_facecolor(color)

    ax2.axvline(IOT_THRESHOLD, color="#F43F5E", ls="--", lw=1.5,
                label=f"Seuil urgence {IOT_THRESHOLD}%")
    ax2.set_title("Distribution des Niveaux", color=TEXT, fontsize=10, fontweight="bold")
    ax2.set_xlabel("Niveau de remplissage (%)", color=MUTED, fontsize=8)
    ax2.set_ylabel("Nombre de bennes", color=MUTED, fontsize=8)
    ax2.tick_params(colors=MUTED, labelsize=7)
    ax2.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax2.spines[:].set_edgecolor("#475569")
    ax2.legend(fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    # ── [3] Remplissage par zone ──────────────────────────────
    ax3 = fig.add_subplot(gs[1, 2])
    ax3.set_facecolor(BG)
    zone_data  = stats["by_zone"]
    zones      = list(zone_data.keys())
    zone_vals  = [zone_data[z] for z in zones]
    zone_clrs  = ["#EF4444" if v >= IOT_THRESHOLD else "#3B82F6" for v in zone_vals]
    hbars      = ax3.barh(zones, zone_vals, color=zone_clrs, height=0.6,
                           edgecolor=BG)
    for bar, v in zip(hbars, zone_vals):
        ax3.text(v + 0.5, bar.get_y() + bar.get_height()/2,
                 f"{v:.1f}%", va="center", fontsize=8,
                 fontweight="bold", color=TEXT)
    ax3.axvline(IOT_THRESHOLD, color="#F43F5E", ls="--", lw=1.2)
    ax3.set_xlim(0, 110)
    ax3.set_title("Remplissage par Zone", color=TEXT, fontsize=10, fontweight="bold")
    ax3.set_xlabel("Taux moyen (%)", color=MUTED, fontsize=8)
    ax3.tick_params(colors=MUTED, labelsize=7)
    ax3.grid(True, color="#334155", ls="--", alpha=0.4, axis="x")
    ax3.spines[:].set_edgecolor("#475569")

    # ── [4] Camembert par statut ──────────────────────────────
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.set_facecolor(BG)
    status_data = stats["by_status"]
    labels_pie  = [k for k, v in status_data.items() if v > 0]
    sizes_pie   = [v for v in status_data.values() if v > 0]
    clrs_pie    = [STATUS_COLORS[k] for k in labels_pie]
    wedges, texts, autotexts = ax4.pie(
        sizes_pie, labels=labels_pie, colors=clrs_pie,
        autopct="%1.0f%%", startangle=90,
        wedgeprops=dict(edgecolor=BG, linewidth=2),
        textprops=dict(color=TEXT, fontsize=8)
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color(BG)
        at.set_fontweight("bold")
    ax4.set_title("Répartition par Statut", color=TEXT, fontsize=10, fontweight="bold")

    # ── [5] Remplissage par type ──────────────────────────────
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.set_facecolor(BG)
    type_data = stats["by_type"]
    types_lbl  = ["Ménager\n(x₁)", "Recyclable\n(x₂)", "Biomédical\n(x₃)"]
    types_vals = [type_data.get("menager", 0), type_data.get("recyclable", 0),
                  type_data.get("biomedical", 0)]
    types_clrs = [WASTE_TYPES["menager"]["color"],
                  WASTE_TYPES["recyclable"]["color"],
                  WASTE_TYPES["biomedical"]["color"]]
    bars5 = ax5.bar(types_lbl, types_vals, color=types_clrs,
                    width=0.5, edgecolor=BG)
    for bar, v in zip(bars5, types_vals):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f"{v:.1f}%", ha="center", va="bottom",
                 fontsize=10, fontweight="bold", color=TEXT)
    ax5.axhline(IOT_THRESHOLD, color="#F43F5E", ls="--", lw=1.2,
                label="Seuil urgence")
    ax5.set_ylim(0, 105)
    ax5.set_title("Remplissage par Type", color=TEXT, fontsize=10, fontweight="bold")
    ax5.set_ylabel("Taux moyen (%)", color=MUTED, fontsize=8)
    ax5.tick_params(colors=MUTED, labelsize=8)
    ax5.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax5.spines[:].set_edgecolor("#475569")
    ax5.legend(fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    # ── [6] Top 10 bennes urgentes ────────────────────────────
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.set_facecolor(BG)
    urgent, attention, _ = manager.prioritize_bins()
    top10 = (urgent + attention)[:10]
    top10.reverse()
    top_ids   = [b["bin_id"].split("_")[1] + "_" + b["bin_id"].split("_")[2]
                 for b in top10]
    top_fills = [b["fill_level"] for b in top10]
    top_clrs  = [STATUS_COLORS[b["status"]] for b in top10]
    hb6 = ax6.barh(top_ids, top_fills, color=top_clrs, height=0.6,
                   edgecolor=BG)
    for bar, v in zip(hb6, top_fills):
        ax6.text(v + 0.3, bar.get_y() + bar.get_height()/2,
                 f"{v:.0f}%", va="center", fontsize=8,
                 fontweight="bold", color=TEXT)
    ax6.axvline(IOT_THRESHOLD, color="#F43F5E", ls="--", lw=1.2)
    ax6.set_xlim(0, 110)
    ax6.set_title("Top 10 Bennes Urgentes", color=TEXT, fontsize=10, fontweight="bold")
    ax6.set_xlabel("Niveau de remplissage (%)", color=MUTED, fontsize=8)
    ax6.tick_params(colors=MUTED, labelsize=7)
    ax6.grid(True, color="#334155", ls="--", alpha=0.4, axis="x")
    ax6.spines[:].set_edgecolor("#475569")

    plt.suptitle(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} — EMSI 2025/2026",
                 color=MUTED, fontsize=9, y=0.01)

    plt.tight_layout(rect=[0, 0.02, 1, 1])
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
        print(f"  → Graphique sauvegardé : {save_path}")
    return fig


# ── Graphique d'historique d'une benne ───────────────────────
def plot_bin_history(manager, bin_id, save_path=None):
    """Trace l'historique de remplissage + prédiction d'une benne."""
    sensor = manager.get_bin(bin_id)
    if not sensor:
        return None

    history = sensor.history[-48:]   # 24 h
    times   = list(range(len(history)))
    fills   = [h["fill_level"] for h in history]
    temps   = [h["temp_c"]    for h in history]

    # Prédiction linéaire (12 points = 6h)
    n, sx, sy = len(times), sum(times), sum(fills)
    sxy = sum(t*f for t, f in zip(times, fills))
    sxx = sum(t**2 for t in times)
    denom = n*sxx - sx**2
    if abs(denom) > 1e-9:
        slope = (n*sxy - sx*sy) / denom
        intercept = (sy - slope*sx) / n
        pred_times = [len(times) + i for i in range(13)]
        pred_fills = [min(100, max(0, slope*t + intercept)) for t in pred_times]
    else:
        pred_times = pred_fills = []

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), facecolor=BG)
    fig.suptitle(f"Historique & Prédiction — {bin_id}  |  Type: {sensor.waste_type}  |  Zone: {sensor.zone}",
                 color=TEXT, fontsize=12, fontweight="bold")

    # Courbe de remplissage
    ax1.set_facecolor(BG)
    ax1.fill_between(times, fills, alpha=0.20, color="#3B82F6")
    ax1.plot(times, fills, color="#3B82F6", lw=2, label="Remplissage réel")
    if pred_times:
        ax1.plot(pred_times, pred_fills, "--", color="#F59E0B", lw=1.8,
                 label="Prédiction (6h)")
        ax1.fill_between(pred_times, pred_fills, alpha=0.10, color="#F59E0B")
    ax1.axhline(IOT_THRESHOLD, color="#EF4444", ls="--", lw=1.2,
                label=f"Seuil {IOT_THRESHOLD}%")
    ax1.axhline(90, color="#7F1D1D", ls=":", lw=1, label="Critique 90%")
    ax1.set_ylim(0, 108)
    ax1.set_ylabel("Remplissage (%)", color=MUTED)
    ax1.tick_params(colors=MUTED, labelsize=8)
    ax1.grid(True, color="#334155", ls="--", alpha=0.4)
    ax1.spines[:].set_edgecolor("#475569")
    ax1.legend(fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    # Courbe de température
    ax2.set_facecolor(BG)
    ax2.plot(times, temps, color="#A78BFA", lw=1.5, label="Température (°C)")
    ax2.fill_between(times, temps, alpha=0.12, color="#A78BFA")
    ax2.set_xlabel("Mesures (×30 min)", color=MUTED)
    ax2.set_ylabel("Température (°C)", color=MUTED)
    ax2.tick_params(colors=MUTED, labelsize=8)
    ax2.grid(True, color="#334155", ls="--", alpha=0.4)
    ax2.spines[:].set_edgecolor("#475569")
    ax2.legend(fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
    return fig


# ── Graphique des prédictions ─────────────────────────────────
def plot_predictions(manager, save_path=None):
    """Graphique des bennes qui atteindront le seuil dans les 24h."""
    from modules.iot_analytics import IoTAnalytics
    analytics  = IoTAnalytics(manager)
    predictions = analytics.predict_all()

    # Filtrer celles avec horizon < 24h
    soon = [p for p in predictions
            if isinstance(p.get("hours_to_threshold"), float)
            and p["hours_to_threshold"] < 24][:15]

    if not soon:
        return None

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG)
    ax.set_facecolor(BG)

    ids    = [p["bin_id"].split("_")[1] + "_" + p["bin_id"].split("_")[2] for p in soon]
    hours  = [p["hours_to_threshold"] for p in soon]
    fills  = [p["current_fill"] for p in soon]
    clrs   = [WASTE_TYPES[p["waste_type"]]["color"] for p in soon]

    bars = ax.barh(ids, hours, color=clrs, height=0.55, edgecolor=BG, alpha=0.88)
    for bar, h_val, fl in zip(bars, hours, fills):
        ax.text(h_val + 0.1, bar.get_y() + bar.get_height()/2,
                f"{h_val:.1f}h  ({fl:.0f}%)", va="center",
                fontsize=8, color=TEXT, fontweight="bold")

    ax.axvline(4,  color="#EF4444", ls="--", lw=1.3, label="4h (urgent)")
    ax.axvline(12, color="#F59E0B", ls="--", lw=1.0, label="12h (attention)")
    ax.set_xlabel("Heures avant d'atteindre le seuil d'urgence", color=MUTED, fontsize=9)
    ax.set_title("⏱️  Prédictions : Bennes Critiques dans les 24h", color=TEXT,
                 fontsize=12, fontweight="bold")
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(True, color="#334155", ls="--", alpha=0.4, axis="x")
    ax.spines[:].set_edgecolor("#475569")

    legend_elems = [mpatches.Patch(facecolor=WASTE_TYPES[t]["color"], label=t.capitalize())
                    for t in WASTE_TYPES]
    ax.legend(handles=legend_elems + [
        plt.Line2D([0],[0], color="#EF4444", ls="--", label="4h"),
        plt.Line2D([0],[0], color="#F59E0B", ls="--", label="12h"),
    ], fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
    return fig
