"""Fixed-gap, spin-singlet BdG benchmarks; this is NOT a spinless Kitaev chain.

Reduced basis: (c_1_up, ..., c_N_up, c_1_down^dagger, ..., c_N_down^dagger).
H = [[h, -D], [-D^dagger, -h*]]. All energies use the same hopping-energy unit.
"""
from __future__ import annotations
import numpy as np


def _n_sites(n):
    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)) or n < 3:
        raise ValueError("n must be an integer >= 3; this avoids two-site ring ambiguity")
    return int(n)


def _real_finite(value, name):
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real scalar") from exc
    if not np.isfinite(value):
        raise ValueError(f"{name} must be a finite real scalar")
    return value


def _profile(value, n, name, real=False):
    values = np.asarray(value)
    if values.ndim == 0:
        values = np.full(n, values)
    if values.shape != (n,):
        raise ValueError(f"{name} must be scalar or have shape ({n},)")
    values = np.asarray(values, dtype=complex)
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{name} must be finite")
    if real and np.any(values.imag != 0):
        raise ValueError(f"{name} must be real for this nonmagnetic lesson")
    return values.real if real else values


def momentum_block(xi, delta):
    xi = _real_finite(xi, "xi")
    delta = complex(delta)
    if not np.isfinite(delta):
        raise ValueError("delta must be finite")
    return np.array([[xi, -delta], [-delta.conjugate(), -xi]], dtype=complex)


def normal_chain(n, hopping=1.0, mu=-0.5, boundary="open", potential=0.0):
    n = _n_sites(n)
    hopping, mu = _real_finite(hopping, "hopping"), _real_finite(mu, "mu")
    if hopping <= 0 or boundary not in {"open", "periodic"}:
        raise ValueError("positive hopping and boundary='open' or 'periodic' required")
    h = np.diag(_profile(potential, n, "potential", real=True) - mu)
    i = np.arange(n-1)
    h[i, i+1] = h[i+1, i] = -hopping
    if boundary == "periodic":
        h[0, -1] = h[-1, 0] = -hopping
    return h


def bdg_chain(n, hopping=1.0, mu=-0.5, delta=0.25, boundary="open", potential=0.0):
    h = normal_chain(n, hopping, mu, boundary, potential)
    pairing = np.diag(_profile(delta, len(h), "delta"))
    return np.block([[h, -pairing], [-pairing.conj().T, -h.conj()]])


def analytic_chain_spectrum(n, hopping=1.0, mu=-0.5, delta=0.25, boundary="open"):
    n = _n_sites(n)
    hopping, mu = _real_finite(hopping, "hopping"), _real_finite(mu, "mu")
    normal_chain(n, hopping, mu, boundary)
    delta = complex(delta)
    if not np.isfinite(delta):
        raise ValueError("delta must be a finite scalar for the analytic uniform result")
    if boundary == "periodic":
        momenta = 2*np.pi*np.arange(n)/n
    else:
        momenta = np.pi*np.arange(1, n+1)/(n+1)
    xi = -2*hopping*np.cos(momenta)-mu
    positive = np.sqrt(xi*xi + abs(delta)**2)
    return np.sort(np.r_[-positive, positive])


def particle_hole_operator(n):
    n = _n_sites(n)
    eye, zero = np.eye(n), np.zeros((n, n))
    # In this reduced spin-singlet block C = tau_y K, not spinless tau_x K.
    return np.block([[zero, -1j*eye], [1j*eye, zero]])


def electron_ldos(energies, eigenvalues, eigenvectors, eta=0.04):
    """Single-spin electron LDOS, summing ALL 2N BdG eigenstates once.

    Return shape (n_energy, n_sites). Lorentzian eta is an illustrative
    spectral broadening, not a DFT smearing or an inferred scattering rate.
    """
    eta = _real_finite(eta, "eta")
    grid, vals, vecs = (np.asarray(x) for x in (energies, eigenvalues, eigenvectors))
    if eta <= 0 or grid.ndim != 1 or vals.ndim != 1 or vals.size < 6 or vals.size % 2:
        raise ValueError("eta > 0 and one-dimensional energy/eigenvalue arrays required")
    if vecs.shape != (vals.size, vals.size) or grid.size == 0:
        raise ValueError("eigenvectors must contain a full square eigenbasis")
    if not all(np.all(np.isfinite(x)) for x in (grid, vals, vecs)):
        raise ValueError("all energies and eigenvectors must be finite")
    if np.iscomplexobj(grid) or np.iscomplexobj(vals):
        raise ValueError("energies must be real")
    n = vals.size // 2
    kernel = eta / (np.pi * ((grid[:, None]-vals[None, :])**2 + eta**2))
    weights = abs(vecs[:n, :].T)**2
    return kernel @ weights
