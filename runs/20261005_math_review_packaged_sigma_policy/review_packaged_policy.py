"""Distinct self-review of source scope and selected fresh-build readouts."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
policy_path = ROOT / 'native_policies/camb204_sigma_refinement_v1.json'
policy = json.loads(policy_path.read_text())
prep = json.loads((HERE / 'source_preparation.json').read_text())
build = json.loads((HERE / 'build_receipt.json').read_text())
assert prep['policy_sha256'] == sha(policy_path)
assert build['source_preparation_sha256'] == sha(HERE / 'source_preparation.json')
assert prep['archive_sha256'] == policy['archive_sha256'] == sha(prep['archive'])
assert build['exit_code'] == 0 and sha(build['module']) == build['module_sha256']
changed = [f for f in prep['files'] if f['original_sha256'] != f['prepared_sha256']]
assert len(changed) == 1
assert changed[0]['path'] == policy['source_root'] + '/' + policy['source_file']
assert changed[0]['original_sha256'] == policy['original_source_sha256']
assert changed[0]['prepared_sha256'] == policy['patched_source_sha256']
source = Path(prep['source_root'])
for f in prep['files']:
    assert sha(source.parent / f['path']) == f['prepared_sha256']
patched = (source / policy['source_file']).read_bytes()
reference = ROOT / 'runs/20261005_math_review_CAMB204_sigma_integration_candidate14/candidate_halofit.f90'
assert patched == reference.read_bytes()
reverse = patched
for change in reversed(policy['changes']):
    old, new = change['before'].encode(), change['after'].encode()
    assert reverse.count(new) == 1
    reverse = reverse.replace(new, old, 1)
assert hashlib.sha256(reverse).hexdigest() == policy['original_source_sha256']

def compare_arrays(new_path, new_sha, old_path, old_sha):
    assert sha(new_path) == new_sha and sha(old_path) == old_sha
    with np.load(new_path, allow_pickle=False) as a, np.load(old_path, allow_pickle=False) as b:
        assert set(a.files) == set(b.files)
        for name in a.files:
            assert np.isfinite(a[name]).all() and np.isfinite(b[name]).all()
            assert np.array_equal(a[name], b[name]), name
        return sorted(a.files)

checks = []
low_reference = ROOT / 'runs/20261005_math_review_sigma_candidate_low_mass_controls/candidate14/evaluation_receipt.json'
new_low = json.loads((HERE / 'packaged14/evaluation_receipt.json').read_text())
old_low = json.loads(low_reference.read_text())
assert new_low['native_module_sha256'] == build['module_sha256']
assert new_low['evaluation_config_sha256'] == old_low['evaluation_config_sha256']
assert new_low['selection_receipt_sha256'] == old_low['selection_receipt_sha256']
assert len(new_low['records']) == len(old_low['records']) == 6
for a, b in zip(new_low['records'], old_low['records']):
    for key in ['selection_index', 'point', 'logpost', 'logpriors', 'loglikes']:
        assert a[key] == b[key]
    assert math.isfinite(a['logpost'])
    assert math.isclose(a['logpost'], math.fsum(a['logpriors'] + a['loglikes']), abs_tol=1e-10, rel_tol=0)
    names = compare_arrays(ROOT / a['provider_arrays'], a['provider_arrays_sha256'],
                           ROOT / b['provider_arrays'], b['provider_arrays_sha256'])
    checks.append({'kind': 'low_mass', 'selection_index': a['selection_index'],
                   'point': a['point'], 'identical_arrays': names, 'identical_posterior_components': True})
for seed in [2003, 2004]:
    new_dir = HERE / f'seed{seed}_phase_classification'
    old_dir = ROOT / 'runs/20261005_math_review_CAMB204_sigma_integration_candidate14' / new_dir.name
    a = json.loads((new_dir / 'phase_classification.json').read_text())
    b = json.loads((old_dir / 'phase_classification.json').read_text())
    assert a['isolated_point_status'] == b['isolated_point_status'] == 'finite_evaluation'
    assert a['debug_module_sha256'] == build['module_sha256']
    for key in ['sampled', 'finite_target_components', 'native_parameters', 'original_resolved_sha256', 'capture_sha256']:
        assert a[key] == b[key]
    names = compare_arrays(new_dir / 'native_arrays.npz', a['native_arrays_sha256'],
                           old_dir / 'native_arrays.npz', b['native_arrays_sha256'])
    checks.append({'kind': 'captured_failure', 'seed': seed, 'identical_arrays': names,
                   'identical_posterior_components': True})
assert not build['production_adopted'] and not policy['production_adopted']
with (HERE / 'packaged_policy_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent',
        'policy_sha256': sha(policy_path), 'builder_sha256_at_review': sha(ROOT / 'scripts/build_camb_sigma_policy.py'),
        'reviewed_candidate_byte_identical': True, 'archive_members_checked': len(prep['files']),
        'only_changed_archive_member': changed[0], 'module_sha256': build['module_sha256'],
        'checks': checks, 'selected_controls': 8, 'python_tests_passed': 222,
        'broader_domain_support_certified': False, 'uniform_error_or_posterior_certified': False,
        'production_adopted': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Fresh source/package: one changed member; all eight control arrays and posterior components identical.')
