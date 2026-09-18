#!/usr/bin/env python3
# ============================================================
#  EMSI — Gestion des Déchets 2025/2026
#  tests/test_etape1.py  —  Tests unitaires de l'Étape 1
#  Lancer : python -m pytest tests/ -v
#           ou : python tests/test_etape1.py
# ============================================================
import sys, os, json, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSettings(unittest.TestCase):
    """Vérifie que config/settings.py est correct."""

    def setUp(self):
        from config import settings
        self.s = settings

    def test_constraints_positive(self):
        self.assertGreater(self.s.FUEL_LIMIT,   0)
        self.assertGreater(self.s.FLEET_LIMIT,  0)
        self.assertGreater(self.s.BUDGET_LIMIT, 0)

    def test_coefficients(self):
        self.assertEqual(self.s.COEF_X1, 8)
        self.assertEqual(self.s.COEF_X2, 7)
        self.assertEqual(self.s.COEF_X3, 11)

    def test_colors_defined(self):
        required = ["primary", "secondary", "success", "warning",
                    "menager", "recyclable", "biomedical"]
        for key in required:
            self.assertIn(key, self.s.COLORS, f"Couleur '{key}' manquante")

    def test_depot_coordinates(self):
        # Marrakech doit être dans ces bornes
        self.assertAlmostEqual(self.s.DEPOT_LAT, 31.6295, places=2)
        self.assertAlmostEqual(self.s.DEPOT_LNG, -7.9811, places=2)

    def test_truck_constraints_keys(self):
        for t in ["menager", "recyclable", "biomedical"]:
            self.assertIn(t, self.s.TRUCK_CONSTRAINTS)
            tc = self.s.TRUCK_CONSTRAINTS[t]
            self.assertIn("fuel",   tc)
            self.assertIn("fleet",  tc)
            self.assertIn("budget", tc)

    def test_directories_created(self):
        self.assertTrue(os.path.isdir(self.s.DATA_DIR))
        self.assertTrue(os.path.isdir(self.s.ASSETS_DIR))
        self.assertTrue(os.path.isdir(self.s.EXPORT_DIR))


class TestSampleData(unittest.TestCase):
    """Vérifie l'intégrité de data/sample_data.json."""

    def setUp(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base, "data", "sample_data.json")) as f:
            self.data = json.load(f)

    def test_chapters_present(self):
        self.assertIn("chapter1", self.data)
        self.assertIn("chapter2", self.data)

    def test_chapter1_solution(self):
        sol = self.data["chapter1"]["optimal_solution"]
        self.assertEqual(sol["x1"], 11)
        self.assertEqual(sol["x2"], 1)
        self.assertEqual(sol["Z"],  94)

    def test_chapter2_integer_solution(self):
        sol = self.data["chapter2"]["integer_solution"]
        self.assertEqual(sol["x1"], 2)
        self.assertEqual(sol["x2"], 5)
        self.assertEqual(sol["x3"], 5)
        self.assertEqual(sol["Z"], 106)

    def test_bins_have_required_fields(self):
        for b in self.data["simulation_bins"]:
            self.assertIn("bin_id",     b)
            self.assertIn("fill_level", b)
            self.assertIn("location",   b)
            self.assertIn("type",       b)
            self.assertIn(b["type"], ["menager", "recyclable", "biomedical"])
            self.assertGreaterEqual(b["fill_level"], 0)
            self.assertLessEqual(b["fill_level"], 100)
            self.assertEqual(len(b["location"]), 2)

    def test_bins_count(self):
        self.assertGreaterEqual(len(self.data["simulation_bins"]), 5)


class TestProjectStructure(unittest.TestCase):
    """Vérifie que tous les dossiers et fichiers requis existent."""

    def setUp(self):
        self.base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _path(self, *parts):
        return os.path.join(self.base, *parts)

    def test_config_dir(self):
        self.assertTrue(os.path.isdir(self._path("config")))

    def test_settings_file(self):
        self.assertTrue(os.path.isfile(self._path("config", "settings.py")))

    def test_modules_dir(self):
        self.assertTrue(os.path.isdir(self._path("modules")))

    def test_ui_dir(self):
        self.assertTrue(os.path.isdir(self._path("ui")))

    def test_data_dir(self):
        self.assertTrue(os.path.isdir(self._path("data")))

    def test_sample_data(self):
        self.assertTrue(os.path.isfile(self._path("data", "sample_data.json")))

    def test_requirements(self):
        self.assertTrue(os.path.isfile(self._path("requirements.txt")))

    def test_main(self):
        self.assertTrue(os.path.isfile(self._path("main.py")))


# ── Lancement direct ─────────────────────────────────────────
if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSettings))
    suite.addTests(loader.loadTestsFromTestCase(TestSampleData))
    suite.addTests(loader.loadTestsFromTestCase(TestProjectStructure))

    GREEN = "\033[92m"; RED = "\033[91m"; BOLD = "\033[1m"; RESET = "\033[0m"
    print(f"\n{BOLD}EMSI — Tests Étape 1{RESET}\n{'─'*40}")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print(f"\n{GREEN}{BOLD}✔  Tous les tests passent — Étape 1 validée !{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}✘  {len(result.failures)} test(s) échoué(s){RESET}\n")
