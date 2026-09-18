#!/usr/bin/env python3
# ============================================================
#  EMSI — Gestion des Déchets 2025/2026
#  tests/test_etape5.py  —  Tests unitaires Étape 5
#  Lancer : python tests/test_etape5.py
# ============================================================
import sys, os, unittest, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib; matplotlib.use("Agg")


# ════════════════════════════════════════════════════════════
class TestWebApp(unittest.TestCase):
    """Tests de tous les endpoints Flask."""

    @classmethod
    def setUpClass(cls):
        from ui.web_app import app
        cls.client = app.test_client()

    def _get_json(self, url):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()

    def test_index_returns_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"EMSI", resp.data)

    def test_api_stats(self):
        d = self._get_json("/api/stats")
        self.assertIn("n_bins", d)
        self.assertIn("fill_avg", d)
        self.assertIn("urgent_count", d)
        self.assertIn("total_weight_kg", d)

    def test_api_stats_n_bins_positive(self):
        d = self._get_json("/api/stats")
        self.assertGreater(d["n_bins"], 0)

    def test_api_bins_default(self):
        d = self._get_json("/api/bins")
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)

    def test_api_bins_limited(self):
        d = self._get_json("/api/bins?limit=5")
        self.assertLessEqual(len(d), 5)

    def test_api_bins_fields(self):
        bins = self._get_json("/api/bins?limit=3")
        for b in bins:
            for k in ["bin_id","fill_level","waste_type","zone","status"]:
                self.assertIn(k, b)

    def test_api_alerts(self):
        d = self._get_json("/api/alerts")
        for k in ["total","critical","urgent","warning"]:
            self.assertIn(k, d)

    def test_api_alerts_non_negative(self):
        d = self._get_json("/api/alerts")
        self.assertGreaterEqual(d["total"],    0)
        self.assertGreaterEqual(d["critical"], 0)

    def test_api_solve_ch1_default(self):
        d = self._get_json("/api/solve/ch1")
        self.assertEqual(d["status"], "optimal")
        self.assertIn("integer", d)
        i = d["integer"]
        self.assertEqual(i["x1"], 11)
        self.assertEqual(i["x2"],  1)
        self.assertEqual(i["Z"],  94)

    def test_api_solve_ch1_parametric(self):
        d = self._get_json("/api/solve/ch1?fuel=60&fleet=50&budget=90")
        self.assertEqual(d["status"], "optimal")
        self.assertGreaterEqual(d["integer"]["Z"], 94)

    def test_api_solve_ch2_default(self):
        d = self._get_json("/api/solve/ch2")
        self.assertEqual(d["status"], "optimal")
        i = d["integer"]
        self.assertEqual(i["x1"], 2)
        self.assertEqual(i["x2"], 5)
        self.assertEqual(i["x3"], 5)
        self.assertEqual(i["Z"], 106)

    def test_api_solve_ch2_iterations(self):
        d = self._get_json("/api/solve/ch2")
        self.assertEqual(d["n_iterations"], 2)

    def test_api_routes_two_opt(self):
        d = self._get_json("/api/routes?method=two_opt")
        self.assertIn("summary", d)
        self.assertIn("trucks",  d)
        s = d["summary"]
        self.assertGreater(s["total_trucks"], 0)
        self.assertGreater(s["total_distance"], 0)

    def test_api_routes_nearest_neighbor(self):
        d = self._get_json("/api/routes?method=nearest_neighbor")
        self.assertIn("summary", d)

    def test_api_report_content(self):
        d = self._get_json("/api/report")
        self.assertIn("content", d)
        self.assertIn("CHAPITRE 1", d["content"])
        self.assertIn("CHAPITRE 2", d["content"])

    def test_chart_simplex(self):
        resp = self.client.get("/chart/simplex")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "image/png")

    def test_chart_ch1(self):
        resp = self.client.get("/chart/ch1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "image/png")

    def test_chart_iot(self):
        resp = self.client.get("/chart/iot")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "image/png")

    def test_chart_routes(self):
        resp = self.client.get("/chart/routes")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "image/png")

    def test_chart_dashboard(self):
        resp = self.client.get("/chart/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "image/png")

    def test_chart_routes_dashboard(self):
        resp = self.client.get("/chart/routes_dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "image/png")

    def test_api_export_json(self):
        resp = self.client.get("/api/export/json")
        self.assertEqual(resp.status_code, 200)


# ════════════════════════════════════════════════════════════
class TestGUIModule(unittest.TestCase):
    """Tests du module ui.dashboard (sans affichage)."""

    def test_dashboard_imports(self):
        from ui.dashboard import WasteManagementApp, TKINTER_AVAILABLE
        self.assertIsNotNone(WasteManagementApp)

    def test_tkinter_flag(self):
        from ui.dashboard import TKINTER_AVAILABLE
        self.assertIsInstance(TKINTER_AVAILABLE, bool)

    def test_run_gui_function_exists(self):
        from ui.dashboard import run_gui
        self.assertTrue(callable(run_gui))

    def test_color_constants(self):
        from ui.dashboard import BG_DARK, BG_MED, TEXT, GREEN, RED
        for c in [BG_DARK, BG_MED, TEXT, GREEN, RED]:
            self.assertTrue(c.startswith("#"))
            self.assertEqual(len(c), 7)


# ════════════════════════════════════════════════════════════
class TestIntegration(unittest.TestCase):
    """Tests d'intégration : pipeline complet."""

    def test_full_pipeline(self):
        """Vérifie que toute la chaîne LP → IoT → Routes → Rapport fonctionne."""
        from modules.linear_prog import solve_chapter1
        from modules.simplex import simplex_chapter2
        from modules.iot_sensors import IoTSensorManager
        from modules.route_optimizer import FleetPlanner

        sol1 = solve_chapter1()
        sol2 = simplex_chapter2()
        self.assertEqual(sol1["status"], "optimal")
        self.assertEqual(sol2["status"], "optimal")

        manager = IoTSensorManager()
        stats   = manager.get_statistics()
        self.assertGreater(stats["n_bins"], 0)

        plan = FleetPlanner(sol2["integer"], manager).plan()
        self.assertGreater(plan["summary"]["total_distance"], 0)

    def test_report_generation(self):
        from modules.linear_prog import rapport_chapter1
        from modules.simplex import rapport_chapter2
        r1 = rapport_chapter1()
        r2 = rapport_chapter2()
        self.assertIn("94", r1)
        self.assertIn("106", r2)

    def test_all_exports_keys_present(self):
        """Vérifie que tous les modules exportent les bonnes fonctions."""
        from modules.linear_prog import (solve_chapter1, get_vertices_ch1,
                                          plot_graphical_method, rapport_chapter1)
        from modules.simplex import (simplex_chapter2, Simplex,
                                     plot_simplex_iterations, rapport_chapter2)
        from modules.iot_sensors import IoTSensorManager, WasteBinSensor
        from modules.iot_analytics import IoTAnalytics, AlertSystem
        from modules.route_optimizer import RouteOptimizer, FleetPlanner, haversine
        for fn in [solve_chapter1, get_vertices_ch1, plot_graphical_method,
                   simplex_chapter2, plot_simplex_iterations,
                   IoTSensorManager, RouteOptimizer, FleetPlanner, haversine]:
            self.assertTrue(callable(fn))


# ── Lancement direct ─────────────────────────────────────────
if __name__ == "__main__":
    B = "\033[1m"; G = "\033[92m"; R = "\033[91m"; RE = "\033[0m"
    print(f"\n{B}EMSI — Tests Étape 5 — Interface GUI & Dashboard Web{RE}")
    print("─" * 58)
    runner = unittest.TextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestWebApp, TestGUIModule, TestIntegration]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    result = runner.run(suite)
    print()
    n = result.testsRun
    if result.wasSuccessful():
        print(f"{G}{B}✔  {n}/{n} tests passent — Étape 5 validée !{RE}\n")
    else:
        f = len(result.failures) + len(result.errors)
        print(f"{R}{B}✘  {f} test(s) échoué(s){RE}\n")
