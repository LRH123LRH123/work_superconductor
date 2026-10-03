"""Independent analytic and consistency tests for the fixed-gap BdG lesson."""
import unittest
import numpy as np
from bdg import (momentum_block, normal_chain, bdg_chain, analytic_chain_spectrum,
                 particle_hole_operator, electron_ldos)


class BdGChecks(unittest.TestCase):
    def test_momentum_spectrum(self):
        for xi in [-2.0, -0.3, 0.0, 0.7, 2.0]:
            delta = 0.25 * np.exp(0.7j)
            expected = np.array([-1, 1]) * np.sqrt(xi*xi + abs(delta)**2)
            np.testing.assert_allclose(np.linalg.eigvalsh(momentum_block(xi, delta)),
                                       expected, atol=1e-12)

    def test_coherence_factors(self):
        xi, delta = 0.7, 0.25
        energy, vectors = np.linalg.eigh(momentum_block(xi, delta))
        self.assertAlmostEqual(abs(vectors[0, 1])**2, (1+xi/energy[1])/2)

    def test_periodic_analytic_spectrum(self):
        h = bdg_chain(24, hopping=1.0, mu=-0.5, delta=0.25, boundary="periodic")
        np.testing.assert_allclose(np.linalg.eigvalsh(h),
                                   analytic_chain_spectrum(24, 1.0, -0.5, 0.25, "periodic"),
                                   atol=1e-11)

    def test_open_analytic_spectrum(self):
        h = bdg_chain(25, hopping=1.0, mu=-0.5, delta=0.25, boundary="open")
        np.testing.assert_allclose(np.linalg.eigvalsh(h),
                                   analytic_chain_spectrum(25, 1.0, -0.5, 0.25, "open"),
                                   atol=1e-11)

    def test_hermiticity_and_reduced_particle_hole(self):
        phases = 0.25 * np.exp(1j * np.linspace(0, 0.8, 12))
        h = bdg_chain(12, delta=phases, potential=np.linspace(-0.2, 0.3, 12))
        c = particle_hole_operator(12)
        np.testing.assert_allclose(h, h.conj().T, atol=1e-12)
        np.testing.assert_allclose(c @ h.conj() @ c.conj().T, -h, atol=1e-12)
        np.testing.assert_allclose(c @ c.conj(), -np.eye(24), atol=1e-12)
        e = np.linalg.eigvalsh(h)
        np.testing.assert_allclose(e, -e[::-1], atol=1e-11)

    def test_normal_limit(self):
        normal = normal_chain(18, mu=-0.5)
        reference = np.sort(np.r_[np.linalg.eigvalsh(normal), -np.linalg.eigvalsh(normal)])
        np.testing.assert_allclose(np.linalg.eigvalsh(bdg_chain(18, mu=-0.5, delta=0)),
                                   reference, atol=1e-11)

    def test_global_phase_invariance(self):
        real = np.linalg.eigvalsh(bdg_chain(18, delta=0.25))
        complex_phase = np.linalg.eigvalsh(bdg_chain(18, delta=0.25*np.exp(1.3j)))
        np.testing.assert_allclose(real, complex_phase, atol=1e-11)

    def test_eigenvectors_and_single_spin_weight(self):
        h = bdg_chain(20, delta=0.25)
        e, v = np.linalg.eigh(h)
        np.testing.assert_allclose(v.conj().T @ v, np.eye(40), atol=1e-12)
        np.testing.assert_allclose(h @ v, v * e[None, :], atol=1e-11)
        np.testing.assert_allclose(np.sum(abs(v[:20, :])**2, axis=1), 1, atol=1e-12)

    def test_ldos_and_positive_only_equivalence(self):
        n, eta = 16, 0.04
        e, v = np.linalg.eigh(bdg_chain(n, delta=0.25))
        grid = np.linspace(-3, 3, 301)
        actual = electron_ldos(grid, e, v, eta)
        keep = e > 0
        lorentz = lambda center: eta / (np.pi * ((grid[:, None] - center)**2 + eta**2))
        expected = (lorentz(e[keep]) @ abs(v[:n, keep].T)**2
                    + lorentz(-e[keep]) @ abs(v[n:, keep].T)**2)
        np.testing.assert_allclose(actual, expected, atol=1e-11)
        self.assertTrue(np.all(actual >= 0))

    def test_scalar_impurity_is_not_shiba_or_majorana(self):
        potential = np.zeros(24)
        potential[12] = 2.0
        e = np.linalg.eigvalsh(bdg_chain(24, delta=0.25, potential=potential))
        self.assertGreaterEqual(np.min(abs(e)), 0.25-1e-12)

    def test_invalid_inputs(self):
        for n in [2, 3.5, True]:
            with self.assertRaises(ValueError):
                bdg_chain(n)
        with self.assertRaises(ValueError):
            bdg_chain(8, boundary="typo")
        with self.assertRaises(ValueError):
            bdg_chain(8, delta=[0.25]*7)
        with self.assertRaises(ValueError):
            bdg_chain(8, mu=float("nan"))
        with self.assertRaises(ValueError):
            electron_ldos([0], np.zeros(4), np.eye(4), 0)
        with self.assertRaises(ValueError):
            electron_ldos([0], np.array([]), np.empty((0, 0)), 0.04)


if __name__ == "__main__":
    unittest.main()
