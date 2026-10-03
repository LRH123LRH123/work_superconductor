"""Reproduce tables, plots and a validation report from the teaching BCS model."""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

from bcs import BCSModel, dynes_dos, to_kelvin


def save_csv(path, columns, header):
    np.savetxt(path, np.column_stack(columns), delimiter=",", header=header,
               comments="", fmt="%.12g")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coupling", type=float, default=0.30)
    parser.add_argument("--cutoff-mev", type=float, default=20.0)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    if not np.isfinite(args.cutoff_mev) or args.cutoff_mev <= 0:
        parser.error("cutoff-mev must be finite and positive")
    model = BCSModel(args.coupling)
    args.out.mkdir(parents=True, exist_ok=True)
    tc = model.critical_temperature()
    d0 = model.delta0_exact
    reduced_t = np.linspace(0, 1.10, 111)
    gaps = np.array([model.gap(t * tc, tc=tc) for t in reduced_t])
    residuals = np.array([model.residual(d, t * tc) if d > 0 else np.nan
                          for t, d in zip(reduced_t, gaps)])
    save_csv(args.out / "gap_vs_temperature.csv",
             [reduced_t, reduced_t * tc, gaps, gaps / d0, residuals],
             "T_over_Tc,kBT_over_Ec,Delta_over_Ec,Delta_over_Delta0,gap_residual")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    ax.plot(reduced_t, gaps / d0, color="#087F8C", lw=2.8, label="Finite-cutoff solution")
    approx = np.zeros_like(reduced_t)
    mask = (reduced_t > 0) & (reduced_t < 1)
    approx[0] = 1
    approx[mask] = np.tanh(1.74 * np.sqrt(1 / reduced_t[mask] - 1))
    ax.plot(reduced_t, approx, "--", color="#C65B35", label="Common interpolation (approx.)")
    ax.set(xlabel=r"$T/T_c$", ylabel=r"$\Delta(T)/\Delta(0)$", ylim=(-0.02, 1.08),
           title=f"Isotropic BCS model: g = {args.coupling:.2f}")
    ax.legend(); ax.grid(alpha=0.16)
    fig.savefig(args.out / "gap_vs_temperature.png", dpi=180); plt.close(fig)

    gs = np.array([0.18, 0.22, 0.26, 0.30, 0.40, 0.50, 0.60])
    tcs = np.array([BCSModel(g).critical_temperature() for g in gs])
    ratios = np.array([2 * BCSModel(g).delta0_exact / t for g, t in zip(gs, tcs)])
    weak_tcs = 2 * np.exp(np.euler_gamma) / np.pi * np.exp(-1 / gs)
    save_csv(args.out / "coupling_scan.csv", [gs, tcs, weak_tcs, ratios],
             "g,kBTc_over_Ec,weak_coupling_Tc,2Delta0_over_kBTc")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), layout="constrained")
    axes[0].semilogy(gs, tcs, "o-", color="#087F8C", label="Numerical")
    axes[0].semilogy(gs, weak_tcs, "--", color="#C65B35", label="Weak-coupling limit")
    axes[0].set(xlabel="g", ylabel=r"$k_BT_c/E_c$"); axes[0].legend()
    axes[1].plot(gs, ratios, "o-", color="#087F8C")
    axes[1].axhline(2 * np.pi / np.exp(np.euler_gamma), color="#C65B35", ls="--")
    axes[1].set(xlabel="g", ylabel=r"$2\Delta(0)/(k_BT_c)$")
    fig.savefig(args.out / "coupling_scan.png", dpi=180); plt.close(fig)

    energies = np.linspace(-3 * d0, 3 * d0, 1201)
    eta = 0.03 * d0
    dos = dynes_dos(energies, d0, eta)
    save_csv(args.out / "dos.csv", [energies / d0, dos], "E_over_Delta0,Ns_over_Nn")
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    ax.plot(energies / d0, dos, color="#087F8C", lw=2)
    ax.axhline(1, color="#B3B3B3", ls="--")
    ax.set(xlabel=r"$E/\Delta(0)$", ylabel=r"$N_s(E)/N_n(0)$",
           title=r"Illustrative Dynes DOS: $\eta/\Delta(0)=0.03$")
    fig.savefig(args.out / "dos.png", dpi=180); plt.close(fig)

    tolerances = [1e-6, 1e-8, 1e-10]
    converged_tc = [BCSModel(args.coupling, e, e).critical_temperature() for e in tolerances]
    save_csv(args.out / "convergence.csv", [tolerances, converged_tc], "quad_tolerance,kBTc_over_Ec")
    report = {
        "model": "constant single-spin DOS; symmetric cutoff; isotropic mean field",
        "coupling_g": args.coupling, "cutoff_mev": args.cutoff_mev,
        "Delta0_over_Ec": d0, "kBTc_over_Ec": tc,
        "Tc_K_for_assumed_cutoff": to_kelvin(tc, args.cutoff_mev),
        "gap_ratio": 2 * d0 / tc,
        "weak_coupling_gap_ratio": float(2 * np.pi / np.exp(np.euler_gamma)),
        "max_gap_residual_below_Tc": float(np.nanmax(np.abs(residuals))),
        "tc_relative_change_tolerance_1e6_to_1e10": abs(converged_tc[0] / converged_tc[-1] - 1),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
        "interpretation": "Learning benchmark, not a material-specific Tc prediction or paper reproduction."
    }
    (args.out / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
