#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  etape2_demo.py  —  Démonstration complète de l'ÉTAPE 2
#  Lancer : python etape2_demo.py
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")   # Sans interface graphique (serveur/CI)
import matplotlib.pyplot as plt

# ── Couleurs terminal ────────────────────────────────────────
B  = "\033[1m"
G  = "\033[92m"
R  = "\033[91m"
Y  = "\033[93m"
C  = "\033[96m"
BL = "\033[94m"
RE = "\033[0m"

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def banner():
    print(f"""
{BL}{B}╔══════════════════════════════════════════════════════════════════╗
║   EMSI — Gestion des Déchets 2025/2026                          ║
║   ÉTAPE 2 : Algorithmes d'Optimisation (LP + Simplexe)          ║
╚══════════════════════════════════════════════════════════════════╝{RE}
""")


# ────────────────────────────────────────────────────────────
#  Bloc 1 : Chapitre 1 — Méthode Graphique
# ────────────────────────────────────────────────────────────
def run_chapter1():
    from modules.linear_prog import solve_chapter1, rapport_chapter1, get_vertices_ch1

    print(f"{B}{'━'*66}{RE}")
    print(f"{B}  📊 CHAPITRE 1 — Programmation Linéaire / Méthode Graphique{RE}")
    print(f"{B}{'━'*66}{RE}\n")

    print(f"  Problème : {C}Max Z = 8x₁ + 6x₂{RE}")
    print(f"  Contraintes :")
    constraints = [
        ("C1", "4x₁ + 3x₂ ≤ 48", "Carburant disponible"),
        ("C2", "2x₁ + 4x₂ ≤ 40", "Capacité de la flotte"),
        ("C3", "6x₁ + 4x₂ ≤ 72", "Budget quotidien"),
        ("C4", "x₁ ≥ 2",          "Min camions ménagers"),
        ("C5", "x₂ ≥ 1",          "Min camions recyclables"),
        ("C6", "8x₁+6x₂ ≥ 50",   "Quantité minimale collecte"),
    ]
    for code, expr, desc in constraints:
        print(f"    {Y}{code}{RE}  {expr:<25} ← {desc}")

    print(f"\n  {C}→ Résolution via scipy.optimize.linprog (méthode HiGHS)...{RE}")
    res = solve_chapter1()
    c = res["continuous"]
    i = res["integer"]
    s = res["saturation_pct"]

    print(f"\n  Solution continue  : x₁ = {c['x1']:.4f},  x₂ = {c['x2']:.4f},  Z = {c['Z']:.2f} t/j")
    print(f"  {G}{B}★ Solution entière : x₁ = {i['x1']},  x₂ = {i['x2']},  Z = {i['Z']} t/jour{RE}")
    print(f"\n  Saturation des contraintes :")

    for k, v in s.items():
        bar_len = int(v / 5)
        bar_color = R if v >= 100 else Y if v >= 90 else G
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"    {k}  [{bar_color}{bar}{RE}]  {v:5.1f}%")

    # Sommets
    verts = get_vertices_ch1()
    print(f"\n  Sommets de la région réalisable ({len(verts)} points) :")
    for vx, vy in verts:
        z_v = 8*vx + 6*vy
        marker = f"  {G}★ OPTIMAL{RE}" if (round(vx)==i['x1'] and round(vy)==i['x2']) else ""
        print(f"    ({vx:.2f}, {vy:.2f})  →  Z = {z_v:.2f}{marker}")

    # Graphique
    print(f"\n  {C}→ Génération du graphique de la région réalisable...{RE}")
    from modules.linear_prog import plot_graphical_method
    fig = plot_graphical_method(save_path=os.path.join(EXPORT_DIR, "ch1_methode_graphique.png"))
    plt.close(fig)
    print(f"  {G}✔  exports/ch1_methode_graphique.png{RE}")


# ────────────────────────────────────────────────────────────
#  Bloc 2 : Chapitre 2 — Méthode du Simplexe
# ────────────────────────────────────────────────────────────
def run_chapter2():
    from modules.simplex import Simplex, rapport_chapter2, plot_simplex_iterations, plot_constraints_saturation

    print(f"\n{B}{'━'*66}{RE}")
    print(f"{B}  🔢 CHAPITRE 2 — Méthode du Simplexe (arithmétique exacte){RE}")
    print(f"{B}{'━'*66}{RE}\n")

    print(f"  Problème : {C}Max Z = 8x₁ + 7x₂ + 11x₃{RE}")
    print(f"  Contraintes :")
    constraints2 = [
        ("C1", "4x₁ + 3x₂ + 5x₃ ≤ 48", "Carburant"),
        ("C2", "2x₁ + 4x₂ + 3x₃ ≤ 40", "Temps opérationnel"),
        ("C3", "6x₁ + 4x₂ + 8x₃ ≤ 72", "Budget"),
    ]
    for code, expr, desc in constraints2:
        print(f"    {Y}{code}{RE}  {expr:<30} ← {desc}")

    print(f"\n  {C}→ Lancement du Simplexe (fractions exactes)...{RE}\n")

    solver = Simplex()
    res    = solver.solve()

    # Affichage de chaque tableau
    for snap in res["iterations"]:
        print(f"  ┌─ {snap['title']} — Z = {snap['z_value']:.4f} ─┐")
        header = f"  │  {'Base':<5}" + "".join(f"{n:>12}" for n in Simplex.VAR_NAMES) + f"{'b':>12}  │"
        print(header)
        print(f"  │{'─'*(len(header)-4)}│")
        bases = snap["basis"] + ["Z"]
        for base, row in zip(bases, snap["rows"]):
            vals = "".join(f"{v:>12}" for v in row)
            print(f"  │  {base:<5}{vals}  │")
        print(f"  └{'─'*(len(header)-4)}┘\n")

    c   = res["continuous"]
    i   = res["integer"]
    sat = i["saturation"]

    print(f"  Solution continue :")
    print(f"    x₁ = {c['x1']:<12}  ({c['x1_float']:.4f})")
    print(f"    x₂ = {c['x2']:<12}  ({c['x2_float']:.4f})")
    print(f"    x₃ = {c['x3']:<12}  ({c['x3_float']:.4f})")
    print(f"    Z  = {c['Z']:<12}  ({c['Z_float']:.4f} t/jour)")

    print(f"\n  Variables d'écart :")
    for k, v in res["slack"].items():
        status = f"  {R}[CONTRAINTE SATURÉE]{RE}" if v == "0" else ""
        print(f"    {k} = {v}{status}")

    print(f"\n  {G}{B}★ Solution entière optimale :{RE}")
    print(f"    x₁ = {G}{i['x1']}{RE}  camions ménagers    (+{8*i['x1']} t/j)")
    print(f"    x₂ = {G}{i['x2']}{RE}  camions recyclables (+{7*i['x2']} t/j)")
    print(f"    x₃ = {G}{i['x3']}{RE}  camions biomédicaux (+{11*i['x3']} t/j)")
    print(f"    {B}Z  = {G}{i['Z']}{RE}{B} tonnes / jour{RE}")

    print(f"\n  Saturation des contraintes :")
    for k, v in sat.items():
        bar_len = int(v / 5)
        bar_color = R if v >= 100 else Y if v >= 90 else G
        bar = "█" * bar_len + "░" * (20 - bar_len)
        status = f"  {R}[SATURÉE]{RE}" if v >= 100 else ""
        print(f"    {k}  [{bar_color}{bar}{RE}]  {v:5.1f}%{status}")

    # Graphiques
    print(f"\n  {C}→ Génération des graphiques du Simplexe...{RE}")
    fig2 = plot_simplex_iterations(save_path=os.path.join(EXPORT_DIR, "ch2_simplex_iterations.png"))
    plt.close(fig2)
    print(f"  {G}✔  exports/ch2_simplex_iterations.png{RE}")

    fig3 = plot_constraints_saturation(save_path=os.path.join(EXPORT_DIR, "ch2_saturation.png"))
    plt.close(fig3)
    print(f"  {G}✔  exports/ch2_saturation.png{RE}")


# ────────────────────────────────────────────────────────────
#  Bloc 3 : Dashboard global + Comparaison
# ────────────────────────────────────────────────────────────
def run_dashboard():
    from modules.visualisation import plot_dashboard_etape2, plot_comparison

    print(f"\n{B}{'━'*66}{RE}")
    print(f"{B}  📈 DASHBOARD COMPLET — Étape 2{RE}")
    print(f"{B}{'━'*66}{RE}\n")

    print(f"  {C}→ Génération du dashboard 4-graphiques...{RE}")
    fig = plot_dashboard_etape2(save_path=os.path.join(EXPORT_DIR, "dashboard_etape2.png"))
    plt.close(fig)
    print(f"  {G}✔  exports/dashboard_etape2.png{RE}")

    print(f"  {C}→ Graphique comparatif Ch.1 vs Ch.2...{RE}")
    fig2 = plot_comparison(save_path=os.path.join(EXPORT_DIR, "comparaison_ch1_ch2.png"))
    plt.close(fig2)
    print(f"  {G}✔  exports/comparaison_ch1_ch2.png{RE}")


# ────────────────────────────────────────────────────────────
#  Bloc 4 : Résumé comparatif final
# ────────────────────────────────────────────────────────────
def run_summary():
    from modules.linear_prog import solve_chapter1
    from modules.simplex import simplex_chapter2

    r1 = solve_chapter1()
    r2 = simplex_chapter2()
    i1 = r1["integer"]
    i2 = r2["integer"]
    gain = round((i2["Z"] - i1["Z"]) / i1["Z"] * 100, 1)

    print(f"\n{B}{'═'*66}{RE}")
    print(f"{B}  RÉSUMÉ COMPARATIF — ÉTAPE 2 COMPLÈTE{RE}")
    print(f"{B}{'═'*66}{RE}")
    print(f"""
  ┌─────────────────────┬──────────────────┬──────────────────┐
  │ Indicateur          │   Chapitre 1     │   Chapitre 2     │
  ├─────────────────────┼──────────────────┼──────────────────┤
  │ Méthode             │ Graphique        │ Simplexe         │
  │ Variables           │ 2  (x₁, x₂)     │ 3  (x₁, x₂, x₃) │
  │ Contraintes         │ 6                │ 3                │
  │ Itérations          │ —                │ {r2["n_iterations"]}                │
  │ x₁ (ménagers)       │ {i1["x1"]:<16} │ {i2["x1"]:<16} │
  │ x₂ (recyclables)    │ {i1["x2"]:<16} │ {i2["x2"]:<16} │
  │ x₃ (biomédicaux)    │ —                │ {i2["x3"]:<16} │
  │ Z (t/jour)          │ {G}{B}{i1["Z"]:<16}{RE} │ {G}{B}{i2["Z"]:<16}{RE} │
  │ Gain                │ référence        │ {Y}+{gain}%{RE}            │
  └─────────────────────┴──────────────────┴──────────────────┘
""")

    print(f"  Graphiques générés dans : {C}./exports/{RE}")
    files = [
        "ch1_methode_graphique.png",
        "ch2_simplex_iterations.png",
        "ch2_saturation.png",
        "dashboard_etape2.png",
        "comparaison_ch1_ch2.png",
    ]
    for f in files:
        path = os.path.join(EXPORT_DIR, f)
        status = f"{G}✔{RE}" if os.path.exists(path) else f"{R}✘{RE}"
        print(f"    {status}  {f}")

    print(f"\n  {G}{B}✔  ÉTAPE 2 VALIDÉE — Prêt pour l'Étape 3 (IoT){RE}")
    print(f"     {C}→ python main.py --mode cli{RE}\n")


# ────────────────────────────────────────────────────────────
def main():
    banner()
    run_chapter1()
    run_chapter2()
    run_dashboard()
    run_summary()

if __name__ == "__main__":
    main()
