"""Collect a one-atom Al SCF scan; do not infer phonon or Tc convergence."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RY_TO_MEV = 13605.693122994
NUMBER = r"([-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?)"


def parse_scf(text):
    if "JOB DONE." not in text or "convergence has been achieved" not in text:
        raise ValueError("SCF is not both converged and completed")
    patterns = {
        "energy_Ry": r"!\s*total energy\s*=\s*" + NUMBER + r"\s*Ry",
        "fermi_eV": r"the Fermi energy is\s*" + NUMBER,
        "pressure_kbar": r"total\s+stress[^\n]*P=\s*" + NUMBER,
        "iterations": r"convergence has been achieved in\s+(\d+)\s+iterations",
    }
    result = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if not matches:
            raise ValueError(f"Missing required field: {key}")
        result[key] = float(matches[-1].replace("D", "E").replace("d", "e"))
    result["iterations"] = int(result["iterations"])
    if not all(np.isfinite(value) for value in result.values()):
        raise ValueError("Non-finite SCF result")
    return result


def summarize(rows, tolerance_meV=1.0):
    cuts = [r["ecutwfc_Ry"] for r in rows]
    if len(cuts) < 2 or any(b <= a for a, b in zip(cuts, cuts[1:])):
        raise ValueError("Need at least two strictly increasing cutoffs")
    if not np.isfinite(tolerance_meV) or tolerance_meV <= 0:
        raise ValueError("Tolerance must be positive and finite")
    reference = rows[-1]["energy_Ry"]
    enriched = []
    for row in rows:
        delta = (row["energy_Ry"] - reference) * RY_TO_MEV
        enriched.append({**row, "difference_meV_per_atom": delta,
                         "abs_difference_meV_per_atom": abs(delta)})
    # The reference alone cannot demonstrate convergence.
    acceptable = [r["ecutwfc_Ry"] for i, r in enumerate(enriched[:-1])
                  if all(x["abs_difference_meV_per_atom"] <= tolerance_meV
                         for x in enriched[i:])]
    return {
        "reference_ecutwfc_Ry": cuts[-1],
        "tolerance_meV_per_atom": tolerance_meV,
        "lowest_tested_acceptable_Ry": min(acceptable) if acceptable else None,
        "rows": enriched,
        "scope": "One atom per cell; fixed ecutrho, k mesh, smearing, geometry and pseudo",
        "limitation": "Finite-reference total-energy criterion only; not phonon, EPC or Tc convergence",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--tolerance-mev", type=float, default=1.0)
    args = parser.parse_args()
    rows, hashes = [], []
    for directory in sorted(args.root.glob("ecut_*"), key=lambda p: int(p.name.split("_")[1])):
        source = (directory / "scf.in").read_text(encoding="utf-8")
        for expression in [r"nat\s*=\s*1\b", r"ecutrho\s*=\s*640\b"]:
            if not re.search(expression, source):
                raise ValueError("This teaching collector assumes nat=1 and ecutrho=640")
        ec = int(directory.name.split("_")[1])
        if not re.search(rf"ecutwfc\s*=\s*{ec}\b", source):
            raise ValueError("Directory and input cutoffs disagree")
        output = directory / "output"
        rows.append({"ecutwfc_Ry": ec, **parse_scf(output.read_text(encoding="utf-8"))})
        for p in [directory / "scf.in", output]:
            hashes.append({"path": p.relative_to(args.root).as_posix(),
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    report = summarize(rows, args.tolerance_mev)
    record_path = args.root / "results/cluster_record.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {}
    archived_hashes = {item["path"]: item["sha256"] for item in record.get("files", [])
                       if "path" in item and "sha256" in item}
    unchanged = bool(archived_hashes) and all(
        item["path"] in archived_hashes and item["sha256"] == archived_hashes[item["path"]]
        for item in hashes)
    report.update({"job_id": record.get("job_id") if unchanged else None,
                   "date": record.get("date") if unchanged else None,
                   "fixed_parameters": {"ecutrho_Ry": 640, "k_mesh": [8, 8, 8],
                                        "k_shift": [1, 1, 1], "smearing": "mv",
                                        "degauss_Ry": 0.02, "nat": 1},
                   "sha256": hashes})
    target = args.root / "results"
    target.mkdir(exist_ok=True)
    with (target / "cutoff_scan.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(report["rows"][0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["rows"])
    (target / "validation.json").write_text(json.dumps(report, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), layout="constrained")
    cutoffs = [r["ecutwfc_Ry"] for r in report["rows"]]
    axes[0].plot(cutoffs, [r["abs_difference_meV_per_atom"] for r in report["rows"]],
                 "o-", color="#117E83")
    axes[0].axhline(args.tolerance_mev, ls="--", color="#C55B43",
                   label=f"{args.tolerance_mev:g} meV/atom target")
    axes[0].set(xlabel="Wavefunction cutoff (Ry)", ylabel="Absolute difference (meV/atom)",
                title="Energy relative to 80 Ry (finite reference)")
    axes[0].legend()
    axes[1].plot(cutoffs, [r["pressure_kbar"] for r in report["rows"]], "o-", color="#857140")
    axes[1].set(xlabel="Wavefunction cutoff (Ry)", ylabel="Pressure (kbar)",
                title="Stress is a separate observable")
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.savefig(target / "cutoff_convergence.png", dpi=180)
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
