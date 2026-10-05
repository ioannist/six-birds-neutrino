"""Check the native replay receipt and its actual frozen-row bridge."""
from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
folder = HERE / 'first_saved_rows'
receipt = json.loads((folder / 'snapshot_receipt.json').read_text())
check = json.loads((folder / 'native_target_verification.json').read_text())
completion = json.loads((folder / 'completion_receipt.json').read_text())
assert completion['exit_code'] == completion['snapshot_command_exit_code'] == 0
assert hashlib.sha256((HERE / 'verify_first_rows.py').read_bytes()).hexdigest() == completion['native_check_script_sha256']
assert hashlib.sha256((HERE / 'snapshot_first_rows.py').read_bytes()).hexdigest() == completion['snapshot_script_sha256']
assert check['snapshot_receipt_sha256'] == hashlib.sha256((folder / 'snapshot_receipt.json').read_bytes()).hexdigest()
for f in receipt['files']:
    saved = (ROOT / f['snapshot']).read_bytes()
    assert hashlib.sha256(saved).hexdigest() == f['sha256']
    source = (ROOT / f['source']).read_bytes()
    if 'source_sha256' not in f:
        assert source.startswith(saved)
    else:
        assert hashlib.sha256(source).hexdigest() == f['source_sha256']
chain = ROOT / receipt['files'][0]['snapshot']
header = chain.read_text().splitlines()[0].lstrip('#').split()
rows = np.atleast_2d(np.loadtxt(chain))
prep = json.loads((HERE / 'preparation_receipt.json').read_text())
assert len(rows) == receipt['stored_rows'] == len(check['checks']) == 1
likelihood_columns = [n for n in header if n.startswith('chi2__') and n != 'chi2__CMB']
assert len(likelihood_columns) == 6
for row, native in zip(rows, check['checks']):
    values = dict(zip(header, row))
    assert all(values[n] == value for n, value in native['point'].items())
    assert native['point'] != prep['initial_point']
    assert row[0] > 0 and row[0] == int(row[0])
    assert abs(values['chi2'] - sum(values[n] for n in likelihood_columns)) < 1e-10
    assert abs(values['minuslogpost'] - values['minuslogprior'] - .5 * values['chi2']) < 1e-10
    assert all(error == 0 for error in native['fresh_minus_recorded'].values())
    assert len(native['fresh_minus_recorded']) == 9
    assert np.isclose(sum(native['CLASS_masses']), values['mnu_sample'], rtol=1e-13, atol=0)
cfg = yaml.safe_load((folder / 'resolved.yaml').read_text())
original = yaml.safe_load((HERE / 'run/resolved.yaml').read_text())
cfg['output'] = original['output']
assert cfg == original
medium = yaml.safe_load((ROOT / 'runs/20261004_math_review_guarded_medium_chain_B_seed1403/resolved.yaml').read_text())
clean = lambda params: {n: {k: v for k, v in p.items() if k not in ['ref', 'proposal']}
                       if isinstance(p, dict) else p for n, p in params.items()}
assert clean(cfg['params']) == clean(medium['params'])
assert cfg['likelihood'] == medium['likelihood'] and cfg.get('prior') == medium.get('prior')
medium_theory = deepcopy(medium['theory'])
medium_theory['classy']['extra_args'].update(l_logstep=1.013, l_linstep=12)
assert cfg['theory'] == medium_theory
runtime = json.loads((HERE / 'post_first_rows_runtime_observation.json').read_text())
assert runtime['owned_live_samplers'] == 25 and runtime['guarded_CLASS_live'] == 17
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_review',
       'selected_row_differs_from_initial_point': True, 'complete_saved_holding_time': int(rows[0, 0]),
       'native_six_component_prior_posterior_discrepancies_all_zero': True,
       'physical_target_matches_medium_B_except_two_angular_grid_controls': True,
       'convergence_or_uniform_accuracy_certified': False,
       'sampler_target_changed_after_launch': False, 'precision_targets_pooled': False,
       'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(folder.rglob('*')) if p.is_file()] +
                [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in [Path(__file__), HERE / 'observe_after_first_rows.py', HERE / 'post_first_rows_runtime_observation.json']]}
with (HERE / 'saved_rows_self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Distinct saved-row self-review passes; all 25 samplers remain live.')
