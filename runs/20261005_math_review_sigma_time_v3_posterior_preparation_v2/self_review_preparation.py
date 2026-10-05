"""Reconstruct targets from source configs and check every native start proof."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
preparation_path = HERE / 'preparation_receipt.json'
preparation = json.loads(preparation_path.read_text())
entries = preparation['entries']
assert len(entries) == len({e['seed'] for e in entries}) == 16
combined_path = ROOT / 'runs/20261005_math_review_sigma_time_v3_packaged/combined_policy_self_review_receipt.json'
combined = json.loads(combined_path.read_text())
assert combined['selected_CMB_controls'] == 20 and combined['warnings_remaining'] == 0
records = []
proofs = {}
for entry in entries:
    source_path = ROOT / entry['source_config']
    assert sha(source_path) == entry['source_config_sha256']
    source = yaml.safe_load(source_path.read_text())
    cfg_path = ROOT / entry['config']
    assert sha(cfg_path) == entry['config_sha256']
    cfg = yaml.safe_load(cfg_path.read_text())
    assert cfg['theory'] == source['theory'] and cfg['likelihood'] == source['likelihood']
    assert cfg.get('prior') == source.get('prior') and cfg['packages_path'] == source['packages_path']
    assert set(cfg) == set(source) and set(cfg['params']) == set(source['params'])
    expected_params = source['params']
    expected_params['mnu']['prior']['max'] = float(entry['prior_upper_eV'])
    for name, value in entry['initial_point'].items():
        expected_params[name]['ref'] = value
    assert cfg['params'] == expected_params
    source_options = source['sampler']['mcmc']
    source_options['seed'] = entry['seed']
    source_options['covmat'] = str((ROOT / entry['proposal']['path']).resolve())
    assert cfg['sampler'] == source['sampler']
    assert cfg['notes']['camb_backend'] == {'module_sha256': entry['module_sha256'], 'solver_version': '2.0.4'}
    assert cfg['notes']['native_policy_sha256'] == sha(ROOT / entry['policy']) == entry['policy_sha256']
    assert sha(ROOT / entry['build_receipt']) == entry['build_receipt_sha256']
    assert entry['module_sha256'] == combined['module_sha256'] == sha(entry['module'])
    assert sha(entry['wrapper']) == entry['wrapper_sha256']
    for path, digest in entry['implementation_sha256'].items():
        assert sha(ROOT / path) == digest
    proposal = ROOT / entry['proposal']['path']
    assert sha(proposal) == entry['proposal']['sha256'] == sha(ROOT / entry['proposal']['copied_from'])
    matrix = np.loadtxt(proposal)
    assert np.isfinite(matrix).all() and matrix.shape == (7, 7)
    assert np.max(np.abs(matrix - matrix.T)) < 1e-18
    np.linalg.cholesky(matrix)
    proof_path = HERE / f'seed{entry["seed"]}/initial_point_verification.json'
    proof = json.loads(proof_path.read_text())
    assert proof['seed'] == entry['seed'] and proof['group'] == entry['group']
    assert proof['initial_point'] == entry['initial_point']
    assert proof['module_sha256'] == entry['module_sha256'] and proof['policy_sha256'] == entry['policy_sha256']
    assert proof['config_sha256'] == entry['config_sha256']
    assert proof['native_initial_point_verified'] and proof['upstream_forced_fresh_likes_and_priors_exact']
    assert proof['provider_arrays_exact'] and proof['actual_launcher_native_guard_checked'] and proof['wrong_module_hash_refused']
    assert proof['sampler_cache_resize_challenge'] == 50
    assert np.isfinite([proof['logposterior'], *proof['logpriors'], *proof['likelihood_components'].values()]).all()
    assert math.isclose(proof['logposterior'], math.fsum(proof['logpriors'] + list(proof['likelihood_components'].values())), abs_tol=1e-9, rel_tol=0)
    arrays_path = proof_path.with_name('initial_provider_arrays.npz')
    assert sha(arrays_path) == proof['provider_arrays_sha256']
    with np.load(arrays_path, allow_pickle=False) as arrays:
        assert all(np.isfinite(arrays[k]).all() for k in arrays.files)
    assert not (ROOT / entry['run_dir']).exists() and not (proof_path.parent / 'launch_receipt.json').exists()
    proofs[entry['seed']] = proof
    records.append({'seed': entry['seed'], 'config_sha256': sha(cfg_path), 'initial_point_proof_sha256': sha(proof_path),
                    'source_target_preserved_except_declared_prior_and_native_policy': True})
shared = []
for lens, first in [('A', 2101), ('B', 2109)]:
    for offset in [0, 1]:
        narrow, wide = proofs[first + offset], proofs[first + 4 + offset]
        assert narrow['initial_point'] == wide['initial_point']
        assert {k: float(v).hex() for k, v in narrow['likelihood_components'].items()} == {
            k: float(v).hex() for k, v in wide['likelihood_components'].items()}
        error = wide['logposterior'] - narrow['logposterior'] + math.log(4)
        assert abs(error) < 1e-10
        shared.append({'lens': lens, 'narrow_seed': first + offset, 'wide_seed': first + 4 + offset,
                       'likelihood_components_binary64_exact': True, 'logposterior_prior_normalizer_shift_error': error})
for group in preparation['targets']:
    assert len([e for e in entries if e['group'] == group]) == 4
    assert (HERE / f'{group}_preflight_stdout.txt').read_text().count('finite start, exact forced-fresh native replay and launcher guard') == 4
    assert 'WARNING: mismatch in integrated times' not in (HERE / f'{group}_preflight_stdout.txt').read_text()
    assert not (HERE / f'{group}_preflight_stderr.txt').read_bytes()
refusal = json.loads((HERE / 'actual_launcher_refusal_receipt.json').read_text())
assert refusal['actual_exit_code'] == 2 and refusal['output_directory_absent']
assert sha(HERE / 'wrong_native_launcher_stderr.txt') == refusal['stderr_sha256']
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_not_independent_agent',
        'records': records, 'shared_point_controls': shared, 'source_targets_rederived': True,
        'all_sixteen_initial_points_verified': True, 'all_sixteen_native_guards_checked': True,
        'provider_arrays_exact_to_forced_fresh_upstream': True, 'time_warnings_remaining': 0,
        'proposal_heuristics_checked': True, 'combined_policy_review_sha256': sha(combined_path),
        'actual_wrong_environment_launcher_exit_code': 2, 'fresh_outputs_confirmed_absent': True,
        'posterior_or_prior_stability_certified': False, 'production_adopted': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Sixteen targets reconstructed and native starts reviewed; four shared-point prior controls pass.')
