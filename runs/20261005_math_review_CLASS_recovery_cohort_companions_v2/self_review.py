"""Reconstruct the fresh cohort design and reject unsupported independence claims."""
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
packet = read(HERE / 'packet_preparation_receipt.json')
source = ROOT / packet['source_root']
for name, digest in packet['sources'].items():
    assert sha(source / name) == digest
    actual = (HERE / name).read_text()
    if name == 'prepare.py':
        for before, after in reversed(packet['prepare_changes']):
            assert actual.count(after) == 1
            actual = actual.replace(after, before)
    assert actual.encode() == (source / name).read_bytes()
preparation = read(HERE / 'preparation_receipt.json')
records = []
for e in preparation['entries']:
    assert sha(ROOT / e['config']) == e['config_sha256']
    assert sha(ROOT / e['source_config']) == e['source_config_sha256']
    assert sha(ROOT / e['anchor_config']) == e['anchor_config_sha256']
    source_cfg = yaml.safe_load((ROOT / e['source_config']).read_text())
    anchor = yaml.safe_load((ROOT / e['anchor_config']).read_text())
    cfg = yaml.safe_load((ROOT / e['config']).read_text())
    assert e['initial_point'] == {n: float(source_cfg['params'][n]['ref']) for n in e['initial_point']}
    expected = deepcopy(anchor['params'])
    for n, value in e['initial_point'].items():
        expected[n]['ref'] = value
        assert expected[n]['prior']['min'] < value < expected[n]['prior']['max']
    assert cfg['params'] == expected
    assert cfg['theory'] == anchor['theory'] and cfg['likelihood'] == anchor['likelihood']
    assert cfg.get('prior') == anchor.get('prior') and cfg['packages_path'] == anchor['packages_path']
    sampler = deepcopy(anchor['sampler'])
    next(iter(sampler.values())).update(seed=e['seed'], covmat=str((ROOT / e['proposal']).resolve()))
    assert cfg['sampler'] == sampler
    assert sha(ROOT / e['proposal']) == sha(ROOT / e['anchor_proposal']) == e['proposal_sha256']
    matrix = np.loadtxt(ROOT / e['proposal'])
    assert matrix.shape == (10, 10) and np.isfinite(matrix).all()
    assert np.max(abs(matrix - matrix.T)) < 1e-15
    np.linalg.cholesky(matrix)
    assert set((ROOT / e['proposal']).read_text().splitlines()[0].lstrip('#').split()) == set(e['initial_point'])
    for path, digest in e['implementation_sha256'].items():
        assert sha(ROOT / path) == digest
    old = read(ROOT / e['historical_launch_receipt'])
    assert sha(ROOT / e['historical_launch_receipt']) == e['historical_launch_receipt_sha256']
    assert e['historical_bound_source_changes'] == [p for p, digest in old['implementation_sha256'].items()
                                                  if sha(ROOT / p) != digest]
    folder = HERE / f'seed{e["seed"]}'
    execution = read(folder / 'preflight_execution_receipt.json')
    proof_path = folder / 'native_preflight_receipt.json'
    proof = read(proof_path)
    assert execution['actual_terminal_exit_code'] == 0
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
    records.append({'seed': e['seed'], 'source_seed': e['source_seed'],
                    'native_preflight_sha256': sha(proof_path), 'declared_target_preserved': True})
assert len(records) == len({r['seed'] for r in records}) == 6
for cohort in preparation['cohorts'].values():
    assert len(cohort['seeds']) == len(set(cohort['seeds'])) == 4
    assert len({tuple(p.items()) for p in cohort['fixed_initial_points']}) == 4
    assert cohort['distinct_declared_rng_seeds_and_starts']
    assert not cohort['independent_PRNG_streams_proved']
    assert not cohort['unconditional_independence_or_stationarity_proved']
    assert 'samplers_independent_conditional_on_fixed_preparation_inputs' not in cohort
    assert cohort['first_history_trigger'] == 1000 and cohort['later_growth_factor'] == [6, 5]
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': records,
        'preparation_sha256': sha(HERE / 'preparation_receipt.json'), 'launcher_sha256': sha(HERE / 'launch.py'),
        'six_fresh_companions_reconstructed': True, 'two_distinct_four_start_designs': True,
        'historical_bound_source_differences_do_not_prove_target_change': True,
        'historical_trajectories_pooled': False, 'independence_or_stationarity_proved': False,
        'uniform_accuracy_or_posterior_qualification_proved': False, 'samplers_launched': 0},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('Six companion starts reviewed; no historical pooling, independence theorem or posterior qualification.')
