"""Compare affine controls and frozen native-chain helper readouts."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

from sbt_spt_audit.mcmc import ess_autocorr, split_rhat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('mcmc_before', HERE / 'mcmc_before.py')
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)

sequence = np.sin(np.arange(512) / 17.)
drift = np.r_[np.tile([0., 1.], 100), np.tile([10., 11.], 100)]
controls = {}
for label, scale in [('ordinary', 1.), ('large', 1e200), ('small', 1e-200)]:
    with np.errstate(all='ignore'):
        old_rhat = before.split_rhat([drift * scale])
    new_rhat = split_rhat([drift * scale])
    new_ess = ess_autocorr(sequence * scale)
    assert np.isclose(new_ess, ess_autocorr(sequence), rtol=1e-12, atol=0)
    assert np.isclose(new_rhat, split_rhat([drift]), rtol=1e-12, atol=0)
    controls[label] = {'new_ess': new_ess, 'new_rhat': new_rhat,
                       'old_rhat': float(old_rhat) if np.isfinite(old_rhat) else 'nonfinite'}
with np.errstate(all='ignore'):
    old_constant_rhat = before.split_rhat([np.full(60, .1), np.full(60, .1)])
assert old_constant_rhat < 1 and np.isnan(split_rhat([np.full(60, .1), np.full(60, .1)]))
controls['identical_decimal_draws'] = {'old_rhat': old_constant_rhat, 'new_rhat': 'undefined'}

ordinary = []
for seed in range(20):
    rng = np.random.default_rng(seed)
    values = rng.normal(size=512) * 10. ** (seed % 5 - 2) + seed / 10.
    old, new = before.ess_autocorr(values), ess_autocorr(values)
    assert np.isclose(old, new, rtol=1e-12, atol=0)
    old_rhat, new_rhat = before.split_rhat([values, values[::-1]]), split_rhat([values, values[::-1]])
    assert np.isclose(old_rhat, new_rhat, rtol=1e-12, atol=0)
    ordinary.append({'seed': seed, 'ess_relative_change': (new - old) / old,
                     'rhat_relative_change': (new_rhat - old_rhat) / old_rhat})

base = ROOT / 'runs/20261004_math_review_guarded_CLASS_first_diagnostics'
groups = {g: sorted((base / g).glob('seed*/chains/*.1.txt'))
          for g in ['quad_A', 'quad_B', 'medium_A', 'medium_B']}
for lens, folder in [('A', '20261004_math_review_spt_chain_snapshots_twelfth_A'),
                     ('B', '20261004_math_review_spt_chain_snapshots_eleventh_B')]:
    groups['SPT_' + lens] = sorted((ROOT / 'runs' / folder).glob('chain_*/chains/*.1.txt'))
actual, files = {}, []
for group, paths in groups.items():
    assert len(paths) == (6 if group.startswith('SPT') else 4)
    expanded = []
    for path in paths:
        raw = path.read_bytes()
        columns = raw.decode().splitlines()[0].lstrip('#').split()
        data = np.atleast_2d(np.loadtxt(path))
        assert len(columns) == data.shape[1]
        data = data[int(.2 * len(data)):]
        name = 'mnu_sample' if 'mnu_sample' in columns else 'mnu'
        assert columns[0] == 'weight' and np.all(data[:, 0] == np.floor(data[:, 0]))
        expanded.append(np.repeat(data[:, columns.index(name)], data[:, 0].astype(np.int64)))
        files.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest()})
    old_ess = sum(before.ess_autocorr(v) for v in expanded)
    new_ess = sum(ess_autocorr(v) for v in expanded)
    old_rhat, new_rhat = before.split_rhat(expanded), split_rhat(expanded)
    assert np.isclose(old_ess, new_ess, rtol=1e-12, atol=0)
    assert np.isclose(old_rhat, new_rhat, rtol=1e-12, atol=0)
    assert (old_rhat <= 1.05) == (new_rhat <= 1.05)
    actual[group] = {'family_count': len(paths), 'old_ess_sum': old_ess, 'new_ess_sum': new_ess,
                     'old_classical_rhat': old_rhat, 'new_classical_rhat': new_rhat,
                     'classical_rhat_1_05_gate_unchanged': True}

assert not (HERE / 'affine_checked_pytest_stderr.txt').read_bytes()
assert '119 passed' in (HERE / 'affine_checked_pytest_stdout.txt').read_text()
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'classical_ESS_and_Rhat_affine_rescaling_and_constant_variance_repair',
           'managed_pytest_exits': [{'session': 31494, 'passed': 112, 'exit_code': 0},
                                   {'session': 31910, 'passed': 115, 'exit_code': 0},
                                   {'session': 90297, 'passed': 118, 'exit_code': 0},
                                   {'session': 57885, 'passed': 119, 'exit_code': 0}],
           'controls': controls, 'ordinary_controls': ordinary, 'actual_frozen_chain_readouts': actual,
           'actual_readout_scope': 'same frozen prefixes through classical helpers; no new native likelihood or rank diagnostic assessment',
           'frozen_chains': files, 'rank_ArviZ_diagnostic_algorithm_changed': False,
           'uniform_floating_point_accuracy_or_convergence_certified': False,
           'paper_modified': False,
           'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
                     and p.name not in ['validation_receipt.json', 'self_review_receipt.json']] +
                    [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in [ROOT / 'src/sbt_spt_audit/mcmc.py', ROOT / 'tests/test_math_repairs.py']]}
(HERE / 'validation_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps(actual, indent=2))
