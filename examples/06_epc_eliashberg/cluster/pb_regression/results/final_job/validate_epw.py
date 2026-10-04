"""EPW-specific technical completion checks using only Python's standard library."""
from pathlib import Path
import math
import re
import sys


def check_log(text):
    if ("Program EPW" not in text or "Total program execution" not in text
            or "Error in routine" in text
            or re.search(r"\b(?:NaN|Infinity|Inf)\b", text, re.I)):
        raise ValueError("Incomplete or nonfinite/error EPW output")
    values = re.findall(r"^\s*lambda\s*:\s*([0-9.+Ee-]+)\s*$", text, re.M)
    if len(values) != 1 or not math.isfinite(float(values[0])) or float(values[0]) <= 0:
        raise ValueError("Missing positive finite integrated EPC coupling")
    return float(values[0])


def parse_table(text, file_format="plain"):
    if file_format not in {"plain", "epw_legacy"}:
        raise ValueError("Unknown spectral file format")
    if file_format == "epw_legacy":
        parts = text.split("Integrated el-ph coupling")
        if len(parts) != 2:
            raise ValueError("Expected exactly one legacy EPW footer")
        text, footer = parts
        number = r"[-+0-9.eEdD]+"
        pattern = (rf"\s*#\s*({number}(?:\s+{number})*)\s*\n"
                   rf"\s*Phonon smearing \(meV\)\s*\n\s*#\s*({number}(?:\s+{number})*)\s*\n"
                   rf"\s*Electron smearing \(eV\)\s+({number})\s*\n"
                   rf"\s*Fermi window \(eV\)\s+({number})\s*\n"
                   rf"\s*Summed el-ph coupling\s+({number})\s*")
        match = re.fullmatch(pattern, footer)
        if not match:
            raise ValueError("Unrecognized or truncated legacy EPW footer")
        groups = [[float(v.replace("D", "E").replace("d", "e")) for v in g.split()]
                  for g in match.groups()]
        if (len(groups[0]) != len(groups[1])
                or not all(math.isfinite(v) and v > 0 for g in groups for v in g)):
            raise ValueError("Invalid legacy EPW footer values")
    rows = [[float(v.replace("D", "E").replace("d", "e")) for v in line.split()] for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]
    if len(rows) < 2 or len(rows[0]) < 2:
        raise ValueError("Missing spectral table")
    previous = 0
    for row in rows:
        if (len(row) != len(rows[0]) or not all(math.isfinite(v) for v in row)
                or row[0] <= previous or any(v < 0 for v in row[1:])):
            raise ValueError("Invalid spectral row")
        previous = row[0]
    if not any(row[1] > 0 for row in rows):
        raise ValueError("First spectral column has no positive weight")
    if file_format == "epw_legacy" and len(groups[0]) != len(rows[0])-1:
        raise ValueError("Footer and spectral column counts differ")
    return rows


def check_table(text, file_format="plain"):
    rows = parse_table(text, file_format)
    return len(rows)


if __name__ == "__main__":
    lam = check_log(Path(sys.argv[1]).read_text(encoding="utf-8"))
    count = check_table(Path(sys.argv[2]).read_text(encoding="utf-8"), "epw_legacy")
    if count != 500:
        raise ValueError("This pinned regression expects 500 spectral rows")
    print(f"EPW_TECHNICAL_CHECK_OK lambda={lam:.7f} rows={count}; not a convergence certificate")
