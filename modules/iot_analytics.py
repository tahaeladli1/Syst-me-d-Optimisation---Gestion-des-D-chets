#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  modules/iot_analytics.py  —  ÉTAPE 3
#  Analyse avancée, modèles prédictifs & système d'alertes
# ============================================================

import math
import json
import os
from datetime import datetime
from collections import defaultdict

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import IOT_THRESHOLD
from modules.iot_sensors import WASTE_TYPES, CITY_ZONES


# ════════════════════════════════════════════════════════════
#  Analyse temps réel
# ════════════════════════════════════════════════════════════
class IoTAnalytics:
    """Analyse les données IoT et génère des indicateurs."""

    def __init__(self, manager):
        self.manager = manager

    # ── KPI globaux ───────────────────────────────────────────
    def compute_kpis(self):
        stats  = self.manager.get_statistics()
        urgent, attention, normal = self.manager.prioritize_bins()
        total  = stats["n_bins"]

        return {
            "taux_remplissage_moyen" : stats["fill_avg"],
            "taux_urgence_pct"       : round(len(urgent) / total * 100, 1),
            "taux_disponibilite_pct" : round(stats["n_online"] / total * 100, 1),
            "poids_total_kg"         : stats["total_weight_kg"],
            "bennes_critiques"       : stats["by_status"].get("CRITICAL", 0),
            "bennes_urgentes"        : stats["by_status"].get("URGENT", 0),
            "bennes_normales"        : stats["by_status"].get("NORMAL", 0),
            "zone_critique"          : stats["hotspot_zone"],
            "remplissage_par_type"   : stats["by_type"],
            "remplissage_par_zone"   : stats["by_zone"],
        }

    # ── Prédiction multi-bennes ───────────────────────────────
    def predict_all(self):
        """Prédit l'évolution des 20 bennes les plus chargées."""
        urgent, attention, _ = self.manager.prioritize_bins()
        top_bins = (urgent + attention)[:20]
        results  = []
        for b in top_bins:
            pred = self.manager.predict_fill_rate(b["bin_id"])
            if pred and "error" not in pred:
                pred["waste_type"] = b["waste_type"]
                pred["zone"]       = b["zone"]
                results.append(pred)
        return sorted(results, key=lambda x: (
            x.get("hours_to_threshold") if isinstance(x.get("hours_to_threshold"), float) else 999
        ))

    # ── Détection des anomalies ───────────────────────────────
    def detect_anomalies(self):
        """Détecte les bennes avec comportement anormal."""
        all_bins   = self.manager.get_all_bins()
        fill_vals  = [b["fill_level"] for b in all_bins]
        avg        = sum(fill_vals) / len(fill_vals)
        std        = math.sqrt(sum((x - avg)**2 for x in fill_vals) / len(fill_vals))

        anomalies = []
        for b in all_bins:
            z_score = (b["fill_level"] - avg) / std if std > 0 else 0
            if abs(z_score) > 2.0:
                anomalies.append({
                    "bin_id"     : b["bin_id"],
                    "fill_level" : b["fill_level"],
                    "z_score"    : round(z_score, 2),
                    "type"       : "SURCHARGE" if z_score > 0 else "SOUS-UTILISATION",
                    "zone"       : b["zone"],
                    "waste_type" : b["waste_type"],
                })
        return sorted(anomalies, key=lambda x: -abs(x["z_score"]))

    # ── Rapport de collecte recommandé ────────────────────────
    def collection_recommendation(self, simplex_solution):
        """
        Combine la solution du simplexe (x1,x2,x3)
        avec les données IoT pour recommander les collectes.
        """
        urgent, attention, _ = self.manager.prioritize_bins()
        sol = simplex_solution

        # Répartition des camions disponibles par type
        available = {
            "menager"   : sol.get("x1", 2),
            "recyclable": sol.get("x2", 5),
            "biomedical": sol.get("x3", 5),
        }

        plan = {}
        for wtype, n_trucks in available.items():
            bins_of_type = sorted(
                [b for b in urgent + attention if b["waste_type"] == wtype],
                key=lambda x: -x["fill_level"]
            )
            # Distribuer les bennes entre camions
            assignments = [[] for _ in range(n_trucks)]
            for i, bin_item in enumerate(bins_of_type):
                assignments[i % n_trucks].append(bin_item)

            plan[wtype] = {
                "n_trucks"    : n_trucks,
                "total_bins"  : len(bins_of_type),
                "assignments" : [
                    {
                        "truck_id" : f"TRUCK_{wtype[:3].upper()}_{k+1:02d}",
                        "n_bins"   : len(a),
                        "bins"     : [b["bin_id"] for b in a],
                        "total_kg" : round(sum(b["weight_kg"] for b in a), 1),
                        "avg_fill" : round(sum(b["fill_level"] for b in a)/len(a), 1) if a else 0,
                    }
                    for k, a in enumerate(assignments) if a
                ]
            }

        return {
            "timestamp"  : datetime.now().isoformat(),
            "solution_lp": sol,
            "plan"       : plan,
            "total_urgent_bins" : len(urgent),
        }


# ════════════════════════════════════════════════════════════
#  Système d'alertes
# ════════════════════════════════════════════════════════════
class AlertSystem:
    """
    Génère et gère les alertes en temps réel
    basées sur les seuils IoT.
    """

    LEVELS = {
        "INFO"    : ("🔵", "white"),
        "WARNING" : ("🟡", "yellow"),
        "URGENT"  : ("🟠", "orange"),
        "CRITICAL": ("🔴", "red"),
    }

    def __init__(self):
        self._alerts = []

    def check_and_generate(self, all_bins):
        """Analyse toutes les bennes et génère les alertes."""
        new_alerts = []
        for b in all_bins:
            fl = b["fill_level"]

            if fl >= 90:
                level, msg = "CRITICAL", f"Benne {b['bin_id']} CRITIQUE : {fl}% — Collecte IMMÉDIATE"
            elif fl >= 70:
                level, msg = "URGENT",   f"Benne {b['bin_id']} URGENTE  : {fl}% — Collecte sous 4h"
            elif fl >= 50:
                level, msg = "WARNING",  f"Benne {b['bin_id']} ATTENTION : {fl}% — Surveiller"
            else:
                continue   # Pas d'alerte pour les niveaux normaux

            alert = {
                "id"        : f"ALT_{len(self._alerts)+len(new_alerts)+1:04d}",
                "level"     : level,
                "bin_id"    : b["bin_id"],
                "fill_level": fl,
                "waste_type": b["waste_type"],
                "zone"      : b["zone"],
                "location"  : b["location"],
                "message"   : msg,
                "timestamp" : datetime.now().isoformat(),
                "resolved"  : False,
            }
            new_alerts.append(alert)

        self._alerts.extend(new_alerts)
        return new_alerts

    def get_active(self, level=None):
        active = [a for a in self._alerts if not a["resolved"]]
        if level:
            active = [a for a in active if a["level"] == level]
        return sorted(active, key=lambda x: (
            {"CRITICAL": 0, "URGENT": 1, "WARNING": 2, "INFO": 3}[x["level"]]
        ))

    def resolve(self, alert_id):
        for a in self._alerts:
            if a["id"] == alert_id:
                a["resolved"] = True
                a["resolved_at"] = datetime.now().isoformat()
                return True
        return False

    @property
    def summary(self):
        active = self.get_active()
        return {
            "total"   : len(active),
            "critical": sum(1 for a in active if a["level"] == "CRITICAL"),
            "urgent"  : sum(1 for a in active if a["level"] == "URGENT"),
            "warning" : sum(1 for a in active if a["level"] == "WARNING"),
        }
