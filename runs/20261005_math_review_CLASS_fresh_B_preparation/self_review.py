"""Reconstruct the B target, sampler, proposal and native-start evidence separately."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
worker = read(HERE / 'worker_preparation_receipt.json')
launcher = read(HERE / 'launcher_preparation_receipt.json')
for r in worker['records'] + [{'name': 'launch.py', **launcher}]:
    assert sha(ROOT / r['source']) == r['source_sha256']
    actual = (HERE / r['name']).read_text()
    for before, after in reversed(r['changes']):
        assert actual.count(after) == 1
        actual = actual.replace(after, before, 1)
    assert actual.encode() == (ROOT / r['source']).read_bytes()
preparation = read(HERE / 'preparation_receipt.json')
execution = read(HERE / 'preflight_execution_receipt.json')
assert execution['all_native_control_workers_terminal']
assert execution['maximum_concurrent_native_controls'] == 2 and execution['samplers_launched'] == 0
assert {r['seed'] for r in execution['records']} == set(range(2401, 2409))
assert all(r['actual_terminal_exit_code'] == 0 for r in execution['records'])
records, signatures = [], {}
for e in preparation['entries']:
    for path, digest in [('config', 'config_sha256'), ('source_config', 'source_config_sha256'),
                         ('source_covariance', 'source_covariance_sha256'),
                         ('proposal_terminal_receipt', 'proposal_terminal_receipt_sha256'),
                         ('build_receipt', 'build_receipt_sha256')]:
        assert sha(ROOT / e[path]) == e[digest]
    source = yaml.safe_load((ROOT / e['source_config']).read_text())
    assert (ROOT / e['source_config']).read_bytes() == (ROOT / e['original_source_config']).read_bytes()
    cfg = yaml.safe_load((ROOT / e['config']).read_text())
    assert cfg['params'] == source['params']
    assert e['initial_point'] == {n: float(source['params'][n]['ref']) for n in e['initial_point']}
    assert all(source['params'][n]['prior']['min'] < value < source['params'][n]['prior']['max']
               for n, value in e['initial_point'].items())
    theory = deepcopy(source['theory'])
    theory['classy']['path'] = 'global'
    assert cfg['theory'] == theory and cfg['likelihood'] == source['likelihood']
    assert cfg.get('prior') == source.get('prior') and cfg['packages_path'] == source['packages_path']
    sampler = deepcopy(source['sampler'])
    next(iter(sampler.values())).update(seed=e['seed'], covmat=str((ROOT / e['proposal']).resolve()))
    assert cfg['sampler'] == sampler
    assert sha(ROOT / e['proposal']) == sha(ROOT / e['source_covariance']) == e['proposal_sha256']
    terminal = read(ROOT / e['proposal_terminal_receipt'])
    covariance_record = next(r for r in terminal['terminal_output_files'] if r['frozen'] == e['source_covariance'])
    assert covariance_record['sha256'] == e['proposal_sha256']
    matrix = np.loadtxt(ROOT / e['proposal'])
    assert matrix.shape == (10, 10) and np.isfinite(matrix).all()
    assert np.max(abs(matrix - matrix.T)) < 1e-15
    np.linalg.cholesky(matrix)
    assert set((ROOT / e['proposal']).read_text().splitlines()[0].lstrip('#').split()) == set(e['initial_point'])
    for path, digest in e['implementation_sha256'].items():
        assert sha(ROOT / path) == digest
    old = read(ROOT / e['historical_launch_receipt'])
    assert sha(ROOT / e['historical_launch_receipt']) == e['historical_launch_receipt_sha256']
    assert old['environment']['OMP_NUM_THREADS'] == e['OMP_NUM_THREADS']
    assert e['historical_bound_source_changes'] == [p for p, digest in old['implementation_sha256'].items()
                                                  if sha(ROOT / p) != digest]
    folder = HERE / f'seed{e["seed"]}'
    proof_path = folder / 'native_preflight_receipt.json'
    proof = read(proof_path)
    assert read(folder / 'preflight_execution_receipt.json')['actual_terminal_exit_code'] == 0
    assert proof['initial_point'] == e['initial_point'] and proof['fresh_initial_point_finite']
    assert proof['config_sha256'] == e['config_sha256']
    assert proof['module_sha256'] == e['module_sha256'] == sha(e['module'])
    assert proof['actual_launcher_guard_checked'] and proof['wrong_native_contract_refused']
    assert np.isfinite([proof['logpost'], *proof['logpriors'], *proof['loglikes'].values()]).all()
    assert set(proof['loglikes']) == set(cfg['likelihood'])
    arrays = folder / 'native_provider_arrays.npz'
    assert sha(arrays) == proof['provider_arrays_sha256']
    with np.load(arrays, allow_pickle=False) as values:
        assert values.files and all(np.isfinite(values[k]).all() for k in values.files)
    assert not (ROOT / e['run_dir']).exists()
    params = deepcopy(cfg['params'])
    for b in params.values():
        if isinstance(b, dict):
            b.pop('ref', None)
            b.pop('proposal', None)
    signature = {'theory': theory, 'likelihood': cfg['likelihood'], 'params': params,
                 'prior': cfg.get('prior'), 'packages_path': cfg['packages_path']}
    signatures.setdefault(e['group'], []).append(signature)
    records.append({'seed': e['seed'], 'source_seed': e['source_seed'],
                    'native_preflight_sha256': sha(proof_path), 'declared_target_and_original_sampler_preserved': True})
assert len(records) == len({r['seed'] for r in records}) == 8
for group, cohort in preparation['cohorts'].items():
    selected = [e for e in preparation['entries'] if e['group'] == group]
    assert cohort['seeds'] == [e['seed'] for e in selected]
    assert len(cohort['seeds']) == len(set(cohort['seeds'])) == 4
    assert cohort['fixed_initial_points'] == [e['initial_point'] for e in selected]
    assert len({tuple(p.items()) for p in cohort['fixed_initial_points']}) == 4
    assert all(s == cohort['target'] for s in signatures[group])
    assert all(e['implementation_sha256'] == cohort['source_code_identity'] for e in selected)
    assert all(e['module_sha256'] == cohort['module_sha256'] and e['OMP_NUM_THREADS'] == cohort['OMP_NUM_THREADS'] for e in selected)
    assert cohort['distinct_declared_rng_seeds_and_starts']
    assert not cohort['independent_PRNG_streams_proved']
    assert not cohort['unconditional_independence_or_stationarity_proved']
    assert cohort['original_terminal_and_surviving_families_retained_separately']
    assert cohort['first_history_trigger'] == 1000 and cohort['later_growth_factor'] == [6, 5]
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': records,
        'preparation_sha256': sha(HERE / 'preparation_receipt.json'), 'launcher_sha256': sha(HERE / 'launch.py'),
        'prepare_script_sha256': sha(HERE / 'prepare.py'), 'eight_fresh_B_starts_reconstructed': True,
        'two_distinct_four_start_designs': True, 'original_sampler_profiles_preserved': True,
        'historical_bound_source_differences_do_not_prove_target_change': True,
        'historical_trajectories_pooled': False, 'independence_or_stationarity_proved': False,
        'uniform_accuracy_or_posterior_qualification_proved': False, 'samplers_launched': 0},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('Eight B starts reconstructed with original sampler profiles; no posterior qualification.')
