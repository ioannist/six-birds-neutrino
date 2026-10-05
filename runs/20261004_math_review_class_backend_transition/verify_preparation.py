"""Adversarially check archives, fresh initializers, target contracts, and native endpoints."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
prepared = json.loads((HERE / 'preparation_receipt.json').read_text())
terminal = json.loads((HERE / 'managed_termination_receipt.json').read_text())
assert len(prepared['records']) == len(terminal['records']) == 15
assert {entry['seed'] for entry in prepared['records']} == {entry['seed'] for entry in terminal['records']}
assert all(entry['exit_code'] == 143 and not entry['still_running'] for entry in terminal['records'])
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
for name, expected in prepared['archive_file_sha256'].items():
    assert sha(HERE / name) == expected
checks = []
targets = {}
for entry in prepared['records']:
    chain = ROOT / entry['archived_chain']
    raw = chain.read_bytes()
    assert raw.endswith(b'\n') and sha(chain) == entry['archived_chain_sha256']
    source_chain = ROOT / entry['run_dir'] / 'chains' / chain.name
    assert source_chain.read_bytes() == raw
    matrix = np.atleast_2d(np.loadtxt(BytesIO(raw)))
    assert len(matrix) == entry['archived_stored_rows']
    assert np.isfinite(matrix).all() and (matrix[:, 0] > 0).all()
    assert (matrix[:, 0] == np.floor(matrix[:, 0])).all()
    header = raw.splitlines()[0].decode().lstrip('#').split()
    old_config_path = (chain.parents[1] / 'resolved.yaml' if not entry.get('resume_seed') else
                       HERE / 'archives' / f"seed{entry['seed']}" / 'active_segment/resume_input.yaml')
    old = yaml.safe_load(old_config_path.read_text())
    new_path = ROOT / entry['config']
    assert sha(new_path) == entry['config_sha256']
    new = yaml.safe_load(new_path.read_text())
    assert not new.get('resume') and 'output' not in new
    assert new['theory'] == old['theory'] and new['likelihood'] == old['likelihood']
    assert set(new['params']) == set(old['params'])
    for name in new['params']:
        a, b = deepcopy(new['params'][name]), deepcopy(old['params'][name])
        if isinstance(a, dict):
            a.pop('ref', None)
            b.pop('ref', None)
        assert a == b, name
    sampler = 'sbt_spt_audit.samplers.FullPrecisionMCMC'
    effective = yaml.safe_load(next((chain.parent).glob('*.updated.yaml')).read_text())['sampler'][sampler]
    old_options = deepcopy(old['sampler'][sampler])
    new_options = deepcopy(new['sampler'][sampler])
    old_options.setdefault('temperature', effective['temperature'])
    old_options.setdefault('oversample_thin', effective['oversample_thin'])
    for options in [old_options, new_options]:
        options.pop('seed')
        options.pop('covmat')
    assert new_options == old_options
    assert new_options['temperature'] == 1 and new_options['oversample_thin'] is False
    assert new['sampler'][sampler]['seed'] == entry['replacement_seed']
    assert sha(ROOT / entry['covariance']) == entry['covariance_sha256']
    covariance = np.loadtxt(ROOT / entry['covariance'])
    assert covariance.shape == (10, 10) and np.isfinite(covariance).all()
    np.linalg.cholesky(covariance)
    values = dict(zip(header, matrix[-1]))
    assert entry['last_complete_row_index'] == len(matrix)-1
    assert {name: float(values[name]) for name in entry['fixed_initial_point']} == entry['fixed_initial_point']
    assert all(new['params'][name]['ref'] == value for name, value in entry['fixed_initial_point'].items())
    proof = json.loads((HERE / 'parent_native_checks' / f"seed{entry['replacement_seed']}.json").read_text())
    assert proof['config_sha256'] == entry['config_sha256'] and proof['chain_sha256'] == entry['archived_chain_sha256']
    assert [item['row_index'] for item in proof['checks']] == [0, len(matrix)-1]
    assert proof['checks'][-1]['point'] == entry['fixed_initial_point']
    assert proof['fresh_initial_point_finite_native_target_verified']
    assert all(all(value == 0 for value in item['fresh_minus_original'].values()) for item in proof['checks'])
    group = entry['cohort'] + '_' + entry['lens']
    physical = {name: deepcopy(new[name]) for name in ['theory', 'likelihood', 'params']}
    for block in physical['params'].values():
        if isinstance(block, dict):
            block.pop('ref', None)
            block.pop('proposal', None)
    if group in targets:
        assert targets[group] == physical
    else:
        targets[group] = physical
    checks.append({'parent_seed': entry['seed'], 'replacement_seed': entry['replacement_seed'],
                   'archived_stored_rows': len(matrix), 'historical_saved_rows': entry['historical_saved_rows'],
                   'physical_target_precision_and_effective_sampler_options_preserved': True,
                   'parent_selected_native_components_exact': True})
existing = yaml.safe_load((ROOT / 'runs/20261004_math_review_class_python_repair/A_seed1201.yaml').read_text())
physical = {name: deepcopy(existing[name]) for name in ['theory', 'likelihood', 'params']}
for block in physical['params'].values():
    if isinstance(block, dict):
        block.pop('ref', None)
        block.pop('proposal', None)
assert targets['medium_A'] == physical
result = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'archive_and_target_contract_self_review',
          'archive_files_checked': len(prepared['archive_file_sha256']), 'checks': checks,
          'parent_native_rows_checked': 30, 'all_selected_components_prior_posterior_exact': True,
          'managed_parent_verifier_sessions': {'quad_A': 12542, 'quad_B': 92330, 'medium_A': 16835, 'medium_B': 16484},
          'all_parent_verifier_exit_codes_zero': True,
          'existing_guarded_seed1201_matches_medium_A_physical_target': True,
          'reviewer': 'self_review_no_independent_agent',
          'original_backend_global_numerical_target_identity_asserted': False,
          'historical_prefixes_appended': False, 'unknown_holding_time_reconstructed': False,
          'posterior_convergence_certified': False, 'uniform_numerical_accuracy_certified': False}
with (HERE / 'preparation_verification.json').open('x') as handle:
    handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('All 15 archives/contracts and 30 fresh native parent-row evaluations verified.')
