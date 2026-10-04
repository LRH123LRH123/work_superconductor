"""Read an explicitly declared legacy EPW five-column positive-frequency profile.

No band labels, DOS weights, analytic continuation, or material claims are inferred.
Schema reference: https://docs.epw-code.org/tutorials/archived/MgB2.html
"""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np

KB_MEV_K = 0.08617333262145


@dataclass(frozen=True)
class GapRows:
    frequency_meV: np.ndarray
    xi_meV: np.ndarray
    Z: np.ndarray
    gap_meV: np.ndarray
    Z_normal: np.ndarray

    def __post_init__(self):
        arrays = []
        for field in self.__dataclass_fields__:
            a = np.array(getattr(self, field), dtype=float, copy=True)
            if a.ndim != 1 or not a.size or not np.all(np.isfinite(a)):
                raise ValueError('GapRows must contain nonempty finite 1-D arrays')
            a.setflags(write=False)
            object.__setattr__(self, field, a)
            arrays.append(a)
        if len({a.size for a in arrays}) != 1:
            raise ValueError('GapRows arrays must have equal lengths')
        if np.any(self.frequency_meV <= 0):
            raise ValueError('This profile requires positive imaginary frequencies')


def parse_legacy_five(text, *, energy_unit):
    """Convert omega, xi and Delta to meV; retain every row and gap sign."""
    if energy_unit not in {'eV', 'meV'}:
        raise ValueError('energy unit must be explicitly eV or meV')
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.split('#', 1)[0].split('!', 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f'line {lineno}: expected exactly 5 columns')
        try:
            values = [float(f.replace('D', 'e').replace('d', 'e')) for f in fields]
        except ValueError as exc:
            raise ValueError(f'line {lineno}: nonnumeric field') from exc
        if not np.all(np.isfinite(values)):
            raise ValueError(f'line {lineno}: fields must be finite')
        if values[0] <= 0:
            raise ValueError(f'line {lineno}: frequency must be positive')
        rows.append(values)
    if not rows:
        raise ValueError('no data rows')
    a = np.asarray(rows)
    factor = 1000 if energy_unit == 'eV' else 1
    a[:, [0, 1, 3]] *= factor
    return GapRows(*(a[:, i] for i in range(5)))


def _positive(value, name):
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and positive')


def check_matsubara(rows, temperature_K, *, atol_meV=.001):
    """Check all rows against odd fermion frequencies, not cyclic frequency f.

    Passing is only grid compatibility, not proof of the true simulation temperature.
    The absolute tolerance accounts for printed decimals; not a physical error bar.
    """
    _positive(temperature_K, 'temperature_K')
    if not np.isfinite(atol_meV) or atol_meV < 0:
        raise ValueError('atol_meV must be finite and nonnegative')
    step = np.pi*KB_MEV_K*temperature_K
    _positive(step, 'Matsubara spacing')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            n = np.rint((rows.frequency_meV/step-1)/2)
            if np.any(n > 2**52):
                raise ValueError('Matsubara index exceeds reliable floating-point resolution')
            expected = (2*n+1)*step
    except FloatingPointError as exc:
        raise ValueError('Matsubara grid arithmetic is not representable') from exc
    residual = float(np.max(np.abs(rows.frequency_meV-expected)))
    if not np.isfinite(residual) or np.any(n < 0) or residual > atol_meV:
        raise ValueError(f'Matsubara grid mismatch: max residual {residual:.6g} meV')
    return residual


def window_report(rows, *, max_frequency_meV=180., max_abs_xi_meV=None):
    """Unweighted raw range and row count only; do not fabricate band statistics."""
    _positive(max_frequency_meV, 'max_frequency_meV')
    # One ULP guards the inclusive endpoint against eV->meV roundoff only.
    mask = rows.frequency_meV <= np.nextafter(max_frequency_meV, np.inf)
    if max_abs_xi_meV is not None:
        if not np.isfinite(max_abs_xi_meV) or max_abs_xi_meV < 0:
            raise ValueError('max_abs_xi_meV must be finite and nonnegative')
        mask &= np.abs(rows.xi_meV) <= np.nextafter(max_abs_xi_meV, np.inf)
    if not np.any(mask):
        raise ValueError('no rows in requested window')
    def bounds(a):
        return [float(np.min(a[mask])), float(np.max(a[mask]))]
    return {'total_rows': len(mask), 'retained_rows': int(np.sum(mask)),
            'excluded_rows': int(np.sum(~mask)),
            'max_frequency_meV': float(max_frequency_meV),
            'max_abs_xi_meV': max_abs_xi_meV,
            'frequency_range_meV': bounds(rows.frequency_meV),
            'gap_range_meV': bounds(rows.gap_meV),
            'has_band_labels': False, 'has_DOS_weights': False,
            'is_paper_reproduction': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    p.add_argument('--energy-unit', choices=['eV', 'meV'], required=True)
    p.add_argument('--temperature-K', type=float, required=True)
    p.add_argument('--max-frequency-meV', type=float, default=180)
    p.add_argument('--max-abs-xi-meV', type=float)
    args = p.parse_args()
    rows = parse_legacy_five(args.file.read_text(encoding='utf-8'), energy_unit=args.energy_unit)
    report = window_report(rows, max_frequency_meV=args.max_frequency_meV,
                           max_abs_xi_meV=args.max_abs_xi_meV)
    report['declared_temperature_K'] = args.temperature_K
    report['grid_residual_meV'] = check_matsubara(rows, args.temperature_K)
    report['temperature_verified_from_run_metadata'] = False
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
