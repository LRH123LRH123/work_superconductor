"""Generate validated spectra and single-spin LDOS plots for the fixed-gap lesson."""
import argparse
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from bdg import (momentum_block, bdg_chain, analytic_chain_spectrum,
                 particle_hole_operator, electron_ldos)


def csv(path, values, columns):
    np.savetxt(path, values, delimiter=",", header=columns, comments="", fmt="%.12g")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    n, hopping, mu, delta, eta = 48, 1.0, -0.5, 0.25, 0.04
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    colors = ["#087F8C", "#C65B35", "#78734C"]
    xi = np.linspace(-3, 3, 241)
    momentum = np.array([np.linalg.eigvalsh(momentum_block(x, delta)) for x in xi])
    reference = np.sqrt(xi*xi+delta*delta)
    csv(args.out / "momentum_spectrum.csv", np.c_[xi, momentum, -reference, reference],
        "xi,E_minus_numeric,E_plus_numeric,E_minus_analytic,E_plus_analytic")
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    ax.plot(xi, momentum[:, 0], color=colors[0], lw=2, label="BdG eigenvalues")
    ax.plot(xi, momentum[:, 1], color=colors[0], lw=2)
    ax.plot(xi[::10], reference[::10], "o", mfc="none", color=colors[1], label="Analytic")
    ax.plot(xi[::10], -reference[::10], "o", mfc="none", color=colors[1])
    ax.set(xlabel=r"$\xi/J$", ylabel=r"$E/J$", title="Uniform 2 x 2 BdG: fixed gap")
    ax.legend()
    fig.savefig(args.out / "momentum_spectrum.png", dpi=180)
    plt.close(fig)

    solutions, errors = {}, {}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), layout="constrained")
    for ax, boundary in zip(axes, ["periodic", "open"]):
        h = bdg_chain(n, hopping, mu, delta, boundary)
        eigenvalues, vectors = np.linalg.eigh(h)
        exact = analytic_chain_spectrum(n, hopping, mu, delta, boundary)
        solutions[boundary] = (h, eigenvalues, vectors)
        errors[boundary] = float(np.max(abs(eigenvalues-exact)))
        csv(args.out / (boundary+"_spectrum.csv"), np.c_[np.arange(2*n), eigenvalues, exact],
            "sorted_index,E_numeric,E_analytic")
        ax.plot(exact, color=colors[0], lw=2, label="Analytic")
        ax.plot(np.arange(0, 2*n, 3), eigenvalues[::3], "o", mfc="none",
                color=colors[1], ms=5, label="Real-space matrix")
        ax.set(xlabel="Sorted eigenvalue index", ylabel="E/J", title=boundary.capitalize())
        ax.legend(fontsize=9)
    fig.savefig(args.out / "chain_spectrum.png", dpi=180)
    plt.close(fig)

    energy_grid = np.linspace(-3, 3, 1201)
    _, ep, vp = solutions["periodic"]
    ho, eo, vo = solutions["open"]
    periodic_ldos = electron_ldos(energy_grid, ep, vp, eta)
    open_ldos = electron_ldos(energy_grid, eo, vo, eta)
    csv(args.out / "boundary_ldos.csv",
        np.c_[energy_grid, periodic_ldos.mean(axis=1), open_ldos[:, 0], open_ldos[:, n//2]],
        "energy,periodic_mean,open_edge,open_center")
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    for values, color, label in zip([periodic_ldos.mean(axis=1), open_ldos[:, 0],
                                    open_ldos[:, n//2]], colors,
                                   ["Periodic mean", "Open edge", "Open center"]):
        ax.plot(energy_grid, values, color=color, label=label, lw=1.5)
    ax.set(xlabel="E/J", ylabel=r"$\rho_{i,\uparrow}$ (1/J)",
           title=f"Single-spin electron LDOS: eta/J={eta}")
    ax.legend(fontsize=9)
    fig.savefig(args.out / "boundary_ldos.png", dpi=180)
    plt.close(fig)

    potential = np.zeros(n)
    potential[n//2] = 2.0
    impurity_h = bdg_chain(n, hopping, mu, delta, "open", potential)
    ei, vi = np.linalg.eigh(impurity_h)
    impurity_ldos = electron_ldos(energy_grid, ei, vi, eta)
    csv(args.out / "impurity_ldos.csv",
        np.c_[energy_grid, open_ldos[:, n//2], impurity_ldos[:, n//2], impurity_ldos[:, n//2+1]],
        "energy,clean_center,impurity_site,neighbor_site")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), layout="constrained")
    axes[0].plot(energy_grid, open_ldos[:, n//2], color=colors[0], label="Clean center")
    axes[0].plot(energy_grid, impurity_ldos[:, n//2], color=colors[1], label="Scalar impurity")
    axes[0].set(xlabel="E/J", ylabel="Single-spin LDOS (1/J)")
    axes[0].legend(fontsize=9)
    axes[1].plot(np.arange(n), impurity_ldos[np.argmin(abs(energy_grid-0.4)), :], color=colors[0])
    axes[1].axvline(n//2, color=colors[1], ls="--")
    axes[1].set(xlabel="Site index (zero-based)", ylabel="LDOS at E/J=0.4")
    fig.savefig(args.out / "impurity_ldos.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), layout="constrained")
    for size, color in zip([24, 48, 96], colors):
        es, vs = np.linalg.eigh(bdg_chain(size, hopping, mu, delta, "periodic"))
        axes[0].plot(energy_grid, electron_ldos(energy_grid, es, vs, eta).mean(axis=1),
                     color=color, label=f"N={size}")
    for broadening, color in zip([0.02, 0.04, 0.08], colors):
        axes[1].plot(energy_grid, electron_ldos(energy_grid, ep, vp, broadening).mean(axis=1),
                     color=color, label=f"eta/J={broadening}")
    for ax in axes:
        ax.set(xlabel="E/J", ylabel="Mean single-spin LDOS (1/J)")
        ax.legend(fontsize=9)
    axes[0].set_title("Finite-size sampling, fixed eta")
    axes[1].set_title("Spectral broadening, fixed N")
    fig.savefig(args.out / "size_and_broadening.png", dpi=180)
    plt.close(fig)

    c = particle_hole_operator(n)
    weight_error = float(np.max(abs(np.sum(abs(vo[:n, :])**2, axis=1)-1)))
    report = {
        "date": "2026-10-03",
        "model": "Fixed-gap spin-singlet reduced BdG block, not a spinless Kitaev model",
        "parameters": {"N": n, "hopping_J": hopping, "mu_over_J": mu,
                       "Delta_over_J": delta, "eta_over_J": eta},
        "momentum_spectrum_max_error": float(np.max(abs(momentum[:, 1]-reference))),
        "chain_spectrum_max_errors": errors,
        "hermiticity_max_error": float(np.max(abs(ho-ho.conj().T))),
        "reduced_particle_hole_max_error": float(np.max(abs(c@ho.conj()@c.conj().T+ho))),
        "paired_spectrum_max_error": float(np.max(abs(eo+eo[::-1]))),
        "eigenvector_orthonormality_max_error": float(np.max(abs(vo.conj().T@vo-np.eye(2*n)))),
        "eigenvector_residual_max_error": float(np.max(abs(ho@vo-vo*eo[None, :]))),
        "single_spin_completeness_max_error": weight_error,
        "finite_window_weight_open_center": float(np.trapz(open_ldos[:, n//2], energy_grid)),
        "minimum_positive_open_energy": float(np.min(eo[eo>0])),
        "minimum_positive_impurity_energy": float(np.min(ei[ei>0])),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "matplotlib": matplotlib.__version__},
        "interpretation": "No gap self-consistency, Tc, transport, or topological invariant. Finite-window LDOS misses Lorentzian tails."
    }
    (args.out / "validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
