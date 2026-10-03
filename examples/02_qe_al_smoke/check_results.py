"""Summarize the saved QE smoke-test logs without claiming convergence of material properties."""
import argparse
import json
from pathlib import Path
import re


def extract(scf, phonon, asr="", asr_modes=""):
    energy = re.search(r"!\s+total energy\s+=\s+([-\d.]+)\s+Ry", scf)
    iterations = re.search(r"convergence has been achieved in\s+(\d+) iterations", scf)
    pattern = r"freq\s*\(\s*(\d+)\)\s*=\s*([-\d.]+)\s*\[THz\]\s*=\s*([-\d.]+)\s*\[cm-1\]"
    modes = [{"mode": int(i), "THz": float(t), "cm-1": float(c)}
             for i, t, c in re.findall(pattern, phonon)]
    corrected = [{"mode": int(i), "THz": float(t), "cm-1": float(c)}
                 for i, t, c in re.findall(pattern, asr_modes)]
    return {
        "pw_done": "JOB DONE" in scf,
        "ph_done": "JOB DONE" in phonon,
        "scf_converged": iterations is not None,
        "iterations": int(iterations.group(1)) if iterations else None,
        "total_energy_Ry": float(energy.group(1)) if energy else None,
        "raw_gamma_modes": modes,
        "asr_done": "JOB DONE" in asr,
        "crystal_asr_gamma_modes": corrected,
        "warnings": [
            "Raw negative Gamma acoustic frequencies are preserved; assess ASR and numerical convergence.",
            "This is not a full phonon dispersion, EPC calculation, or superconducting Tc prediction.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    scf = (args.results / "output").read_text(encoding="utf-8")
    phonon = (args.results / "phonon.output").read_text(encoding="utf-8")
    asr_file = args.results / "asr.output"
    asr = asr_file.read_text(encoding="utf-8") if asr_file.exists() else ""
    modes_file = args.results / "al.gamma.asr.modes"
    asr_modes = modes_file.read_text(encoding="utf-8") if modes_file.exists() else ""
    result = extract(scf, phonon, asr, asr_modes)
    print(json.dumps(result, indent=2))
    if not (result["pw_done"] and result["ph_done"] and result["scf_converged"]
            and len(result["raw_gamma_modes"]) == 3):
        raise SystemExit("Smoke-test log checks failed")
    if asr_file.exists() and not (result["asr_done"] and len(result["crystal_asr_gamma_modes"]) == 3):
        raise SystemExit("ASR postprocessing log checks failed")


if __name__ == "__main__":
    main()
