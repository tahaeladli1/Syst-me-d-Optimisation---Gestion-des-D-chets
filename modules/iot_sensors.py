#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  modules/iot_sensors.py  —  ÉTAPE 3
#  Intégration IoT & Collecte de Données en Temps Réel
#  Inspiré de : ROHITH-M10/IOT-Smart-Waste-Management-System
# ============================================================

import random
import math
import json
import os
import time
import threading
from datetime import datetime, timedelta
from collections import deque

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    IOT_THRESHOLD, DEPOT_LAT, DEPOT_LNG,
    DEFAULT_CITY, DATA_DIR
)

# ── Types de déchets & propriétés ────────────────────────────
WASTE_TYPES = {
    "menager"    : {"coef_obj": 8,  "fill_rate": 3.5, "color": "#2196F3", "emoji": "🔵"},
    "recyclable" : {"coef_obj": 7,  "fill_rate": 2.8, "color": "#4CAF50", "emoji": "♻️"},
    "biomedical" : {"coef_obj": 11, "fill_rate": 1.9, "color": "#FF9800", "emoji": "🟠"},
}

# ── Zones de la ville ─────────────────────────────────────────
CITY_ZONES = {
    "Medina"      : {"lat": 31.6317, "lng": -7.9870, "n_bins": 10},
    "Gueliz"      : {"lat": 31.6328, "lng": -7.9992, "n_bins": 8},
    "Hivernage"   : {"lat": 31.6215, "lng": -7.9934, "n_bins": 6},
    "Majorelle"   : {"lat": 31.6369, "lng": -7.9940, "n_bins": 5},
    "M'Hamid"     : {"lat": 31.5985, "lng": -8.0152, "n_bins": 7},
    "Palmeraie"   : {"lat": 31.6567, "lng": -7.9619, "n_bins": 4},
}


# ════════════════════════════════════════════════════════════
#  CLASSE : Capteur individuel (un conteneur)
# ════════════════════════════════════════════════════════════
class WasteBinSensor:
    """
    Simule un capteur IoT ultra-sons fixé sur un conteneur.
    Génère un historique de remplissage réaliste avec :
      - tendance journalière (rush matin & soir)
      - bruit aléatoire
      - collecte simulée (remise à 0)
    """

    def __init__(self, bin_id, lat, lng, waste_type, zone, capacity_kg=500):
        self.bin_id      = bin_id
        self.location    = [round(lat, 6), round(lng, 6)]
        self.waste_type  = waste_type
        self.zone        = zone
        self.capacity_kg = capacity_kg

        # État courant
        self.fill_level  = random.uniform(5, 90)   # % de remplissage
        self.last_collect= datetime.now() - timedelta(hours=random.randint(6, 48))
        self.battery_pct = random.uniform(65, 100)
        self.is_online   = random.random() > 0.05  # 95 % uptime

        # Historique (48 h × mesures toutes les 30 min = 96 points max)
        self._history = deque(maxlen=96)
        self._generate_history()

    # ── Génération de l'historique ────────────────────────────
    def _generate_history(self):
        """Génère 48 h d'historique réaliste."""
        base_rate = WASTE_TYPES[self.waste_type]["fill_rate"]   # %/h
        level = max(0, self.fill_level - base_rate * 48 * random.uniform(0.4, 0.8))
        now   = datetime.now()

        for i in range(96):
            t = now - timedelta(minutes=30 * (95 - i))
            hour = t.hour

            # Modulation selon l'heure (rush 8h-12h et 17h-21h)
            if 8 <= hour <= 12 or 17 <= hour <= 21:
                rate = base_rate * random.uniform(1.2, 1.8)
            elif 2 <= hour <= 6:
                rate = base_rate * random.uniform(0.1, 0.3)
            else:
                rate = base_rate * random.uniform(0.7, 1.2)

            level = min(100, level + rate * 0.5 + random.gauss(0, 0.4))
            level = max(0, level)

            # Simulation d'une collecte si > 95 %
            if level >= 95:
                level = random.uniform(3, 8)

            self._history.append({
                "timestamp" : t.isoformat(),
                "fill_level": round(level, 1),
                "temp_c"    : round(random.uniform(18, 38), 1),
            })

        self.fill_level = self._history[-1]["fill_level"]

    # ── Lecture courante ──────────────────────────────────────
    def read(self):
        """Simule une lecture temps réel du capteur."""
        if not self.is_online:
            return None

        # Avancer le niveau de remplissage
        base_rate   = WASTE_TYPES[self.waste_type]["fill_rate"]
        hour        = datetime.now().hour
        if 8 <= hour <= 12 or 17 <= hour <= 21:
            rate = base_rate * random.uniform(1.2, 1.8)
        else:
            rate = base_rate * random.uniform(0.5, 1.0)

        self.fill_level = min(100, self.fill_level + rate * random.uniform(0.01, 0.05))
        self.battery_pct = max(0, self.battery_pct - random.uniform(0, 0.02))

        reading = {
            "bin_id"      : self.bin_id,
            "fill_level"  : round(self.fill_level, 1),
            "waste_type"  : self.waste_type,
            "zone"        : self.zone,
            "location"    : self.location,
            "capacity_kg" : self.capacity_kg,
            "weight_kg"   : round(self.capacity_kg * self.fill_level / 100, 1),
            "battery_pct" : round(self.battery_pct, 1),
            "temperature" : round(random.uniform(18, 38), 1),
            "timestamp"   : datetime.now().isoformat(),
            "status"      : self._get_status(),
        }
        self._history.append({
            "timestamp" : reading["timestamp"],
            "fill_level": reading["fill_level"],
            "temp_c"    : reading["temperature"],
        })
        return reading

    def _get_status(self):
        if self.fill_level >= 90:  return "CRITICAL"
        if self.fill_level >= 70:  return "URGENT"
        if self.fill_level >= 50:  return "WARNING"
        return "NORMAL"

    @property
    def history(self):
        return list(self._history)

    def simulate_collection(self):
        """Simule une opération de collecte (vidange)."""
        self.fill_level  = random.uniform(2, 8)
        self.last_collect = datetime.now()
        self._history.append({
            "timestamp" : datetime.now().isoformat(),
            "fill_level": self.fill_level,
            "temp_c"    : 25.0,
        })


# ════════════════════════════════════════════════════════════
#  CLASSE : Gestionnaire de capteurs (réseau IoT)
# ════════════════════════════════════════════════════════════
class IoTSensorManager:
    """
    Gestionnaire central du réseau de capteurs IoT.
    Gère la simulation, la récupération, l'analyse et
    la prédiction des données des bennes.
    """

    def __init__(self, n_bins=None, api_url=None, api_key=None):
        self.api_url   = api_url
        self.api_key   = api_key
        self._sensors  = {}
        self._lock     = threading.Lock()
        self._polling  = False

        # Génère le réseau de bennes à partir des zones
        self._build_sensor_network(n_bins)
        print(f"  [IoT] ✔ Réseau initialisé : {len(self._sensors)} capteurs "
              f"sur {len(CITY_ZONES)} zones de {DEFAULT_CITY}")

    # ── Construction du réseau ────────────────────────────────
    def _build_sensor_network(self, n_bins=None):
        idx = 1
        type_cycle = list(WASTE_TYPES.keys())

        for zone_name, zone_info in CITY_ZONES.items():
            count = n_bins or zone_info["n_bins"]
            for j in range(count):
                waste_type = type_cycle[(idx - 1) % len(type_cycle)]
                # Position légèrement aléatoire autour du centre de zone
                lat = zone_info["lat"] + random.uniform(-0.008, 0.008)
                lng = zone_info["lng"] + random.uniform(-0.008, 0.008)
                bin_id = f"BIN_{idx:03d}_{zone_name[:3].upper()}"

                sensor = WasteBinSensor(
                    bin_id      = bin_id,
                    lat         = lat,
                    lng         = lng,
                    waste_type  = waste_type,
                    zone        = zone_name,
                    capacity_kg = random.choice([300, 500, 750, 1000]),
                )
                self._sensors[bin_id] = sensor
                idx += 1

    # ── Lecture de tous les capteurs ─────────────────────────
    def get_all_bins(self):
        """Retourne les données actuelles de toutes les bennes."""
        readings = []
        with self._lock:
            for sensor in self._sensors.values():
                r = sensor.read()
                if r:
                    readings.append(r)
        return readings

    # ── Triage par priorité ───────────────────────────────────
    def prioritize_bins(self, threshold=None):
        """
        Classifie les bennes selon leur urgence.
        Retourne (urgent, attention, normal).
        """
        thr = threshold or IOT_THRESHOLD
        all_bins = self.get_all_bins()

        urgent    = sorted([b for b in all_bins if b["fill_level"] >= thr],
                           key=lambda x: -x["fill_level"])
        attention = [b for b in all_bins if 50 <= b["fill_level"] < thr]
        normal    = [b for b in all_bins if b["fill_level"] < 50]

        return urgent, attention, normal

    # ── Statistiques globales ─────────────────────────────────
    def get_statistics(self):
        """Calcule les statistiques du réseau IoT."""
        all_bins   = self.get_all_bins()
        n          = len(all_bins)
        if n == 0:
            return {}

        fill_vals  = [b["fill_level"] for b in all_bins]
        by_type    = {t: [] for t in WASTE_TYPES}
        by_zone    = {}
        by_status  = {"CRITICAL": 0, "URGENT": 0, "WARNING": 0, "NORMAL": 0}
        total_kg   = 0

        for b in all_bins:
            by_type[b["waste_type"]].append(b["fill_level"])
            by_zone.setdefault(b["zone"], []).append(b["fill_level"])
            by_status[b["status"]] = by_status.get(b["status"], 0) + 1
            total_kg += b["weight_kg"]

        # Taux moyen par type
        type_avg = {t: round(sum(v)/len(v), 1) if v else 0
                    for t, v in by_type.items()}
        # Taux moyen par zone
        zone_avg = {z: round(sum(v)/len(v), 1)
                    for z, v in by_zone.items()}
        # Zone la plus surchargée
        hotspot  = max(zone_avg, key=zone_avg.get) if zone_avg else None

        return {
            "n_bins"         : n,
            "n_online"       : sum(1 for b in all_bins),
            "fill_avg"       : round(sum(fill_vals) / n, 1),
            "fill_max"       : round(max(fill_vals), 1),
            "fill_min"       : round(min(fill_vals), 1),
            "total_weight_kg": round(total_kg, 1),
            "by_type"        : type_avg,
            "by_zone"        : zone_avg,
            "by_status"      : by_status,
            "hotspot_zone"   : hotspot,
            "urgent_count"   : by_status.get("URGENT",0) + by_status.get("CRITICAL",0),
            "timestamp"      : datetime.now().isoformat(),
        }

    # ── Prédiction du taux de remplissage ─────────────────────
    def predict_fill_rate(self, bin_id):
        """
        Prédit le taux de remplissage futur d'une benne
        via régression linéaire sur son historique.
        """
        sensor = self._sensors.get(bin_id)
        if not sensor:
            return None

        history = sensor.history[-24:]   # 12 dernières heures
        if len(history) < 4:
            return {"error": "Historique insuffisant"}

        levels = [h["fill_level"] for h in history]
        times  = list(range(len(levels)))

        # Régression linéaire simple (moindres carrés)
        n    = len(times)
        sx   = sum(times)
        sy   = sum(levels)
        sxy  = sum(t*l for t, l in zip(times, levels))
        sxx  = sum(t**2 for t in times)
        denom = n*sxx - sx**2

        if abs(denom) < 1e-9:
            return {"error": "Pas de tendance détectable"}

        slope  = (n*sxy - sx*sy) / denom
        intercept = (sy - slope*sx) / n

        current = levels[-1]
        if slope <= 0:
            hours_to_full = float("inf")
            hours_to_thr  = float("inf")
        else:
            hours_to_full = (100 - current) / (slope * 2)  # 2 lectures/h
            hours_to_thr  = (IOT_THRESHOLD - current) / (slope * 2)

        # Niveau prédit dans 6 h, 12 h, 24 h
        def pred(h):
            return min(100, max(0, current + slope * 2 * h))

        return {
            "bin_id"        : bin_id,
            "current_fill"  : round(current, 1),
            "rate_per_hour" : round(slope * 2, 3),
            "trend"         : "↑ hausse" if slope > 0.1 else ("↓ baisse" if slope < -0.1 else "→ stable"),
            "predicted_6h"  : round(pred(6), 1),
            "predicted_12h" : round(pred(12), 1),
            "predicted_24h" : round(pred(24), 1),
            "hours_to_threshold" : round(hours_to_thr, 1) if hours_to_thr < 999 else "∞",
            "hours_to_full"      : round(hours_to_full, 1) if hours_to_full < 999 else "∞",
            "recommendation" : _recommend(current, hours_to_thr),
        }

    # ── Rapport JSON complet ──────────────────────────────────
    def export_json(self, filepath=None):
        """Exporte l'état complet du réseau en JSON."""
        stats    = self.get_statistics()
        urgent, attention, normal = self.prioritize_bins()
        predictions = {}
        for bid in list(self._sensors.keys())[:10]:  # 10 premières bennes
            pred = self.predict_fill_rate(bid)
            if pred and "error" not in pred:
                predictions[bid] = pred

        report = {
            "generated_at": datetime.now().isoformat(),
            "city"        : DEFAULT_CITY,
            "statistics"  : stats,
            "urgent_bins" : urgent,
            "predictions" : predictions,
        }

        if filepath is None:
            filepath = os.path.join(DATA_DIR, "iot_report.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return filepath, report

    # ── Simulation d'une collecte ─────────────────────────────
    def simulate_collection(self, bin_ids):
        """Simule la collecte des bennes spécifiées."""
        collected = []
        with self._lock:
            for bid in bin_ids:
                if bid in self._sensors:
                    before = self._sensors[bid].fill_level
                    self._sensors[bid].simulate_collection()
                    after  = self._sensors[bid].fill_level
                    collected.append({
                        "bin_id"     : bid,
                        "fill_before": round(before, 1),
                        "fill_after" : round(after, 1),
                        "collected_kg": round(
                            self._sensors[bid].capacity_kg * (before - after) / 100, 1
                        ),
                    })
        return collected

    # ── Accès direct aux capteurs ────────────────────────────
    @property
    def sensors(self):
        return dict(self._sensors)

    def get_bin(self, bin_id):
        return self._sensors.get(bin_id)


# ── Fonction utilitaire ───────────────────────────────────────
def _recommend(fill_level, hours_to_threshold):
    if fill_level >= 90:
        return "🔴 COLLECTE IMMÉDIATE"
    if fill_level >= 70:
        return "🟠 Programmer collecte sous 4 h"
    if isinstance(hours_to_threshold, (int, float)) and hours_to_threshold < 12:
        return "🟡 Planifier collecte dans les 12 h"
    return "🟢 Collecte planifiée normale"
