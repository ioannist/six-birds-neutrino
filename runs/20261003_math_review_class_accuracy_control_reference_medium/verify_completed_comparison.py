"""Reconcile all four completed coordinates; provide no uniform error bound."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
paths = {
    'reference_medium': HERE / 'metrics.json',
    'reference': ROOT / 'runs/20261003_math_review_class_accuracy_control_reference/metrics.json',
    'medium': ROOT / 'runs/20261003_math_review_class_accuracy_control_medium/metrics.json',
}
launch = json.loads((HERE / 'launch_receipt.json').read_text())
for name, digest in launch['inputs_sha256'].items():
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest
runtime = json.loads((HERE / 'runtime_state.json').read_text())
assert runtime['status'] == 'complete_sampled_sensitivity_control_not_error_certificate'
data = {key: json.loads(path.read_text()) for key, path in paths.items()}
coverage_path = HERE / 'legacy_coverage_verification.json'
coverage = json.loads(coverage_path.read_text())
assert coverage['completed_control_baseline_sha256'] == hashlib.sha256((HERE / 'baseline.yaml').read_bytes()).hexdigest()
for key, item in coverage['records'].items():
    assert item['metrics_sha256'] == hashlib.sha256(paths[key].read_bytes()).hexdigest()
    for phase, proof in item['phases'].items():
        config_path = paths[key].parent / (phase + '.yaml')
        assert proof['configuration_sha256'] == hashlib.sha256(config_path.read_bytes()).hexdigest()
        assert proof['requested_spectrum_ell_max'] == {'tt': 4095, 'ee': 4095}
points = json.loads((HERE / 'points.json').read_text())
assert set(points) == {'audit_A', 'audit_B', 'audit_A_mass_minus', 'audit_A_mass_plus'}
records = {key: value['records'] for key, value in data.items()}
assert set(records['reference_medium']) == {'baseline', 'selected_reference_settings'}
assert data['reference_medium']['precision_settings_source'] == json.loads((HERE / 'precision_settings.json').read_text())
assert yaml.safe_load((HERE / 'baseline.yaml').read_text()) == yaml.safe_load((HERE / 'input.yaml').read_text())
for phase in records['reference_medium'].values():
    assert set(phase) == set(points)


def own(record, lens):
    other = 'lensB' if lens == 'A' else 'lensA'
    return math.fsum(value for name, value in record['native_chi2'].items() if name != other)


results = {}
for label, point in points.items():
    lens = 'B' if label == 'audit_B' else 'A'
    baseline = records['reference_medium']['baseline'][label]
    selected = records['reference_medium']['selected_reference_settings'][label]
    for key, group in records.items():
        for phase in ['baseline', 'selected_reference_settings']:
            item = group[phase][label]
            assert item['point'] == point
            if 'spectrum_ell_max' in item:
                assert item['spectrum_ell_max'] == {'tt': 4095, 'ee': 4095}
            else:
                assert coverage['records'][key]['phases'][phase]['requested_spectrum_ell_max'] == {'tt': 4095, 'ee': 4095}
            assert set(item['native_chi2']) == set(baseline['native_chi2'])
            assert all(math.isfinite(value) for value in item['native_chi2'].values())
            assert math.isfinite(item['elapsed_seconds']) and item['elapsed_seconds'] > 0
        assert group['baseline'][label]['native_chi2'] == baseline['native_chi2']
    results[label] = {
        'point': point,
        'own_joint_reference_medium_minus_controls': {
            key: own(selected, lens) - own(group['selected_reference_settings'][label], lens)
            for key, group in records.items() if key != 'reference_medium'},
        'elapsed_seconds': selected['elapsed_seconds'],
    }
local_changes = {}
for key, group in records.items():
    source = group['selected_reference_settings']['audit_A']
    local_changes[key] = {}
    for suffix, offset in [('minus', -.001), ('plus', .001)]:
        moved = group['selected_reference_settings']['audit_A_mass_' + suffix]
        assert source['point'].keys() == moved['point'].keys()
        assert all(source['point'][name] == moved['point'][name] for name in source['point'] if name != 'mnu_sample')
        assert math.isclose(moved['point']['mnu_sample'] - source['point']['mnu_sample'], offset, rel_tol=0, abs_tol=1e-16)
        local_changes[key][suffix] = own(moved, 'A') - own(source, 'A')
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'four_completed_fixed_coordinates_and_conditional_A_mass_offsets',
    'source_sha256': {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()},
    'launch_inputs_sha256_verified': True,
    'legacy_coverage_verification_sha256': hashlib.sha256(coverage_path.read_bytes()).hexdigest(),
    'coverage_basis': 'explicit_completed_control_metadata_and_initialized_saved_legacy_configurations',
    'all_baseline_native_components_equal_prior_controls': True,
    'results': results, 'A_local_mass_changes': local_changes,
    'A_local_change_reference_medium_minus_controls': {
        key: {suffix: local_changes['reference_medium'][suffix] - changes[suffix] for suffix in ['minus', 'plus']}
        for key, changes in local_changes.items() if key != 'reference_medium'},
    'interpretation': 'Quadrature and integrator settings change together. Agreement applies only at these four declared coordinates.',
    'posterior_accuracy_certified': False, 'interval_error_certified': False,
}
(HERE / 'completed_comparison_verification.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps(receipt, indent=2, allow_nan=False))
