"""Distinct self-review of combined source scope and selected numerical controls."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import tarfile

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
policy_path = ROOT / 'native_policies/camb204_sigma_time_v3.json'
policy = json.loads(policy_path.read_text())
prep = json.loads((HERE / 'source_preparation.json').read_text())
build = json.loads((HERE / 'build_receipt.json').read_text())
assert sha(policy_path) == prep['policy_sha256'] == build['policy_sha256']
assert sha(HERE / 'source_preparation.json') == build['source_preparation_sha256']
assert build['exit_code'] == 0 and build['build_profile'] == 'optimized'
assert build['policy_id'] == policy['policy_id'] == prep['policy_id']
assert sha(build['module']) == build['module_sha256']
assert sha(build['compiler']) == build['compiler_sha256']
assert sha(prep['archive']) == policy['archive_sha256']
source_root = Path(prep['source_root'])
specs = {policy['source_root'] + '/' + s['source_file']: s for s in policy['sources']}
assert set(specs) == {'camb-2.0.4/fortran/halofit.f90', 'camb-2.0.4/fortran/results.f90'}
assert {e['path'] for e in prep['files'] if e['original_sha256'] != e['prepared_sha256']} == set(specs)
with tarfile.open(prep['archive']) as archive:
    assert {m.name for m in archive.getmembers() if m.isfile()} == {e['path'] for e in prep['files']}
    for entry in prep['files']:
        prepared = (source_root.parent / entry['path']).read_bytes()
        original = archive.extractfile(entry['path']).read()
        assert hashlib.sha256(original).hexdigest() == entry['original_sha256']
        assert hashlib.sha256(prepared).hexdigest() == entry['prepared_sha256']
        if entry['path'] in specs:
            spec = specs[entry['path']]
            assert entry['original_sha256'] == spec['original_source_sha256']
            assert entry['prepared_sha256'] == spec['patched_source_sha256']
            reverse = prepared
            for change in reversed(spec['changes']):
                after, before = change['after'].encode(), change['before'].encode()
                assert reverse.count(after) == 1
                reverse = reverse.replace(after, before, 1)
            assert reverse == original
        else:
            assert prepared == original
assert (source_root / 'fortran/halofit.f90').read_bytes() == (ROOT / 'runs/20261005_math_review_sigma_limit22_candidate/candidate_halofit.f90').read_bytes()
assert (source_root / 'fortran/results.f90').read_bytes() == (ROOT / 'runs/20261005_math_review_sigma_time_endpoint_candidate_v3/candidate_results.f90').read_bytes()

contract = json.loads((HERE / 'comparison_contract.json').read_text())
selection_path = HERE / 'selection_receipt.json'
assert sha(selection_path) == contract['selection_sha256'] == sha(ROOT / contract['selection'])
selection = json.loads(selection_path.read_text())
baseline_path = ROOT / contract['baseline']
assert sha(baseline_path) == contract['baseline_sha256']
baseline = json.loads(baseline_path.read_text())
actual = json.loads((HERE / 'controls/evaluation_receipt.json').read_text())
assert len(selection['records']) == len(actual['records']) == len(baseline['records']) == 20
assert actual['policy_sha256'] == sha(policy_path)
assert actual['build_receipt_sha256'] == sha(HERE / 'build_receipt.json')
assert actual['native_module_sha256'] == build['module_sha256'] == sha(actual['native_module'])
assert baseline['native_module_sha256'] == sha(baseline['native_module'])
assert actual['selection_receipt_sha256'] == baseline['selection_receipt_sha256'] == sha(selection_path)
assert actual['evaluation_config_sha256'] == baseline['evaluation_config_sha256']
reproduction = json.loads((ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation/reproduction_contract.json').read_text())['entries']['2003']
config_path = ROOT / reproduction['run_dir'] / 'resolved.yaml'
assert sha(config_path) == actual['evaluation_config_sha256']
config = yaml.safe_load(config_path.read_text())
reports = []
for i, (selected, previous, observed) in enumerate(zip(selection['records'], baseline['records'], actual['records'])):
    assert sha(ROOT / selected['source_receipt']) == selected['source_receipt_sha256']
    assert observed == json.loads((HERE / f'controls/point{i}_receipt.json').read_text())
    assert observed['selection_index'] == previous['selection_index'] == i
    assert observed['point'] == previous['point'] == selected['point']
    assert all(config['params'][k]['prior']['min'] < v < config['params'][k]['prior']['max'] for k, v in observed['point'].items())
    for r in [previous, observed]:
        assert r['status'] == 'finite_evaluation'
        assert not r['native_error_is_posterior_rejection']
        assert np.isfinite([r['logpost'], *r['loglikes'], *r['logpriors']]).all()
        assert math.isclose(r['logpost'], math.fsum(r['loglikes'] + r['logpriors']), abs_tol=1e-9, rel_tol=0)
        assert sha(ROOT / r['provider_arrays']) == r['provider_arrays_sha256']
    assert [float(v).hex() for v in observed['logpriors']] == [float(v).hex() for v in previous['logpriors']]
    assert float(observed['loglikes'][1]).hex() == float(previous['loglikes'][1]).hex()
    delta = observed['logpost'] - previous['logpost']
    assert abs(delta) <= contract['logpost_absolute_tolerance']
    arrays = {}
    with np.load(ROOT / previous['provider_arrays'], allow_pickle=False) as a, np.load(ROOT / observed['provider_arrays'], allow_pickle=False) as b:
        assert set(a.files) == set(b.files)
        for name in a.files:
            assert a[name].shape == b[name].shape
            assert np.isfinite(a[name]).all() and np.isfinite(b[name]).all()
            absolute = float(np.max(np.abs(a[name] - b[name])))
            norm = float(np.max(np.abs(a[name])))
            if not norm:
                assert absolute == 0
            relative = absolute / norm if norm else 0.
            assert relative <= contract['array_normalized_infinity_tolerance']
            arrays[name] = relative
    reports.append({'selection_index': i, 'point': observed['point'], 'combined_minus_sigma_only_logpost': delta,
                    'normalized_array_differences': arrays, 'priors_and_BAO_binary64_exact': True})

warnings = (HERE / 'controls_corrected_stdout.txt').read_text().count('WARNING: mismatch in integrated times')
assert warnings == contract['integrated_time_warning_count_required'] == 0
order = json.loads((HERE / 'near_zero_time_controls_receipt.json').read_text())
assert len(order['records']) == 15
assert all(r['monotone'] and r['final_time'] == r['tau0'] for r in order['records'])
api = json.loads((HERE / 'normalized_time_api_receipt.json').read_text())
old_api_path = ROOT / 'runs/20261005_math_review_sigma_time_endpoint_candidate_v3/baseline_time_api_receipt.json'
old_api = json.loads(old_api_path.read_text())
assert api['point'] == old_api['point'] == order['point']
assert api['module_sha256'] == build['module_sha256']
assert api['records'] == old_api['records'] and len(api['records']) == 60
assert api['empty_array_preserved'] and old_api['empty_array_preserved']
with (HERE / 'combined_policy_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_not_independent_agent',
        'policy_sha256': sha(policy_path), 'module_sha256': build['module_sha256'],
        'source_members_checked': len(prep['files']), 'changed_files': sorted(specs), 'source_reversed_exactly': True,
        'comparison_contract_sha256': sha(HERE / 'comparison_contract.json'), 'records': reports,
        'selected_CMB_controls': 20, 'warnings_remaining': warnings,
        'maximum_logpost_difference': max(abs(r['combined_minus_sigma_only_logpost']) for r in reports),
        'maximum_normalized_array_difference': max(v for r in reports for v in r['normalized_array_differences'].values()),
        'near_zero_order_and_endpoint_controls': 15, 'unchanged_explicit_tolerance_and_nonzero_API_records': 60,
        'empty_array_preserved': True, 'baseline_API_receipt_sha256': sha(old_api_path),
        'mathematical_scope': 'For finite positive total S and tau0 T and ordered nonnegative partials s_i<=S, T*(s_i/S) is monotone, nonnegative and has exact final endpoint T. Exact real additive integrals have S=T; sampled floating quadrature error is not globally certified.',
        'uniform_physical_error_or_prior_support_or_posterior_certificate': False, 'production_adopted': False},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('Both source patches and all 20 matched CMB, 15 ordering and 60 API controls reviewed.')
