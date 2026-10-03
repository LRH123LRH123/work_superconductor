"""Independent limits and physical consistency checks for the teaching solver."""
import unittest
import numpy as np
from scipy.integrate import quad
from bcs import BCSModel, dynes_dos, to_kelvin


class BCSChecks(unittest.TestCase):
    def test_zero_temperature_integral(self):
        model = BCSModel()
        d0 = model.delta0_exact
        integral = quad(lambda x: 1 / np.sqrt(x*x + d0*d0), 0, 1)[0]
        self.assertAlmostEqual(integral, 1 / model.coupling, places=9)

    def test_weak_coupling_limits(self):
        model = BCSModel(0.18)
        tc = model.critical_temperature()
        reference = 2 * np.exp(np.euler_gamma) / np.pi * np.exp(-1 / 0.18)
        self.assertLess(abs(tc / reference - 1), 1e-6)
        self.assertLess(abs(2 * model.delta0_exact / tc - 3.527753977862), 1e-4)

    def test_monotonic_gap_and_residual(self):
        model = BCSModel()
        tc = model.critical_temperature()
        ts = np.linspace(0, 0.99 * tc, 25)
        ds = np.array([model.gap(t) for t in ts])
        # The exponentially small low-T change is below floating-point resolution.
        self.assertTrue(np.all(np.diff(ds) <= 1e-12))
        self.assertLess(ds[-1], ds[0])
        self.assertTrue(np.all(ds > 0))
        self.assertLess(max(abs(model.residual(d, t)) for d, t in zip(ds, ts)), 1e-8)

    def test_normal_state_and_endpoint(self):
        model = BCSModel()
        tc = model.critical_temperature()
        self.assertEqual(model.gap(tc), 0)
        self.assertEqual(model.gap(1.2 * tc), 0)
        self.assertLess(abs(model.residual(0, tc)), 1e-8)

    def test_coupling_increases_tc(self):
        ts = [BCSModel(g).critical_temperature() for g in (0.2, 0.3, 0.5)]
        self.assertTrue(np.all(np.diff(ts) > 0))

    def test_dos_symmetry_and_normal_limit(self):
        e = np.linspace(-1, 1, 101)
        self.assertTrue(np.allclose(dynes_dos(e, 0), 1))
        self.assertTrue(np.allclose(dynes_dos(e, 0.2), dynes_dos(-e, 0.2)))

    def test_units_and_bad_inputs(self):
        self.assertAlmostEqual(to_kelvin(0.1, 20), 23.209036243, places=7)
        for g in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                BCSModel(g)
        with self.assertRaises(ValueError):
            BCSModel().gap(-1)
        for value in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                to_kelvin(0.1, value)
            with self.assertRaises(ValueError):
                dynes_dos([0.0], 0.2, value)
            with self.assertRaises(ValueError):
                BCSModel().gap(0.02, tc=value)
        with self.assertRaises(ValueError):
            dynes_dos([float("nan")], 0.2)


if __name__ == "__main__":
    unittest.main()
