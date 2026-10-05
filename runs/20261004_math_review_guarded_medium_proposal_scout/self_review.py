"""Recompute the pilot and generalized eigenvalues by distinct formulas."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigvalsh
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / 'scout_receipt.json').read_text())
for f in receipt['files']:
    assert hashlib.sha256((ROOT / f['snapshot']).read_bytes()).hexdigest() == f['sha256']
pilot_root = (ROOT / receipt['pilot_verification']).parent
for lens, pilot in receipt['pilot_records'].items():
    names = pilot['parameters']
    xs, ws = [], []
    for path in sorted((pilot_root / ('quad_' + lens)).glob('seed*/chains/*.1.txt')):
        columns = path.read_text().splitlines()[0].lstrip('#').split()
        rows = np.atleast_2d(np.loadtxt(path))
        rows = rows[len(rows) // 5:]
        xs.append(rows[:, [columns.index(n) for n in names]])
        ws.append(rows[:, 0])
    x, w = np.concatenate(xs), np.concatenate(ws)
    # NumPy's frequency-weight implementation is distinct from the scout's product.
    recomputed = np.cov(x, rowvar=False, fweights=w, ddof=0)
    saved = np.loadtxt(ROOT / pilot['covariance_file'])
    np.testing.assert_allclose(recomputed, saved, rtol=2e-12, atol=1e-24)
    assert len(x) == pilot['stored_rows_after_burn']
    assert int(w.sum()) == pilot['represented_steps_after_burn']
    assert not pilot['posterior_covariance_certified'] and not pilot['prior_diagnostic_pass']
comparisons = []
for record in receipt['medium_proposal_comparisons']:
    folder = HERE / f"seed{record['seed']}"
    names = (folder / 'current.covmat').read_text().splitlines()[0].lstrip('#').split()
    pilot = receipt['pilot_records'][record['lens']]
    assert len(names) == len(set(names)) == 10 and set(names) == set(pilot['parameters'])
    order = [pilot['parameters'].index(n) for n in names]
    c = np.loadtxt(ROOT / pilot['covariance_file'])[np.ix_(order, order)]
    current = np.loadtxt(folder / 'current.covmat')
    generalized = eigvalsh(c, current)
    np.testing.assert_allclose(generalized, record['pilot_covariance_in_current_proposal_basis_eigenvalues'], rtol=2e-12, atol=1e-14)
    cfg = yaml.safe_load((folder / 'resolved.yaml').read_text())
    initial_path = Path(cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['covmat'])
    assert initial_path.read_text().splitlines()[0].lstrip('#').split() == names
    assert record['current_equals_initial'] and record['proposal_updates'] == 0
    np.testing.assert_allclose(current, np.loadtxt(initial_path), rtol=5e-15, atol=1e-20)
    comparisons.append({'seed': record['seed'], 'generalized_eigenvalue_max_abs_discrepancy':
                        float(np.max(np.abs(generalized - record['pilot_covariance_in_current_proposal_basis_eigenvalues']))),
                        'initial_covariance_sha256': hashlib.sha256(initial_path.read_bytes()).hexdigest()})
assert len(comparisons) == 8
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_review',
       'scout_receipt_sha256': hashlib.sha256((HERE / 'scout_receipt.json').read_bytes()).hexdigest(),
       'self_review_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'weighted_covariance_recomputed_by_frequency_weights': True,
       'generalized_eigenvalues_recomputed_without_whitening': comparisons,
       'pilot_is_unconverged_initialization_only': True, 'posterior_targets_pooled': False,
       'efficiency_or_convergence_certified': False}
with (HERE / 'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Both pilot covariances and all eight generalized comparisons pass self-review.')
