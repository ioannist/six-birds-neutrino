"""Separate self-review of target isolation and recorded native arithmetic."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
prep = read(HERE / 'preparation_receipt.json')
result = read(HERE / 'preflight_receipt.json')
completion = read(HERE / 'preflight_completion.json')
state = read(ROOT / 'runs/20261003_math_review_validation/review_state.json')
assert completion['exit_code'] == 0
assert not (HERE / 'preflight_stderr.txt').read_bytes()
assert set(prep['groups']) == {'current_A4095', 'current_B4095'}
assert set(prep['implementation_sha256']) == {str(p.relative_to(ROOT)) for p in (ROOT / 'src/sbt_spt_audit').rglob('*.py')}
for path, digest in prep['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
finite = rejected = 0
comparisons = []
for group, entry in prep['groups'].items():
    original = ROOT / entry['source_config']
    assert sha(original) == entry['source_config_sha256']
    full = yaml.safe_load(original.read_text())
    baseline = {k: deepcopy(v) for k, v in full.items() if k in {'theory', 'likelihood', 'params', 'packages_path', 'prior'}}
    assert baseline['params']['mnu']['prior'] == {'min': 0.0, 'max': 5.0}
    source_entry = next(e for e in state['fresh_CAMB_posterior_chains'] if e['seed'] == entry['baseline_seed'])
    assert source_entry['group'] == group
    assert source_entry['config_sha256'] == entry['source_config_sha256']
    assert entry['points']['original_reference'] == source_entry['initial_point']
    native_path = ROOT / entry['native_baseline_verification']
    assert sha(native_path) == entry['native_baseline_verification_sha256']
    native = read(native_path)
    source_record = next(r for r in native['records'] if r['seed'] == entry['baseline_seed'])
    assert entry['points']['selected_latest_frozen_row'] == source_record['checks'][-1]['point']
    for label, mass in [('mass_6_eV', 6.0), ('mass_12_eV', 12.0)]:
        point = deepcopy(source_entry['initial_point']); point['mnu'] = mass
        assert entry['points'][label] == point
    for kind in ['module', 'wrapper']:
        assert sha(entry['expected_environment'][kind]) == entry['expected_environment'][kind + '_sha256']
    caps = {}
    assert set(entry['controls']) == {'5', '10', '20'}
    for cap, control in entry['controls'].items():
        model_path = ROOT / control['path']
        assert sha(model_path) == control['sha256']
        actual = yaml.safe_load(model_path.read_text())
        expected = deepcopy(baseline)
        expected['params']['mnu']['prior']['max'] = float(cap)
        assert actual == expected and 'sampler' not in actual and 'output' not in actual
        data = read(model_path.parent / 'native_points.json')
        assert data['group'] == group and data['upper_eV'] == float(cap)
        assert data['config_sha256'] == control['sha256']
        caps[cap] = data['points']
        assert set(data['points']) == set(entry['points'])
        for label, point in data['points'].items():
            assert point['point'] == entry['points'][label]
            if point['point']['mnu'] > float(cap):
                assert point['status'] == 'outside_declared_mass_prior'
                assert point['logposterior'] is None and point['native_likelihood_evaluated'] is False
                rejected += 1
            else:
                assert point['status'] == 'finite_native_target'
                assert point['upstream_forced_fresh_exact'] is True
                assert point['likelihood_components']
                assert all(math.isfinite(v) for v in [point['logposterior'], point['logprior'], *point['likelihood_components'].values()])
                assert abs(point['logposterior'] - point['logprior'] - math.fsum(point['likelihood_components'].values())) < 1e-9
                finite += 1
    for cap in ['10', '20']:
        for label in ['original_reference', 'selected_latest_frozen_row']:
            base, widened = caps['5'][label], caps[cap][label]
            assert base['likelihood_components'] == widened['likelihood_components']
            shift = math.log(5.0) - math.log(float(cap))
            prior_error = widened['logprior'] - base['logprior'] - shift
            posterior_error = widened['logposterior'] - base['logposterior'] - shift
            assert max(abs(prior_error), abs(posterior_error)) < 1e-10
            comparisons.append({'group': group, 'upper_eV': float(cap), 'point_label': label,
                                'expected_log_density_shift': shift, 'prior_shift_error': prior_error,
                                'posterior_shift_error': posterior_error, 'likelihood_components_exactly_equal': True})
assert finite == result['native_finite_points'] == 18
assert rejected == result['prior_rejected_points'] == 6
assert len(comparisons) == len(result['comparisons']) == 8
for reconstructed, recorded in zip(comparisons, result['comparisons']):
    for key in reconstructed:
        if isinstance(reconstructed[key], float):
            assert abs(reconstructed[key] - recorded[key]) < 1e-14
        else:
            assert reconstructed[key] == recorded[key]
assert result['samplers_launched'] == 0
assert not result['tail_probability_estimated'] and not result['quantile_stability_estimated']
assert not result['uniform_solver_accuracy_certified']
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct self-review',
           'six_models_rederived_from_original_targets': True, 'only_prior_upper_endpoint_changed': True,
           'source_and_native_hashes_unchanged': True, 'finite_points': finite, 'prior_rejected_points': rejected,
           'common_point_comparisons_recomputed': len(comparisons),
           'maximum_prior_shift_error': max(abs(c['prior_shift_error']) for c in comparisons),
           'maximum_posterior_shift_error': max(abs(c['posterior_shift_error']) for c in comparisons),
           'conditional_law_premises_remain_explicit': ['identical likelihood and other priors', 'proper positive-evidence wide posterior'],
           'posterior_tail_or_quantile_stability_established': False, 'uniform_accuracy_established': False,
           'preflight_receipt_sha256': sha(HERE / 'preflight_receipt.json'),
           'preparation_receipt_sha256': sha(HERE / 'preparation_receipt.json')}
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps(receipt, indent=2), flush=True)
