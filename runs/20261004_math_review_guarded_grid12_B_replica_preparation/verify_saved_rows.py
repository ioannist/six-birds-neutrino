"""Self-review first saved-row target accounting in the four grid12 starts."""
from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
runtime = json.loads((HERE / 'post_saved_rows_runtime_observation.json').read_text())
identities = {r['seed']: r for r in runtime['records']}
reference = None
records, files = [], []
for seed in [1501, 1502, 1503, 1504]:
    root = HERE.parent / f'20261004_math_review_guarded_grid12_trial_B_seed{seed}'
    folder = root / 'first_saved_rows'
    snapshot = json.loads((folder / 'snapshot_receipt.json').read_text())
    proof = json.loads((folder / 'native_target_verification.json').read_text())
    completion = json.loads((folder / 'completion_receipt.json').read_text())
    assert snapshot['seed'] == proof['seed'] == seed and completion['exit_code'] == 0
    assert completion['snapshot_command_exit_code'] == 0
    assert hashlib.sha256((root / 'verify_first_rows.py').read_bytes()).hexdigest() == completion['native_check_script_sha256']
    assert hashlib.sha256((root / 'snapshot_first_rows.py').read_bytes()).hexdigest() == completion['snapshot_script_sha256']
    assert hashlib.sha256((folder / 'snapshot_receipt.json').read_bytes()).hexdigest() == proof['snapshot_receipt_sha256']
    for f in snapshot['files']:
        data = (ROOT / f['snapshot']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == f['sha256']
        live = (ROOT / f['source']).read_bytes()
        if 'source_sha256' not in f:
            assert live.startswith(data)
        else:
            assert hashlib.sha256(live).hexdigest() == f['source_sha256']
    chain = ROOT / snapshot['files'][0]['snapshot']
    header = chain.read_text().splitlines()[0].lstrip('#').split()
    rows = np.atleast_2d(np.loadtxt(chain))
    assert len(header) == len(set(header))
    assert len(rows) == snapshot['stored_rows'] == len(proof['checks'])
    assert np.all(np.isfinite(rows)) and np.all(rows[:, 0] > 0) and np.all(rows[:, 0] == np.floor(rows[:, 0]))
    components = [n for n in header if n.startswith('chi2__') and n != 'chi2__CMB']
    assert len(components) == 6
    prep = json.loads((root / 'preparation_receipt.json').read_text())
    for index, (row, check) in enumerate(zip(rows, proof['checks'])):
        values = dict(zip(header, row))
        assert check['row_index'] == index
        assert all(values[n] == x for n, x in check['point'].items())
        assert len(check['fresh_minus_recorded']) == 9 and all(v == 0 for v in check['fresh_minus_recorded'].values())
        assert abs(values['chi2'] - sum(values[n] for n in components)) < 1e-10
        assert abs(values['minuslogpost'] - values['minuslogprior'] - .5 * values['chi2']) < 1e-10
        assert np.isclose(sum(check['CLASS_masses']), values['mnu_sample'], rtol=1e-13, atol=0)
    cfg = yaml.safe_load((folder / 'resolved.yaml').read_text())
    actual = yaml.safe_load((root / 'run/resolved.yaml').read_text())
    cfg['output'] = actual['output']
    assert cfg == actual
    clean = deepcopy(cfg)
    for parameter in clean['params'].values():
        if isinstance(parameter, dict):
            parameter.pop('ref', None); parameter.pop('proposal', None)
    target = {k: clean.get(k) for k in ['params', 'likelihood', 'theory', 'prior', 'packages_path']}
    if reference is None:
        reference = target
    else:
        assert target == reference
    witness = json.loads((folder / 'solver_backend.json').read_text())
    assert proof['module_sha256'] == witness['module_sha256'] == prep['native_module_sha256']
    assert identities[seed]['status'] == 'live_same_owned_identity'
    records.append({'seed': seed, 'saved_rows_verified': len(rows), 'complete_represented_steps': int(rows[:, 0].sum()),
                    'first_saved_mass_eV': proof['checks'][0]['point']['mnu_sample'],
                    'all_native_component_prior_posterior_discrepancies_zero': True})
    files += [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted(folder.rglob('*')) if p.is_file()]
assert runtime['owned_live_samplers'] == 28 and runtime['grid12_B_live'] == 4
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_review',
       'scope': 'four_grid12_B_initial_saved_prefixes_actual_native_target_accounting',
       'records': records, 'same_numerical_target_and_physical_model_checked': True,
       'four_distinct_RNG_seeds_and_starting_points': True, 'other_precision_cohorts_pooled': False,
       'every_transition_verified': False, 'posterior_convergence_or_uniform_accuracy_certified': False,
       'files': files,
       'runtime_observation_sha256': hashlib.sha256((HERE / 'post_saved_rows_runtime_observation.json').read_bytes()).hexdigest(),
       'verification_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / 'saved_rows_verification.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps(records, indent=2))
