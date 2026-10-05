"""Distinct self-review of the full selected limit and compiler comparisons."""
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
baseline = ROOT / 'runs/20261005_math_review_CAMB204_sigma_integration_candidate14/candidate_halofit.f90'
for maximum in [22, 24]:
    directory = ROOT / f'runs/20261005_math_review_sigma_limit{maximum}_candidate'
    prep = json.loads((directory / 'source_preparation.json').read_text())
    assert sha(prep['candidate_source']) == prep['candidate_sha256'] == sha(directory / 'candidate_halofit.f90')
    reverse = (directory / 'candidate_halofit.f90').read_text()
    for before, after in reversed(prep['changes']):
        assert reverse.count(after) == 1
        reverse = reverse.replace(after, before, 1)
    assert reverse.encode() == baseline.read_bytes()

policy_path = ROOT / 'native_policies/camb204_sigma_refinement_v2.json'
policy = json.loads(policy_path.read_text())
prep = json.loads((HERE / 'source_preparation.json').read_text())
build = json.loads((HERE / 'build_receipt.json').read_text())
assert prep['policy_sha256'] == sha(policy_path) == build['policy_sha256']
assert sha(HERE / 'source_preparation.json') == build['source_preparation_sha256']
assert build['policy_id'] == policy['policy_id'] and build['build_profile'] == 'optimized'
assert build['exit_code'] == 0 and sha(build['module']) == build['module_sha256']
changed = [p for p in prep['files'] if p['original_sha256'] != p['prepared_sha256']]
assert len(changed) == 1 and changed[0]['path'] == 'camb-2.0.4/fortran/halofit.f90'
for p in prep['files']:
    assert sha(Path(prep['source_root']).parent / p['path']) == p['prepared_sha256']
assert (Path(prep['source_root']) / policy['source_file']).read_bytes() == (ROOT / 'runs/20261005_math_review_sigma_limit22_candidate/candidate_halofit.f90').read_bytes()

selection_path = HERE / 'selection_receipt.json'
selection = json.loads(selection_path.read_text())
assert len(selection['records']) == 20
contract = json.loads((ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation/reproduction_contract.json').read_text())['entries']['2003']
config_path = ROOT / contract['run_dir'] / 'resolved.yaml'
assert sha(config_path) == contract['effective_config_sha256']
config = yaml.safe_load(config_path.read_text())
for i, selected in enumerate(selection['records']):
    receipt_path = ROOT / selected['source_receipt']
    assert sha(receipt_path) == selected['source_receipt_sha256']
    source = json.loads(receipt_path.read_text())
    point = selected['point']
    assert all(config['params'][k]['prior']['min'] < v < config['params'][k]['prior']['max'] for k, v in point.items())
    if selected['kind'] == 'mass_grid':
        assert i < 12 and point['mnu'] == [.05, 1., 4.9, 5.1, 10., 19.][i % 6]
        assert selected['anchor_seed'] == (2003 if i < 6 else 2004)
        assert all(point[k] == v for k, v in source['sampled'].items() if k != 'mnu')
    elif selected['kind'] == 'captured_high_mass_failure':
        assert i in [12, 13] and point == source['sampled']
    else:
        assert selected['kind'] == 'low_mass_control' and i >= 14
        assert any(point == check['point'] for record in source['records'] for check in record['checks'])

roots = [ROOT / 'runs/20261005_math_review_sigma_limit22_candidate',
         ROOT / 'runs/20261005_math_review_sigma_limit24_candidate', HERE]
evaluations = [json.loads((r / 'controls/evaluation_receipt.json').read_text()) for r in roots]
assert all(len(e['records']) == 20 for e in evaluations)
assert all(e['selection_receipt_sha256'] == sha(selection_path) for e in evaluations)
assert all(e['evaluation_config_sha256'] == sha(config_path) for e in evaluations)
assert all(sha(e['native_module']) == e['native_module_sha256'] for e in evaluations)
assert evaluations[2]['native_module_sha256'] == build['module_sha256']
agreement = json.loads((HERE / 'comparison_contract.json').read_text())
reports = []
for i, (audit, finer, optimized) in enumerate(zip(*(e['records'] for e in evaluations))):
    for r, directory in zip([audit, finer, optimized], roots):
        assert r == json.loads((directory / f'controls/point{i}_receipt.json').read_text())
        assert r['selection_index'] == i and r['point'] == selection['records'][i]['point']
        assert r['status'] == 'finite_evaluation' and math.isfinite(r['logpost'])
        assert not r['native_error_is_posterior_rejection']
        assert math.isclose(r['logpost'], math.fsum(r['logpriors'] + r['loglikes']), abs_tol=1e-9, rel_tol=0)
    assert audit['logpost'] == finer['logpost']
    assert audit['logpriors'] == finer['logpriors'] == optimized['logpriors']
    assert audit['loglikes'] == finer['loglikes']
    assert float(audit['loglikes'][1]).hex() == float(optimized['loglikes'][1]).hex()
    post_difference = optimized['logpost'] - audit['logpost']
    assert abs(post_difference) <= agreement['optimized_vs_audit_logpost_absolute_tolerance']
    arrays = {}
    for r in [audit, finer, optimized]:
        assert sha(ROOT / r['provider_arrays']) == r['provider_arrays_sha256']
    with np.load(ROOT / audit['provider_arrays'], allow_pickle=False) as a, np.load(ROOT / finer['provider_arrays'], allow_pickle=False) as b, np.load(ROOT / optimized['provider_arrays'], allow_pickle=False) as c:
        assert set(a.files) == set(b.files) == set(c.files)
        for name in a.files:
            assert np.isfinite(a[name]).all() and np.isfinite(b[name]).all() and np.isfinite(c[name]).all()
            assert np.array_equal(a[name], b[name])
            difference = float(np.max(np.abs(a[name] - c[name])))
            norm = float(np.max(np.abs(a[name])))
            if norm == 0:
                assert difference == 0
            normalized = difference / norm if norm else 0.
            assert normalized <= agreement['optimized_vs_audit_array_normalized_infinity_tolerance']
            arrays[name] = normalized
    reports.append({'selection_index': i, 'point': audit['point'],
                    'limit22_vs24_components_and_arrays_identical': True,
                    'optimized_minus_audit_logpost': post_difference,
                    'optimized_array_normalized_differences': arrays,
                    'priors_and_BAO_binary64_identical': True})
warnings = {str(r.relative_to(ROOT)): (r / 'controls_stdout.txt').read_text().count('WARNING: mismatch in integrated times') for r in roots}
assert len(set(warnings.values())) == 1 and next(iter(warnings.values())) > 0
with (HERE / 'limit_controls_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': reports,
        'selected_evaluations_checked': 60, 'policy_source_only_one_member_changed': True,
        'source_members_checked': len(prep['files']), 'native_module_sha256': build['module_sha256'],
        'comparison_contract_sha256': sha(HERE / 'comparison_contract.json'),
        'maximum_optimized_logpost_difference': max(abs(r['optimized_minus_audit_logpost']) for r in reports),
        'maximum_optimized_normalized_array_difference': max(v for r in reports for v in r['optimized_array_normalized_differences'].values()),
        'native_time_warning_counts': warnings, 'warning_harmlessness_established': False,
        'uniform_error_or_prior_support_or_posterior_certificate': False, 'production_adopted': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Sixty finite selected evaluations reviewed; exact22/24 equality; optimized comparisons pass; time warnings remain separately under review.')
