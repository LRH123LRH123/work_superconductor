"""Constant-DOS, isotropic BCS model with a symmetric energy cutoff.

All energies and k_B*T are measured in units of the cutoff E_c.
g = N_single_spin(0) * V; the DOS normalization is stated in the tutorial.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

KB_EV_K = 8.617333262145e-5


@dataclass(frozen=True)
class BCSModel:
    coupling: float = 0.30
    epsabs: float = 1e-10
    epsrel: float = 1e-10

    def __post_init__(self):
        if not math.isfinite(self.coupling) or self.coupling <= 0:
            raise ValueError("coupling must be finite and positive")
        if not 0 < self.epsabs < 1 or not 0 < self.epsrel < 1:
            raise ValueError("quadrature tolerances must lie between 0 and 1")
        if 1 / self.coupling > 27:
            raise ValueError("gap too small for this teaching solver; use a log-scale solver")

    @property
    def delta0_exact(self) -> float:
        """Exact T=0 gap of this finite-cutoff model, not a weak-coupling fit."""
        return 1.0 / math.sinh(1.0 / self.coupling)

    def integral(self, delta: float, temperature: float) -> float:
        if not math.isfinite(delta) or not math.isfinite(temperature):
            raise ValueError("delta and temperature must be finite")
        if delta < 0 or temperature < 0:
            raise ValueError("delta and temperature must be nonnegative")
        if temperature == 0:
            return math.inf if delta == 0 else math.asinh(1 / delta)

        def kernel(xi):
            energy = math.hypot(xi, delta)
            # tanh(E/2t)/E has a finite limit as E -> 0 at positive t.
            if energy == 0:
                return 1 / (2 * temperature)
            return math.tanh(energy / (2 * temperature)) / energy

        scale = max(delta, temperature)
        points = sorted({x for x in (scale, 10 * scale) if 0 < x < 1})
        return quad(kernel, 0.0, 1.0, points=points,
                    epsabs=self.epsabs, epsrel=self.epsrel, limit=300)[0]

    def residual(self, delta: float, temperature: float) -> float:
        return self.integral(delta, temperature) - 1 / self.coupling

    def critical_temperature(self) -> float:
        """Find the linearized pairing temperature without fitting Delta(T)."""
        d0 = self.delta0_exact
        scaled_t = brentq(lambda y: self.residual(0.0, y * d0),
                          0.01, 10.0, xtol=1e-12, rtol=1e-12)
        return scaled_t * d0

    def gap(self, temperature: float, tc: float | None = None) -> float:
        if not math.isfinite(temperature) or temperature < 0:
            raise ValueError("temperature must be finite and nonnegative")
        if temperature == 0:
            return self.delta0_exact
        if tc is None:
            tc = self.critical_temperature()
        if not math.isfinite(tc) or tc <= 0:
            raise ValueError("tc must be finite and positive")
        if temperature >= tc:
            return 0.0
        d0 = self.delta0_exact
        return d0 * brentq(lambda y: self.residual(y * d0, temperature),
                          0.0, 1.0, xtol=1e-12, rtol=1e-12)


def dynes_dos(energies, delta: float, broadening: float = 0.002):
    """N_s(E)/N_n(0) with phenomenological Dynes broadening, not measured DOS."""
    if not math.isfinite(delta) or not math.isfinite(broadening) or delta < 0 or broadening <= 0:
        raise ValueError("finite delta >= 0 and finite broadening > 0 required")
    energies = np.asarray(energies, dtype=float)
    if not np.all(np.isfinite(energies)):
        raise ValueError("energies must be finite")
    z = np.abs(energies) + 1j * broadening
    return np.real(z / np.sqrt(z * z - delta * delta))


def to_kelvin(temperature: float, cutoff_mev: float) -> float:
    if not math.isfinite(cutoff_mev) or cutoff_mev <= 0:
        raise ValueError("cutoff_mev must be finite and positive")
    if not math.isfinite(temperature) or temperature < 0:
        raise ValueError("temperature must be finite and nonnegative")
    return temperature * cutoff_mev * 1e-3 / KB_EV_K
