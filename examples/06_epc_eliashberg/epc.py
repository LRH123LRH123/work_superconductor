"""Original spectral postprocessing and finite positive-Matsubara Einstein model.

Energies use meV; alpha2F uses the dimensionless energy-axis convention.
This small solver is not EPW and does not infer a material spectral function.
"""
from pathlib import Path
import numpy as np
from scipy.linalg import eig
from cluster.pb_regression.validate_epw import parse_table

RY_TO_MEV = 13605.693122994
KB_MEV_K = 0.08617333262145


def load_spectrum(path, frequency_unit, spectral_column=1, file_format="plain"):
    factors = {"Ry": RY_TO_MEV, "eV": 1000.0, "meV": 1.0}
    if frequency_unit not in factors:
        raise ValueError("Declare frequency units: Ry, eV, or meV")
    data = np.asarray(parse_table(Path(path).read_text(encoding="utf-8"), file_format))
    if (not isinstance(spectral_column, int) or spectral_column < 1
            or spectral_column >= data.shape[1]):
        raise ValueError("Invalid zero-based alpha2F column")
    w, a = data[:, 0]*factors[frequency_unit], data[:, spectral_column]
    validate_spectrum(w, a)
    return w, a


def validate_spectrum(w, a):
    w, a = np.asarray(w, dtype=float), np.asarray(a, dtype=float)
    if (w.ndim != 1 or a.ndim != 1 or w.shape != a.shape or len(w) < 2
            or not np.all(np.isfinite(w)) or not np.all(np.isfinite(a))
            or np.any(w <= 0) or np.any(np.diff(w) <= 0) or np.any(a < 0)):
        raise ValueError("Need finite positive strictly increasing frequencies and nonnegative alpha2F")
    return w, a


def cumulative_trapezoid(y, x):
    return np.r_[0.0, np.cumsum(0.5*(y[:-1]+y[1:])*np.diff(x))]


def moments(w, a):
    w, a = validate_spectrum(w, a)
    cumulative = cumulative_trapezoid(2*a/w, w)
    lam = cumulative[-1]
    if not np.isfinite(lam) or lam <= 0:
        raise ValueError("Spectrum must give positive finite coupling")
    logmoment = np.trapz(2*a/w*np.log(w/1.0), w)/lam
    square = np.trapz(2*a*w, w)/lam
    return {"lambda": float(lam), "omega_log_meV": float(np.exp(logmoment)),
            "omega2_meV": float(np.sqrt(square)),
            "cumulative_lambda": cumulative.tolist(),
            "integration_range_meV": [float(w[0]), float(w[-1])],
            "low_frequency_extrapolated": False}


def tc_estimates(lam, omega_log_meV, omega2_meV, mu_star):
    values = [lam, omega_log_meV, omega2_meV, mu_star]
    if (not np.all(np.isfinite(values)) or min(values[:3]) <= 0 or mu_star < 0
            or omega2_meV < omega_log_meV*(1-1e-10)):
        raise ValueError("Invalid spectral moments or mu_star")
    denominator = lam-mu_star*(1+0.62*lam)
    if denominator <= 0:
        raise ValueError("McMillan denominator is nonpositive; approximation is not applicable")
    base = omega_log_meV/KB_MEV_K/1.2*np.exp(-1.04*(1+lam)/denominator)
    ratio = omega2_meV/omega_log_meV
    f1 = (1+(lam/(2.46*(1+3.8*mu_star)))**1.5)**(1/3)
    lambda2 = 1.82*(1+6.3*mu_star)*ratio
    f2 = 1+(ratio-1)*lam**2/(lam**2+lambda2**2)
    return {"mu_star": float(mu_star), "modified_mcmillan_K": float(base),
            "allen_dynes_K": float(base*f1*f2), "f1": float(f1), "f2": float(f2),
            "is_eliashberg_solution": False}


def qe_rectangle_moments(w, a):
    """Match the uniform-bin sum used by the supplied ALPHA2F reference output."""
    w, a = validate_spectrum(w, a)
    step = w[1]-w[0]
    if not np.allclose(np.diff(w), step, rtol=1e-9, atol=1e-12):
        raise ValueError("Reference rectangle sum requires a uniform energy grid")
    weights = 2*a/w*step
    lam = weights.sum()
    if lam <= 0:
        raise ValueError("No positive reference spectral weight")
    return {"lambda": float(lam), "omega_log_meV": float(np.exp(np.sum(weights*np.log(w))/lam)),
            "omega2_meV": float(np.sqrt(np.sum(weights*w*w)/lam)),
            "cumulative_lambda": np.cumsum(weights).tolist(),
            "rule": "Uniform-bin rectangle sum matching supplied QE output"}


def einstein_kernel(nu_meV, lam, omega_meV):
    if not np.all(np.isfinite([lam, omega_meV])) or lam < 0 or omega_meV <= 0:
        raise ValueError("Invalid Einstein parameters")
    nu = np.asarray(nu_meV, dtype=float)
    if not np.all(np.isfinite(nu)):
        raise ValueError("Nonfinite frequency difference")
    return lam*omega_meV**2/(omega_meV**2+nu**2)


def linearized(T_K, lam, omega_meV, mu_star, n_positive=96, coulomb_cutoff_meV=100):
    if (not np.all(np.isfinite([T_K, lam, omega_meV, mu_star, coulomb_cutoff_meV]))
            or T_K <= 0 or lam < 0 or omega_meV <= 0 or mu_star < 0
            or coulomb_cutoff_meV <= 0 or not isinstance(n_positive, int)
            or not 2 <= n_positive <= 512):
        raise ValueError("Invalid finite-Matsubara model parameters")
    w = (2*np.arange(n_positive)+1)*np.pi*KB_MEV_K*T_K
    minus = einstein_kernel(w[:, None]-w[None, :], lam, omega_meV)
    plus = einstein_kernel(w[:, None]+w[None, :], lam, omega_meV)
    factor = np.pi*KB_MEV_K*T_K
    z = 1+factor/w*np.sum(minus-plus, axis=1)
    pair = minus+plus-2*mu_star*(w<coulomb_cutoff_meV)[None, :]
    matrix = factor*pair/(z[:, None]*w[None, :])
    return w, minus, plus, z, matrix


def instability(T_K, lam, omega_meV, mu_star, n_positive=96, coulomb_cutoff_meV=100):
    *_, matrix = linearized(T_K, lam, omega_meV, mu_star, n_positive, coulomb_cutoff_meV)
    values, vectors = eig(matrix)
    real = np.flatnonzero(abs(values.imag) < 1e-9)
    if not len(real):
        raise ValueError("No real instability eigenvalue found")
    index = real[np.argmax(values[real].real)]
    value, vector = float(values[index].real), vectors[:, index].real
    residual = np.max(np.abs(matrix@vector-value*vector))
    return {"eigenvalue": value, "eigen_residual": float(residual)}


def find_tc(lower_K, upper_K, lam, omega_meV, mu_star, n_positive=96,
            coulomb_cutoff_meV=100, width_K=0.01):
    if not (0 < lower_K < upper_K and np.isfinite(width_K) and width_K > 0):
        raise ValueError("Invalid temperature bracket")
    def eigen(T):
        return instability(T, lam, omega_meV, mu_star, n_positive, coulomb_cutoff_meV)["eigenvalue"]
    if eigen(lower_K) <= 1 or eigen(upper_K) > 1:
        raise ValueError("Need superconducting lower bound and normal upper bound")
    for _ in range(80):
        if upper_K-lower_K <= width_K:
            break
        middle = (lower_K+upper_K)/2
        if eigen(middle) > 1:
            lower_K = middle
        else:
            upper_K = middle
    return {"lower_K": float(lower_K), "upper_K": float(upper_K),
            "midpoint_K": float((lower_K+upper_K)/2), "n_positive": n_positive,
            "is_material_prediction": False, "matsubara_cutoff_converged": False}


def solve_gap(T_K, lam, omega_meV, mu_star, n_positive=96, coulomb_cutoff_meV=100,
              max_iterations=3000, mixing=0.3):
    if not 0 < mixing <= 1 or not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError("Invalid nonlinear iteration controls")
    w, minus, plus, normal_z, _ = linearized(T_K, lam, omega_meV, mu_star,
                                           n_positive, coulomb_cutoff_meV)
    value = instability(T_K, lam, omega_meV, mu_star, n_positive, coulomb_cutoff_meV)["eigenvalue"]
    superconducting = value > 1
    gap = np.full(n_positive, 0.2*omega_meV) if superconducting else np.zeros(n_positive)
    z = normal_z.copy()
    factor = np.pi*KB_MEV_K*T_K
    pair = minus+plus-2*mu_star*(w<coulomb_cutoff_meV)[None, :]
    for iteration in range(1, max_iterations+1):
        denominator = np.sqrt(w*w+gap*gap)
        new_z = 1+factor/w*((minus-plus)@(w/denominator))
        new_gap = factor*(pair@(gap/denominator))/new_z
        dz, dg = np.max(abs(new_z-z)), np.max(abs(new_gap-gap))
        if dg < 1e-8 and dz < 1e-9:
            return {"T_K": float(T_K), "frequency_meV": w.tolist(), "gap_meV": gap.tolist(),
                    "Z": z.tolist(), "iterations": iteration, "gap_residual_meV": float(dg),
                    "Z_residual": float(dz), "superconducting": bool(superconducting),
                    "linearized_eigenvalue": value, "is_material_prediction": False}
        gap = (1-mixing)*gap+mixing*new_gap
        z = (1-mixing)*z+mixing*new_z
    raise ValueError("Nonlinear equations did not reach the declared fixed-point residual")
