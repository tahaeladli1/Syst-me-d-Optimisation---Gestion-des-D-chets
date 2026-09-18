#!/usr/bin/env python3
# ============================================================
#  EMSI — Gestion des Déchets 2025/2026
#  tests/test_etape4.py  —  Tests unitaires Étape 4
#  Lancer : python tests/test_etape4.py
# ============================================================
import sys, os, unittest, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib; matplotlib.use("Agg")


# ════════════════════════════════════════════════════════════
class TestHaversine(unittest.TestCase):

    def test_same_point_zero(self):
        from modules.route_optimizer import haversine
        self.assertAlmostEqual(haversine([31.63, -7.99], [31.63, -7.99]), 0, places=4)

    def test_known_distance(self):
        from modules.route_optimizer import haversine
        # Paris → Marseille ≈ 660 km
        d = haversine([48.8566, 2.3522], [43.2965, 5.3698])
        self.assertGreater(d, 600)
        self.assertLess(d, 720)

    def test_symmetry(self):
        from modules.route_optimizer import haversine
        a, b = [31.63, -7.99], [31.62, -8.01]
        self.assertAlmostEqual(haversine(a, b), haversine(b, a), places=8)

    def test_positive(self):
        from modules.route_optimizer import haversine
        d = haversine([31.63, -7.99], [31.64, -7.98])
        self.assertGreater(d, 0)


# ════════════════════════════════════════════════════════════
class TestDistanceMatrix(unittest.TestCase):

    def setUp(self):
        from modules.route_optimizer import build_distance_matrix
        self.locs = [
            {"id":"A","location":[31.63,-7.99]},
            {"id":"B","location":[31.64,-7.98]},
            {"id":"C","location":[31.62,-8.00]},
        ]
        self.matrix = build_distance_matrix(self.locs)

    def test_diagonal_zero(self):
        for i in range(3):
            self.assertAlmostEqual(self.matrix[i][i], 0, places=6)

    def test_symmetric(self):
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(self.matrix[i][j], self.matrix[j][i], places=8)

    def test_positive_off_diagonal(self):
        for i in range(3):
            for j in range(3):
                if i != j:
                    self.assertGreater(self.matrix[i][j], 0)


# ════════════════════════════════════════════════════════════
class TestRouteOptimizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from modules.route_optimizer import RouteOptimizer
        from modules.iot_sensors import IoTSensorManager
        cls.optimizer = RouteOptimizer()
        m = IoTSensorManager()
        urgent, att, _ = m.prioritize_bins()
        cls.bins = (urgent + att)[:10]

    def test_nearest_neighbor_returns_tuple(self):
        route, dist = self.optimizer.nearest_neighbor(self.bins)
        self.assertIsInstance(route, list)
        self.assertIsInstance(dist, float)

    def test_nearest_neighbor_starts_ends_depot(self):
        route, _ = self.optimizer.nearest_neighbor(self.bins)
        self.assertEqual(route[0]["id"],  "DEPOT")
        self.assertEqual(route[-1]["id"], "DEPOT")

    def test_nearest_neighbor_visits_all(self):
        route, _ = self.optimizer.nearest_neighbor(self.bins)
        # Route = DEPOT + all bins + DEPOT
        self.assertEqual(len(route), len(self.bins) + 2)

    def test_nearest_neighbor_positive_distance(self):
        _, dist = self.optimizer.nearest_neighbor(self.bins)
        self.assertGreater(dist, 0)

    def test_cheapest_insertion_returns_tuple(self):
        route, dist = self.optimizer.cheapest_insertion(self.bins)
        self.assertIsInstance(route, list)
        self.assertGreater(dist, 0)

    def test_cheapest_insertion_visits_all(self):
        route, _ = self.optimizer.cheapest_insertion(self.bins)
        self.assertEqual(len(route), len(self.bins) + 2)

    def test_two_opt_returns_triple(self):
        route_nn, _ = self.optimizer.nearest_neighbor(self.bins)
        route, dist, n_imp = self.optimizer.two_opt(route_nn)
        self.assertIsInstance(route, list)
        self.assertIsInstance(dist, float)
        self.assertIsInstance(n_imp, int)

    def test_two_opt_not_worse_than_nn(self):
        route_nn, dist_nn = self.optimizer.nearest_neighbor(self.bins)
        _, dist_2opt, _  = self.optimizer.two_opt(route_nn)
        self.assertLessEqual(dist_2opt, dist_nn + 1e-6)

    def test_optimize_route_nn(self):
        res = self.optimizer.optimize_route(self.bins, method="nearest_neighbor")
        self._check_result(res)

    def test_optimize_route_ci(self):
        res = self.optimizer.optimize_route(self.bins, method="cheapest_insertion")
        self._check_result(res)

    def test_optimize_route_two_opt(self):
        res = self.optimizer.optimize_route(self.bins, method="two_opt")
        self._check_result(res)

    def _check_result(self, res):
        for k in ["distance_km","duration_min","weight_kg",
                  "fuel_L","n_bins","route","stops","method"]:
            self.assertIn(k, res)
        self.assertGreater(res["distance_km"], 0)
        self.assertGreaterEqual(res["n_bins"],  0)
        self.assertGreater(res["fuel_L"],       0)

    def test_result_distance_km_positive(self):
        res = self.optimizer.optimize_route(self.bins, method="two_opt")
        self.assertGreater(res["distance_km"], 0)

    def test_stops_have_required_fields(self):
        res = self.optimizer.optimize_route(self.bins, method="two_opt")
        for s in res["stops"]:
            for k in ["from_id","to_id","distance_km","duration_min"]:
                self.assertIn(k, s)

    def test_fuel_proportional_to_distance(self):
        res = self.optimizer.optimize_route(self.bins, method="two_opt")
        expected = res["distance_km"] * 0.25
        self.assertAlmostEqual(res["fuel_L"], expected, places=1)

    def test_empty_bins_returns_zero(self):
        res = self.optimizer.optimize_route([], method="two_opt")
        self.assertEqual(res["distance_km"], 0)
        self.assertEqual(res["n_bins"], 0)

    def test_gain_pct_non_negative(self):
        res = self.optimizer.optimize_route(self.bins, method="two_opt")
        self.assertGreaterEqual(res["gain_pct"], 0)

    def test_duration_matches_distance(self):
        """Durée = distance / 30 km/h × 60 min."""
        res = self.optimizer.optimize_route(self.bins, method="two_opt")
        expected_min = res["distance_km"] / 30 * 60
        self.assertAlmostEqual(res["duration_min"], expected_min, delta=1.0)


# ════════════════════════════════════════════════════════════
class TestFleetPlanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from modules.iot_sensors import IoTSensorManager
        from modules.route_optimizer import FleetPlanner
        from modules.simplex import simplex_chapter2
        cls.manager = IoTSensorManager()
        sol = simplex_chapter2()["integer"]
        cls.planner = FleetPlanner(sol, cls.manager)
        cls.plan    = cls.planner.plan()

    def test_plan_has_summary(self):
        self.assertIn("summary", self.plan)

    def test_plan_has_trucks(self):
        self.assertIn("trucks", self.plan)

    def test_all_waste_types_present(self):
        for wtype in ["menager","recyclable","biomedical"]:
            self.assertIn(wtype, self.plan["trucks"])

    def test_summary_keys(self):
        s = self.plan["summary"]
        for k in ["total_trucks","total_bins","total_distance",
                  "total_weight_kg","total_fuel_L","avg_distance"]:
            self.assertIn(k, s)

    def test_total_distance_positive(self):
        self.assertGreater(self.plan["summary"]["total_distance"], 0)

    def test_correct_number_menager_trucks(self):
        n = len(self.plan["trucks"]["menager"])
        self.assertEqual(n, 2)   # x1=2

    def test_correct_number_recyclable_trucks(self):
        n = len(self.plan["trucks"]["recyclable"])
        self.assertGreaterEqual(n, 1)   # x2=5 trucks max

    def test_correct_number_biomedical_trucks(self):
        n = len(self.plan["trucks"]["biomedical"])
        self.assertGreaterEqual(n, 1)   # x3=5 trucks max

    def test_truck_has_route(self):
        for wtype, trucks in self.plan["trucks"].items():
            for t in trucks:
                self.assertIn("route", t)
                self.assertGreater(len(t["route"]), 0)

    def test_truck_ids_unique(self):
        all_ids = [t["truck_id"]
                   for trucks in self.plan["trucks"].values()
                   for t in trucks]
        self.assertEqual(len(all_ids), len(set(all_ids)))

    def test_load_pct_present(self):
        for trucks in self.plan["trucks"].values():
            for t in trucks:
                self.assertIn("load_pct", t)
                self.assertGreaterEqual(t["load_pct"], 0)

    def test_total_bins_matches_sum(self):
        computed = sum(t["n_bins"]
                       for trucks in self.plan["trucks"].values()
                       for t in trucks)
        self.assertEqual(computed, self.plan["summary"]["total_bins"])


# ════════════════════════════════════════════════════════════
class TestRouteVisualisations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from modules.iot_sensors import IoTSensorManager
        from modules.route_optimizer import FleetPlanner
        from modules.simplex import simplex_chapter2
        cls.manager = IoTSensorManager()
        sol = simplex_chapter2()["integer"]
        cls.plan = FleetPlanner(sol, cls.manager).plan()

    def test_routes_map(self):
        import matplotlib.pyplot as plt
        from modules.route_visualisation import plot_routes_map
        fig = plot_routes_map(self.plan)
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 3)
        plt.close(fig)

    def test_fleet_dashboard(self):
        import matplotlib.pyplot as plt
        from modules.route_visualisation import plot_fleet_dashboard
        fig = plot_fleet_dashboard(self.plan)
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_algorithm_comparison(self):
        import matplotlib.pyplot as plt
        from modules.route_visualisation import plot_algorithm_comparison
        fig = plot_algorithm_comparison(self.manager)
        if fig:
            self.assertEqual(len(fig.axes), 3)
            plt.close(fig)

    def test_single_truck_route(self):
        import matplotlib.pyplot as plt
        from modules.route_visualisation import plot_single_truck_route
        truck = next(t for trucks in self.plan["trucks"].values()
                     for t in trucks if t["n_bins"] > 0)
        fig = plot_single_truck_route(truck)
        self.assertIsNotNone(fig)
        plt.close(fig)


# ── Lancement direct ─────────────────────────────────────────
if __name__ == "__main__":
    B = "\033[1m"; G = "\033[92m"; R = "\033[91m"; RE = "\033[0m"
    print(f"\n{B}EMSI — Tests Étape 4 — Optimisation des Routes{RE}")
    print("─" * 55)
    runner = unittest.TextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestHaversine, TestDistanceMatrix, TestRouteOptimizer,
                TestFleetPlanner, TestRouteVisualisations]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    result = runner.run(suite)
    print()
    n = result.testsRun
    if result.wasSuccessful():
        print(f"{G}{B}✔  {n}/{n} tests passent — Étape 4 validée !{RE}\n")
    else:
        f = len(result.failures) + len(result.errors)
        print(f"{R}{B}✘  {f} test(s) échoué(s){RE}\n")
