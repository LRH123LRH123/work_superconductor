"""Tests target units, spectral moments, and finite-Matsubara equations, not DFT scans."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
try:
    import epc
except ImportError:
    epc = None


class EPCChecks(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(epc, "The spectral/Eliashberg implementation is not present yet")

    def test_frequency_units_do_not_rescale_dimensionless_a2f(self):
        w = np.linspace(1, 10, 1001)
        a = 0.01*w
        r = epc.moments(w, a)
        self.assertAlmostEqual(r["lambda"], 0.18, places=12)
        scaled = epc.moments(2*w, a)
        self.assertAlmostEqual(scaled["lambda"], r["lambda"], places=12)
        self.assertAlmostEqual(scaled["omega_log_meV"], 2*r["omega_log_meV"], places=11)
        self.assertAlmostEqual(scaled["omega2_meV"], 2*r["omega2_meV"], places=11)

    def test_logarithmic_moment_matches_independent_integral(self):
        w = np.linspace(1, 10, 10001)
        r = epc.moments(w, 0.01*w)
        expected = np.exp((10*np.log(10)-10+1)/9)
        self.assertLess(abs(r["omega_log_meV"]-expected), 1e-7)

    def test_qe_rectangle_rule_differs_from_trapezoid_at_nonzero_endpoint(self):
        self.assertTrue(hasattr(epc, "qe_rectangle_moments"), "Reference rectangle rule is missing")
        w, a = np.array([1., 2., 3.]), np.array([0., .2, .3])
        rectangle = epc.qe_rectangle_moments(w, a)
        self.assertAlmostEqual(rectangle["lambda"], 0.4)
        trapezoid = epc.moments(w, a)
        self.assertAlmostEqual(rectangle["lambda"]-trapezoid["lambda"], 0.1)

    def test_rectangle_reference_rule_rejects_nonuniform_bins(self):
        self.assertTrue(hasattr(epc, "qe_rectangle_moments"))
        with self.assertRaises(ValueError):
            epc.qe_rectangle_moments([1, 2, 4], [0, .2, .3])

    def test_load_requires_units_and_preserves_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"s.dat"
            p.write_text("# w A extra\n1D-3 0.2 99\n2D-3 0.4 98\n", encoding="utf-8")
            w, a = epc.load_spectrum(p, "Ry")
            np.testing.assert_allclose(w, np.array([0.001, 0.002])*epc.RY_TO_MEV)
            np.testing.assert_allclose(a, [0.2, 0.4])
            with self.assertRaises(ValueError):
                epc.load_spectrum(p, "unknown")

    def test_bad_spectra_fail_instead_of_clipping(self):
        for w, a in [([1, 1], [1, 2]), ([2, 1], [1, 2]),
                     ([1, 2], [-1, 1]), ([1, np.nan], [1, 1]),
                     ([0, 1], [1, 1]), ([-1, 1], [0, 1]), ([1, 2], [0, 0])]:
            with self.subTest(w=w, a=a), self.assertRaises(ValueError):
                epc.moments(w, a)

    def test_zero_frequency_is_not_silently_dropped(self):
        with self.assertRaises(ValueError):
            epc.moments([0, 1, 2], [0, 0.1, 0.2])

    def test_mcmillan_and_full_allen_dynes_are_distinct(self):
        r = epc.tc_estimates(1.5, 10.0, 15.0, 0.1)
        base = 10/epc.KB_MEV_K/1.2*np.exp(-1.04*2.5/(1.5-0.1*(1+0.62*1.5)))
        self.assertAlmostEqual(r["modified_mcmillan_K"], base)
        self.assertGreater(r["allen_dynes_K"], base)
        with self.assertRaises(ValueError):
            epc.tc_estimates(0.01, 10, 15, 0.3)

    def test_einstein_kernel_is_even_and_static_value_is_lambda(self):
        nu = np.array([-20.0, 0, 20])
        np.testing.assert_allclose(epc.einstein_kernel(nu, 1.2, 10), [0.24, 1.2, 0.24])

    def test_positive_frequency_folding_matches_full_signed_sum(self):
        w, minus, plus, z, matrix = epc.linearized(8, 1.0, 10, 0.1, 8, 10)
        signed = np.r_[-w[::-1], w]
        trial_gap = np.linspace(.1, .8, len(w))
        signed_gap = np.r_[trial_gap[::-1], trial_gap]
        for i, wn in enumerate(w):
            normal = 1+np.pi*epc.KB_MEV_K*8/wn*np.sum(
                epc.einstein_kernel(wn-signed, 1, 10)*np.sign(signed))
            self.assertAlmostEqual(z[i], normal, places=12)
            full_pair = np.pi*epc.KB_MEV_K*8/z[i]*np.sum(
                (epc.einstein_kernel(wn-signed, 1, 10)-.1*(abs(signed)<10))
                *signed_gap/abs(signed))
            self.assertAlmostEqual((matrix@trial_gap)[i], full_pair, places=12)

    def test_linearized_eigenpair_satisfies_equation(self):
        r = epc.instability(8, 1, 10, 0.1, 48, 100)
        self.assertLess(r["eigen_residual"], 1e-10)
        self.assertTrue(np.isfinite(r["eigenvalue"]))

    def test_zero_coupling_is_normal_and_has_no_tc_bracket(self):
        r = epc.solve_gap(5, 0, 10, 0, 48, 100)
        np.testing.assert_allclose(r["gap_meV"], 0)
        np.testing.assert_allclose(r["Z"], 1)
        with self.assertRaises(ValueError):
            epc.find_tc(2, 20, 0, 10, 0, 48, 100)

    def test_nonlinear_solution_has_small_fixed_point_residual(self):
        r = epc.solve_gap(4, 1, 10, 0.1, 64, 100)
        self.assertTrue(r["superconducting"])
        self.assertGreater(r["gap_meV"][0], 0.1)
        self.assertLess(r["gap_residual_meV"], 1e-7)
        self.assertLess(r["Z_residual"], 1e-8)
        w = (2*np.arange(64)+1)*np.pi*epc.KB_MEV_K*4
        signed = np.r_[-w[::-1], w]
        gap, z = np.array(r["gap_meV"]), np.array(r["Z"])
        signed_gap = np.r_[gap[::-1], gap]
        denominator = np.sqrt(signed*signed+signed_gap*signed_gap)
        kernel = 100/(100+(w[:, None]-signed[None, :])**2)
        factor = np.pi*epc.KB_MEV_K*4
        full_z = 1+factor/w*(kernel@(signed/denominator))
        full_pair = factor*((kernel-.1*(abs(signed)<100)[None, :])@(signed_gap/denominator))
        self.assertLess(np.max(abs(z-full_z)), 1e-9)
        self.assertLess(np.max(abs(z*gap-full_pair)), 3e-8)

    def test_normal_solution_above_instability(self):
        r = epc.solve_gap(30, 1, 10, 0.1, 48, 100)
        self.assertFalse(r["superconducting"])
        np.testing.assert_allclose(r["gap_meV"], 0)

    def test_tc_bracket_is_reported_not_assumed(self):
        r = epc.find_tc(2, 25, 1, 10, 0.1, 48, 100)
        self.assertLess(r["upper_K"]-r["lower_K"], 0.011)
        self.assertGreater(epc.instability(r["lower_K"], 1, 10, 0.1, 48, 100)["eigenvalue"], 1)
        self.assertLessEqual(epc.instability(r["upper_K"], 1, 10, 0.1, 48, 100)["eigenvalue"], 1)

    def test_invalid_solver_parameters_rejected(self):
        for t, lam, omega, mu, n, cutoff in [(0, 1, 10, .1, 48, 100),
                (5, -1, 10, .1, 48, 100), (5, 1, 0, .1, 48, 100),
                (5, 1, 10, -1, 48, 100), (5, 1, 10, .1, 1, 100),
                (5, 1, 10, .1, 48, np.nan)]:
            with self.assertRaises(ValueError):
                epc.linearized(t, lam, omega, mu, n, cutoff)


if __name__ == "__main__":
    unittest.main()
