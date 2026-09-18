#!/usr/bin/env python3
# ============================================================
#  EMSI — Gestion des Déchets 2025/2026
#  tests/test_etape3.py  —  Tests unitaires de l'Étape 3
#  Lancer : python tests/test_etape3.py
# ============================================================
import sys, os, unittest, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib; matplotlib.use("Agg")


# ════════════════════════════════════════════════════════════
class TestWasteBinSensor(unittest.TestCase):

    def setUp(self):
        from modules.iot_sensors import WasteBinSensor
        self.sensor = WasteBinSensor("TEST_001", 31.63, -7.99,
                                     "menager", "Gueliz")

    def test_fill_level_range(self):
        self.assertGreaterEqual(self.sensor.fill_level, 0)
        self.assertLessEqual(self.sensor.fill_level, 100)

    def test_battery_range(self):
        self.assertGreaterEqual(self.sensor.battery_pct, 0)
        self.assertLessEqual(self.sensor.battery_pct, 100)

    def test_read_returns_dict(self):
        r = self.sensor.read()
        self.assertIsNotNone(r)
        for k in ["bin_id","fill_level","waste_type","location","status","timestamp"]:
            self.assertIn(k, r)

    def test_read_fill_in_range(self):
        r = self.sensor.read()
        self.assertGreaterEqual(r["fill_level"], 0)
        self.assertLessEqual(r["fill_level"], 100)

    def test_status_values(self):
        r = self.sensor.read()
        self.assertIn(r["status"], ["CRITICAL","URGENT","WARNING","NORMAL"])

    def test_location_format(self):
        r = self.sensor.read()
        self.assertEqual(len(r["location"]), 2)
        self.assertIsInstance(r["location"][0], float)

    def test_history_non_empty(self):
        self.assertGreater(len(self.sensor.history), 0)

    def test_simulate_collection(self):
        self.sensor.fill_level = 95
        self.sensor.simulate_collection()
        self.assertLessEqual(self.sensor.fill_level, 15)

    def test_history_has_required_keys(self):
        for h in self.sensor.history[:5]:
            self.assertIn("timestamp",  h)
            self.assertIn("fill_level", h)
            self.assertIn("temp_c",     h)


# ════════════════════════════════════════════════════════════
class TestIoTSensorManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from modules.iot_sensors import IoTSensorManager
        cls.manager = IoTSensorManager()

    def test_sensors_created(self):
        self.assertGreater(len(self.manager.sensors), 0)

    def test_get_all_bins_returns_list(self):
        bins = self.manager.get_all_bins()
        self.assertIsInstance(bins, list)
        self.assertGreater(len(bins), 0)

    def test_all_bins_have_required_fields(self):
        bins = self.manager.get_all_bins()
        for b in bins[:5]:
            for k in ["bin_id","fill_level","waste_type","zone","location","status"]:
                self.assertIn(k, b)

    def test_prioritize_returns_three_lists(self):
        urgent, attention, normal = self.manager.prioritize_bins()
        self.assertIsInstance(urgent, list)
        self.assertIsInstance(attention, list)
        self.assertIsInstance(normal, list)

    def test_urgent_bins_above_threshold(self):
        from config.settings import IOT_THRESHOLD
        urgent, _, _ = self.manager.prioritize_bins()
        for b in urgent:
            self.assertGreaterEqual(b["fill_level"], IOT_THRESHOLD)

    def test_normal_bins_below_50(self):
        _, _, normal = self.manager.prioritize_bins()
        for b in normal:
            self.assertLess(b["fill_level"], 50)

    def test_statistics_keys(self):
        stats = self.manager.get_statistics()
        for k in ["n_bins","fill_avg","fill_max","fill_min",
                  "total_weight_kg","by_type","by_zone","by_status"]:
            self.assertIn(k, stats)

    def test_statistics_fill_avg_range(self):
        stats = self.manager.get_statistics()
        self.assertGreaterEqual(stats["fill_avg"], 0)
        self.assertLessEqual(stats["fill_avg"], 100)

    def test_statistics_by_type_has_all_types(self):
        stats = self.manager.get_statistics()
        for t in ["menager","recyclable","biomedical"]:
            self.assertIn(t, stats["by_type"])

    def test_statistics_by_zone_non_empty(self):
        stats = self.manager.get_statistics()
        self.assertGreater(len(stats["by_zone"]), 0)

    def test_predict_fill_rate(self):
        bin_id = list(self.manager.sensors.keys())[0]
        pred   = self.manager.predict_fill_rate(bin_id)
        self.assertIsNotNone(pred)
        if "error" not in pred:
            self.assertIn("rate_per_hour", pred)
            self.assertIn("predicted_6h",  pred)
            self.assertIn("predicted_24h", pred)
            self.assertIn("recommendation",pred)

    def test_predict_unknown_bin(self):
        pred = self.manager.predict_fill_rate("NONEXISTENT_000")
        self.assertIsNone(pred)

    def test_simulate_collection(self):
        bin_id  = list(self.manager.sensors.keys())[0]
        before  = self.manager.sensors[bin_id].fill_level
        result  = self.manager.simulate_collection([bin_id])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["bin_id"], bin_id)
        after = self.manager.sensors[bin_id].fill_level
        self.assertLess(after, before + 5)

    def test_export_json(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            filepath, report = self.manager.export_json(path)
            self.assertTrue(os.path.exists(filepath))
            with open(filepath) as f:
                data = json.load(f)
            self.assertIn("statistics", data)
            self.assertIn("urgent_bins", data)
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ════════════════════════════════════════════════════════════
class TestIoTAnalytics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from modules.iot_sensors import IoTSensorManager
        from modules.iot_analytics import IoTAnalytics
        cls.manager   = IoTSensorManager()
        cls.analytics = IoTAnalytics(cls.manager)

    def test_kpis_keys(self):
        kpis = self.analytics.compute_kpis()
        for k in ["taux_remplissage_moyen","taux_urgence_pct",
                  "bennes_critiques","poids_total_kg"]:
            self.assertIn(k, kpis)

    def test_kpis_ranges(self):
        kpis = self.analytics.compute_kpis()
        self.assertGreaterEqual(kpis["taux_remplissage_moyen"], 0)
        self.assertLessEqual(kpis["taux_remplissage_moyen"],   100)
        self.assertGreaterEqual(kpis["taux_urgence_pct"], 0)
        self.assertLessEqual(kpis["taux_urgence_pct"],   100)

    def test_predict_all_returns_list(self):
        preds = self.analytics.predict_all()
        self.assertIsInstance(preds, list)

    def test_detect_anomalies_returns_list(self):
        anomalies = self.analytics.detect_anomalies()
        self.assertIsInstance(anomalies, list)

    def test_anomaly_fields(self):
        anomalies = self.analytics.detect_anomalies()
        for a in anomalies[:3]:
            for k in ["bin_id","fill_level","z_score","type","zone"]:
                self.assertIn(k, a)
            self.assertIn(a["type"], ["SURCHARGE","SOUS-UTILISATION"])

    def test_collection_recommendation(self):
        sol = {"x1": 2, "x2": 5, "x3": 5, "Z": 106}
        plan = self.analytics.collection_recommendation(sol)
        self.assertIn("plan", plan)
        self.assertIn("menager",    plan["plan"])
        self.assertIn("recyclable", plan["plan"])
        self.assertIn("biomedical", plan["plan"])
        for wtype, info in plan["plan"].items():
            self.assertIn("n_trucks",    info)
            self.assertIn("assignments", info)


# ════════════════════════════════════════════════════════════
class TestAlertSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from modules.iot_sensors import IoTSensorManager
        from modules.iot_analytics import AlertSystem
        manager = IoTSensorManager()
        cls.alert_sys = AlertSystem()
        all_bins = manager.get_all_bins()
        cls.alert_sys.check_and_generate(all_bins)

    def test_alerts_generated(self):
        self.assertGreater(len(self.alert_sys.get_active()), 0)

    def test_alert_fields(self):
        for a in self.alert_sys.get_active()[:3]:
            for k in ["id","level","bin_id","fill_level","message","timestamp"]:
                self.assertIn(k, a)

    def test_alert_levels_valid(self):
        for a in self.alert_sys.get_active():
            self.assertIn(a["level"], ["INFO","WARNING","URGENT","CRITICAL"])

    def test_summary_keys(self):
        s = self.alert_sys.summary
        for k in ["total","critical","urgent","warning"]:
            self.assertIn(k, s)

    def test_resolve_alert(self):
        active = self.alert_sys.get_active()
        if active:
            aid = active[0]["id"]
            result = self.alert_sys.resolve(aid)
            self.assertTrue(result)


# ════════════════════════════════════════════════════════════
class TestIoTVisualisations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from modules.iot_sensors import IoTSensorManager
        cls.manager = IoTSensorManager()

    def test_dashboard_creates_figure(self):
        import matplotlib.pyplot as plt
        from modules.iot_visualisation import plot_iot_dashboard
        fig = plot_iot_dashboard(self.manager)
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_bin_history_creates_figure(self):
        import matplotlib.pyplot as plt
        from modules.iot_visualisation import plot_bin_history
        bin_id = list(self.manager.sensors.keys())[0]
        fig = plot_bin_history(self.manager, bin_id)
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_predictions_figure(self):
        import matplotlib.pyplot as plt
        from modules.iot_visualisation import plot_predictions
        fig = plot_predictions(self.manager)
        if fig:
            plt.close(fig)


# ── Lancement direct ─────────────────────────────────────────
if __name__ == "__main__":
    B = "\033[1m"; G = "\033[92m"; R = "\033[91m"; RE = "\033[0m"
    print(f"\n{B}EMSI — Tests Étape 3 — Intégration IoT{RE}")
    print("─" * 55)
    runner = unittest.TextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestWasteBinSensor, TestIoTSensorManager,
                TestIoTAnalytics, TestAlertSystem, TestIoTVisualisations]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    result = runner.run(suite)
    print()
    n = result.testsRun
    if result.wasSuccessful():
        print(f"{G}{B}✔  {n}/{n} tests passent — Étape 3 validée !{RE}\n")
    else:
        f = len(result.failures) + len(result.errors)
        print(f"{R}{B}✘  {f} test(s) échoué(s){RE}\n")
