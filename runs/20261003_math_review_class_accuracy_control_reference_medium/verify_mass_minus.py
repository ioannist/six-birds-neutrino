"""Reconcile the completed A mass-minus point and its conditional local change."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
paths = {
    'reference_medium': HERE / 'mass_minus_progress_snapshot.json',
    'reference': ROOT / 'runs/20261003_math_review_class_accuracy_control_reference/metrics.json',
    'medium': ROOT / 'runs/20261003_math_review_class_accuracy_control_medium/metrics.json',
}
data = {key: json.loads(path.read_text()) for key, path in paths.items()}
records = {key: value if key == 'reference_medium' else value['records']
           for key, value in data.items()}
labels = ['audit_A', 'audit_A_mass_minus']


def own(record):
    return math.fsum(value for name, value in record['native_chi2'].items() if name != 'lensB')


differences = {}
for label in labels:
    base = records['reference_medium']['baseline'][label]
    selected = records['reference_medium']['selected_reference_settings'][label]
    assert selected['spectrum_ell_max'] == {'tt': 4095, 'ee': 4095}
    assert base['point'] == selected['point']
    assert all(math.isfinite(value) for value in selected['native_chi2'].values())
    differences[label] = {}
    for key in ['reference', 'medium']:
        other_base = records[key]['baseline'][label]
        other = records[key]['selected_reference_settings'][label]
        assert base['point'] == other_base['point'] == other['point']
        assert base['native_chi2'] == other_base['native_chi2']
        assert set(selected['native_chi2']) == set(other['native_chi2'])
        differences[label][key] = own(selected) - own(other)
local_changes = {}
for key, group in records.items():
    source, minus = [group['selected_reference_settings'][label] for label in labels]
    assert source['point'].keys() == minus['point'].keys()
    assert all(source['point'][name] == minus['point'][name]
               for name in source['point'] if name != 'mnu_sample')
    assert math.isclose(source['point']['mnu_sample'] - minus['point']['mnu_sample'],
                        .001, rel_tol=0, abs_tol=1e-16)
    local_changes[key] = own(minus) - own(source)
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'completed_conditional_A_minus_0.001_eV_point_A_plus_still_pending',
    'source_sha256': {key: hashlib.sha256(path.read_bytes()).hexdigest()
                      for key, path in paths.items()},
    'baseline_native_components_equal_prior_controls': True,
    'only_sampled_mass_differs_between_local_pair': True,
    'own_joint_reference_medium_minus_controls': differences,
    'A_mass_minus_own_joint_chi2_change': local_changes,
    'local_change_reference_medium_minus_controls': {
        key: local_changes['reference_medium'] - local_changes[key]
        for key in ['reference', 'medium']},
    'native_mass_minus_record': records['reference_medium']['selected_reference_settings']['audit_A_mass_minus'],
    'interpretation': 'Quadrature and integrator settings change together. Agreement is local to this fixed-coordinate mass pair; no posterior or interval error certificate follows.',
    'posterior_accuracy_certified': False,
    'interval_error_certified': False,
}
(HERE / 'mass_minus_comparison.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
