"""Reconstruct the two recovery configurations without inferring exact resume or exit cause."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries = json.loads((HERE / 'preparation_receipt.json').read_text())['entries']
assert {e['seed'] for e in entries} == {2201, 2202}
records = []
for e in entries:
    assert sha(ROOT / e['source_config']) == e['source_config_sha256']
    source = yaml.safe_load((ROOT / e['source_config']).read_text())
    cfg = yaml.safe_load((ROOT / e['config']).read_text())
    assert sha(ROOT / e['config']) == e['config_sha256']
    assert source['likelihood'] == cfg['likelihood'] and source.get('prior') == cfg.get('prior')
    theory = deepcopy(source['theory'])
    theory['classy']['path'] = 'global'
    assert cfg['theory'] == theory
    params = deepcopy(source['params'])
    for n, v in e['initial_point'].items():
        params[n]['ref'] = v
    assert cfg['params'] == params
    sampler = deepcopy(source['sampler'])
    options = next(iter(sampler.values()))
    options.update(seed=e['seed'], covmat=str((ROOT / e['proposal']).resolve()))
    assert cfg['sampler'] == sampler
    assert cfg['packages_path'] == source['packages_path']
    assert sha(ROOT / e['source_covariance']) == sha(ROOT / e['proposal']) == e['proposal_sha256']
    matrix = np.loadtxt(ROOT / e['proposal'])
    assert np.isfinite(matrix).all() and np.max(np.abs(matrix - matrix.T)) < 1e-15
    np.linalg.cholesky(matrix)
    raw = (ROOT / e['source_chain']).read_bytes()
    assert sha(ROOT / e['source_chain']) == e['source_chain_sha256']
    raw = raw[:raw.rfind(b'\n') + 1]
    header = raw.decode().splitlines()[0].lstrip('#').split()
    rows = [line.split() for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
    last = dict(zip(header, rows[-1]))
    assert last == e['source_row'] and Fraction(last['weight']).denominator == 1
    assert e['initial_point'] == {n: float(last[n]) for n in e['initial_point']}
    assert all(cfg['params'][n]['prior']['min'] < v < cfg['params'][n]['prior']['max'] for n, v in e['initial_point'].items())
    terminal_path = ROOT / e['terminal_receipt']
    assert sha(terminal_path) == e['terminal_receipt_sha256']
    terminal = json.loads(terminal_path.read_text())
    assert terminal['exit_code'] is None and terminal['exit_reason'] is None
    checkpoint = next(f for f in terminal['terminal_output_files'] if f['source'].endswith('.checkpoint'))
    data = yaml.safe_load((ROOT / checkpoint['frozen']).read_text())
    fields = next(iter(data['sampler'].values()))
    assert not fields['converged']
    assert set(fields) == {'converged', 'Rminus1_last', 'burn_in', 'mpi_size'}
    proof_path = HERE / f'seed{e["seed"]}' / 'native_preflight_receipt.json'
    proof = json.loads(proof_path.read_text())
    assert proof['selected_terminal_row_native_match'] and proof['actual_launcher_guard_checked']
    assert proof['wrong_guarded_contract_refused'] and proof['config_sha256'] == e['config_sha256']
    assert proof['module_sha256'] == e['module_sha256'] == sha(e['module'])
    assert proof['initial_point'] == e['initial_point']
    errors = proof['native_check']['fresh_minus_recorded']
    assert all(np.isfinite(v) and abs(v) <= 1e-9 for v in errors.values())
    arrays_path = proof_path.with_name('native_provider_arrays.npz')
    assert sha(arrays_path) == proof['provider_arrays_sha256']
    with np.load(arrays_path, allow_pickle=False) as arrays:
        assert all(np.isfinite(arrays[k]).all() for k in arrays.files)
    assert not (ROOT / e['run_dir']).exists()
    records.append({'seed': e['seed'], 'parent_seed': e['parent_seed'], 'proof_sha256': sha(proof_path),
                    'maximum_native_component_error': max(abs(v) for v in errors.values()),
                    'preserved_checkpoint_fields': sorted(fields), 'proposal_positive_definite': True})
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_not_independent_agent',
        'records': records, 'both_recovery_targets_rederived': True,
        'declared_physics_likelihood_priors_and_native_settings_preserved': True,
        'fresh_seed_and_output_required': True, 'exact_resume_state_supplied': False,
        'global_floating_target_equivalence_asserted': False, 'original_terminal_histories_pooled': False,
        'unknown_exit_causes_inferred': False, 'posterior_qualified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Two recovery targets and finite native points reviewed; exact resume and convergence remain unasserted.')
