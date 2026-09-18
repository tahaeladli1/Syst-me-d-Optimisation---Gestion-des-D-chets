#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  modules/route_visualisation.py  —  ÉTAPE 4
#  Visualisations : cartes de tournées & tableaux de bord
# ============================================================

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DEPOT_LAT, DEPOT_LNG
from modules.route_optimizer import haversine

BG    = "#1E293B"
BG2   = "#0F172A"
TEXT  = "#F1F5F9"
MUTED = "#94A3B8"

TRUCK_COLORS = {
    "menager"    : ["#2196F3","#1565C0","#0D47A1"],
    "recyclable" : ["#4CAF50","#2E7D32","#1B5E20","#00897B","#00695C"],
    "biomedical" : ["#FF9800","#E65100","#BF360C","#FF6F00","#E65100"],
}
WASTE_COLOR = {
    "menager"   : "#2196F3",
    "recyclable": "#4CAF50",
    "biomedical": "#FF9800",
}


# ════════════════════════════════════════════════════════════
#  1. Carte des tournées
# ════════════════════════════════════════════════════════════
def plot_routes_map(fleet_plan, save_path=None):
    """
    Carte géographique de toutes les tournées par type de camion.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 7), facecolor=BG)
    fig.suptitle(
        "Carte des Tournées Optimisées — EMSI 2025/2026\n"
        f"Méthode : {fleet_plan.get('method','2-opt').upper()}  |  "
        f"{fleet_plan['summary']['total_trucks']} camions  |  "
        f"{fleet_plan['summary']['total_distance']:.1f} km total",
        color=TEXT, fontsize=13, fontweight="bold", y=0.98
    )

    types = ["menager", "recyclable", "biomedical"]
    titles = ["🔵 Ménagers (x₁=2)", "♻️  Recyclables (x₂=5)", "🟠 Biomédicaux (x₃=5)"]
    depot  = [DEPOT_LNG, DEPOT_LAT]

    for ax, wtype, title in zip(axes, types, titles):
        ax.set_facecolor(BG2)
        trucks = fleet_plan["trucks"].get(wtype, [])
        palette = TRUCK_COLORS.get(wtype, ["#3B82F6"]*5)

        if not trucks:
            ax.text(0.5, 0.5, "Aucune tournée", ha="center", va="center",
                    transform=ax.transAxes, color=MUTED, fontsize=11)
            ax.set_title(title, color=TEXT, fontsize=11, fontweight="bold")
            continue

        # Dépôt
        ax.scatter(*depot, marker="*", c="#FBBF24", s=250, zorder=6,
                   label="Dépôt", edgecolors="white", linewidths=0.8)

        for k, truck in enumerate(trucks):
            color = palette[k % len(palette)]
            route = truck["route"]

            # Tracé de la route
            lngs = [p["location"][1] for p in route]
            lats = [p["location"][0] for p in route]
            ax.plot(lngs, lats, "-o", color=color, lw=1.8,
                    markersize=6, markerfacecolor=color,
                    markeredgecolor="white", markeredgewidth=0.5,
                    alpha=0.85, label=truck["truck_id"],
                    zorder=4)

            # Flèches de direction
            for i in range(0, len(lngs)-1, max(1, len(lngs)//4)):
                dx = lngs[i+1] - lngs[i]
                dy = lats[i+1] - lats[i]
                ax.annotate("", xy=(lngs[i]+dx*0.6, lats[i]+dy*0.6),
                            xytext=(lngs[i]+dx*0.4, lats[i]+dy*0.4),
                            arrowprops=dict(arrowstyle="->", color=color,
                                           lw=1.2), zorder=5)

            # Numérotation des arrêts (hors dépôt)
            for j, stop in enumerate(route[1:-1], 1):
                ax.text(stop["location"][1], stop["location"][0], str(j),
                        fontsize=6.5, ha="center", va="center",
                        color="white", fontweight="bold",
                        bbox=dict(boxstyle="circle,pad=0.15",
                                  facecolor=color, edgecolor="none",
                                  alpha=0.85), zorder=7)

        ax.set_title(title, color=TEXT, fontsize=11, fontweight="bold")
        ax.set_xlabel("Longitude", color=MUTED, fontsize=8)
        ax.set_ylabel("Latitude",  color=MUTED, fontsize=8)
        ax.tick_params(colors=MUTED, labelsize=7)
        ax.grid(True, color="#334155", ls="--", alpha=0.3)
        ax.spines[:].set_edgecolor("#475569")
        ax.legend(loc="lower right", fontsize=6.5, facecolor=BG,
                  edgecolor="#475569", labelcolor=TEXT)

        # Annotations métriques
        total_km = sum(t["distance_km"] for t in trucks)
        total_kg = sum(t["weight_kg"] for t in trucks)
        ax.text(0.02, 0.97,
                f"{len(trucks)} camion(s)  |  {total_km:.1f} km  |  {total_kg:.0f} kg",
                transform=ax.transAxes, fontsize=7.5, color="#FBBF24",
                va="top", fontweight="bold",
                bbox=dict(facecolor="#1E293B", edgecolor="#475569",
                          alpha=0.85, boxstyle="round,pad=0.3"))

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
    return fig


# ════════════════════════════════════════════════════════════
#  2. Dashboard métriques de flotte
# ════════════════════════════════════════════════════════════
def plot_fleet_dashboard(fleet_plan, save_path=None):
    """
    Tableau de bord 2×3 avec les métriques clés des tournées.
    """
    fig = plt.figure(figsize=(16, 10), facecolor=BG)
    fig.suptitle(
        "📊  Dashboard Flotte — Étape 4 : Optimisation des Routes\n"
        "EMSI 2025/2026  |  Méthode 2-Opt + Nearest Neighbor",
        color=TEXT, fontsize=13, fontweight="bold", y=0.98
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.5, wspace=0.38)

    summary = fleet_plan["summary"]
    sol     = fleet_plan["lp_solution"]

    # ── Graphe 1 : Distance par camion ───────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(BG)
    all_trucks = []
    for wtype, trucks in fleet_plan["trucks"].items():
        for t in trucks:
            all_trucks.append(t)

    t_ids   = [t["truck_id"].replace("TRUCK_","").replace("_0","") for t in all_trucks]
    t_dists = [t["distance_km"] for t in all_trucks]
    t_clrs  = [WASTE_COLOR[t["waste_type"]] for t in all_trucks]

    bars1 = ax1.bar(range(len(t_ids)), t_dists, color=t_clrs,
                    edgecolor=BG, width=0.65)
    ax1.set_xticks(range(len(t_ids)))
    ax1.set_xticklabels(t_ids, rotation=45, ha="right", fontsize=7, color=MUTED)
    for bar, v in zip(bars1, t_dists):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                 f"{v:.1f}", ha="center", va="bottom", fontsize=7,
                 color=TEXT, fontweight="bold")
    ax1.set_title("Distance par Camion (km)", color=TEXT,
                  fontsize=10, fontweight="bold")
    ax1.set_ylabel("km", color=MUTED, fontsize=8)
    ax1.tick_params(colors=MUTED)
    ax1.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax1.spines[:].set_edgecolor("#475569")

    # ── Graphe 2 : Poids collecté par camion ─────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BG)
    t_weights = [t["weight_kg"] for t in all_trucks]
    bars2 = ax2.bar(range(len(t_ids)), t_weights, color=t_clrs,
                    edgecolor=BG, width=0.65)
    ax2.set_xticks(range(len(t_ids)))
    ax2.set_xticklabels(t_ids, rotation=45, ha="right", fontsize=7, color=MUTED)
    for bar, v in zip(bars2, t_weights):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+10,
                 f"{v:.0f}", ha="center", va="bottom", fontsize=7,
                 color=TEXT, fontweight="bold")
    ax2.set_title("Poids Collecté par Camion (kg)", color=TEXT,
                  fontsize=10, fontweight="bold")
    ax2.set_ylabel("kg", color=MUTED, fontsize=8)
    ax2.tick_params(colors=MUTED)
    ax2.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax2.spines[:].set_edgecolor("#475569")

    # ── Graphe 3 : Taux de chargement ────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor(BG)
    t_loads  = [t.get("load_pct", 0) for t in all_trucks]
    t_clrs3  = ["#EF4444" if v >= 90 else "#F59E0B" if v >= 70
                else "#10B981" for v in t_loads]
    ax3.barh(range(len(t_ids)), t_loads, color=t_clrs3,
             height=0.6, edgecolor=BG)
    ax3.set_yticks(range(len(t_ids)))
    ax3.set_yticklabels(t_ids, fontsize=7, color=MUTED)
    ax3.axvline(100, color="#F43F5E", ls="--", lw=1.2)
    for i, v in enumerate(t_loads):
        ax3.text(v+0.5, i, f"{v:.0f}%", va="center",
                 fontsize=7, color=TEXT, fontweight="bold")
    ax3.set_xlim(0, 120)
    ax3.set_title("Taux de Chargement (%)", color=TEXT,
                  fontsize=10, fontweight="bold")
    ax3.tick_params(colors=MUTED)
    ax3.grid(True, color="#334155", ls="--", alpha=0.4, axis="x")
    ax3.spines[:].set_edgecolor("#475569")

    # ── Graphe 4 : Comparaison NN vs 2-Opt ───────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.set_facecolor(BG)
    nn_dists   = [t.get("distance_nn_km", t["distance_km"]) for t in all_trucks]
    opt_dists  = [t["distance_km"] for t in all_trucks]
    x4 = np.arange(len(t_ids))
    w  = 0.38
    ax4.bar(x4-w/2, nn_dists,  w, label="Nearest Neighbor",
            color="#6366F1", edgecolor=BG, alpha=0.9)
    ax4.bar(x4+w/2, opt_dists, w, label="2-Opt (optimisé)",
            color="#10B981", edgecolor=BG, alpha=0.9)
    ax4.set_xticks(x4)
    ax4.set_xticklabels(t_ids, rotation=45, ha="right", fontsize=7, color=MUTED)
    ax4.set_title("NN vs 2-Opt (km)", color=TEXT,
                  fontsize=10, fontweight="bold")
    ax4.set_ylabel("Distance (km)", color=MUTED, fontsize=8)
    ax4.tick_params(colors=MUTED)
    ax4.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax4.spines[:].set_edgecolor("#475569")
    ax4.legend(fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    # ── Graphe 5 : Distance totale par type ──────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.set_facecolor(BG)
    types_lbl = ["Ménager", "Recyclable", "Biomédical"]
    types_key = ["menager", "recyclable", "biomedical"]
    type_km   = [sum(t["distance_km"] for t in fleet_plan["trucks"].get(k,[]))
                 for k in types_key]
    type_n    = [len(fleet_plan["trucks"].get(k,[])) for k in types_key]
    clrs5     = [WASTE_COLOR[k] for k in types_key]
    bars5 = ax5.bar(types_lbl, type_km, color=clrs5, width=0.5, edgecolor=BG)
    for bar, km, n in zip(bars5, type_km, type_n):
        ax5.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                 f"{km:.1f} km\n({n} camions)", ha="center", va="bottom",
                 fontsize=8.5, color=TEXT, fontweight="bold")
    ax5.set_title("Distance par Type de Déchet", color=TEXT,
                  fontsize=10, fontweight="bold")
    ax5.set_ylabel("km total", color=MUTED, fontsize=8)
    ax5.tick_params(colors=MUTED)
    ax5.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax5.spines[:].set_edgecolor("#475569")

    # ── Graphe 6 : KPI résumé ─────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.set_facecolor(BG)
    ax6.axis("off")
    ax6.set_title("Résumé de la Flotte", color=TEXT,
                  fontsize=10, fontweight="bold", pad=8)

    avg_gain = np.mean([t.get("gain_pct", 0) for t in all_trucks])

    kpis = [
        ("Total camions",     str(summary["total_trucks"]),         "#10B981"),
        ("Total bennes",      str(summary["total_bins"]),           "#3B82F6"),
        ("Distance totale",   f"{summary['total_distance']:.1f} km", "#F59E0B"),
        ("Poids collecté",    f"{summary['total_weight_kg']:.0f} kg","#A78BFA"),
        ("Carburant total",   f"{summary['total_fuel_L']:.1f} L",   "#F97316"),
        ("Gain 2-Opt moyen",  f"{avg_gain:.1f}%",                   "#10B981"),
        ("Dist. moy/camion",  f"{summary['avg_distance']:.2f} km",  "#6366F1"),
        ("Solution LP",
         f"x₁={sol['x1']} x₂={sol['x2']} x₃={sol['x3']}",         "#FBBF24"),
    ]
    for i, (label, val, color) in enumerate(kpis):
        y = 0.93 - i * 0.115
        ax6.text(0.03, y, label, transform=ax6.transAxes,
                 fontsize=8.5, color=MUTED)
        ax6.text(0.97, y, val, transform=ax6.transAxes,
                 fontsize=9.5, color=color, fontweight="bold", ha="right")
        ax6.plot([0.03, 0.97], [y-0.045, y-0.045],
                 transform=ax6.transAxes, color="#334155", lw=0.6)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
    return fig


# ════════════════════════════════════════════════════════════
#  3. Comparaison des algorithmes
# ════════════════════════════════════════════════════════════
def plot_algorithm_comparison(manager, save_path=None):
    """
    Compare les 3 algorithmes sur un sous-ensemble de bennes.
    """
    from modules.route_optimizer import RouteOptimizer
    from modules.simplex import simplex_chapter2

    urgent, attention, _ = manager.prioritize_bins()
    sample = (urgent + attention)[:12]

    if not sample:
        return None

    optimizer = RouteOptimizer()
    methods   = ["nearest_neighbor", "cheapest_insertion", "two_opt"]
    labels    = ["Nearest\nNeighbor", "Cheapest\nInsertion", "2-Opt"]
    results   = []
    for m in methods:
        r = optimizer.optimize_route(sample, method=m)
        results.append(r)

    dists = [r["distance_km"] for r in results]
    times = [r["compute_ms"] for r in results]
    clrs  = ["#6366F1", "#F59E0B", "#10B981"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor=BG)
    fig.suptitle("Comparaison des Algorithmes de Routage (TSP)",
                 color=TEXT, fontsize=13, fontweight="bold")

    # Distance
    ax1 = axes[0]
    ax1.set_facecolor(BG)
    bars = ax1.bar(labels, dists, color=clrs, width=0.5, edgecolor=BG)
    for bar, v in zip(bars, dists):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                 f"{v:.2f} km", ha="center", va="bottom",
                 fontsize=10, color=TEXT, fontweight="bold")
    best_d = min(dists)
    ax1.axhline(best_d, color="#F43F5E", ls="--", lw=1.2, label=f"Meilleur {best_d:.2f} km")
    ax1.set_title("Distance Totale (km)", color=TEXT, fontsize=11, fontweight="bold")
    ax1.set_ylabel("km", color=MUTED)
    ax1.tick_params(colors=MUTED)
    ax1.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax1.spines[:].set_edgecolor("#475569")
    ax1.legend(fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    # Temps de calcul
    ax2 = axes[1]
    ax2.set_facecolor(BG)
    bars2 = ax2.bar(labels, times, color=clrs, width=0.5, edgecolor=BG)
    for bar, v in zip(bars2, times):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                 f"{v:.1f} ms", ha="center", va="bottom",
                 fontsize=10, color=TEXT, fontweight="bold")
    ax2.set_title("Temps de Calcul (ms)", color=TEXT, fontsize=11, fontweight="bold")
    ax2.set_ylabel("ms", color=MUTED)
    ax2.tick_params(colors=MUTED)
    ax2.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax2.spines[:].set_edgecolor("#475569")

    # Radar : score global
    ax3 = axes[2]
    ax3.set_facecolor(BG)
    cats   = ["Distance\n(inversé)", "Vitesse\n(inversé)", "Qualité"]
    n      = len(cats)
    angles = [i/n*2*np.pi for i in range(n)] + [0]

    max_d = max(dists); max_t = max(times)
    scores = []
    for r, d, t in zip(results, dists, times):
        quality = r.get("gain_pct", 0) / max(0.1, max(rr.get("gain_pct",0) for rr in results))
        scores.append([
            1 - (d / max_d),
            1 - (t / max_t),
            quality,
        ])

    for i, (score, label, color) in enumerate(zip(scores, labels, clrs)):
        vals = score + [score[0]]
        ax3.plot(angles, vals, color=color, lw=2, label=label.replace("\n"," "))
        ax3.fill(angles, vals, color=color, alpha=0.10)

    ax3.set_xticks(angles[:-1])
    ax3.set_xticklabels(cats, color=MUTED, fontsize=8)
    ax3.set_ylim(0, 1.1)
    ax3.tick_params(colors=MUTED, labelsize=7)
    ax3.set_facecolor(BG)
    try:
        ax3.spines["polar"].set_edgecolor("#475569")
    except KeyError:
        pass
    ax3.grid(True, color="#334155", alpha=0.4)
    ax3.yaxis.set_tick_params(labelcolor=MUTED, labelsize=6)
    ax3.set_title("Score Global", color=TEXT, fontsize=11, fontweight="bold", pad=12)
    ax3.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1),
               fontsize=8, facecolor=BG, edgecolor="#475569", labelcolor=TEXT)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
    return fig


# ════════════════════════════════════════════════════════════
#  4. Détail d'une tournée (segments + métriques)
# ════════════════════════════════════════════════════════════
def plot_single_truck_route(truck_result, save_path=None):
    """
    Affiche la carte + les métriques détaillées d'un seul camion.
    """
    route  = truck_result["route"]
    stops  = truck_result["stops"]
    wtype  = truck_result.get("waste_type", "menager")
    color  = WASTE_COLOR.get(wtype, "#3B82F6")
    t_id   = truck_result.get("truck_id", "TRUCK_001")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor=BG)
    fig.suptitle(
        f"Détail Tournée : {t_id}  |  Type: {wtype}  |  "
        f"{truck_result['distance_km']:.2f} km  |  "
        f"{truck_result['duration_min']:.0f} min  |  "
        f"{truck_result['weight_kg']:.0f} kg",
        color=TEXT, fontsize=12, fontweight="bold"
    )

    # ── Carte ────────────────────────────────────────────────
    ax1.set_facecolor(BG2)
    lngs = [p["location"][1] for p in route]
    lats = [p["location"][0] for p in route]

    # Dégradé de couleur pour la progression
    n_seg = len(lngs) - 1
    cmap  = plt.cm.get_cmap("cool" if wtype == "biomedical" else
                             "Greens" if wtype == "recyclable" else "Blues")
    for i in range(n_seg):
        c = cmap(0.4 + 0.5 * i / max(1, n_seg))
        ax1.plot([lngs[i], lngs[i+1]], [lats[i], lats[i+1]],
                 "-", color=c, lw=2.5, zorder=3)
        # Flèche
        mx = (lngs[i]+lngs[i+1])/2
        my = (lats[i]+lats[i+1])/2
        dx = lngs[i+1]-lngs[i]; dy = lats[i+1]-lats[i]
        ax1.annotate("", xy=(mx+dx*0.01, my+dy*0.01),
                     xytext=(mx-dx*0.01, my-dy*0.01),
                     arrowprops=dict(arrowstyle="->", color=c, lw=1.5),
                     zorder=5)

    # Bennes numérotées
    for j, point in enumerate(route):
        if point.get("id") == "DEPOT" or j == 0 or j == len(route)-1:
            ax1.scatter(point["location"][1], point["location"][0],
                        c="#FBBF24", s=160, marker="*", zorder=6,
                        edgecolors="white", linewidths=0.8)
            ax1.text(point["location"][1], point["location"][0]+0.0005,
                     "DÉPÔT", ha="center", fontsize=6.5,
                     color="#FBBF24", fontweight="bold")
        else:
            ax1.scatter(point["location"][1], point["location"][0],
                        c=color, s=70, zorder=5,
                        edgecolors="white", linewidths=0.5)
            ax1.text(point["location"][1], point["location"][0],
                     str(j), ha="center", va="center",
                     fontsize=6, color="white", fontweight="bold", zorder=7)

    ax1.set_title(f"Carte — {t_id}", color=TEXT, fontsize=10, fontweight="bold")
    ax1.set_xlabel("Longitude", color=MUTED, fontsize=8)
    ax1.set_ylabel("Latitude",  color=MUTED, fontsize=8)
    ax1.tick_params(colors=MUTED, labelsize=7)
    ax1.grid(True, color="#334155", ls="--", alpha=0.3)
    ax1.spines[:].set_edgecolor("#475569")

    # ── Profil de la tournée ──────────────────────────────────
    ax2.set_facecolor(BG)
    seg_labels  = [f"{s['from_id'].split('_')[1] if '_' in s['from_id'] else 'DPT'}"
                   f"→{s['to_id'].split('_')[1] if '_' in s['to_id'] else 'DPT'}"
                   for s in stops]
    seg_km      = [s["distance_km"] for s in stops]
    seg_min     = [s["duration_min"] for s in stops]
    x2          = np.arange(len(stops))

    ax2b = ax2.twinx()
    ax2.bar(x2, seg_km, color=color, width=0.5, alpha=0.85,
            edgecolor=BG, label="Distance (km)")
    ax2b.plot(x2, seg_min, "o--", color="#FBBF24", lw=1.8,
              markersize=6, label="Durée (min)")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(seg_labels, rotation=60, ha="right",
                        fontsize=6.5, color=MUTED)
    ax2.set_title("Profil des Segments", color=TEXT, fontsize=10, fontweight="bold")
    ax2.set_ylabel("km", color=color, fontsize=8)
    ax2b.set_ylabel("min", color="#FBBF24", fontsize=8)
    ax2.tick_params(colors=MUTED)
    ax2b.tick_params(colors="#FBBF24")
    ax2.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax2.spines[:].set_edgecolor("#475569")
    ax2b.spines[:].set_edgecolor("#475569")

    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    ax2.legend(h1+h2, l1+l2, fontsize=8, facecolor=BG,
               edgecolor="#475569", labelcolor=TEXT)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
    return fig
