#!/usr/bin/env python3
# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  modules/route_optimizer.py  —  ÉTAPE 4
#  Optimisation Dynamique des Routes de Collecte
#  Inspiré de : jtsimoes/smart-city-waste-management
# ============================================================

import math
import sys, os
from itertools import permutations
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DEPOT_LAT, DEPOT_LNG, DEFAULT_CITY


# ── Dépôt central ─────────────────────────────────────────────
DEPOT = {"id": "DEPOT", "location": [DEPOT_LAT, DEPOT_LNG], "name": f"Dépôt {DEFAULT_CITY}"}


# ════════════════════════════════════════════════════════════
#  Fonctions de distance
# ════════════════════════════════════════════════════════════
def haversine(p1, p2):
    """Distance en km entre deux points GPS [lat, lng]."""
    R = 6371
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def build_distance_matrix(locations):
    """Construit la matrice des distances (km) entre tous les points."""
    n = len(locations)
    matrix = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            d = haversine(locations[i]["location"], locations[j]["location"])
            matrix[i][j] = matrix[j][i] = round(d, 4)
    return matrix


# ════════════════════════════════════════════════════════════
#  Algorithmes de routage
# ════════════════════════════════════════════════════════════
class RouteOptimizer:
    """
    Moteur d'optimisation des tournées de collecte.
    Implémente plusieurs heuristiques TSP :
      1. Voisin le plus proche (Nearest Neighbor)
      2. Insertion la moins coûteuse (Cheapest Insertion)
      3. 2-Opt (amélioration locale)
    """

    def __init__(self, depot=None):
        self.depot = depot or DEPOT

    # ── Algorithme 1 : Voisin le plus proche ─────────────────
    def nearest_neighbor(self, bins):
        """
        Heuristique gloutonne : à chaque étape, aller à la benne
        non visitée la plus proche. Complexité O(n²).
        """
        if not bins:
            return [], 0.0

        unvisited = list(bins)
        route     = [self.depot]
        current   = self.depot
        total_km  = 0.0

        while unvisited:
            nearest = min(unvisited,
                          key=lambda b: haversine(current["location"], b["location"]))
            total_km += haversine(current["location"], nearest["location"])
            route.append(nearest)
            current = nearest
            unvisited.remove(nearest)

        # Retour au dépôt
        total_km += haversine(current["location"], self.depot["location"])
        route.append(self.depot)

        return route, round(total_km, 3)

    # ── Algorithme 2 : Insertion la moins coûteuse ────────────
    def cheapest_insertion(self, bins):
        """
        Insertion itérative : cherche à chaque étape l'insertion
        qui augmente le moins le coût total. Complexité O(n³).
        """
        if not bins:
            return [], 0.0
        if len(bins) == 1:
            d = haversine(self.depot["location"], bins[0]["location"]) * 2
            return [self.depot, bins[0], self.depot], round(d, 3)

        # Tour initial : dépôt → benne la + loin → dépôt
        def _bin_key(b):
            return b.get("bin_id") or b.get("id") or str(id(b))

        farthest  = max(bins, key=lambda b: haversine(self.depot["location"], b["location"]))
        tour      = [self.depot, farthest, self.depot]
        remaining = [b for b in bins if _bin_key(b) != _bin_key(farthest)]

        while remaining:
            best_cost = float("inf")
            best_bin  = None
            best_pos  = None

            for b in remaining:
                for i in range(len(tour) - 1):
                    # Coût d'insertion de b entre tour[i] et tour[i+1]
                    d_orig = haversine(tour[i]["location"], tour[i+1]["location"])
                    d_new  = (haversine(tour[i]["location"], b["location"]) +
                              haversine(b["location"], tour[i+1]["location"]))
                    delta  = d_new - d_orig
                    if delta < best_cost:
                        best_cost = delta
                        best_bin  = b
                        best_pos  = i + 1

            tour.insert(best_pos, best_bin)
            remaining.remove(best_bin)

        total_km = sum(
            haversine(tour[i]["location"], tour[i+1]["location"])
            for i in range(len(tour) - 1)
        )
        return tour, round(total_km, 3)

    # ── Algorithme 3 : 2-Opt (amélioration locale) ───────────
    def two_opt(self, route, max_iter=200):
        """
        Amélioration locale 2-Opt : inverse des sous-séquences
        pour réduire les croisements. Complexité O(n² × iter).
        Retourne (route améliorée, distance totale, n_améliorations).
        """
        best    = list(route)
        improved = True
        n_improv = 0
        iterations = 0

        while improved and iterations < max_iter:
            improved = False
            iterations += 1
            for i in range(1, len(best) - 2):
                for j in range(i + 1, len(best) - 1):
                    # Distance actuelle : ...→i→i+1→...→j→j+1→...
                    d_before = (haversine(best[i-1]["location"], best[i]["location"]) +
                                haversine(best[j]["location"],   best[j+1]["location"] if j+1 < len(best) else best[0]["location"]))
                    # Distance après inversion i..j
                    d_after  = (haversine(best[i-1]["location"], best[j]["location"]) +
                                haversine(best[i]["location"],   best[j+1]["location"] if j+1 < len(best) else best[0]["location"]))
                    if d_after < d_before - 1e-10:
                        best[i:j+1] = reversed(best[i:j+1])
                        improved = True
                        n_improv += 1

        total_km = sum(
            haversine(best[k]["location"], best[k+1]["location"])
            for k in range(len(best) - 1)
        )
        return best, round(total_km, 3), n_improv

    # ── Calcul complet pour un groupe de bennes ───────────────
    def optimize_route(self, bins, method="two_opt"):
        """
        Lance l'algorithme complet sur un groupe de bennes.
        Retourne un dict détaillé avec métriques.
        """
        if not bins:
            return {"route": [self.depot], "distance_km": 0, "n_bins": 0,
                    "method": method, "stops": []}

        t0 = datetime.now()

        # Étape 1 : Voisin le plus proche (point de départ)
        route_nn, dist_nn = self.nearest_neighbor(bins)

        if method == "nearest_neighbor":
            final_route, final_dist = route_nn, dist_nn
            n_improv = 0
        elif method == "cheapest_insertion":
            final_route, final_dist = self.cheapest_insertion(bins)
            n_improv = 0
        else:  # two_opt (défaut)
            final_route, final_dist, n_improv = self.two_opt(route_nn)

        elapsed = (datetime.now() - t0).total_seconds() * 1000

        # Calcul des métriques segment par segment
        stops = []
        for i in range(len(final_route) - 1):
            a = final_route[i]
            b = final_route[i+1]
            seg_km   = haversine(a["location"], b["location"])
            seg_min  = seg_km / 30 * 60  # Vitesse 30 km/h en ville
            stops.append({
                "from_id"    : a.get("id", "DEPOT"),
                "to_id"      : b.get("id", "DEPOT"),
                "distance_km": round(seg_km, 3),
                "duration_min": round(seg_min, 1),
                "fill_level" : b.get("fill_level", 0),
                "waste_type" : b.get("waste_type", "—"),
            })

        total_duration = sum(s["duration_min"] for s in stops)
        total_weight   = sum(b.get("weight_kg", 0) for b in bins)
        fuel_L         = round(final_dist * 0.25, 1)   # 25 L/100 km

        return {
            "method"        : method,
            "n_bins"        : len(bins),
            "route"         : final_route,
            "stops"         : stops,
            "distance_km"   : final_dist,
            "distance_nn_km": dist_nn,
            "gain_pct"      : round((dist_nn - final_dist) / dist_nn * 100, 1) if dist_nn > 0 else 0,
            "duration_min"  : round(total_duration, 1),
            "duration_h"    : round(total_duration / 60, 2),
            "weight_kg"     : round(total_weight, 1),
            "fuel_L"        : fuel_L,
            "n_improvements": n_improv,
            "compute_ms"    : round(elapsed, 2),
        }


# ════════════════════════════════════════════════════════════
#  Planificateur de flotte complet
# ════════════════════════════════════════════════════════════
class FleetPlanner:
    """
    Combine la solution LP (x1,x2,x3) avec les données IoT
    pour planifier la flotte complète de collecte.
    """

    def __init__(self, lp_solution, manager):
        self.solution = lp_solution   # {"x1":2, "x2":5, "x3":5, "Z":106}
        self.manager  = manager
        self.optimizer = RouteOptimizer()

    def plan(self, method="two_opt"):
        """
        Crée le plan de tournées complet pour tous les camions.
        Retourne un dict par type de déchet.
        """
        urgent, attention, _ = self.manager.prioritize_bins()
        all_priority = urgent + attention

        truck_config = {
            "menager"    : {"n": self.solution.get("x1", 2), "capacity_kg": 8000,  "emoji": "🔵"},
            "recyclable" : {"n": self.solution.get("x2", 5), "capacity_kg": 6000,  "emoji": "♻️ "},
            "biomedical" : {"n": self.solution.get("x3", 5), "capacity_kg": 3000,  "emoji": "🟠"},
        }

        full_plan = {
            "timestamp"  : datetime.now().isoformat(),
            "method"     : method,
            "lp_solution": self.solution,
            "trucks"     : {},
            "summary"    : {},
        }

        total_km   = 0
        total_bins = 0
        total_kg   = 0
        total_fuel = 0

        for wtype, cfg in truck_config.items():
            bins_for_type = [b for b in all_priority if b["waste_type"] == wtype]
            n_trucks      = cfg["n"]

            if not bins_for_type or n_trucks == 0:
                full_plan["trucks"][wtype] = []
                continue

            # Répartition capacité : remplir chaque camion jusqu'à sa limite
            assignments = self._assign_bins_to_trucks(
                bins_for_type, n_trucks, cfg["capacity_kg"]
            )

            truck_routes = []
            for k, assigned_bins in enumerate(assignments):
                if not assigned_bins:
                    continue
                result = self.optimizer.optimize_route(assigned_bins, method=method)
                result["truck_id"]   = f"TRUCK_{wtype[:3].upper()}_{k+1:02d}"
                result["waste_type"] = wtype
                result["capacity_kg"]= cfg["capacity_kg"]
                result["load_pct"]   = round(result["weight_kg"] / cfg["capacity_kg"] * 100, 1)
                truck_routes.append(result)

                total_km   += result["distance_km"]
                total_bins += result["n_bins"]
                total_kg   += result["weight_kg"]
                total_fuel += result["fuel_L"]

            full_plan["trucks"][wtype] = truck_routes

        full_plan["summary"] = {
            "total_trucks"   : sum(len(v) for v in full_plan["trucks"].values()),
            "total_bins"     : total_bins,
            "total_distance" : round(total_km, 2),
            "total_weight_kg": round(total_kg, 1),
            "total_fuel_L"   : round(total_fuel, 1),
            "avg_distance"   : round(total_km / max(1, sum(len(v) for v in full_plan["trucks"].values())), 2),
        }

        return full_plan

    def _assign_bins_to_trucks(self, bins, n_trucks, capacity_kg):
        """Répartit les bennes entre camions (tri par remplissage décroissant)."""
        sorted_bins  = sorted(bins, key=lambda b: -b["fill_level"])
        assignments  = [[] for _ in range(n_trucks)]
        truck_loads  = [0.0] * n_trucks

        for b in sorted_bins:
            # Affecter au camion le moins chargé qui peut encore accepter
            idx = min(range(n_trucks), key=lambda i: truck_loads[i])
            if truck_loads[idx] + b.get("weight_kg", 0) <= capacity_kg:
                assignments[idx].append(b)
                truck_loads[idx] += b.get("weight_kg", 0)
            else:
                # Débordement : mettre dans le moins chargé
                assignments[idx].append(b)

        return assignments
