#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  modules/linear_prog.py  —  ÉTAPE 2
#  Chapitre 1 : Programmation Linéaire — Méthode Graphique
#  Max Z = 8x1 + 6x2  (2 variables, 6 contraintes)
# ============================================================

import numpy as np
from scipy.optimize import linprog
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    FUEL_LIMIT, FLEET_LIMIT, BUDGET_LIMIT,
    MIN_MENAGER, MIN_RECYCLABLE, MIN_COLLECTE,
    COEF_X1, COLORS
)


# ── 1. Résolution par SciPy (linprog) ───────────────────────
def solve_chapter1(fuel=None, fleet=None, budget=None):
    """
    Résout le PL du Chapitre 1 via scipy.optimize.linprog.

    Max Z = 8x1 + 6x2
    C1 : 4x1 + 3x2 <= fuel    (carburant)
    C2 : 2x1 + 4x2 <= fleet   (capacité flotte)
    C3 : 6x1 + 4x2 <= budget  (budget)
    C4 : x1 >= 2
    C5 : x2 >= 1
    C6 : 8x1 + 6x2 >= 50

    Retourne un dict avec la solution et les détails.
    """
    f  = fuel   or FUEL_LIMIT
    fl = fleet  or FLEET_LIMIT
    b  = budget or BUDGET_LIMIT

    # linprog minimise → négatif pour maximiser
    c     = [-8, -6]
    A_ub  = [
        [ 4,  3],   # C1 carburant
        [ 2,  4],   # C2 flotte
        [ 6,  4],   # C3 budget
        [-1,  0],   # C4 x1 >= 2  → -x1 <= -2
        [ 0, -1],   # C5 x2 >= 1  → -x2 <= -1
        [-8, -6],   # C6 Z >= 50  → -8x1-6x2 <= -50
    ]
    b_ub  = [f, fl, b, -MIN_MENAGER, -MIN_RECYCLABLE, -MIN_COLLECTE]
    bounds = [(0, None), (0, None)]

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if res.status != 0:
        return {"status": "infeasible", "message": res.message}

    x1_cont, x2_cont = res.x
    Z_cont = -res.fun

    # Ajustement entier : énumération des voisins
    best = None
    for dx1 in [0, 1]:
        for dx2 in [0, 1]:
            ix1 = int(x1_cont) + dx1
            ix2 = int(x2_cont) + dx2
            if _feasible_ch1(ix1, ix2, f, fl, b):
                Z = 8*ix1 + 6*ix2
                if best is None or Z > best["Z"]:
                    best = {"x1": ix1, "x2": ix2, "Z": Z}

    # Saturation des contraintes
    if best:
        saturation = {
            "C1": round((4*best["x1"] + 3*best["x2"]) / f  * 100, 1),
            "C2": round((2*best["x1"] + 4*best["x2"]) / fl * 100, 1),
            "C3": round((6*best["x1"] + 4*best["x2"]) / b  * 100, 1),
        }
    else:
        saturation = {}

    return {
        "status"          : "optimal",
        "method"          : "Méthode Graphique (scipy linprog)",
        "chapter"         : 1,
        "objective"       : "Max Z = 8x₁ + 6x₂",
        "continuous"      : {"x1": round(x1_cont, 4), "x2": round(x2_cont, 4),
                             "Z": round(Z_cont, 4)},
        "integer"         : best,
        "saturation_pct"  : saturation,
        "constraints_used": {"C1": f, "C2": fl, "C3": b},
    }


def _feasible_ch1(x1, x2, f, fl, b):
    return (
        4*x1 + 3*x2 <= f  and
        2*x1 + 4*x2 <= fl and
        6*x1 + 4*x2 <= b  and
        x1 >= MIN_MENAGER      and
        x2 >= MIN_RECYCLABLE   and
        8*x1 + 6*x2 >= MIN_COLLECTE
    )


# ── 2. Sommets de la région réalisable (pour graphe) ─────────
def get_vertices_ch1(f=48, fl=40, b=72):
    """
    Calcule les sommets de la région réalisable du Chapitre 1
    pour le tracé du graphique de la méthode graphique.
    """
    from itertools import combinations

    # Toutes les droites frontières sous forme Ax = b
    lines = [
        (np.array([4, 3]),  f),    # C1
        (np.array([2, 4]),  fl),   # C2
        (np.array([6, 4]),  b),    # C3
        (np.array([1, 0]),  2),    # C4 x1=2
        (np.array([0, 1]),  1),    # C5 x2=1
    ]

    vertices = []
    for (a1, b1), (a2, b2) in combinations(lines, 2):
        A = np.array([a1, a2], dtype=float)
        rhs = np.array([b1, b2], dtype=float)
        if abs(np.linalg.det(A)) < 1e-9:
            continue
        pt = np.linalg.solve(A, rhs)
        if pt[0] >= 0 and pt[1] >= 0 and _feasible_ch1(pt[0], pt[1], f, fl, b):
            vertices.append(tuple(np.round(pt, 6)))

    # Dédupliquer
    unique = list(dict.fromkeys(vertices))
    # Trier par angle pour tracer le polygone
    if unique:
        cx = sum(v[0] for v in unique) / len(unique)
        cy = sum(v[1] for v in unique) / len(unique)
        unique.sort(key=lambda v: np.arctan2(v[1]-cy, v[0]-cx))

    return unique


# ── 3. Graphique de la méthode graphique ─────────────────────
def plot_graphical_method(save_path=None):
    """
    Trace la région réalisable, les contraintes et la solution
    optimale du Chapitre 1. Retourne la figure matplotlib.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection

    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("#1E293B")
    ax.set_facecolor("#1E293B")
    for spine in ax.spines.values():
        spine.set_edgecolor("#475569")

    x = np.linspace(0, 18, 500)

    constraint_lines = [
        (lambda x: (48 - 4*x) / 3,  "#3B82F6", "C1: 4x₁+3x₂≤48 (Carburant)"),
        (lambda x: (40 - 2*x) / 4,  "#10B981", "C2: 2x₁+4x₂≤40 (Flotte)"),
        (lambda x: (72 - 6*x) / 4,  "#F59E0B", "C3: 6x₁+4x₂≤72 (Budget)"),
        (lambda x: np.full_like(x, 1), "#A78BFA", "C5: x₂≥1"),
    ]

    for fn, color, label in constraint_lines:
        y = fn(x)
        ax.plot(x, np.clip(y, 0, 20), color=color, lw=2, label=label)

    ax.axvline(x=2, color="#F472B6", lw=2, label="C4: x₁≥2")

    # Région réalisable
    verts = get_vertices_ch1()
    if len(verts) >= 3:
        poly = MplPolygon(verts, closed=True,
                          facecolor="#2E75B6", alpha=0.20,
                          edgecolor="#60A5FA", linewidth=1.5)
        ax.add_patch(poly)

    # Sommets + valeurs Z
    sol = solve_chapter1()
    best_x1, best_x2 = sol["integer"]["x1"], sol["integer"]["x2"]

    for vx, vy in verts:
        z_val = 8*vx + 6*vy
        ax.plot(vx, vy, 'o', color="#FBBF24", markersize=8, zorder=5)
        ax.annotate(f"({vx:.1f}, {vy:.1f})\nZ={z_val:.1f}",
                    xy=(vx, vy), xytext=(vx+0.3, vy+0.4),
                    fontsize=7.5, color="#E2E8F0",
                    arrowprops=dict(arrowstyle="->", color="#94A3B8", lw=0.8))

    # Solution optimale
    ax.plot(best_x1, best_x2, '*', color="#F43F5E", markersize=18,
            zorder=6, label=f"★ Optimal : x₁={best_x1}, x₂={best_x2}, Z={sol['integer']['Z']}")

    # Droite objectif Z=94
    zx = np.linspace(0, 12, 300)
    zy = (sol["integer"]["Z"] - 8*zx) / 6
    ax.plot(zx, zy, '--', color="#F43F5E", lw=1.5, alpha=0.6, label=f"Z={sol['integer']['Z']} (droite objectif)")

    ax.set_xlim(-0.5, 14)
    ax.set_ylim(-0.5, 14)
    ax.set_xlabel("x₁ (camions ménagers)", color="#CBD5E1", fontsize=11)
    ax.set_ylabel("x₂ (camions recyclables)", color="#CBD5E1", fontsize=11)
    ax.set_title("Chapitre 1 — Méthode Graphique\nRégion réalisable & Solution optimale",
                 color="#F1F5F9", fontsize=13, fontweight="bold", pad=14)
    ax.tick_params(colors="#94A3B8")
    ax.grid(True, color="#334155", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=8, facecolor="#1E293B",
              edgecolor="#475569", labelcolor="#E2E8F0")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


# ── 4. Export rapport texte ──────────────────────────────────
def rapport_chapter1():
    """Retourne un rapport texte formaté de la résolution Ch.1."""
    res = solve_chapter1()
    if res["status"] != "optimal":
        return f"Problème infaisable : {res['message']}"

    c = res["continuous"]
    i = res["integer"]
    s = res["saturation_pct"]
    lines = [
        "═" * 58,
        "  CHAPITRE 1 — Méthode Graphique",
        "  EMSI  |  Optimisation Gestion des Déchets 2025/2026",
        "═" * 58,
        "",
        "  Fonction objectif : Max Z = 8x₁ + 6x₂",
        "",
        "  Contraintes :",
        "    C1 : 4x₁ + 3x₂ ≤ 48   (Carburant)",
        "    C2 : 2x₁ + 4x₂ ≤ 40   (Capacité flotte)",
        "    C3 : 6x₁ + 4x₂ ≤ 72   (Budget)",
        "    C4 : x₁ ≥ 2            (Min ménagers)",
        "    C5 : x₂ ≥ 1            (Min recyclables)",
        "    C6 : 8x₁+6x₂ ≥ 50     (Min collecte)",
        "",
        f"  Solution continue : x₁={c['x1']}, x₂={c['x2']}, Z={c['Z']} t/j",
        "",
        f"  ★ Solution entière optimale :",
        f"      x₁ = {i['x1']}  (camions ménagers)",
        f"      x₂ = {i['x2']}  (camions recyclables)",
        f"      Z  = {i['Z']} tonnes/jour",
        "",
        "  Saturation des contraintes :",
        f"    C1 Carburant : {s.get('C1','?')}%",
        f"    C2 Flotte    : {s.get('C2','?')}%",
        f"    C3 Budget    : {s.get('C3','?')}%",
        "",
        "═" * 58,
    ]
    return "\n".join(lines)
