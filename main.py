#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  main.py  —  Point d'entrée principal
#  Usage :
#    python main.py              → Lance la GUI (Étape 5)
#    python main.py --mode cli   → Terminal (Étape 1 demo)
#    python main.py --mode info  → Affiche la configuration
# ============================================================

import argparse
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Couleurs ANSI ────────────────────────────────────────────
B  = "\033[1m"
G  = "\033[92m"
R  = "\033[91m"
Y  = "\033[93m"
C  = "\033[96m"
BL = "\033[94m"
RE = "\033[0m"

# ────────────────────────────────────────────────────────────
def mode_info():
    """Affiche toute la configuration du projet."""
    from config.settings import (
        PROJECT_NAME, VERSION, SCHOOL, ACADEMIC_YEAR, AUTHORS,
        FUEL_LIMIT, FLEET_LIMIT, BUDGET_LIMIT,
        COEF_X1, COEF_X2, COEF_X3,
        TRUCK_CONSTRAINTS, DEFAULT_CITY, DEPOT_LAT, DEPOT_LNG,
        BASE_DIR
    )
    print(f"""
{BL}{B}╔══════════════════════════════════════════════════════════╗
║       {PROJECT_NAME}       ║
║              Version {VERSION}  —  {SCHOOL}  {ACADEMIC_YEAR}             ║
╚══════════════════════════════════════════════════════════╝{RE}

{B}━━ Équipe ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RE}
  {C}{'  ·  '.join(AUTHORS)}{RE}

{B}━━ Modèle Linéaire ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RE}
  Fonction objectif : {G}Z = {COEF_X1}x₁ + {COEF_X2}x₂ + {COEF_X3}x₃  (t/jour){RE}
  C1 Carburant   ≤  {FUEL_LIMIT} unités/jour
  C2 Temps flotte ≤  {FLEET_LIMIT} heures/jour
  C3 Budget       ≤  {BUDGET_LIMIT} 000 DHS/jour

{B}━━ Camions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RE}""")
    for t, c in TRUCK_CONSTRAINTS.items():
        print(f"  {Y}{t:<12}{RE}  carburant={c['fuel']}  temps={c['fleet']}  budget={c['budget']}")

    print(f"""
{B}━━ Localisation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RE}
  Ville : {DEFAULT_CITY}  |  Dépôt : lat={DEPOT_LAT}, lng={DEPOT_LNG}

{B}━━ Répertoire du projet ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RE}
  {BASE_DIR}
""")

# ────────────────────────────────────────────────────────────
def mode_cli():
    """Mode terminal : démo Étape 1 — chargement et affichage des données."""
    from config.settings import PROJECT_NAME, COLORS

    print(f"\n{BL}{B}══ {PROJECT_NAME} — Mode CLI ══{RE}\n")

    # Charger les données de simulation
    data_path = os.path.join(os.path.dirname(__file__), "data", "sample_data.json")
    try:
        with open(data_path) as f:
            data = json.load(f)
        print(f"{G}✔  Données chargées depuis data/sample_data.json{RE}")
    except FileNotFoundError:
        print(f"{R}✘  Fichier sample_data.json introuvable. Lancez d'abord setup_check.py{RE}")
        sys.exit(1)

    # ── Afficher la configuration des deux chapitres ─────────
    print(f"\n{B}━━ CHAPITRE 1 — Méthode Graphique ━━━━━━━━━━━━━━━━━━━━━━{RE}")
    ch1 = data["chapter1"]
    print(f"  Objectif : {C}{ch1['objective']}{RE}")
    print(f"  Contraintes :")
    for k, v in ch1["constraints"].items():
        print(f"    {Y}{k}{RE}  {v['expr']:<25}  ← {v['desc']}")
    sol = ch1["optimal_solution"]
    print(f"  {G}{B}★  Solution optimale : x₁={sol['x1']}, x₂={sol['x2']}, Z={sol['Z']} t/jour{RE}")

    print(f"\n{B}━━ CHAPITRE 2 — Méthode du Simplexe ━━━━━━━━━━━━━━━━━━━{RE}")
    ch2 = data["chapter2"]
    print(f"  Objectif : {C}{ch2['objective']}{RE}")
    print(f"  Contraintes :")
    for k, v in ch2["constraints"].items():
        print(f"    {Y}{k}{RE}  {v['expr']:<30}  ← {v['desc']}")
    csol = ch2["continuous_solution"]
    isol = ch2["integer_solution"]
    print(f"  Solution continue : x₁={csol['x1']}, x₂={csol['x2']}, x₃={csol['x3']}, Z={csol['Z']} t/j")
    print(f"  {G}{B}★  Solution entière  : x₁={isol['x1']}, x₂={isol['x2']}, x₃={isol['x3']}, Z={isol['Z']} t/jour{RE}")

    # ── Afficher l'état des bennes ───────────────────────────
    print(f"\n{B}━━ BENNES DE SIMULATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RE}")
    bins = data["simulation_bins"]
    print(f"  {'ID':<10} {'Type':<12} {'Niveau':>8}  {'Statut'}")
    print(f"  {'─'*50}")
    for b in sorted(bins, key=lambda x: -x["fill_level"]):
        fl = b["fill_level"]
        if fl >= 80:
            status = f"{R}🔴 URGENT{RE}"
        elif fl >= 60:
            status = f"{Y}🟡 Attention{RE}"
        else:
            status = f"{G}🟢 Normal{RE}"
        print(f"  {b['bin_id']:<10} {b['type']:<12} {fl:>6}%   {status}")

    urgent = [b for b in bins if b["fill_level"] >= 70]
    print(f"\n  {Y}⚠  {len(urgent)} benne(s) nécessitent une collecte urgente (≥ 70%){RE}")
    print(f"\n{C}  Prochaine étape → python main.py --mode gui  (Étape 5){RE}\n")

# ────────────────────────────────────────────────────────────
def mode_gui():
    """Lance l'interface graphique Tkinter (Étape 5 — disponible après étape 2-4)."""
    try:
        from ui.dashboard import WasteManagementApp
        import tkinter as tk
        root = tk.Tk()
        app = WasteManagementApp(root)
        root.mainloop()
    except ImportError as e:
        print(f"\n{Y}⚠  L'interface GUI sera disponible après l'Étape 5.{RE}")
        print(f"   Erreur : {e}")
        print(f"\n{C}→  Pour l'instant, lancez : python main.py --mode cli{RE}\n")
        mode_cli()

# ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="EMSI — Gestion des Déchets — Système d'Optimisation 2025/2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes disponibles :
  gui   → Interface graphique Tkinter  (Étape 5)
  cli   → Mode terminal de démonstration (disponible maintenant)
  info  → Afficher toute la configuration du projet

Exemples :
  python main.py
  python main.py --mode cli
  python main.py --mode info
        """
    )
    parser.add_argument("--mode", choices=["gui", "cli", "info"], default="cli",
                        help="Mode de lancement (défaut: cli)")
    args = parser.parse_args()

    dispatch = {"gui": mode_gui, "cli": mode_cli, "info": mode_info}
    dispatch[args.mode]()

if __name__ == "__main__":
    main()
