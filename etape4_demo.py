#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  etape4_demo.py  —  Démonstration complète ÉTAPE 4
#  Optimisation Dynamique des Routes de Collecte
#  Inspiré de : jtsimoes/smart-city-waste-management
#  Lancer : python etape4_demo.py
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B  = "\033[1m";  G  = "\033[92m";  R  = "\033[91m"
Y  = "\033[93m"; C  = "\033[96m";  BL = "\033[94m"; RE = "\033[0m"
M  = "\033[95m"

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def banner():
    print(f"""
{BL}{B}╔══════════════════════════════════════════════════════════════════╗
║   EMSI — Gestion des Déchets 2025/2026                          ║
║   ÉTAPE 4 : Optimisation Dynamique des Routes de Collecte       ║
║   Algorithmes : Nearest Neighbor · Cheapest Insertion · 2-Opt   ║
║   Inspiré de  : jtsimoes/smart-city-waste-management            ║
╚══════════════════════════════════════════════════════════════════╝{RE}
""")


# ────────────────────────────────────────────────────────────
#  BLOC 1 : Algorithmes de routage — démo sur un seul groupe
# ────────────────────────────────────────────────────────────
def run_bloc1_algorithms(manager):
    from modules.route_optimizer import RouteOptimizer

    print(f"{B}{'━'*68}{RE}")
    print(f"{B}  🔢 BLOC 1 — Algorithmes TSP (sur 12 bennes urgentes){RE}")
    print(f"{B}{'━'*68}{RE}\n")

    urgent, attention, _ = manager.prioritize_bins()
    sample = (urgent + attention)[:12]

    print(f"  Bennes sélectionnées : {len(sample)}")
    print(f"  {'ID':<16} {'Type':<12} {'Niveau':>8}  Location")
    print(f"  {'─'*55}")
    for b in sample:
        print(f"  {b['bin_id']:<16} {b['waste_type']:<12} {b['fill_level']:>7.1f}%  "
              f"[{b['location'][0]:.4f}, {b['location'][1]:.4f}]")

    optimizer = RouteOptimizer()
    methods   = [
        ("nearest_neighbor",   "Nearest Neighbor (glouton)"),
        ("cheapest_insertion", "Cheapest Insertion (constructif)"),
        ("two_opt",            "2-Opt (amélioration locale)"),
    ]

    print(f"\n  {'Algorithme':<30} {'Distance':>10}  {'Durée':>8}  {'Gain':>8}  {'Temps calc.':>11}")
    print(f"  {'─'*68}")

    best_dist = float("inf")
    results   = {}
    for key, label in methods:
        res = optimizer.optimize_route(sample, method=key)
        results[key] = res
        gain_str = f"{res['gain_pct']:.1f}%" if key != "nearest_neighbor" else "réf."
        dist_color = G if res["distance_km"] < best_dist else RE
        best_dist  = min(best_dist, res["distance_km"])
        print(f"  {label:<30} {dist_color}{res['distance_km']:>8.3f} km{RE}  "
              f"{res['duration_min']:>6.1f} min  {Y}{gain_str:>7}{RE}  "
              f"{res['compute_ms']:>8.1f} ms")

    # Détail de la meilleure route (2-opt)
    best = results["two_opt"]
    print(f"\n  {G}{B}★ Meilleure route — 2-Opt : {best['distance_km']} km "
          f"({best['n_improvements']} amélioration(s)){RE}")
    print(f"\n  Séquence : {C}DÉPÔT{RE}", end="")
    for stop in best["route"][1:-1]:
        fill_c = R if stop.get("fill_level", 0) >= 90 else Y if stop.get("fill_level",0) >= 70 else G
        print(f" → {fill_c}{stop['bin_id'].split('_')[1]}{RE}", end="")
    print(f" → {C}DÉPÔT{RE}\n")

    return results


# ────────────────────────────────────────────────────────────
#  BLOC 2 : Plan complet de la flotte (LP × IoT)
# ────────────────────────────────────────────────────────────
def run_bloc2_fleet(manager):
    from modules.route_optimizer import FleetPlanner
    from modules.simplex import simplex_chapter2

    print(f"{B}{'━'*68}{RE}")
    print(f"{B}  🚛 BLOC 2 — Plan Complet de la Flotte (LP + IoT){RE}")
    print(f"{B}{'━'*68}{RE}\n")

    sol = simplex_chapter2()["integer"]
    print(f"  Solution LP (Simplexe Ch.2) :")
    print(f"    {G}x₁={sol['x1']} camions ménagers{RE}     (coeff objectif = 8,  +{8*sol['x1']} t/j)")
    print(f"    {G}x₂={sol['x2']} camions recyclables{RE}  (coeff objectif = 7,  +{7*sol['x2']} t/j)")
    print(f"    {G}x₃={sol['x3']} camions biomédicaux{RE}  (coeff objectif = 11, +{11*sol['x3']} t/j)")
    print(f"    {B}Z  = {G}{sol['Z']} t/jour{RE}\n")

    print(f"  {C}→ Calcul du plan de tournées (2-Opt)...{RE}")
    planner = FleetPlanner(sol, manager)
    plan    = planner.plan(method="two_opt")
    s       = plan["summary"]

    print(f"\n  {'TYPE':<12}  {'CAMION':<18}  {'BENNES':>7}  {'KM':>8}  {'KG':>8}  {'CHARGE':>7}  {'FUEL':>7}")
    print(f"  {'─'*72}")

    type_icons = {"menager": "🔵", "recyclable": "♻️ ", "biomedical": "🟠"}

    for wtype, trucks in plan["trucks"].items():
        icon = type_icons.get(wtype, "🚛")
        for t in trucks:
            charge_c = R if t["load_pct"] >= 90 else Y if t["load_pct"] >= 70 else G
            print(f"  {icon} {wtype:<10}  {t['truck_id']:<18}  {t['n_bins']:>6}  "
                  f"{t['distance_km']:>7.2f}  {t['weight_kg']:>7.0f}  "
                  f"{charge_c}{t['load_pct']:>6.0f}%{RE}  {t['fuel_L']:>6.1f}L")

    print(f"\n  {'─'*72}")
    print(f"  {B}TOTAL{RE}                              "
          f"  {s['total_bins']:>6}  "
          f"{G}{s['total_distance']:>7.2f}{RE}  "
          f"{G}{s['total_weight_kg']:>7.0f}{RE}  "
          f"         {Y}{s['total_fuel_L']:>6.1f}L{RE}")
    print(f"\n  {B}Résumé :{RE} {s['total_trucks']} camions · "
          f"{s['total_bins']} bennes · "
          f"{s['total_distance']:.2f} km total · "
          f"{s['total_fuel_L']:.1f} L carburant")

    return plan


# ────────────────────────────────────────────────────────────
#  BLOC 3 : Analyse de performance 2-Opt
# ────────────────────────────────────────────────────────────
def run_bloc3_performance(plan):
    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  📐 BLOC 3 — Analyse Performance 2-Opt vs Nearest Neighbor{RE}")
    print(f"{B}{'━'*68}{RE}\n")

    all_trucks  = []
    for trucks in plan["trucks"].values():
        all_trucks.extend(trucks)

    total_nn  = sum(t.get("distance_nn_km", t["distance_km"]) for t in all_trucks)
    total_opt = sum(t["distance_km"] for t in all_trucks)
    global_gain = (total_nn - total_opt) / total_nn * 100 if total_nn > 0 else 0

    print(f"  {'CAMION':<20}  {'NN (km)':>9}  {'2-Opt (km)':>11}  {'Gain':>8}  {'Amélioration(s)':>16}")
    print(f"  {'─'*68}")
    for t in all_trucks:
        nn_d   = t.get("distance_nn_km", t["distance_km"])
        opt_d  = t["distance_km"]
        gain   = t.get("gain_pct", 0)
        n_imp  = t.get("n_improvements", 0)
        g_c    = G if gain > 2 else Y if gain > 0 else RE
        print(f"  {t['truck_id']:<20}  {nn_d:>8.3f}   {opt_d:>10.3f}  "
              f"{g_c}{gain:>7.1f}%{RE}  {n_imp:>16}")

    print(f"  {'─'*68}")
    g_c = G if global_gain > 2 else Y
    print(f"  {'TOTAL':<20}  {total_nn:>8.3f}   {total_opt:>10.3f}  "
          f"{g_c}{B}{global_gain:>7.1f}%{RE}\n")
    print(f"  {G}★ Gain global 2-Opt vs NN : {global_gain:.1f}% "
          f"({total_nn-total_opt:.2f} km économisés){RE}")


# ────────────────────────────────────────────────────────────
#  BLOC 4 : Simulation d'une collecte complète
# ────────────────────────────────────────────────────────────
def run_bloc4_simulation(manager, plan):
    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  ▶️  BLOC 4 — Simulation Collecte Complète (avec MAJ IoT){RE}")
    print(f"{B}{'━'*68}{RE}\n")

    from modules.iot_analytics import AlertSystem

    alert_sys = AlertSystem()
    alert_sys.check_and_generate(manager.get_all_bins())
    before_summ = alert_sys.summary

    print(f"  Avant collecte : {R}{before_summ['critical']} CRITICAL{RE}  "
          f"{Y}{before_summ['urgent']} URGENT{RE}  "
          f"\033[33m{before_summ['warning']} WARNING{RE}\n")

    collected_total = []
    for wtype, trucks in plan["trucks"].items():
        for t in trucks:
            bin_ids = [s["to_id"] for s in t["stops"]
                       if s["to_id"] != "DEPOT" and s["to_id"] in manager.sensors]
            if bin_ids:
                result = manager.simulate_collection(bin_ids)
                collected_total.extend(result)
                total_kg = sum(r["collected_kg"] for r in result)
                print(f"  {type_icons_local(wtype)} {t['truck_id']:<20} "
                      f"→ {len(result)} bennes vidées  |  {G}{total_kg:.0f} kg collectés{RE}")

    # Nouvelles alertes après collecte
    alert_sys2 = AlertSystem()
    alert_sys2.check_and_generate(manager.get_all_bins())
    after_summ = alert_sys2.summary

    print(f"\n  Après collecte  : {R}{after_summ['critical']} CRITICAL{RE}  "
          f"{Y}{after_summ['urgent']} URGENT{RE}  "
          f"\033[33m{after_summ['warning']} WARNING{RE}")

    total_kg_sim = sum(r["collected_kg"] for r in collected_total)
    print(f"\n  {G}{B}✔ Collecte simulée : {len(collected_total)} bennes · "
          f"{total_kg_sim:.0f} kg collectés{RE}")


def type_icons_local(wtype):
    return {"menager": "🔵", "recyclable": "♻️ ", "biomedical": "🟠"}.get(wtype, "🚛")


# ────────────────────────────────────────────────────────────
#  BLOC 5 : Génération des visualisations
# ────────────────────────────────────────────────────────────
def run_bloc5_visualisations(manager, plan, algo_results):
    from modules.route_visualisation import (
        plot_routes_map, plot_fleet_dashboard,
        plot_algorithm_comparison, plot_single_truck_route,
    )

    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  📊 BLOC 5 — Génération des Visualisations{RE}")
    print(f"{B}{'━'*68}{RE}\n")

    charts = [
        ("Carte des tournées...",           "route_map.png",
         lambda: plot_routes_map(plan)),
        ("Dashboard métriques flotte...",   "route_fleet_dashboard.png",
         lambda: plot_fleet_dashboard(plan)),
        ("Comparaison algorithmes...",      "route_algo_comparison.png",
         lambda: plot_algorithm_comparison(manager)),
    ]

    for label, fname, fn in charts:
        print(f"  {C}→ {label}{RE}")
        try:
            fig = fn()
            path = os.path.join(EXPORT_DIR, fname)
            if fig:
                fig.savefig(path, dpi=150, bbox_inches="tight",
                            facecolor="#1E293B")
                plt.close(fig)
                print(f"  {G}✔  exports/{fname}{RE}")
        except Exception as e:
            print(f"  {Y}⚠  {fname} : {e}{RE}")

    # Tournée la plus chargée
    all_trucks = [t for tl in plan["trucks"].values() for t in tl]
    if all_trucks:
        best_truck = max(all_trucks, key=lambda t: t["n_bins"])
        print(f"  {C}→ Détail tournée : {best_truck['truck_id']}...{RE}")
        try:
            fig = plot_single_truck_route(best_truck)
            path = os.path.join(EXPORT_DIR, "route_single_truck.png")
            fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#1E293B")
            plt.close(fig)
            print(f"  {G}✔  exports/route_single_truck.png{RE}")
        except Exception as e:
            print(f"  {Y}⚠  route_single_truck.png : {e}{RE}")


# ────────────────────────────────────────────────────────────
#  RÉSUMÉ FINAL
# ────────────────────────────────────────────────────────────
def run_summary(plan, manager):
    from modules.route_optimizer import RouteOptimizer
    from modules.iot_sensors import CITY_ZONES

    s = plan["summary"]
    urgent, attention, _ = manager.prioritize_bins()

    all_trucks = [t for tl in plan["trucks"].values() for t in tl]
    avg_gain   = sum(t.get("gain_pct",0) for t in all_trucks) / max(1,len(all_trucks))

    print(f"\n{B}{'═'*68}{RE}")
    print(f"{B}  RÉSUMÉ — ÉTAPE 4 COMPLÈTE{RE}")
    print(f"{B}{'═'*68}{RE}")
    print(f"""
  ┌──────────────────────────────────────────────────────────────┐
  │  Solution LP     │  x₁=2 · x₂=5 · x₃=5  →  Z=106 t/jour     │
  │  Camions déployés│  {s['total_trucks']:<10} sur 3 types de déchets        │
  │  Bennes collectées│  {s['total_bins']:<10} bennes urgentes/attention     │
  │  Distance totale │  {s['total_distance']:<8.2f} km                             │
  │  Carburant       │  {s['total_fuel_L']:<8.1f} L  (~25 L/100 km)             │
  │  Poids collecté  │  {s['total_weight_kg']:<8.0f} kg                            │
  │  Gain 2-Opt moy  │  {avg_gain:<8.1f}% vs Nearest Neighbor              │
  └──────────────────────────────────────────────────────────────┘
""")

    exports = [
        "route_map.png",
        "route_fleet_dashboard.png",
        "route_algo_comparison.png",
        "route_single_truck.png",
    ]
    print(f"  Graphiques générés dans {C}./exports/{RE} :")
    for f in exports:
        path   = os.path.join(EXPORT_DIR, f)
        status = f"{G}✔{RE}" if os.path.exists(path) else f"{Y}—{RE}"
        print(f"    {status}  {f}")

    print(f"\n  Étapes complétées :")
    for n, label, ok in [
        (1, "Configuration & Structure",           True),
        (2, "Algorithmes LP + Simplexe",           True),
        (3, "Intégration IoT & Données Temps Réel",True),
        (4, "Optimisation Dynamique des Routes",   True),
        (5, "Interface GUI & Dashboard Web",       False),
    ]:
        icon = f"{G}✅{RE}" if ok else f"{Y}🔜{RE}"
        print(f"    {icon}  Étape {n} — {label}")

    print(f"\n  {G}{B}✔  ÉTAPE 4 VALIDÉE — Prêt pour l'Étape 5 (Interface GUI){RE}")
    print(f"     {C}→ python etape5_demo.py{RE}\n")


# ────────────────────────────────────────────────────────────
def main():
    from modules.iot_sensors import IoTSensorManager

    banner()

    print(f"  {C}→ Initialisation du réseau IoT...{RE}")
    manager = IoTSensorManager()
    print()

    algo_results = run_bloc1_algorithms(manager)
    plan         = run_bloc2_fleet(manager)
    run_bloc3_performance(plan)
    run_bloc4_simulation(manager, plan)
    run_bloc5_visualisations(manager, plan, algo_results)
    run_summary(plan, manager)


if __name__ == "__main__":
    main()
