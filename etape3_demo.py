#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  etape3_demo.py  —  Démonstration complète de l'ÉTAPE 3
#  Lancer : python etape3_demo.py
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B  = "\033[1m";  G = "\033[92m";  R = "\033[91m"
Y  = "\033[93m"; C = "\033[96m";  BL= "\033[94m"; RE= "\033[0m"

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def banner():
    print(f"""
{BL}{B}╔══════════════════════════════════════════════════════════════════╗
║   EMSI — Gestion des Déchets 2025/2026                          ║
║   ÉTAPE 3 : Intégration IoT & Collecte de Données Temps Réel   ║
║   Inspiré de : ROHITH-M10/IOT-Smart-Waste-Management-System     ║
╚══════════════════════════════════════════════════════════════════╝{RE}
""")


# ────────────────────────────────────────────────────────────
def run_bloc1_init():
    """Initialisation du réseau de capteurs."""
    from modules.iot_sensors import IoTSensorManager, CITY_ZONES

    print(f"{B}{'━'*68}{RE}")
    print(f"{B}  📡 BLOC 1 — Initialisation du Réseau de Capteurs IoT{RE}")
    print(f"{B}{'━'*68}{RE}\n")

    print(f"  Zones de collecte configurées :")
    for zone, info in CITY_ZONES.items():
        print(f"    {Y}{zone:<12}{RE}  lat={info['lat']}  lng={info['lng']}  "
              f"→ {info['n_bins']} bennes")

    print(f"\n  {C}→ Création du réseau IoT...{RE}")
    manager = IoTSensorManager()

    stats = manager.get_statistics()
    print(f"\n  Réseau initialisé :")
    print(f"    Capteurs actifs    : {G}{stats['n_bins']}{RE}")
    print(f"    Poids total estimé : {G}{stats['total_weight_kg']:.0f} kg{RE}")
    print(f"    Remplissage moyen  : {G}{stats['fill_avg']:.1f}%{RE}")
    print(f"    Benne la + chargée : {R}{stats['fill_max']:.1f}%{RE}")
    print(f"    Benne la + légère  : {G}{stats['fill_min']:.1f}%{RE}")

    return manager


# ────────────────────────────────────────────────────────────
def run_bloc2_status(manager):
    """Affichage du statut de toutes les bennes."""
    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  🔍 BLOC 2 — Statut Temps Réel de Toutes les Bennes{RE}")
    print(f"{B}{'━'*68}{RE}\n")

    urgent, attention, normal = manager.prioritize_bins()

    print(f"  {'ID':<16} {'Zone':<12} {'Type':<12} {'Niveau':>8}  {'Statut'}")
    print(f"  {'─'*60}")

    all_sorted = sorted(urgent + attention + normal,
                        key=lambda x: -x["fill_level"])

    for i, b in enumerate(all_sorted):
        fl     = b["fill_level"]
        status = b["status"]
        if status == "CRITICAL":  sc, mark = R, "🔴"
        elif status == "URGENT":  sc, mark = Y, "🟠"
        elif status == "WARNING": sc, mark = "\033[33m", "🟡"
        else:                     sc, mark = G, "🟢"

        bar_len = int(fl / 5)
        bar     = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {b['bin_id']:<16} {b['zone']:<12} {b['waste_type']:<12} "
              f"{fl:>6.1f}%  {sc}{bar}{RE} {mark}")

        if i >= 19 and len(all_sorted) > 20:
            print(f"  {Y}  ... et {len(all_sorted)-20} autres bennes{RE}")
            break

    print(f"\n  Résumé :")
    print(f"    {R}CRITICAL  : {sum(1 for b in urgent    if b['status']=='CRITICAL')}{RE}")
    print(f"    {Y}URGENT    : {sum(1 for b in urgent    if b['status']=='URGENT')}{RE}")
    print(f"    \033[33mWARNING   : {len(attention)}{RE}")
    print(f"    {G}NORMAL    : {len(normal)}{RE}")


# ────────────────────────────────────────────────────────────
def run_bloc3_predictions(manager):
    """Prédictions de remplissage."""
    from modules.iot_analytics import IoTAnalytics

    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  🔮 BLOC 3 — Prédictions & Analyse Temps Réel{RE}")
    print(f"{B}{'━'*68}{RE}\n")

    analytics   = IoTAnalytics(manager)
    predictions = analytics.predict_all()

    print(f"  {'BIN ID':<16} {'Type':<12} {'Actuel':>8} {'6h':>8} {'12h':>8} {'Seuil dans':>12}  Tendance")
    print(f"  {'─'*72}")

    for p in predictions[:15]:
        hh = p.get("hours_to_threshold")
        if isinstance(hh, float):
            hh_str = f"{hh:.1f} h"
            if hh < 4:   scolor = R
            elif hh < 12: scolor = Y
            else:         scolor = G
        else:
            hh_str = "∞"
            scolor = G

        print(f"  {p['bin_id']:<16} {p['waste_type']:<12} "
              f"{p['current_fill']:>7.1f}% "
              f"{p['predicted_6h']:>7.1f}% "
              f"{p['predicted_12h']:>7.1f}% "
              f"  {scolor}{hh_str:>10}{RE}  {p['trend']}")

    # Anomalies
    print(f"\n  {B}── Anomalies détectées ──{RE}")
    anomalies = analytics.detect_anomalies()
    if not anomalies:
        print(f"  {G}Aucune anomalie détectée.{RE}")
    else:
        for a in anomalies[:5]:
            tag = R if a["type"] == "SURCHARGE" else C
            print(f"  {tag}{a['type']}{RE}  {a['bin_id']:<16} "
                  f"fill={a['fill_level']:.1f}%  z={a['z_score']:+.2f}  ({a['zone']})")


# ────────────────────────────────────────────────────────────
def run_bloc4_alertes(manager):
    """Système d'alertes."""
    from modules.iot_analytics import AlertSystem

    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  🚨 BLOC 4 — Système d'Alertes Automatiques{RE}")
    print(f"{B}{'━'*68}{RE}\n")

    alert_sys = AlertSystem()
    all_bins  = manager.get_all_bins()
    new_alerts = alert_sys.check_and_generate(all_bins)

    summary = alert_sys.summary
    print(f"  Alertes générées : {len(new_alerts)}")
    print(f"    {R}CRITICAL : {summary['critical']}{RE}")
    print(f"    {Y}URGENT   : {summary['urgent']}{RE}")
    print(f"    \033[33mWARNING  : {summary['warning']}{RE}")

    print(f"\n  Top 10 alertes actives :")
    print(f"  {'ID':<10} {'Niveau':<10} {'BIN':<16} {'Fill':>7}  Message")
    print(f"  {'─'*65}")
    for a in alert_sys.get_active()[:10]:
        lv = a["level"]
        sc = R if lv == "CRITICAL" else Y if lv == "URGENT" else "\033[33m"
        print(f"  {a['id']:<10} {sc}{lv:<10}{RE} {a['bin_id']:<16} "
              f"{a['fill_level']:>6.1f}%  {a['message'][:35]}")

    return alert_sys


# ────────────────────────────────────────────────────────────
def run_bloc5_recommendation(manager):
    """Plan de collecte recommandé (LP + IoT)."""
    from modules.simplex import simplex_chapter2
    from modules.iot_analytics import IoTAnalytics

    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  📋 BLOC 5 — Plan de Collecte Recommandé (LP + IoT){RE}")
    print(f"{B}{'━'*68}{RE}\n")

    sol       = simplex_chapter2()["integer"]
    analytics = IoTAnalytics(manager)
    plan      = analytics.collection_recommendation(sol)

    print(f"  Solution LP utilisée : x₁={sol['x1']}, x₂={sol['x2']}, x₃={sol['x3']}, Z={sol['Z']} t/j")
    print(f"  Bennes urgentes total : {plan['total_urgent_bins']}\n")

    for wtype, info in plan["plan"].items():
        emoji = {"menager":"🔵", "recyclable":"♻️ ", "biomedical":"🟠"}[wtype]
        print(f"  {emoji} {wtype.upper():<14} — {info['n_trucks']} camions pour {info['total_bins']} bennes")
        for assign in info["assignments"]:
            print(f"    {G}{assign['truck_id']}{RE}  : {assign['n_bins']} bennes  "
                  f"|  {assign['total_kg']:.0f} kg  |  moy {assign['avg_fill']:.0f}%")


# ────────────────────────────────────────────────────────────
def run_bloc6_visualisations(manager):
    """Génération de tous les graphiques IoT."""
    from modules.iot_visualisation import (
        plot_iot_dashboard, plot_bin_history, plot_predictions
    )

    print(f"\n{B}{'━'*68}{RE}")
    print(f"{B}  📊 BLOC 6 — Génération des Visualisations IoT{RE}")
    print(f"{B}{'━'*68}{RE}\n")

    print(f"  {C}→ Dashboard IoT complet...{RE}")
    fig1 = plot_iot_dashboard(manager,
             save_path=os.path.join(EXPORT_DIR, "iot_dashboard.png"))
    plt.close(fig1)
    print(f"  {G}✔  exports/iot_dashboard.png{RE}")

    # Historique d'une benne urgente
    urgent, _, _ = manager.prioritize_bins()
    if urgent:
        bin_id = urgent[0]["bin_id"]
        print(f"  {C}→ Historique benne {bin_id}...{RE}")
        fig2 = plot_bin_history(manager, bin_id,
                 save_path=os.path.join(EXPORT_DIR, "iot_bin_history.png"))
        if fig2: plt.close(fig2)
        print(f"  {G}✔  exports/iot_bin_history.png{RE}")

    print(f"  {C}→ Graphique des prédictions critiques...{RE}")
    fig3 = plot_predictions(manager,
             save_path=os.path.join(EXPORT_DIR, "iot_predictions.png"))
    if fig3:
        plt.close(fig3)
        print(f"  {G}✔  exports/iot_predictions.png{RE}")
    else:
        print(f"  {Y}⚠  Aucune benne critique dans les 24h{RE}")

    # Export JSON
    print(f"  {C}→ Export rapport JSON...{RE}")
    path, _ = manager.export_json()
    print(f"  {G}✔  {path}{RE}")


# ────────────────────────────────────────────────────────────
def run_summary(manager):
    """Résumé final de l'Étape 3."""
    stats = manager.get_statistics()
    urgent, attention, normal = manager.prioritize_bins()

    print(f"\n{B}{'═'*68}{RE}")
    print(f"{B}  RÉSUMÉ — ÉTAPE 3 COMPLÈTE{RE}")
    print(f"{B}{'═'*68}{RE}")
    print(f"""
  ┌──────────────────────────────────────────────────────────┐
  │  Réseau IoT   │  {stats['n_bins']} capteurs  /  {len(CITY_ZONES_TEMP)} zones de Marrakech     │
  │  Remplissage  │  moy={stats['fill_avg']:.1f}%  max={stats['fill_max']:.1f}%  min={stats['fill_min']:.1f}%      │
  │  Urgences     │  {R}{len(urgent)} bennes urgentes{RE}  /  {Y}{len(attention)} en attention{RE}              │
  │  Poids total  │  {stats['total_weight_kg']:.0f} kg collectables                          │
  │  Graphiques   │  dashboard · historique · prédictions   │
  └──────────────────────────────────────────────────────────┘
""")
    files = ["iot_dashboard.png", "iot_bin_history.png",
             "iot_predictions.png", "iot_report.json"]
    for f in files:
        path = os.path.join(EXPORT_DIR, f) if not f.endswith(".json") else \
               os.path.join(os.path.dirname(__file__), "data", f)
        status = f"{G}✔{RE}" if os.path.exists(path) else f"{Y}—{RE}"
        print(f"    {status}  {f}")

    print(f"\n  {G}{B}✔  ÉTAPE 3 VALIDÉE — Prêt pour l'Étape 4 (Routes){RE}")
    print(f"     {C}→ python etape4_demo.py{RE}\n")


# ── Import pour résumé ────────────────────────────────────────
from modules.iot_sensors import CITY_ZONES as CITY_ZONES_TEMP


# ────────────────────────────────────────────────────────────
def main():
    banner()
    manager = run_bloc1_init()
    run_bloc2_status(manager)
    run_bloc3_predictions(manager)
    alert_sys = run_bloc4_alertes(manager)
    run_bloc5_recommendation(manager)
    run_bloc6_visualisations(manager)
    run_summary(manager)

if __name__ == "__main__":
    main()
