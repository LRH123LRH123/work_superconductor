"""Rebuild fixed model outputs and verify the executed two-band learning package."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import nbformat


def validate_package(example):
    problems = []
    saved = json.loads((example/'results/validation.json').read_text(encoding='utf-8'))
    name = 'two_band_learning_validation'
    spec = importlib.util.spec_from_file_location(name, example/'two_band.py')
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        model = module.Model([.4, .6], [[2.5, .3], [.3, 1]], np.full((2, 2), .1))
        iso = module.Model([1], [[.904]], [[.1]])
        params = saved['parameters']
        expected = {'dos_weights': model.weights, 'bare_lambda': model.bare_lambda,
                    'lambda_ij': model.lambda_matrix, 'mu_ij_star': model.mu_matrix,
                    'lambda_rows': [1.18, .72], 'average_lambda': .904, 'average_mu_star': .1,
                    'omega_E_meV': 10, 'coulomb_cutoff_meV': 100, 'n_positive': 96,
                    'mixing': .3, 'temperature_curve_max_iterations': 10000}
        for key, value in expected.items():
            if not np.allclose(params[key], value, rtol=0, atol=1e-14):
                problems.append(f'Two-band parameter mismatch: {key}')
        tc = module.find_tc(2, 25, model)
        for key, m in [('two_band_tc', model), ('isotropic_tc', iso)]:
            rebuilt = module.find_tc(2, 25, m)
            for field in ['lower_K', 'upper_K', 'midpoint_K', 'n_positive']:
                if rebuilt[field] != saved[key][field]:
                    problems.append(f'Two-band Tc cannot be rebuilt: {key}/{field}')
            if saved[key]['is_material_prediction'] or saved[key]['matsubara_cutoff_converged']:
                problems.append(f'Unsupported material/cutoff claim: {key}')
        at4 = module.solve_gap(4, model)
        for key in ['frequency_meV', 'gap_meV', 'Z']:
            if not np.allclose(at4[key], saved['frequency_solution_T4'][key], rtol=1e-10, atol=1e-10):
                problems.append(f'Two-band nonlinear rebuild mismatch: {key}')
        expected_t = [2, 4, 6, 8, 9, 10, tc['upper_K'], 12, 15, 20]
        if [row['T_K'] for row in saved['temperature_results']] != expected_t:
            problems.append('Unexpected two-band temperature list')
        for row in saved['temperature_results']:
            rebuilt = module.solve_gap(row['T_K'], model, max_iterations=10000)
            isorebuilt = module.solve_gap(row['T_K'], iso, max_iterations=10000)
            if not np.allclose(np.array(rebuilt['gap_meV'])[:, 0], row['band_gap_iw0_meV'], atol=1e-10, rtol=1e-10):
                problems.append('Two-band temperature gap differs from rebuilt equation')
            if abs(isorebuilt['gap_meV'][0][0]-row['isotropic_gap_iw0_meV']) > 1e-10:
                problems.append('Two-band isotropic comparison differs from rebuilt equation')
            for field, bound in [('gap_residual_meV', 1e-8), ('Z_residual', 1e-9),
                                 ('isotropic_gap_residual_meV', 1e-8), ('isotropic_Z_residual', 1e-9)]:
                if not 0 <= row[field] < bound:
                    problems.append(f'Two-band unmixed residual failed: {field}')
        mode = module.instability(tc['midpoint_K'], model)
        if (mode['eigen_residual'] >= 1e-11 or not np.allclose(
                mode['mode'], saved['leading_mode_at_Tc_midpoint']['mode'], atol=1e-10, rtol=1e-10)):
            problems.append('Two-band leading eigenmode/residual differs')
        weighted = model.weights[:, None]*model.lambda_matrix
        equal_rows = module.Model([.4, .6], np.full((2, 2), .904), np.full((2, 2), .1))
        _, z2, b2 = module.linearized(6, equal_rows)
        _, z1, b1 = module.linearized(6, iso)
        probe = np.sin(np.arange(96)+.2)
        limits = {'reciprocity_max_error': float(np.max(abs(weighted-weighted.T))),
                  'equal_rows_single_band_matrix_action_max_error': float(np.max(abs(
                      b2@np.tile(probe, 2)-np.tile(b1@probe, 2)))),
                  'equal_rows_single_band_Z_max_error': float(np.max(abs(z2-z1)))}
        for field, value in limits.items():
            if not 0 <= saved[field] < 1e-13 or abs(saved[field]-value) > 1e-14:
                problems.append(f'Two-band analytic limit failed: {field}')
        if any(saved['scope'].values()):
            problems.append('Two-band model makes an unsupported scope claim')
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    notebook = nbformat.read(example/'双带Eliashberg交互教程.ipynb', as_version=4)
    nbformat.validate(notebook)
    cells = [c for c in notebook.cells if c.cell_type == 'code']
    if len(cells) != 8 or any(c.execution_count is None for c in cells):
        problems.append('Two-band notebook has missing/unexecuted cells')
    if any(o.output_type == 'error' for c in cells for o in c.outputs):
        problems.append('Two-band notebook contains errors')
    manifest = json.loads((example/'source_manifest.json').read_text(encoding='utf-8'))
    if (manifest['paper']['redistributed'] or manifest['paper']['doi'] != '10.1103/PhysRevB.87.024505'
            or manifest['paper']['read_pdf_sha256'] != '01703e759102d01e44218ec65f03e1c05e35e224dc2844fa54361013db2ef237'):
        problems.append('Two-band paper provenance mismatch')
    if list(example.rglob('*.pdf')):
        problems.append('Source PDF unexpectedly copied into model package')
    return problems


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    failures = validate_package(root/'examples/07_two_band_eliashberg')
    if failures:
        raise SystemExit('\n'.join(failures))
    print('PASS: two-band fixed model and isotropic comparison rebuilt, scope/provenance checked, 8 cells executed')
