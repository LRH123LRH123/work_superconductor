"""Validate teaching scope, pinned sources, archived jobs and executable notebook."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import nbformat
import numpy as np


def validate_package(example):
    example = Path(example)
    problems = []
    manifest = json.loads((example/"reference/source_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        if item["stored_in_repository"]:
            file = example/"reference/qe-7.5"/item["source_path"]
            if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"] or file.stat().st_size != item["bytes"]:
                problems.append(f"EPC official source changed: {item['source_path']}")
    cluster = example/"cluster/pb_regression"
    record = json.loads((cluster/"results/cluster_record.json").read_text(encoding="utf-8"))
    for item in record["files"]+record["final_job_files"]:
        if not item.get("archived_local", True):
            continue
        file = cluster/item["path"]
        if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"] or file.stat().st_size != item["bytes"]:
            problems.append(f"EPC cluster source changed: {item['path']}")
    for attempt in record["attempts"]:
        snapshot = json.loads((cluster/f"results/job_{attempt['job_id']}_snapshot.json").read_text(encoding="utf-8"))
        if snapshot["schedulerState"] != attempt["state"] or not snapshot["schedulerTerminal"]:
            problems.append("EPC job record differs from captured scheduler state")
    if ([a["state"] for a in record["attempts"]] != ["FAILED", "FAILED", "COMPLETED"]
            or record["selected_raw_data_job_id"] != "313824"):
        problems.append("EPC job identities/scope were silently changed")
    for name in ["scf.in", "nscf.in", "epw.in", "pb.a2f.01.300.000"]:
        if (cluster/"results"/name).read_bytes() != (cluster/"results/final_job"/name).read_bytes():
            problems.append(f"EPC retry physical inputs or spectrum differ: {name}")
    if (cluster/"validate_epw.py").read_bytes() != (cluster/"results/final_job/validate_epw.py").read_bytes():
        problems.append("EPC active checker differs from successful cluster checker")
    for file in [cluster/"submit.sh", cluster/"prepare_cluster.py", cluster/"validate_epw.py",
                 *cluster.glob("results/*.in"), *cluster.glob("results/final_job/*.in")]:
        if b"\r" in file.read_bytes():
            problems.append(f"EPC cluster script/input must use LF: {file}")
    if "PB_FIXED_REGRESSION_OK" not in (cluster/"results/final_job/slurm-313836.out").read_text():
        problems.append("EPC final cluster stdout lacks validated completion")

    spec = importlib.util.spec_from_file_location("epc_learning_validation", example/"epc.py")
    module = importlib.util.module_from_spec(spec)
    previous = sys.path.copy()
    try:
        sys.path.insert(0, str(example))
        spec.loader.exec_module(module)
        saved = json.loads((example/"results/validation.json").read_text(encoding="utf-8"))
        for section, file, unit, fmt in [
            ("al_reference", example/"reference/qe-7.5/PHonon/examples/tetra_example/reference/aluminum.a2F.dat", "Ry", "plain"),
            ("pb_regression", cluster/"results/pb.a2f.01.300.000", "meV", "epw_legacy"),
        ]:
            w, a = module.load_spectrum(file, unit, 1, fmt)
            rebuilt = module.moments(w, a)
            for key in ["lambda", "omega_log_meV", "omega2_meV", "cumulative_lambda"]:
                if not np.allclose(rebuilt[key], saved[section][key], rtol=1e-12, atol=1e-12):
                    problems.append(f"EPC saved spectral moment differs from archive: {section}/{key}")
        al = saved["al_reference"]
        w, a = module.load_spectrum(example/"reference/qe-7.5/PHonon/examples/tetra_example/reference/aluminum.a2F.dat", "Ry")
        if abs(module.qe_rectangle_moments(w, a)["lambda"]-al["reference_lambda_from_a2f"]) > 1e-6:
            problems.append("EPC Al reference bin sum is not reproduced")
        pb = saved["pb_regression"]
        if pb["lambda_benchmark_difference"] > 2e-6 or pb["raw_data_job_id"] != "313824":
            problems.append("EPC Pb benchmark comparison/identity invalid")
        tc = module.find_tc(2, 25, 1, 10, .1)
        if tc != saved["einstein_tc_bracket"]:
            problems.append("EPC finite model Tc cannot be rebuilt")
        model = module.solve_gap(4, 1, 10, .1)
        for key in ["gap_meV", "Z"]:
            if not np.allclose(model[key], saved["frequency_solution_T4"][key], rtol=1e-10, atol=1e-10):
                problems.append(f"EPC nonlinear model cannot be rebuilt: {key}")
        if tc["is_material_prediction"] or tc["matsubara_cutoff_converged"]:
            problems.append("EPC model makes an unsupported material/cutoff claim")
        for row in saved["einstein_temperature_results"]:
            if not (0 <= row["gap_residual_meV"] < 1e-8 and 0 <= row["Z_residual"] < 1e-9):
                problems.append("EPC nonlinear residual failed")
    finally:
        sys.path[:] = previous
    notebook = nbformat.read(example/"EPC与Eliashberg交互教程.ipynb", as_version=4)
    nbformat.validate(notebook)
    cells = [c for c in notebook.cells if c.cell_type == "code"]
    if len(cells) != 8 or any(c.execution_count is None for c in cells):
        problems.append("EPC Notebook has missing/unexecuted code cells")
    if any(o.output_type == "error" for c in cells for o in c.outputs):
        problems.append("EPC Notebook contains an error")
    return problems


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    problems = validate_package(root/"examples/06_epc_eliashberg")
    if problems:
        raise SystemExit("\n".join(problems))
    print("PASS: EPC reference/cluster hashes, real job identities, spectral/model rebuild and 8 executed cells")
