"""Compare immutable proposal matrices; neither is a covariance certificate."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigvalsh

HERE = Path(__file__).resolve().parent
inputs = json.loads((HERE / 'inputs.json').read_text())
results = {}
for lens in ['A', 'B']:
    matrices = {}
    asymmetry = {}
    names = None
    for label in ['static', 'learned_default']:
        filename = f'{lens}_{label}.covmat'
        path = HERE / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == inputs['records'][filename]['sha256']
        header = path.read_text().splitlines()[0].lstrip('#').split()
        assert len(set(header)) == len(header)
        if names is None:
            names = header
        assert set(names) == set(header)
        matrix = np.loadtxt(path)
        assert matrix.shape == (len(header), len(header))
        assert np.all(np.isfinite(matrix))
        sigma = np.sqrt(np.diag(matrix))
        assert np.all(np.isfinite(sigma)) and np.all(sigma > 0)
        unit = matrix / sigma[:, None] / sigma[None, :]
        asymmetry[label] = float(np.max(np.abs(unit - unit.T)))
        assert asymmetry[label] <= 64 * np.finfo(float).eps
        # Record and average only roundoff-scale antisymmetry before SPD checks.
        matrix = (matrix + matrix.T) / 2
        order = [header.index(name) for name in names]
        matrices[label] = matrix[np.ix_(order, order)]
        np.linalg.cholesky(matrices[label])
    static, learned = matrices['static'], matrices['learned_default']
    sd = np.sqrt(np.diag(learned))
    normalized = {key: matrix / sd[:, None] / sd[None, :]
                  for key, matrix in matrices.items()}
    eigenvalues = eigvalsh(normalized['static'], normalized['learned_default'])
    assert np.all(np.isfinite(eigenvalues)) and np.all(eigenvalues > 0)
    results[lens] = {
        'input_max_asymmetry_in_correlation_units': asymmetry,
        'static_over_learned_standard_deviation': dict(zip(names, np.sqrt(np.diag(static) / np.diag(learned)).tolist())),
        'generalized_variance_eigenvalues': eigenvalues.tolist(),
        'condition_number_after_learned_diagonal_normalization': {
            key: float(np.linalg.cond(matrix)) for key, matrix in normalized.items()},
    }
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': inputs['scope'],
    'inputs_sha256': hashlib.sha256((HERE / 'inputs.json').read_bytes()).hexdigest(),
    'results': results,
    'interpretation': 'Default-target learned covariance is an unconverged proposal-shape reference. This comparison neither measures intermediate-target efficiency nor certifies posterior covariance.',
    'sampler_changed': False,
    'posterior_covariance_certified': False,
    'efficiency_improvement_certified': False,
}
(HERE / 'comparison_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(results, indent=2))
