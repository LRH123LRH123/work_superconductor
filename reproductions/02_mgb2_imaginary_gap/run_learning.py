"""Rebuild the explicitly synthetic format-check report; no material solver."""
import hashlib
import json
from pathlib import Path
from gap_io import parse_legacy_five, check_matsubara, window_report


def collect(root):
    path = root/'fixtures/synthetic_legacy_five.dat'
    rows = parse_legacy_five(path.read_text(encoding='utf-8'), energy_unit='eV')
    return {'fixture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_kind': 'original_synthetic_format_fixture',
            'is_author_data': False, 'is_material_calculation': False,
            'declared_T_K': 10., 'temperature_verified_from_run_metadata': False,
            'grid_residual_meV': check_matsubara(rows, 10),
            'full_window': window_report(rows),
            'narrow_window': window_report(rows, max_frequency_meV=2.707,
                                           max_abs_xi_meV=50),
            'new_cluster_jobs': 0}


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    output = root/'results/validation.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(collect(root), indent=2, allow_nan=False)+'\n',
                      encoding='utf-8', newline='\n')
    print('PASS: original synthetic fixture report rebuilt. NOT MgB2 or paper results.')
