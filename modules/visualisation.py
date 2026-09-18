#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  modules/visualisation.py  —  ÉTAPE 2
#  Génération de tous les graphiques et tableaux comparatifs
# ============================================================

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import COLORS


# ────────────────────────────────────────────────────────────
#  Dashboard complet Étape 2 (4 graphiques en un)
# ────────────────────────────────────────────────────────────
def plot_dashboard_etape2(save_path=None):
    """
    Dashboard 2×2 :
      [1] Région réalisable Ch.1 (méthode graphique)
      [2] Évolution Z simplexe
      [3] Allocation optimale Ch.2 (barres)
      [4] Saturation des contraintes (barres horizontales)
    """
    from modules.linear_prog import plot_graphical_method, solve_chapter1
    from modules.simplex import Simplex, simplex_chapter2

    BG = "#1E293B"
    fig = plt.figure(figsize=(16, 11), facecolor=BG)
    fig.suptitle(
        "EMSI — Tableau de Bord Optimisation Gestion des Déchets\n"
        "Étape 2 : Algorithmes de Programmation Linéaire",
        color="#F1F5F9", fontsize=14, fontweight="bold", y=0.98
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.35)

    # ── Graphique 1 : Méthode graphique Ch.1 ─────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(BG)
    _draw_graphical(ax1)

    # ── Graphique 2 : Évolution Z simplexe ───────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BG)
    solver = Simplex()
    res    = solver.solve()
    z_vals = [snap["z_value"] for snap in res["iterations"]]
    labels = [f"Init" if i == 0 else f"Itér.{i}" for i in range(len(z_vals))]
    ax2.plot(labels, z_vals, "o-", color="#3B82F6", lw=2.5,
             markersize=11, markerfacecolor="#F59E0B", zorder=5)
    for lbl, z in zip(labels, z_vals):
        ax2.annotate(f"{z:.1f}", (lbl, z),
                     textcoords="offset points", xytext=(0, 11),
                     ha="center", fontsize=9, color="#E2E8F0")
    ax2.set_title("Convergence du Simplexe", color="#F1F5F9",
                  fontsize=11, fontweight="bold")
    ax2.set_ylabel("Z (t/jour)", color="#CBD5E1")
    ax2.tick_params(colors="#94A3B8")
    ax2.grid(True, color="#334155", ls="--", alpha=0.5)
    ax2.spines[:].set_edgecolor("#475569")
    ax2.set_ylim(0, max(z_vals) * 1.18)
    ax2.fill_between(range(len(z_vals)), z_vals,
                     alpha=0.12, color="#3B82F6")

    # ── Graphique 3 : Allocation optimale Ch.2 ───────────────
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_facecolor(BG)
    sol    = res["integer"]
    types  = ["Ménager\n(x₁)", "Recyclable\n(x₂)", "Biomédical\n(x₃)"]
    counts = [sol["x1"], sol["x2"], sol["x3"]]
    clrs   = ["#3B82F6", "#10B981", "#F59E0B"]
    bars   = ax3.bar(types, counts, color=clrs, edgecolor=BG,
                     linewidth=1.5, width=0.5)
    for bar, n, coef, total in zip(bars, counts, [8,7,11],
                                   [8*sol["x1"], 7*sol["x2"], 11*sol["x3"]]):
        ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.07,
                 f"{n} camions\n+{total}t", ha="center", va="bottom",
                 fontsize=8.5, color="#F1F5F9", fontweight="bold")
    ax3.set_title(f"Allocation Optimale — Z★ = {sol['Z']} t/jour",
                  color="#F1F5F9", fontsize=11, fontweight="bold")
    ax3.set_ylabel("Nombre de camions", color="#CBD5E1")
    ax3.tick_params(colors="#94A3B8")
    ax3.set_ylim(0, max(counts)*1.45)
    ax3.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax3.spines[:].set_edgecolor("#475569")

    # ── Graphique 4 : Saturation des contraintes ─────────────
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor(BG)
    sat    = sol["saturation"]
    c_lbls = ["C1 Carburant", "C2 Temps", "C3 Budget"]
    c_vals = [sat["C1"], sat["C2"], sat["C3"]]
    c_clrs = ["#EF4444" if v >= 100 else "#F59E0B" if v >= 90 else "#10B981"
              for v in c_vals]
    hbars = ax4.barh(c_lbls, c_vals, color=c_clrs, height=0.40,
                     edgecolor=BG)
    ax4.axvline(100, color="#F43F5E", ls="--", lw=1.8, label="Limite 100%")
    for bar, v in zip(hbars, c_vals):
        ax4.text(v+0.8, bar.get_y()+bar.get_height()/2,
                 f"{v}%", va="center", fontsize=11,
                 fontweight="bold", color="#F1F5F9")
    ax4.set_xlim(0, 118)
    ax4.set_title("Saturation des Contraintes", color="#F1F5F9",
                  fontsize=11, fontweight="bold")
    ax4.set_xlabel("Taux d'utilisation (%)", color="#CBD5E1")
    ax4.tick_params(colors="#94A3B8")
    ax4.grid(True, color="#334155", ls="--", alpha=0.4, axis="x")
    ax4.spines[:].set_edgecolor("#475569")
    ax4.legend(fontsize=9, facecolor="#334155",
               edgecolor="#475569", labelcolor="#E2E8F0")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight",
                    facecolor=BG)
        print(f"  → Graphique sauvegardé : {save_path}")
    return fig


# ── Sous-fonction : tracé région réalisable ──────────────────
def _draw_graphical(ax):
    from modules.linear_prog import get_vertices_ch1, solve_chapter1
    from matplotlib.patches import Polygon as MplPolygon

    BG = "#1E293B"
    x  = np.linspace(0, 15, 400)

    defs = [
        (lambda x: (48-4*x)/3, "#3B82F6", "C1 Carburant"),
        (lambda x: (40-2*x)/4, "#10B981", "C2 Flotte"),
        (lambda x: (72-6*x)/4, "#F59E0B", "C3 Budget"),
        (lambda x: np.ones_like(x), "#A78BFA", "C5: x₂=1"),
    ]
    for fn, col, lbl in defs:
        y = fn(x)
        ax.plot(x, np.clip(y, 0, 15), color=col, lw=1.8, label=lbl)
    ax.axvline(2, color="#F472B6", lw=1.8, label="C4: x₁=2")

    verts = get_vertices_ch1()
    if len(verts) >= 3:
        poly = MplPolygon(verts, closed=True,
                          facecolor="#2E75B6", alpha=0.18,
                          edgecolor="#60A5FA", lw=1.5)
        ax.add_patch(poly)

    sol = solve_chapter1()
    bx, by = sol["integer"]["x1"], sol["integer"]["x2"]
    for vx, vy in verts:
        ax.plot(vx, vy, "o", color="#FBBF24", ms=6, zorder=5)

    ax.plot(bx, by, "*", color="#F43F5E", ms=16, zorder=6,
            label=f"★ x₁={bx}, x₂={by}, Z={sol['integer']['Z']}")

    ax.set_xlim(-0.5, 13); ax.set_ylim(-0.5, 13)
    ax.set_title("Ch.1 — Région Réalisable", color="#F1F5F9",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("x₁ (ménagers)", color="#CBD5E1", fontsize=9)
    ax.set_ylabel("x₂ (recyclables)", color="#CBD5E1", fontsize=9)
    ax.tick_params(colors="#94A3B8")
    ax.grid(True, color="#334155", ls="--", alpha=0.4)
    ax.spines[:].set_edgecolor("#475569")
    ax.legend(loc="upper right", fontsize=7,
              facecolor=BG, edgecolor="#475569", labelcolor="#E2E8F0")


# ── Comparaison Ch.1 vs Ch.2 ─────────────────────────────────
def plot_comparison(save_path=None):
    """Graphique de comparaison des deux chapitres."""
    from modules.linear_prog import solve_chapter1
    from modules.simplex import simplex_chapter2

    BG = "#1E293B"
    r1 = solve_chapter1()
    r2 = simplex_chapter2()

    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
    ax.set_facecolor(BG)

    chapters = ["Chapitre 1\n(Graphique)", "Chapitre 2\n(Simplexe)"]
    z_vals   = [r1["integer"]["Z"], r2["integer"]["Z"]]
    colors   = ["#3B82F6", "#10B981"]

    bars = ax.bar(chapters, z_vals, color=colors, width=0.4,
                  edgecolor=BG, linewidth=1.5)
    for bar, z in zip(bars, z_vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                f"{z} t/jour", ha="center", va="bottom",
                fontsize=14, fontweight="bold", color="#F1F5F9")

    gain = round((z_vals[1]-z_vals[0])/z_vals[0]*100, 1)
    ax.annotate(f"Gain : +{gain}%",
                xy=(1, z_vals[1]), xytext=(0.5, z_vals[1]+3),
                fontsize=11, color="#F59E0B", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#F59E0B"))

    ax.set_ylim(80, 115)
    ax.set_title("Comparaison des Solutions Optimales",
                 color="#F1F5F9", fontsize=13, fontweight="bold")
    ax.set_ylabel("Z — Collecte (tonnes/jour)", color="#CBD5E1")
    ax.tick_params(colors="#94A3B8")
    ax.grid(True, color="#334155", ls="--", alpha=0.4, axis="y")
    ax.spines[:].set_edgecolor("#475569")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
    return fig
