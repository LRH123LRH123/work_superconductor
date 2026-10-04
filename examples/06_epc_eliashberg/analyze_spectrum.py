"""Analyze a declared alpha2F column without guessing units or fitting material data."""
from pathlib import Path
import argparse
import json
from epc import load_spectrum, moments, tc_estimates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spectrum", type=Path)
    parser.add_argument("--unit", required=True, choices=["Ry", "eV", "meV"])
    parser.add_argument("--column", type=int, default=1, help="Zero-based alpha2F column; first is 1")
    parser.add_argument("--mu-star", type=float, default=0.1)
    parser.add_argument("--format", choices=["plain", "epw_legacy"], default="plain")
    parser.add_argument("--moments-only", action="store_true", help="Do not compute approximate Tc formulas")
    args = parser.parse_args()
    w, a = load_spectrum(args.spectrum, args.unit, args.column, args.format)
    report = moments(w, a)
    report.pop("cumulative_lambda")
    if not args.moments_only:
        report["formula_estimates"] = tc_estimates(report["lambda"], report["omega_log_meV"],
                                               report["omega2_meV"], args.mu_star)
    print(json.dumps(report, indent=2))
