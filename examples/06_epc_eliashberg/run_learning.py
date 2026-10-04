"""Rebuild official Al postprocessing and a separate Einstein-model learning exercise."""
from pathlib import Path
import csv
import hashlib
import json
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from epc import load_spectrum, moments, qe_rectangle_moments, tc_estimates, find_tc, solve_gap, RY_TO_MEV
from cluster.pb_regression.validate_epw import check_log, check_table

ROOT = Path(__file__).resolve().parent


def build():
    manifest = json.loads((ROOT/"reference/source_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        if item["stored_in_repository"]:
            path = ROOT/"reference/qe-7.5"/item["source_path"]
            if (hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]
                    or path.stat().st_size != item["bytes"]):
                raise ValueError("Official source differs from the pinned manifest")
    source = ROOT/"reference/qe-7.5/PHonon/examples/tetra_example/reference/aluminum.a2F.dat"
    w, a = load_spectrum(source, "Ry")
    al = moments(w, a)
    al["qe_rectangle_rule"] = qe_rectangle_moments(w, a)
    al["origin"] = "Official QE Al reference, not our previous Al SCF calculation"
    al["reference_lambda_from_a2f"] = 0.3963915104345056
    al["reference_omega_log_Ry"] = 1.950315478791357e-3
    al["lambda_reference_difference"] = abs(al["qe_rectangle_rule"]["lambda"]-al["reference_lambda_from_a2f"])
    al["omega_log_reference_difference_meV"] = abs(al["qe_rectangle_rule"]["omega_log_meV"]-al["reference_omega_log_Ry"]*RY_TO_MEV)
    if al["lambda_reference_difference"] > 1e-6 or al["omega_log_reference_difference_meV"] > 1e-4:
        raise ValueError("Spectral integration does not reproduce the supplied reference")
    al["tc_formula_example"] = tc_estimates(al["lambda"], al["omega_log_meV"], al["omega2_meV"], 0.1)
    pb_root = ROOT/"cluster/pb_regression"
    record = json.loads((pb_root/"results/cluster_record.json").read_text(encoding="utf-8"))
    for item in record["files"]:
        data = (pb_root/item["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"] or len(data) != item["bytes"]:
            raise ValueError("Cluster archive/source hash mismatch")
    spectrum = pb_root/"results/pb.a2f.01.300.000"
    if check_table(spectrum.read_text(), "epw_legacy") != 500:
        raise ValueError("Unexpected pinned spectral row count")
    pw, pa = load_spectrum(spectrum, "meV", 1, "epw_legacy")
    pb = moments(pw, pa)
    pb["lambda_from_cluster_log"] = check_log((pb_root/"results/output").read_text())
    benchmark = ROOT/"reference/qe-7.5/test-suite/epw_metal/benchmark.out.git.inp=epw1.in.args=3"
    pb["lambda_upstream_benchmark"] = float(re.search(r"^\s*lambda\s*:\s*([0-9.]+)\s*$", benchmark.read_text(), re.M)[1])
    pb["lambda_benchmark_difference"] = abs(pb["lambda_from_cluster_log"]-pb["lambda_upstream_benchmark"])
    pb["footer_lambda_column1"] = 0.1608855
    if pb["lambda_benchmark_difference"] > 2e-6 or abs(pb["lambda"]-pb["footer_lambda_column1"]) > 2e-6:
        raise ValueError("Pinned Pb benchmark differs beyond the predeclared print-level tolerance")
    pb["raw_data_job_id"] = record["selected_raw_data_job_id"]
    pb["scope"] = "3^3 to 6^3 regression; upstream DFPT reused; not a material Tc prediction"
    parameters = {"lambda": 1.0, "Omega_meV": 10.0, "mu_star": 0.1,
                  "n_positive": 96, "coulomb_cutoff_meV": 100.0}
    tc = find_tc(2, 25, 1, 10, .1, 96, 100)
    solutions = [solve_gap(t, 1, 10, .1, 96, 100) for t in [2, 4, 6, 8, 10, 12, 15, 20, 25]]
    rows = [{k: s[k] for k in ["T_K", "iterations", "gap_residual_meV", "Z_residual",
                               "linearized_eigenvalue", "superconducting"]}
            | {"Delta_iw0_meV": s["gap_meV"][0], "Z_iw0": s["Z"][0]} for s in solutions]
    target = ROOT/"results"
    target.mkdir(exist_ok=True)
    report = {"date": "2026-10-04", "al_reference": al, "pb_regression": pb, "einstein_parameters": parameters,
              "einstein_tc_bracket": tc, "einstein_temperature_results": rows,
              "frequency_solution_T4": solutions[1],
              "scope": "Fixed teaching model and reference postprocessing; no DFT convergence scans or material Tc claim"}
    (target/"validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8", newline="\n")
    with (target/"einstein_gap_temperature.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13})
    teal, coral = "#117E83", "#C55B43"
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    axes[0].plot(pw, pa, color=teal)
    axes[0].set(xlabel="Phonon energy (meV)", ylabel="alpha2F (column 1)")
    axes[1].plot(pw, pb["cumulative_lambda"], color=coral)
    axes[1].set(xlabel="Phonon energy (meV)", ylabel="Cumulative lambda")
    fig.suptitle("Pb coarse regression: our SCF/NSCF/EPW, upstream DFPT; not a material prediction")
    fig.savefig(target/"pb_regression_spectrum.png", dpi=180); plt.close(fig)
    data = np.loadtxt(source)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), layout="constrained")
    axes[0].plot(w, a, color=teal)
    axes[0].set(xlabel="Phonon energy (meV)", ylabel="alpha2F (dimensionless)")
    axes[1].plot(w, al["cumulative_lambda"], color=coral)
    axes[1].set(xlabel="Phonon energy (meV)", ylabel="Cumulative lambda")
    axes[2].plot(w, data[:, 2]/RY_TO_MEV, color=teal)
    axes[2].set(xlabel="Phonon energy (meV)", ylabel="Phonon DOS (1/meV)")
    fig.suptitle("Official Al reference: offline spectral postprocessing, not a new cluster run")
    fig.savefig(target/"al_spectral_moments.png", dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    temperatures = [r["T_K"] for r in rows]
    axes[0].plot(temperatures, [r["Delta_iw0_meV"] for r in rows], "o-", color=teal)
    axes[0].set(xlabel="Temperature (K)", ylabel="Delta(i omega_0) (meV)")
    axes[1].plot(temperatures, [r["linearized_eigenvalue"] for r in rows], "o-", color=coral)
    axes[1].axhline(1, ls="--", color="#546968")
    axes[1].set(xlabel="Temperature (K)", ylabel="Largest real gap-kernel eigenvalue")
    for ax in axes:
        ax.axvspan(tc["lower_K"], tc["upper_K"], color="#857140", alpha=.3)
    fig.suptitle("Einstein teaching model; fixed 96 positive Matsubara frequencies, not Pb")
    fig.savefig(target/"einstein_gap_temperature.png", dpi=180); plt.close(fig)
    s = solutions[1]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    axes[0].plot(s["frequency_meV"], s["gap_meV"], "o-", markersize=3, color=teal)
    axes[0].set(xlabel="Positive Matsubara energy (meV)", ylabel="Delta(i omega_n) (meV)")
    axes[1].plot(s["frequency_meV"], s["Z"], "o-", markersize=3, color=coral)
    axes[1].set(xlabel="Positive Matsubara energy (meV)", ylabel="Z(i omega_n)")
    fig.suptitle("Einstein model at 4 K: imaginary-axis functions, not real-axis spectral gaps")
    fig.savefig(target/"einstein_frequency.png", dpi=180); plt.close(fig)
    print(json.dumps({"Al_lambda": al["lambda"], "Al_omega_log_meV": al["omega_log_meV"],
                      "Einstein_Tc_bracket_K": [tc["lower_K"], tc["upper_K"]],
                      "max_gap_residual_meV": max(r["gap_residual_meV"] for r in rows)}, indent=2))
    return report


if __name__ == "__main__":
    build()
