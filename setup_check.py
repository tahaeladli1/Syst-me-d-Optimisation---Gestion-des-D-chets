#!/usr/bin/env python3
# ============================================================
#  EMSI — Gestion des Déchets 2025/2026
#  setup_check.py  —  Vérification de l'environnement (Étape 1)
#  Lancer : python setup_check.py
# ============================================================

import sys
import os
import importlib
import platform
import json

# ── Couleurs ANSI pour le terminal ──────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner():
    print(f"""
{BLUE}{BOLD}╔══════════════════════════════════════════════════════════════╗
║     EMSI — Optimisation de la Gestion des Déchets 2025/2026  ║
║          ÉTAPE 1 : Vérification de l'Environnement           ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")

def check_python():
    print(f"{BOLD}[ Python ]{RESET}")
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 9):
        print(f"  {GREEN}✔  Python {version_str}{RESET}  (requis ≥ 3.9)")
    else:
        print(f"  {RED}✘  Python {version_str} — version trop ancienne ! Installez Python 3.9+{RESET}")
    print(f"  {CYAN}→  Plateforme : {platform.system()} {platform.machine()}{RESET}\n")
    return v >= (3, 9)

def check_libraries():
    print(f"{BOLD}[ Bibliothèques Python ]{RESET}")
    libs = [
        ("numpy",      "numpy",      "Calcul numérique & matrices"),
        ("scipy",      "scipy",      "Optimisation linéaire (linprog)"),
        ("matplotlib", "matplotlib", "Graphiques & visualisation"),
        ("pandas",     "pandas",     "Manipulation des données"),
        ("tkinter",    "tkinter",    "Interface graphique (GUI)"),
        ("PIL",        "Pillow",     "Traitement d'images"),
        ("flask",      "Flask",      "Dashboard web"),
        ("folium",     "folium",     "Cartographie interactive"),
        ("requests",   "requests",  "Requêtes HTTP / API IoT"),
        ("fractions",  "fractions",  "Arithmétique exacte (Simplexe)"),
        ("json",       "json",       "Lecture des données JSON"),
    ]
    results = {}
    for import_name, pip_name, description in libs:
        try:
            mod = importlib.import_module(import_name)
            ver = getattr(mod, "__version__", "✓")
            print(f"  {GREEN}✔  {pip_name:<15}{RESET} v{ver:<10} — {description}")
            results[pip_name] = True
        except ImportError:
            print(f"  {RED}✘  {pip_name:<15}{RESET} NON INSTALLÉ  — {description}")
            print(f"       {YELLOW}→  pip install {pip_name.lower()}{RESET}")
            results[pip_name] = False
    print()
    return results

def check_project_structure():
    print(f"{BOLD}[ Structure du Projet ]{RESET}")
    base = os.path.dirname(os.path.abspath(__file__))
    expected = [
        ("config/",            "Configuration globale"),
        ("config/settings.py", "Paramètres du projet"),
        ("modules/",           "Algorithmes d'optimisation"),
        ("ui/",                "Interfaces graphiques"),
        ("data/",              "Données & simulation"),
        ("data/sample_data.json", "Données de démonstration"),
        ("tests/",             "Tests unitaires"),
        ("assets/",            "Images & icônes"),
        ("requirements.txt",   "Dépendances Python"),
    ]
    all_ok = True
    for rel_path, description in expected:
        full_path = os.path.join(base, rel_path)
        if os.path.exists(full_path):
            print(f"  {GREEN}✔  {rel_path:<30}{RESET} — {description}")
        else:
            print(f"  {RED}✘  {rel_path:<30}{RESET} — {description}  {YELLOW}(manquant){RESET}")
            all_ok = False
    print()
    return all_ok

def check_config():
    print(f"{BOLD}[ Configuration (config/settings.py) ]{RESET}")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config.settings import (
            PROJECT_NAME, VERSION, FUEL_LIMIT, FLEET_LIMIT,
            BUDGET_LIMIT, COLORS, DEPOT_LAT, DEPOT_LNG
        )
        print(f"  {GREEN}✔  Projet      : {PROJECT_NAME} v{VERSION}{RESET}")
        print(f"  {GREEN}✔  Contraintes : C1={FUEL_LIMIT}  C2={FLEET_LIMIT}  C3={BUDGET_LIMIT}{RESET}")
        print(f"  {GREEN}✔  Dépôt       : lat={DEPOT_LAT}  lng={DEPOT_LNG} ({RESET}Marrakech{GREEN}){RESET}")
        print(f"  {GREEN}✔  Palette     : {len(COLORS)} couleurs définies{RESET}")
        print()
        return True
    except Exception as e:
        print(f"  {RED}✘  Erreur lors du chargement : {e}{RESET}\n")
        return False

def check_sample_data():
    print(f"{BOLD}[ Données de Simulation ]{RESET}")
    path = os.path.join(os.path.dirname(__file__), "data", "sample_data.json")
    try:
        with open(path) as f:
            data = json.load(f)
        ch1 = data["chapter1"]["optimal_solution"]
        ch2 = data["chapter2"]["integer_solution"]
        bins = data["simulation_bins"]
        print(f"  {GREEN}✔  Chapitre 1 — Solution : x1={ch1['x1']}, x2={ch1['x2']}, Z={ch1['Z']} t/j{RESET}")
        print(f"  {GREEN}✔  Chapitre 2 — Solution : x1={ch2['x1']}, x2={ch2['x2']}, x3={ch2['x3']}, Z={ch2['Z']} t/j{RESET}")
        print(f"  {GREEN}✔  Bennes simulées        : {len(bins)} conteneurs chargés{RESET}")
        urgent = [b for b in bins if b["fill_level"] >= 70]
        print(f"  {YELLOW}⚠  Bennes urgentes (≥70%): {len(urgent)}{RESET}")
        print()
        return True
    except Exception as e:
        print(f"  {RED}✘  Erreur : {e}{RESET}\n")
        return False

def print_summary(python_ok, libs, struct_ok, config_ok, data_ok):
    missing_libs = [k for k, v in libs.items() if not v]
    total = 5
    passed = sum([python_ok, all(libs.values()), struct_ok, config_ok, data_ok])

    print(f"{BOLD}{'═'*64}{RESET}")
    print(f"{BOLD}  RÉSUMÉ DE L'ÉTAPE 1{RESET}")
    print(f"{BOLD}{'═'*64}{RESET}")
    score_color = GREEN if passed == total else (YELLOW if passed >= 3 else RED)
    print(f"  Score : {score_color}{BOLD}{passed}/{total}{RESET} vérifications réussies\n")

    if missing_libs:
        print(f"  {YELLOW}⚠  Bibliothèques manquantes :{RESET}")
        print(f"     {CYAN}pip install {' '.join(missing_libs).lower()}{RESET}\n")

    if passed == total:
        print(f"  {GREEN}{BOLD}✔  ÉTAPE 1 COMPLÈTE — Prêt pour l'Étape 2 !{RESET}")
        print(f"  {CYAN}   Prochain : python main.py  (ou  python main.py --mode cli){RESET}")
    else:
        print(f"  {YELLOW}  Corrigez les erreurs ci-dessus puis relancez : python setup_check.py{RESET}")
    print(f"\n{BOLD}{'═'*64}{RESET}\n")

def main():
    banner()
    python_ok = check_python()
    libs      = check_libraries()
    struct_ok = check_project_structure()
    config_ok = check_config()
    data_ok   = check_sample_data()
    print_summary(python_ok, libs, struct_ok, config_ok, data_ok)

if __name__ == "__main__":
    main()
