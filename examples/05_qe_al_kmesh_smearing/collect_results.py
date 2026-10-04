"""Analyze a complete Al k-mesh/smearing grid without claiming a zero-smearing limit."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re

import numpy as np

RY_TO_MEV = 13605.693122994
NUM = r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?)"


def parse_scf(text):
    if ("JOB DONE." not in text or "convergence has been achieved" not in text
            or "Error in routine" in text):
        raise ValueError("SCF must be converged and completed without a QE error")
    patterns = {
        "energy_Ry": r"!\s*total energy\s*=\s*" + NUM + r"\s*Ry",
        "internal_energy_Ry": r"internal energy E=F\+TS\s*=\s*" + NUM,
        "minus_TS_Ry": r"smearing contrib\.\s*\(-TS\)\s*=\s*" + NUM,
        "fermi_eV": r"the Fermi energy is\s*" + NUM,
        "pressure_kbar": r"total\s+stress[^\n]*P=\s*" + NUM,
        "scf_accuracy_Ry": r"estimated scf accuracy\s*<\s*" + NUM,
        "iterations": r"convergence has been achieved in\s+(\d+)\s+iterations",
        "n_irreducible_k": r"number of k points=\s*(\d+)",
        "nbnd": r"number of Kohn-Sham states=\s*(\d+)",
        "degauss_output_Ry": r"smearing,\s*width \(Ry\)=\s*" + NUM,
    }
    result = {}
    for key, expression in patterns.items():
        matches = re.findall(expression, text)
        if not matches:
            raise ValueError(f"Missing QE field: {key}")
        result[key] = float(matches[-1].replace("D", "E").replace("d", "e"))
    if not all(np.isfinite(value) for value in result.values()):
        raise ValueError("Non-finite QE result")
    for key in ["iterations", "n_irreducible_k", "nbnd"]:
        result[key] = int(result[key])
        if result[key] <= 0:
            raise ValueError(f"Invalid positive integer: {key}")
    warning_pattern = r"c_bands:\s*\d+\s+eigenvalues not converged"
    final_iteration = re.split(r"iteration\s*#\s*\d+[^\n]*\n", text, flags=re.I)[-1]
    result["band_warning_messages_total"] = len(re.findall(warning_pattern, text))
    result["band_warning_messages_final_iteration"] = len(re.findall(warning_pattern, final_iteration))
    if result["band_warning_messages_final_iteration"]:
        raise ValueError("Final iteration still reports unconverged eigenvalues")
    identity = result["energy_Ry"]-result["minus_TS_Ry"]-result["internal_energy_Ry"]
    if abs(identity) > 2.1e-8:
        raise ValueError("F, -TS and internal E do not agree at QE print precision")
    return result


def validate_input(text, case):
    """Validate only the documented scalar one-atom teaching input, not all QE syntax."""
    clean = "\n".join(line.split("!", 1)[0] for line in text.splitlines())
    expected = {"ibrav": 2, "celldm(1)": 7.65339, "nat": 1, "ntyp": 1,
                "ecutwfc": 60, "ecutrho": 640, "nbnd": 6, "mixing_beta": 0.5,
                "conv_thr": 1e-10, "degauss": case["degauss_Ry"]}
    for key, value in expected.items():
        matches = re.findall(r"\b"+re.escape(key)+r"\s*=\s*"+NUM, clean, re.I)
        if len(matches) != 1:
            raise ValueError(f"Need one supported input assignment: {key}")
        actual = float(matches[0].replace("d", "e").replace("D", "E"))
        if not np.isclose(actual, value, rtol=1e-12, atol=1e-15):
            raise ValueError(f"Changed fixed/case parameter: {key}")
    for key, value in {"calculation": "scf", "occupations": "smearing",
                       "smearing": "mv", "prefix": "al", "outdir": "./scratch"}.items():
        matches = re.findall(r"\b"+key+r"\s*=\s*['\"]([^'\"]+)['\"]", clean, re.I)
        if matches != [value]:
            raise ValueError(f"Unexpected input string: {key}")
    match = re.search(r"K_POINTS\s+automatic\s*\n\s*(\d+)\s+(\d+)\s+(\d+)\s+"
                      r"(\d+)\s+(\d+)\s+(\d+)", clean, re.I)
    if not match or list(map(int, match.groups())) != [case["k_mesh"]]*3+[1, 1, 1]:
        raise ValueError("Wrong k grid/shift")
    if ("Al.pbe-n-kjpaw_psl.1.0.0.UPF" not in clean
            or not re.search(r"ATOMIC_POSITIONS\s+crystal\s*\n\s*Al\s+0\s+0\s+0\s*(?:\n|$)", clean)):
        raise ValueError("Unexpected pseudo or geometry")


def summarize(rows, thresholds):
    for key in ["energy_meV_per_atom", "pressure_kbar", "fermi_eV"]:
        if not np.isfinite(thresholds[key]) or thresholds[key] <= 0:
            raise ValueError("Thresholds must be positive and finite")
    pairs = [(r["degauss_Ry"], r["k_mesh"]) for r in rows]
    if len(set(pairs)) != len(pairs) or not rows:
        raise ValueError("Empty or duplicate scan")
    sigmas = sorted({r["degauss_Ry"] for r in rows}, reverse=True)
    grids = sorted({r["k_mesh"] for r in rows})
    if len(grids) < 3 or len(sigmas) < 2 or len(rows) != len(grids)*len(sigmas):
        raise ValueError("Need a complete rectangular grid: >=3 k meshes, >=2 smearings")
    for row in rows:
        for key in ["energy_Ry", "internal_energy_Ry", "pressure_kbar", "fermi_eV",
                    "degauss_Ry", "k_mesh"]:
            if not np.isfinite(row[key]):
                raise ValueError("Non-finite scan value")
        if row["degauss_Ry"] <= 0 or row["k_mesh"] < 2 or int(row["k_mesh"]) != row["k_mesh"]:
            raise ValueError("Invalid grid or smearing")
    enriched, summaries = [], []
    for sigma in sigmas:
        data = sorted([r for r in rows if r["degauss_Ry"] == sigma], key=lambda r: r["k_mesh"])
        reference = data[-1]
        plane = []
        for row in data:
            d_energy = (row["energy_Ry"]-reference["energy_Ry"])*RY_TO_MEV
            d_pressure = row["pressure_kbar"]-reference["pressure_kbar"]
            d_fermi = row["fermi_eV"]-reference["fermi_eV"]
            plane.append({**row, "energy_difference_meV_per_atom": d_energy,
                          "abs_energy_difference_meV_per_atom": abs(d_energy),
                          "pressure_difference_kbar": d_pressure,
                          "fermi_difference_eV": d_fermi,
                          "passes_joint_reference_test":
                          abs(d_energy) <= thresholds["energy_meV_per_atom"]
                          and abs(d_pressure) <= thresholds["pressure_kbar"]
                          and abs(d_fermi) <= thresholds["fermi_eV"]})
        acceptable = [row["k_mesh"] for i, row in enumerate(plane[:-1])
                      if all(p["passes_joint_reference_test"] for p in plane[i:])]
        summaries.append({"degauss_Ry": sigma, "reference_k": grids[-1],
                          "lowest_joint_acceptable_k": min(acceptable) if acceptable else None})
        enriched.extend(plane)
    candidates = [s["lowest_joint_acceptable_k"] for s in summaries]
    common = max(candidates) if all(k is not None for k in candidates) else None
    max_grid = [r for r in rows if r["k_mesh"] == grids[-1]]
    span = lambda key: max(r[key] for r in max_grid)-min(r[key] for r in max_grid)
    return {"rows": enriched, "thresholds": thresholds, "sigma_summaries": summaries,
            "common_tested_k": common, "reference_k": grids[-1],
            "sigma_sensitivity_at_max_k": {
                "energy_span_meV_per_atom": span("energy_Ry")*RY_TO_MEV,
                "internal_energy_span_meV_per_atom": span("internal_energy_Ry")*RY_TO_MEV,
                "pressure_span_kbar": span("pressure_kbar"), "fermi_span_eV": span("fermi_eV"),
                "is_zero_smearing_error_estimate": False},
            "scope": "Same-sigma finite-k references only; not zero-smearing, phonon, EPC or Tc convergence"}


def collect(root):
    plan = json.loads((root / "scan_plan.json").read_text(encoding="utf-8"))
    fixed = {"ecutwfc_Ry": 60, "ecutrho_Ry": 640, "celldm1_bohr": 7.65339,
             "nat": 1, "nbnd": 6, "smearing": "mv", "conv_thr_Ry": 1e-10,
             "k_shift": [1, 1, 1], "pseudopotential": "Al.pbe-n-kjpaw_psl.1.0.0.UPF"}
    if plan["fixed_parameters"] != fixed:
        raise ValueError("Plan differs from the documented fixed input contract")
    rows, hashes = [], []
    for case in plan["cases"]:
        input_path, output_path = root / case["id"] / "scf.in", root / case["id"] / "output"
        validate_input(input_path.read_text(encoding="utf-8"), case)
        parsed = parse_scf(output_path.read_text(encoding="utf-8"))
        if (not np.isclose(parsed["degauss_output_Ry"], case["degauss_Ry"])
                or parsed["nbnd"] != plan["fixed_parameters"]["nbnd"]
                or not 0 <= parsed["scf_accuracy_Ry"] <= plan["fixed_parameters"]["conv_thr_Ry"]):
            raise ValueError(f"Input/output or SCF accuracy mismatch: {case['id']}")
        rows.append({**case, **parsed})
        for p in [input_path, output_path]:
            hashes.append({"path": p.relative_to(root).as_posix(),
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    report = summarize(rows, plan["thresholds"])
    if report["reference_k"] != plan["reference_k"]:
        raise ValueError("Plan/reference mismatch")
    report.update({"fixed_parameters": plan["fixed_parameters"], "sha256": hashes})
    record_path = root / "results/cluster_record.json"
    if record_path.exists():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        archived = {r["path"]: r["sha256"] for r in record["files"]}
        unchanged = all(archived.get(r["path"]) == r["sha256"] for r in hashes)
        unchanged &= archived.get("scan_plan.json") == hashlib.sha256((root / "scan_plan.json").read_bytes()).hexdigest()
        report.update({"job_id": record["job_id"] if unchanged else None,
                       "date": record["date"] if unchanged else None})
    else:
        report.update({"job_id": None, "date": None})
    return report


def plot(report, target):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14})
    colors = ["#117E83", "#C55B43", "#857140"]
    sigmas = [s["degauss_Ry"] for s in report["sigma_summaries"]]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), layout="constrained")
    for sigma, color in zip(sigmas, colors):
        data = [r for r in report["rows"] if r["degauss_Ry"] == sigma]
        x = [r["k_mesh"] for r in data]
        for ax, key in zip(axes, ["abs_energy_difference_meV_per_atom",
                                  "pressure_difference_kbar", "fermi_difference_eV"]):
            ax.plot(x, [abs(r[key]) for r in data], "o-", color=color, label=f"sigma={sigma} Ry")
    labels = [("energy_meV_per_atom", "Energy difference (meV/atom)"),
              ("pressure_kbar", "Pressure difference (kbar)"), ("fermi_eV", "Fermi difference (eV)")]
    for ax, (threshold_key, label) in zip(axes, labels):
        ax.axhline(report["thresholds"][threshold_key], color="#546968", ls="--")
        ax.set(xlabel="k grid along each axis", ylabel=label)
        ax.set_xticks(sorted({r["k_mesh"] for r in report["rows"]}))
        ax.grid(alpha=0.2)
    axes[0].legend(fontsize=10)
    fig.suptitle(f"Each sigma compared ONLY with its own {report['reference_k']}^3 reference")
    fig.savefig(target / "kmesh_convergence.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), layout="constrained")
    max_data = sorted([r for r in report["rows"] if r["k_mesh"] == report["reference_k"]],
                      key=lambda r: r["degauss_Ry"])
    x = [r["degauss_Ry"] for r in max_data]
    for key, label, ax in zip(["energy_Ry", "pressure_kbar", "fermi_eV"],
                              ["F difference (meV/atom)",
                               "Pressure (kbar)", "Fermi energy (eV)"], axes):
        y = [((r[key]-max_data[0][key])*RY_TO_MEV if key == "energy_Ry" else r[key]) for r in max_data]
        ax.plot(x, y, "o-", color=colors[0])
        ax.set(xlabel="Cold-smearing width (Ry)", ylabel=label)
        ax.set_xticks(x)
        ax.margins(x=0.12)
        ax.grid(alpha=0.2)
    fig.suptitle("Smearing sensitivity at maximum tested k grid; NOT a zero-width extrapolation")
    fig.savefig(target / "smearing_sensitivity.png", dpi=180)
    plt.close(fig)
    grid_values = sorted({r["k_mesh"] for r in report["rows"]})
    matrix = np.array([[next(r["abs_energy_difference_meV_per_atom"] for r in report["rows"]
                             if r["degauss_Ry"] == sigma and r["k_mesh"] == k)
                        for k in grid_values] for sigma in sigmas])
    fig, ax = plt.subplots(figsize=(7.5, 3.6), layout="constrained")
    im = ax.imshow(matrix, cmap="YlGnBu", aspect="auto")
    ax.set(xticks=range(len(grid_values)), xticklabels=grid_values,
           yticks=range(len(sigmas)), yticklabels=sigmas,
           xlabel="k grid along each axis", ylabel="sigma (Ry)",
           title="Same-sigma energy differences (meV/atom)")
    for i in range(len(sigmas)):
        for j in range(len(grid_values)):
            ax.text(j, i, f"{matrix[i,j]:.3f}", ha="center", va="center",
                    color="white" if matrix[i,j] > 0.5*matrix.max() else "#183b3c")
    fig.colorbar(im, ax=ax, label="meV/atom")
    fig.savefig(target / "energy_grid.png", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    report = collect(args.root)
    target = args.root / "results"
    target.mkdir(exist_ok=True)
    with (target / "kmesh_smearing_scan.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(report["rows"][0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["rows"])
    (target / "validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8", newline="\n")
    plot(report, target)
    print(json.dumps({k: v for k, v in report.items() if k not in {"rows", "sha256"}}, indent=2))


if __name__ == "__main__":
    main()
