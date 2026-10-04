"""Original finite, even-frequency, band-averaged Einstein Eliashberg model.

lambda_ij = bare_lambda_ij * p_j already contains the destination DOS weight.
This is not a k-resolved EPW solver or a MgB2 parameterization. Energies: meV.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.linalg import eig
from scipy.sparse.csgraph import connected_components

KB_MEV_K = 0.08617333262145


@dataclass(frozen=True)
class Model:
    weights: object
    bare_lambda: object
    bare_mu: object
    omega_meV: float = 10.
    coulomb_cutoff_meV: float = 100.
    n_positive: int = 96
    lambda_matrix: np.ndarray = field(init=False, repr=False)
    mu_matrix: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        p = np.array(self.weights, dtype=float, copy=True)
        v = np.array(self.bare_lambda, dtype=float, copy=True)
        u = np.array(self.bare_mu, dtype=float, copy=True)
        if (p.ndim != 1 or not 1 <= len(p) <= 8 or not np.all(np.isfinite(p))
                or np.any(p <= 0) or not np.isclose(p.sum(), 1, rtol=0, atol=1e-12)):
            raise ValueError('DOS weights must be finite, positive and sum to one')
        for matrix in (v, u):
            if (matrix.shape != (len(p), len(p)) or not np.all(np.isfinite(matrix))
                    or np.any(matrix < 0) or not np.allclose(matrix, matrix.T, rtol=0, atol=1e-12)):
                raise ValueError('Bare matrices must be finite, nonnegative and symmetric')
        if (not np.all(np.isfinite([self.omega_meV, self.coulomb_cutoff_meV]))
                or min(self.omega_meV, self.coulomb_cutoff_meV) <= 0
                or type(self.n_positive) is not int or not 2 <= self.n_positive <= 256
                or len(p)*self.n_positive > 512):
            raise ValueError('Invalid energies or dense teaching matrix size (maximum 512)')
        for name, value in [('weights', p), ('bare_lambda', v), ('bare_mu', u),
                            ('lambda_matrix', v*p[None, :]), ('mu_matrix', u*p[None, :])]:
            value.flags.writeable = False
            object.__setattr__(self, name, value)

    @property
    def average_lambda(self):
        return float(self.weights @ self.lambda_matrix.sum(axis=1))

    @property
    def average_mu(self):
        return float(self.weights @ self.mu_matrix.sum(axis=1))


def kernels(T_K, model):
    if not np.isfinite(T_K) or T_K <= 0:
        raise ValueError('Temperature must be finite and positive')
    w = (2*np.arange(model.n_positive)+1)*np.pi*KB_MEV_K*T_K
    omega2 = model.omega_meV**2
    lam = model.lambda_matrix[:, :, None, None]
    minus = lam*omega2/(omega2+(w[:, None]-w[None, :])**2)
    plus = lam*omega2/(omega2+(w[:, None]+w[None, :])**2)
    pair = minus+plus-2*model.mu_matrix[:, :, None, None]*(w<model.coulomb_cutoff_meV)
    return w, minus-plus, pair


def linearized(T_K, model):
    w, normal, pair = kernels(T_K, model)
    factor = np.pi*KB_MEV_K*T_K
    z = 1+factor/w[None, :]*normal.sum(axis=(1, 3))
    blocks = factor*pair/(z[:, None, :, None]*w[None, None, None, :])
    # Flatten (i,n) as rows and (j,m) as columns, never (i,j) as rows.
    size = len(model.weights)*model.n_positive
    matrix = blocks.transpose(0, 2, 1, 3).reshape(size, size)
    return w, z, matrix


def leading_eigenpair(matrix):
    matrix = np.asarray(matrix, dtype=float)
    if (matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]
            or not matrix.size or not np.all(np.isfinite(matrix))):
        raise ValueError('Eigenproblem requires a finite square real matrix')
    values, vectors = eig(matrix)
    real = np.flatnonzero(abs(values.imag) < 1e-9)
    if not len(real):
        raise ValueError('No real pairing eigenvalue found')
    index = real[np.argmax(values[real].real)]
    value, vector = float(values[index].real), vectors[:, index].real
    pivot = np.argmax(abs(vector))
    vector = vector/vector[pivot]
    residual = float(np.max(abs(matrix@vector-value*vector)))
    return value, vector, residual


def instability(T_K, model):
    _, _, matrix = linearized(T_K, model)
    value, vector, residual = leading_eigenpair(matrix)
    return {'eigenvalue': value, 'eigen_residual': residual,
            'mode': vector.reshape(len(model.weights), model.n_positive).tolist()}


def find_tc(lower_K, upper_K, model, width_K=.01):
    if (not np.all(np.isfinite([lower_K, upper_K, width_K]))
            or not 0 < lower_K < upper_K or width_K <= 0):
        raise ValueError('Invalid temperature bracket')
    def eigen(T):
        return instability(T, model)['eigenvalue']
    if eigen(lower_K) <= 1 or eigen(upper_K) > 1:
        raise ValueError('Need superconducting lower and normal upper bounds')
    for _ in range(80):
        if upper_K-lower_K <= width_K:
            break
        middle = (lower_K+upper_K)/2
        if eigen(middle) > 1:
            lower_K = middle
        else:
            upper_K = middle
    if upper_K-lower_K > width_K:
        raise ValueError('Temperature bisection did not reach requested width')
    return {'lower_K': float(lower_K), 'upper_K': float(upper_K),
            'midpoint_K': float((lower_K+upper_K)/2), 'n_positive': model.n_positive,
            'is_material_prediction': False, 'matsubara_cutoff_converged': False}


def solve_gap(T_K, model, mixing=.3, max_iterations=4000):
    if (not np.isfinite(mixing) or not 0 < mixing <= 1
            or type(max_iterations) is not int or max_iterations < 1):
        raise ValueError('Invalid nonlinear iteration controls')
    w, normal, pair = kernels(T_K, model)
    linear = instability(T_K, model)
    superconducting = linear['eigenvalue'] > 1
    gap = np.zeros((len(model.weights), model.n_positive))
    coulomb_active = bool(np.any(w < model.coulomb_cutoff_meV))
    graph = (model.lambda_matrix > 0) | ((model.mu_matrix > 0) & coulomb_active)
    count, labels = connected_components(graph, directed=False)
    component_eigenvalues = []
    if count == 1:
        component_eigenvalues.append(linear['eigenvalue'])
        if superconducting:
            gap = .2*model.omega_meV*np.array(linear['mode'])
    else:
        # Each unstable disconnected block needs its own nonzero seed.
        _, _, matrix = linearized(T_K, model)
        for component in range(count):
            bands = np.flatnonzero(labels == component)
            indices = (bands[:, None]*model.n_positive+np.arange(model.n_positive)).ravel()
            value, vector, _ = leading_eigenpair(matrix[np.ix_(indices, indices)])
            component_eigenvalues.append(value)
            if value > 1:
                gap[bands] = .2*model.omega_meV*vector.reshape(len(bands), model.n_positive)
    factor = np.pi*KB_MEV_K*T_K
    z = 1+factor/w[None, :]*normal.sum(axis=(1, 3))
    for iteration in range(1, max_iterations+1):
        denominator = np.sqrt(w[None, :]**2+gap**2)
        new_z = 1+factor/w[None, :]*np.einsum('ijnm,jm->in', normal, w/denominator)
        new_gap = factor*np.einsum('ijnm,jm->in', pair, gap/denominator)/new_z
        dg, dz = float(np.max(abs(new_gap-gap))), float(np.max(abs(new_z-z)))
        if dg < 1e-8 and dz < 1e-9:
            for component, value in enumerate(component_eigenvalues):
                if value > 1 and np.max(abs(gap[labels == component])) < 1e-6:
                    raise ValueError('Unstable component collapsed to a trivial solution')
            return {'T_K': float(T_K), 'frequency_meV': w.tolist(), 'gap_meV': gap.tolist(),
                    'Z': z.tolist(), 'iterations': iteration, 'gap_residual_meV': dg,
                    'Z_residual': dz, 'superconducting': bool(superconducting),
                    'linearized_eigenvalue': linear['eigenvalue'], 'is_material_prediction': False,
                    'component_instability_eigenvalues': component_eigenvalues,
                    'band_component_labels': labels.tolist()}
        gap = (1-mixing)*gap+mixing*new_gap
        z = (1-mixing)*z+mixing*new_z
    raise ValueError('Nonlinear equations did not reach declared unmixed residuals')
