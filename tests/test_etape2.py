#!/usr/bin/env python3
# ============================================================
#  EMSI — Gestion des Déchets 2025/2026
#  tests/test_etape2.py  —  Tests unitaires de l'Étape 2
#  Lancer : python tests/test_etape2.py
# ============================================================
import sys, os, unittest, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")


# ════════════════════════════════════════════════════════════
#  Tests — Chapitre 1 : Méthode Graphique
# ════════════════════════════════════════════════════════════
class TestChapter1(unittest.TestCase):

    def setUp(self):
        from modules.linear_prog import solve_chapter1
        self.res = solve_chapter1()
        self.sol = self.res["integer"]

    def test_status_optimal(self):
        self.assertEqual(self.res["status"], "optimal")

    def test_integer_solution_x1(self):
        self.assertEqual(self.sol["x1"], 11, "x₁ doit être 11")

    def test_integer_solution_x2(self):
        self.assertEqual(self.sol["x2"], 1, "x₂ doit être 1")

    def test_optimal_Z_value(self):
        self.assertEqual(self.sol["Z"], 94, "Z doit être 94 t/jour")

    def test_Z_formula(self):
        computed = 8*self.sol["x1"] + 6*self.sol["x2"]
        self.assertEqual(computed, self.sol["Z"])

    def test_constraint_C1(self):
        x1, x2 = self.sol["x1"], self.sol["x2"]
        self.assertLessEqual(4*x1 + 3*x2, 48, "C1 : carburant")

    def test_constraint_C2(self):
        x1, x2 = self.sol["x1"], self.sol["x2"]
        self.assertLessEqual(2*x1 + 4*x2, 40, "C2 : flotte")

    def test_constraint_C3(self):
        x1, x2 = self.sol["x1"], self.sol["x2"]
        self.assertLessEqual(6*x1 + 4*x2, 72, "C3 : budget")

    def test_constraint_C4_min_menager(self):
        self.assertGreaterEqual(self.sol["x1"], 2, "C4 : x₁≥2")

    def test_constraint_C5_min_recyclable(self):
        self.assertGreaterEqual(self.sol["x2"], 1, "C5 : x₂≥1")

    def test_non_negative(self):
        self.assertGreaterEqual(self.sol["x1"], 0)
        self.assertGreaterEqual(self.sol["x2"], 0)

    def test_saturation_keys(self):
        sat = self.res["saturation_pct"]
        for k in ["C1", "C2", "C3"]:
            self.assertIn(k, sat)
            self.assertGreater(sat[k], 0)
            self.assertLessEqual(sat[k], 100.1)

    def test_vertices_non_empty(self):
        from modules.linear_prog import get_vertices_ch1
        verts = get_vertices_ch1()
        self.assertGreater(len(verts), 0, "Il faut au moins 1 sommet réalisable")

    def test_vertices_all_feasible(self):
        from modules.linear_prog import get_vertices_ch1
        verts = get_vertices_ch1()
        for vx, vy in verts:
            self.assertGreaterEqual(vx, -1e-6)
            self.assertGreaterEqual(vy, -1e-6)
            self.assertLessEqual(4*vx + 3*vy, 48 + 1e-4)
            self.assertLessEqual(2*vx + 4*vy, 40 + 1e-4)
            self.assertLessEqual(6*vx + 4*vy, 72 + 1e-4)

    def test_graphical_method_generates_figure(self):
        import matplotlib.pyplot as plt
        from modules.linear_prog import plot_graphical_method
        fig = plot_graphical_method()
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_rapport_chapter1_contains_solution(self):
        from modules.linear_prog import rapport_chapter1
        report = rapport_chapter1()
        self.assertIn("94", report)
        self.assertIn("x₁", report)

    def test_parametric_different_fuel(self):
        from modules.linear_prog import solve_chapter1
        res_high = solve_chapter1(fuel=60)
        self.assertEqual(res_high["status"], "optimal")
        self.assertGreaterEqual(res_high["integer"]["Z"], 94)


# ════════════════════════════════════════════════════════════
#  Tests — Chapitre 2 : Méthode du Simplexe
# ════════════════════════════════════════════════════════════
class TestChapter2(unittest.TestCase):

    def setUp(self):
        from modules.simplex import Simplex, simplex_chapter2
        self.solver = Simplex()
        self.res    = self.solver.solve()
        self.sol    = self.res["integer"]
        self.cont   = self.res["continuous"]

    def test_status_optimal(self):
        self.assertEqual(self.res["status"], "optimal")

    def test_integer_x1(self):
        self.assertEqual(self.sol["x1"], 2)

    def test_integer_x2(self):
        self.assertEqual(self.sol["x2"], 5)

    def test_integer_x3(self):
        self.assertEqual(self.sol["x3"], 5)

    def test_integer_Z(self):
        self.assertEqual(self.sol["Z"], 106)

    def test_Z_formula(self):
        z = 8*self.sol["x1"] + 7*self.sol["x2"] + 11*self.sol["x3"]
        self.assertEqual(z, self.sol["Z"])

    def test_constraint_C1(self):
        x1, x2, x3 = self.sol["x1"], self.sol["x2"], self.sol["x3"]
        self.assertLessEqual(4*x1 + 3*x2 + 5*x3, 48)

    def test_constraint_C2(self):
        x1, x2, x3 = self.sol["x1"], self.sol["x2"], self.sol["x3"]
        self.assertLessEqual(2*x1 + 4*x2 + 3*x3, 40)

    def test_constraint_C3(self):
        x1, x2, x3 = self.sol["x1"], self.sol["x2"], self.sol["x3"]
        self.assertLessEqual(6*x1 + 4*x2 + 8*x3, 72)

    def test_non_negative(self):
        for v in [self.sol["x1"], self.sol["x2"], self.sol["x3"]]:
            self.assertGreaterEqual(v, 0)

    def test_saturation_c1_c3_saturated(self):
        sat = self.sol["saturation"]
        self.assertAlmostEqual(sat["C1"], 100.0, places=0)
        self.assertAlmostEqual(sat["C3"], 100.0, places=0)

    def test_two_iterations(self):
        self.assertEqual(self.res["n_iterations"], 2,
                         "Le simplexe doit converger en 2 itérations")

    def test_iterations_z_increasing(self):
        z_vals = [snap["z_value"] for snap in self.res["iterations"]]
        for i in range(1, len(z_vals)):
            self.assertGreaterEqual(z_vals[i], z_vals[i-1] - 1e-6)

    def test_continuous_z_above_integer(self):
        self.assertGreaterEqual(self.cont["Z_float"], self.sol["Z"] - 1e-4)

    def test_slack_variables_non_negative(self):
        from fractions import Fraction
        for k, v in self.res["slack"].items():
            self.assertGreaterEqual(float(Fraction(v)), -1e-9)

    def test_basis_has_correct_length(self):
        for snap in self.res["iterations"]:
            self.assertEqual(len(snap["basis"]), 3)

    def test_simplex_chapter2_function(self):
        from modules.simplex import simplex_chapter2
        res = simplex_chapter2()
        self.assertEqual(res["integer"]["Z"], 106)

    def test_iterations_plot(self):
        import matplotlib.pyplot as plt
        from modules.simplex import plot_simplex_iterations
        fig = plot_simplex_iterations()
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_saturation_plot(self):
        import matplotlib.pyplot as plt
        from modules.simplex import plot_constraints_saturation
        fig = plot_constraints_saturation()
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_rapport_chapter2(self):
        from modules.simplex import rapport_chapter2
        report = rapport_chapter2()
        self.assertIn("106", report)
        self.assertIn("x₁", report)
        self.assertIn("x₃", report)

    def test_parametric_different_budget(self):
        from modules.simplex import Simplex
        s = Simplex(budget=80)
        r = s.solve()
        self.assertEqual(r["status"], "optimal")
        self.assertGreaterEqual(r["integer"]["Z"], 106)


# ════════════════════════════════════════════════════════════
#  Tests — Visualisation
# ════════════════════════════════════════════════════════════
class TestVisualisation(unittest.TestCase):

    def test_dashboard_etape2(self):
        import matplotlib.pyplot as plt
        from modules.visualisation import plot_dashboard_etape2
        fig = plot_dashboard_etape2()
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.axes), 4)
        plt.close(fig)

    def test_comparison_plot(self):
        import matplotlib.pyplot as plt
        from modules.visualisation import plot_comparison
        fig = plot_comparison()
        self.assertIsNotNone(fig)
        plt.close(fig)

    def test_gain_is_positive(self):
        from modules.linear_prog import solve_chapter1
        from modules.simplex import simplex_chapter2
        z1 = solve_chapter1()["integer"]["Z"]
        z2 = simplex_chapter2()["integer"]["Z"]
        self.assertGreater(z2, z1, "Ch.2 doit être meilleur que Ch.1")

    def test_gain_value(self):
        from modules.linear_prog import solve_chapter1
        from modules.simplex import simplex_chapter2
        z1 = solve_chapter1()["integer"]["Z"]
        z2 = simplex_chapter2()["integer"]["Z"]
        gain = (z2 - z1) / z1 * 100
        self.assertAlmostEqual(gain, 12.77, delta=0.5)


# ── Lancement direct ─────────────────────────────────────────
if __name__ == "__main__":
    B = "\033[1m"; G = "\033[92m"; R = "\033[91m"; RE = "\033[0m"
    print(f"\n{B}EMSI — Tests Étape 2 — Algorithmes d'Optimisation{RE}")
    print("─" * 55)
    runner = unittest.TextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestChapter1, TestChapter2, TestVisualisation]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    result = runner.run(suite)
    print()
    if result.wasSuccessful():
        n = result.testsRun
        print(f"{G}{B}✔  {n}/{n} tests passent — Étape 2 validée !{RE}\n")
    else:
        f = len(result.failures) + len(result.errors)
        print(f"{R}{B}✘  {f} test(s) échoué(s){RE}\n")
