"""Reconstruct each target and challenge unintended configuration changes."""
from copy import deepcopy
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
read = lambda p: json.loads(Path(p).read_text())
prep = read(HERE / 'preparation_receipt.json')
state = read(ROOT / 'runs/20261003_math_review_validation/review_state.json')
existing = {e['seed'] for e in state['fresh_CAMB_posterior_chains']}
entries = prep['entries']
assert len(entries) == len({e['seed'] for e in entries}) == 8
assert {e['seed'] for e in entries} == set(range(2001, 2009))
assert not existing.intersection(e['seed'] for e in entries)
assert {e['group'] for e in entries} == {'upper20_A4095', 'upper20_B4095'}
for record in read(HERE / 'worker_preparation_receipt.json')['files']:
    original = ROOT / record['source']; changed = ROOT / record['destination']
    assert sha(original) == record['source_sha256'] and sha(changed) == record['destination_sha256']
    reconstructed = changed.read_text()
    for before, after in reversed(record['changes']):
        assert reconstructed.count(after) == 1
        reconstructed = reconstructed.replace(after, before)
    assert reconstructed == original.read_text()
checked = []
for group in sorted({e['group'] for e in entries}):
    assert read(HERE / (group + '_preflight_completion.json'))['exit_code'] == 0
    assert not (HERE / (group + '_preflight_stderr.txt')).read_bytes()
    subset = [e for e in entries if e['group'] == group]
    assert len(subset) == 4
    assert {e['initial_point_label'] for e in subset} == {'original_reference', 'selected_latest_frozen_row', 'mass_6_eV', 'mass_12_eV'}
    assert len({tuple(e['initial_point'].items()) for e in subset}) == 4
    for e in subset:
        assert sha(ROOT / e['baseline_config']) == e['baseline_config_sha256']
        source = yaml.safe_load((ROOT / e['baseline_config']).read_text())
        actual = yaml.safe_load((ROOT / e['config']).read_text())
        assert sha(ROOT / e['config']) == e['config_sha256']
        expected = deepcopy(source)
        expected['params']['mnu']['prior']['max'] = 20.0
        for name, value in e['initial_point'].items(): expected['params'][name]['ref'] = value
        expected['run_name'] = f'fresh_CAMB_{group}_seed{e["seed"]}'
        expected['sampler']['mcmc']['seed'] = e['seed']
        expected['sampler']['mcmc']['covmat'] = str(ROOT / e['proposal']['path'])
        expected['notes'].update({'mass_prior': 'uniform[0,20] eV', 'initial_point_label': e['initial_point_label'],
                                  'numerical_target': group, 'math_review': 'Wider-prior control; independent output and RNG; posterior qualification pending.'})
        assert expected == actual
        for name in e['initial_point']:
            assert actual['params'][name]['prior']['min'] <= e['initial_point'][name] <= actual['params'][name]['prior']['max']
        assert e['scheduling_nice'] == 5
        for path, digest in e['implementation_sha256'].items(): assert sha(ROOT / path) == digest
        proposal = ROOT / e['proposal']['path']; old_proposal = ROOT / e['proposal']['copied_from']
        assert proposal.read_bytes() == old_proposal.read_bytes() and sha(proposal) == e['proposal']['sha256']
        matrix = np.loadtxt(proposal)
        assert np.max(np.abs(matrix - matrix.T)) < 1e-18
        np.linalg.cholesky(matrix)
        proof_path = HERE / f'seed{e["seed"]}' / 'initial_point_verification.json'
        proof = read(proof_path)
        assert proof['seed'] == e['seed'] and proof['group'] == group
        assert proof['initial_point'] == e['initial_point'] and proof['config_sha256'] == e['config_sha256']
        assert proof['module_sha256'] == e['module_sha256'] == sha(e['module'])
        assert sha(e['wrapper']) == e['wrapper_sha256']
        assert proof['native_initial_point_verified'] and proof['upstream_forced_fresh_likes_and_priors_exact']
        assert proof['previous_preflight_components_exact'] and proof['sampler_cache_resize_challenge'] == 50
        assert math.isfinite(proof['logposterior'])
        assert all(math.isfinite(v) for v in [*proof['likelihood_components'].values(), *proof['logpriors']])
        assert abs(proof['logposterior'] - math.fsum([*proof['likelihood_components'].values(), *proof['logpriors']])) < 1e-9
        assert sha(ROOT / e['control']) == e['control_sha256']
        previous = read(ROOT / e['control'])['points'][e['initial_point_label']]
        assert proof['likelihood_components'] == previous['likelihood_components']
        assert proof['logposterior'] == previous['logposterior']
        assert proof['effective_CAMB_extra_args'] == actual['theory']['camb']['extra_args']
        checked.append({'seed': e['seed'], 'group': group, 'config_sha256': e['config_sha256'],
                        'initial_proof_sha256': sha(proof_path), 'start_mass_eV': e['initial_point']['mnu']})
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct self-review',
                       'checked': checked, 'targets': 2, 'native_initial_points': 8,
                       'only_target_change_is_prior_upper_endpoint': True, 'distinct_starts_per_target': 4,
                       'likelihood_other_priors_solver_and_sampler_options_preserved': True,
                       'proposal_changes_only_byte_identical_path': True, 'worker_source_transformations_reversed': True,
                       'primary_40_jobs_changed': False, 'posterior_qualified': False,
                       'tail_or_quantile_stability_inferred': False}, indent=2, allow_nan=False) + '\n')
print('Eight native initial proofs and full configuration reconstruction pass distinct self-review.', flush=True)
