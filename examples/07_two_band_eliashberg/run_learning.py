"""Generate fixed two-band and isotropic-comparison artifacts, not DFT scans."""
from pathlib import Path
import json
import platform
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from two_band import Model, linearized, instability, find_tc, solve_gap

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'results'


def teaching_model():
    return Model([.4, .6], [[2.5, .3], [.3, 1.]], np.full((2, 2), .1))


def build():
    OUT.mkdir(exist_ok=True)
    model = teaching_model()
    isotropic = Model([1], [[model.average_lambda]], [[model.average_mu]])
    tc, tc_iso = find_tc(2, 25, model), find_tc(2, 25, isotropic)
    temperatures = [2., 4., 6., 8., 9., 10., tc['upper_K'], 12., 15., 20.]
    rows = []
    for t in temperatures:
        result, iso = solve_gap(t, model, max_iterations=10000), solve_gap(t, isotropic, max_iterations=10000)
        rows.append({'T_K': t, 'band_gap_iw0_meV': np.array(result['gap_meV'])[:, 0].tolist(),
                     'isotropic_gap_iw0_meV': iso['gap_meV'][0][0],
                     'eigenvalue': result['linearized_eigenvalue'],
                     'gap_residual_meV': result['gap_residual_meV'],
                     'Z_residual': result['Z_residual'], 'iterations': result['iterations'],
                     'isotropic_gap_residual_meV': iso['gap_residual_meV'],
                     'isotropic_Z_residual': iso['Z_residual'],
                     'isotropic_iterations': iso['iterations']})
    at4 = solve_gap(4, model)
    mode = instability(tc['midpoint_K'], model)
    p = model.weights
    balanced = p[:, None]*model.lambda_matrix
    equal_rows = Model(p, np.full((2, 2), .904), np.full((2, 2), .1))
    w, z, matrix = linearized(6, equal_rows)
    _, z1, b1 = linearized(6, isotropic)
    probe = np.sin(np.arange(model.n_positive)+.2)
    reduction_error = float(np.max(abs(matrix@np.tile(probe, 2)-np.tile(b1@probe, 2))))
    report = {'parameters': {'dos_weights': p.tolist(), 'bare_lambda': model.bare_lambda.tolist(),
                            'lambda_ij': model.lambda_matrix.tolist(), 'mu_ij_star': model.mu_matrix.tolist(),
                            'omega_E_meV': 10., 'coulomb_cutoff_meV': 100., 'n_positive': 96,
                            'lambda_rows': model.lambda_matrix.sum(axis=1).tolist(),
                            'average_lambda': model.average_lambda, 'average_mu_star': model.average_mu,
                            'mixing': .3, 'temperature_curve_max_iterations': 10000},
              'two_band_tc': tc, 'isotropic_tc': tc_iso,
              'frequency_solution_T4': at4, 'temperature_results': rows,
              'leading_mode_at_Tc_midpoint': mode,
              'reciprocity_max_error': float(np.max(abs(balanced-balanced.T))),
              'equal_rows_single_band_matrix_action_max_error': reduction_error,
              'equal_rows_single_band_Z_max_error': float(np.max(abs(z-z1))),
              'scope': {'is_material_prediction': False, 'is_MgB2_fit': False,
                        'is_paper_figure_reproduction': False, 'analytic_continuation_done': False,
                        'matsubara_cutoff_converged': False, 'new_cluster_jobs': 0,
                        'new_dft_convergence_scans': 0},
              'runtime': {'python': platform.python_version(), 'numpy': np.__version__,
                          'scipy': scipy.__version__, 'matplotlib': matplotlib.__version__}}
    (OUT/'validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n',
                                       encoding='utf-8', newline='\n')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False})
    colors = ['#117E83', '#C55B43']
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    im = ax.imshow(model.lambda_matrix, cmap='YlGnBu', vmin=0, vmax=1.2)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f'{model.lambda_matrix[i,j]:.2f}', ha='center', va='center',
                    fontsize=30, color='white' if model.lambda_matrix[i,j]>.8 else '#183B3C')
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=['A: p=0.4', 'B: p=0.6'],
           yticklabels=['Band A', 'Band B'], xlabel='Destination band j (DOS already included)',
           ylabel='Initial band i', title='Original teaching model: lambda_ij = V_ij p_j')
    ax.tick_params(labelsize=13)
    ax.xaxis.label.set_size(14); ax.yaxis.label.set_size(14)
    colorbar = fig.colorbar(im, ax=ax, label='Dimensionless coupling')
    colorbar.ax.tick_params(labelsize=13); colorbar.ax.yaxis.label.set_size(14)
    fig.tight_layout(); fig.savefig(OUT/'coupling_matrix.png', dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.1))
    t = np.array(temperatures); gaps = np.array([r['band_gap_iw0_meV'] for r in rows])
    for i in range(2):
        axes[0].plot(t, gaps[:, i], 'o-', color=colors[i], label=f'Band {"AB"[i]}')
    axes[0].plot(t, [r['isotropic_gap_iw0_meV'] for r in rows], 's--', color='#857140',
                 label=r'Isotropic (same $\bar\lambda$)')
    axes[0].axvspan(tc['lower_K'], tc['upper_K'], color='#117E83', alpha=.3)
    axes[0].axvline(tc['midpoint_K'], color='#117E83', linestyle=':', linewidth=1)
    axes[0].text(tc['midpoint_K']+.4, 1.15, 'Tc bracket ~10.09 K', color='#117E83', rotation=90, fontsize=9)
    axes[0].set(xlabel='Temperature (K)', ylabel='Delta(i w_0) / meV', ylim=(-.05, 2.5))
    axes[0].legend(fontsize=11)
    axes[1].plot(t, [r['eigenvalue'] for r in rows], 'o-', color=colors[0])
    axes[1].axhline(1, color='#C55B43', linestyle='--')
    axes[1].set(xlabel='Temperature (K)', ylabel='Largest real pairing eigenvalue')
    for ax in axes:
        ax.tick_params(labelsize=12)
        ax.xaxis.label.set_size(13); ax.yaxis.label.set_size(13)
    fig.suptitle('Fixed finite model: not MgB2, not a material prediction')
    fig.tight_layout(); fig.savefig(OUT/'two_band_temperature.png', dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.1))
    for i in range(2):
        axes[0].plot(at4['frequency_meV'], at4['gap_meV'][i], color=colors[i], label=f'Band {"AB"[i]}')
        axes[1].plot(at4['frequency_meV'], at4['Z'][i], color=colors[i], label=f'Band {"AB"[i]}')
    axes[0].set(xlabel='Positive Matsubara energy (meV)', ylabel='Delta(i w_n) / meV')
    axes[1].set(xlabel='Positive Matsubara energy (meV)', ylabel='Z(i w_n)')
    for ax in axes:
        ax.legend(); ax.grid(alpha=.15)
    fig.suptitle('Original two-band model at 4 K: imaginary-axis quantities only')
    fig.tight_layout(); fig.savefig(OUT/'two_band_frequency.png', dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9.2, 4.0))
    w = (2*np.arange(96)+1)*np.pi*.08617333262145*tc['midpoint_K']
    for i in range(2):
        ax.plot(w, mode['mode'][i], color=colors[i], label=f'Band {"AB"[i]}')
    ax.set(xlabel='Positive Matsubara energy (meV)', ylabel='Normalized linear gap mode',
           title='Leading pairing mode near finite-model Tc (not a nonlinear gap)')
    ax.legend(); ax.grid(alpha=.15)
    fig.tight_layout(); fig.savefig(OUT/'leading_mode.png', dpi=170); plt.close(fig)
    print(json.dumps({'two_band_tc': tc, 'isotropic_tc': tc_iso,
                      'gap_at_4K_meV': np.array(at4['gap_meV'])[:, 0].tolist(),
                      'max_gap_residual': max(r['gap_residual_meV'] for r in rows),
                      'single_band_reduction_error': reduction_error}, indent=2))
    return report


if __name__ == '__main__':
    build()
