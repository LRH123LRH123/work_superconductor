"""Independent signed-frequency and analytical checks for a teaching model."""
import unittest
import numpy as np
from two_band import Model, linearized, leading_eigenpair, instability, find_tc, solve_gap

KB = 0.08617333262145


def fixture():
    return Model([.4, .6], [[2.5, .3], [.3, 1.]], np.full((2, 2), .1), 10., 100., 32)


def signed_update(model, temperature, gap):
    # This reference never calls the folded kernel or update implementation.
    b, count = gap.shape
    positive = (2*np.arange(count)+1)*np.pi*KB*temperature
    signed = np.r_[-positive[::-1], positive]
    extended = np.concatenate([gap[:, ::-1], gap], axis=1)
    denominator = np.sqrt(signed[None, :]**2+extended**2)
    z = np.ones_like(gap)
    new_gap = np.zeros_like(gap)
    for i in range(b):
        for n, w in enumerate(positive):
            for j in range(b):
                kernel = model.lambda_matrix[i, j]*model.omega_meV**2/(
                    model.omega_meV**2+(w-signed)**2)
                z[i, n] += np.pi*KB*temperature/w*np.sum(kernel*signed/denominator[j])
                new_gap[i, n] += np.pi*KB*temperature*np.sum(
                    (kernel-model.mu_matrix[i, j]*(abs(signed)<model.coulomb_cutoff_meV))
                    *extended[j]/denominator[j])
    return z, new_gap/z


class TwoBandTests(unittest.TestCase):
    def test_destination_dos_and_reciprocity(self):
        m = fixture()
        np.testing.assert_allclose(m.lambda_matrix, [[1., .18], [.12, .6]])
        np.testing.assert_allclose(m.mu_matrix, [[.04, .06], [.04, .06]])
        np.testing.assert_allclose(m.weights[:, None]*m.lambda_matrix,
                                   (m.weights[:, None]*m.lambda_matrix).T)
        self.assertAlmostEqual(m.average_lambda, .904)
        self.assertFalse(np.allclose(m.lambda_matrix, m.lambda_matrix.T))

    def test_weights_are_not_silently_normalized(self):
        with self.assertRaises(ValueError):
            Model([4, 6], np.ones((2, 2)), np.ones((2, 2))*.1)

    def test_invalid_model_inputs(self):
        for weights, coupling, coulomb in [
            ([0, 1], np.ones((2, 2)), np.zeros((2, 2))),
            ([.4, .6], [[1, .3], [.2, 1]], np.zeros((2, 2))),
            ([.4, .6], [[1, -.1], [-.1, 1]], np.zeros((2, 2))),
            ([.4, .6], np.ones((2, 2)), [[.1, .2], [.1, .1]]),
            ([.4, .6], [[1, np.nan], [np.nan, 1]], np.zeros((2, 2))),
            ([.4, .6], np.ones((1, 1)), np.zeros((2, 2))),
        ]:
            with self.subTest(weights=weights, coupling=coupling), self.assertRaises(ValueError):
                Model(weights, coupling, coulomb)

    def test_parameters_and_temperature_rejected(self):
        for options in [dict(omega_meV=0), dict(coulomb_cutoff_meV=-1),
                        dict(n_positive=1), dict(n_positive=True), dict(omega_meV=np.inf)]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                Model([1], [[1]], [[.1]], **options)
        for temperature in [0, -1, np.nan, np.inf]:
            with self.assertRaises(ValueError):
                linearized(temperature, fixture())

    def test_linearized_full_signed_sum_with_cutoff_crossing(self):
        m = Model([.4, .6], [[2.5, .3], [.3, 1]], np.full((2, 2), .1), 10, 12, 16)
        w, z, matrix = linearized(5, m)
        self.assertTrue(w[0] < 12 < w[-1])
        independent_z, _ = signed_update(m, 5, np.zeros((2, 16)))
        np.testing.assert_allclose(z, independent_z, atol=2e-14)
        for column in [0, 5, 15, 16, 24, 31]:
            basis = np.zeros((2, 16)); basis.flat[column] = 1e-6
            _, updated = signed_update(m, 5, basis)
            np.testing.assert_allclose(matrix[:, column], updated.ravel()/1e-6,
                                       rtol=1e-10, atol=1e-12)

    def test_equal_rows_reduce_to_analytical_single_band(self):
        t, lam, mu, n = 6, .9, .1, 16
        m = Model([.4, .6], np.full((2, 2), lam), np.full((2, 2), mu), 10, 100, n)
        w, z, matrix = linearized(t, m)
        minus = lam*100/(100+(w[:, None]-w[None, :])**2)
        plus = lam*100/(100+(w[:, None]+w[None, :])**2)
        expected_z = 1+np.pi*KB*t/w*np.sum(minus-plus, axis=1)
        single = np.pi*KB*t*(minus+plus-2*mu*(w<100)[None, :])/(
            expected_z[:, None]*w[None, :])
        np.testing.assert_allclose(z, np.tile(expected_z, (2, 1)))
        vector = np.sin(np.arange(n)+.2)
        np.testing.assert_allclose(matrix@np.tile(vector, 2), np.tile(single@vector, 2))
        self.assertAlmostEqual(instability(t, m)['eigenvalue'], leading_eigenpair(single)[0])

    def test_largest_real_not_absolute_eigenvalue(self):
        value, vector, residual = leading_eigenpair(np.diag([-5., .9, .3]))
        self.assertEqual(value, .9)
        self.assertLess(residual, 1e-14)
        self.assertEqual(np.max(abs(vector)), 1)

    def test_band_permutation_covariance(self):
        m = fixture(); permutation = np.array([1, 0])
        p = Model(m.weights[permutation], m.bare_lambda[np.ix_(permutation, permutation)],
                  m.bare_mu[np.ix_(permutation, permutation)], 10, 100, 32)
        w, z, matrix = linearized(5, m)
        wp, zp, bp = linearized(5, p)
        indices = np.r_[np.arange(32, 64), np.arange(32)]
        np.testing.assert_allclose(wp, w)
        np.testing.assert_allclose(zp, z[permutation])
        np.testing.assert_allclose(bp, matrix[np.ix_(indices, indices)])
        self.assertAlmostEqual(instability(5, m)['eigenvalue'], instability(5, p)['eigenvalue'])

    def test_unconnected_blocks_remain_independent(self):
        m = Model([.4, .6], [[2.5, 0], [0, 1]], [[.25, 0], [0, 1/6]], n_positive=16)
        _, _, matrix = linearized(6, m)
        self.assertEqual(np.max(abs(matrix[:16, 16:])), 0)
        self.assertEqual(np.max(abs(matrix[16:, :16])), 0)

    def test_unconnected_nonlinear_bands_reduce_independently(self):
        two = Model([.5, .5], np.diag([2., 1.8]), np.diag([.2, .2]), n_positive=32)
        result = solve_gap(4, two)
        for i, lam in enumerate([1., .9]):
            one = Model([1], [[lam]], [[.1]], n_positive=32)
            independent = solve_gap(4, one)
            np.testing.assert_allclose(result['gap_meV'][i], independent['gap_meV'][0], atol=1e-7)
            np.testing.assert_allclose(result['Z'][i], independent['Z'][0], atol=1e-9)

    def test_disconnected_stable_component_stays_normal(self):
        two = Model([.5, .5], np.diag([2., .2]), np.diag([.2, .2]), n_positive=32)
        result = solve_gap(4, two)
        self.assertTrue(result['superconducting'])
        self.assertGreater(result['gap_meV'][0][0], 0)
        self.assertEqual(np.max(abs(np.array(result['gap_meV'][1]))), 0)

    def test_inactive_coulomb_links_do_not_merge_components(self):
        two = Model([.5, .5], np.diag([2., 1.8]), np.full((2, 2), .2),
                    coulomb_cutoff_meV=1, n_positive=32)
        result = solve_gap(4, two)
        for i, lam in enumerate([1., .9]):
            one = Model([1], [[lam]], [[0]], n_positive=32)
            independent = solve_gap(4, one)
            np.testing.assert_allclose(result['gap_meV'][i], independent['gap_meV'][0], atol=1e-7)
            np.testing.assert_allclose(result['Z'][i], independent['Z'][0], atol=1e-9)
        self.assertEqual(result['band_component_labels'], [0, 1])

    def test_tc_bracket_and_scope(self):
        m = fixture(); result = find_tc(2, 25, m)
        self.assertLessEqual(result['upper_K']-result['lower_K'], .01)
        self.assertGreater(instability(result['lower_K'], m)['eigenvalue'], 1)
        self.assertLessEqual(instability(result['upper_K'], m)['eigenvalue'], 1)
        self.assertFalse(result['is_material_prediction'])
        self.assertFalse(result['matsubara_cutoff_converged'])

    def test_missing_bracket_rejected(self):
        m = Model([1], [[0]], [[0]], n_positive=16)
        for bounds in [(2, 25), (25, 2), (0, 25), (np.nan, 25)]:
            with self.assertRaises(ValueError):
                find_tc(*bounds, m)

    def test_nonlinear_signed_equation_residual(self):
        m = fixture(); result = solve_gap(4, m)
        gap, z = np.array(result['gap_meV']), np.array(result['Z'])
        expected_z, expected_gap = signed_update(m, 4, gap)
        self.assertLess(np.max(abs(expected_z-z)), 1e-9)
        self.assertLess(np.max(abs(expected_gap-gap)), 1e-8)
        self.assertGreater(gap[0, 0], gap[1, 0])
        self.assertGreater(gap[1, 0], 0)

    def test_normal_branch_is_exact_zero(self):
        result = solve_gap(25, fixture())
        self.assertFalse(result['superconducting'])
        self.assertEqual(np.max(abs(np.array(result['gap_meV']))), 0)

    def test_nonlinear_equal_rows_reduce(self):
        one = Model([1], [[1]], [[.1]], n_positive=32)
        two = Model([.4, .6], np.ones((2, 2)), np.full((2, 2), .1), n_positive=32)
        a, b = solve_gap(4, one), solve_gap(4, two)
        np.testing.assert_allclose(b['gap_meV'], np.tile(a['gap_meV'], (2, 1)), atol=1e-7)
        np.testing.assert_allclose(b['Z'], np.tile(a['Z'], (2, 1)), atol=1e-9)

    def test_iteration_controls_and_failure(self):
        for options in [dict(mixing=0), dict(mixing=1.1), dict(max_iterations=0)]:
            with self.assertRaises(ValueError):
                solve_gap(4, fixture(), **options)
        with self.assertRaises(ValueError):
            solve_gap(4, fixture(), max_iterations=1)

    def test_model_arrays_are_readonly(self):
        m = fixture()
        with self.assertRaises(ValueError):
            m.lambda_matrix[0, 0] = 3


if __name__ == '__main__':
    unittest.main()
