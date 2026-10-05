"""Recompute accounting and local mass comparisons from completed native records."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
paths = {
    'broader': HERE / 'metrics.json',
    'seven': ROOT / 'runs/20261003_math_review_class_accuracy_control/metrics.json',
    'medium': ROOT / 'runs/20261003_math_review_class_accuracy_control_medium/metrics.json',
    'lensing': ROOT / 'runs/20261003_math_review_class_accuracy_control_lensing/metrics.json',
}
data = {k: json.loads(p.read_text()) for k, p in paths.items()}
records = {k: v['records'] for k, v in data.items()}
names = ['audit_A', 'audit_B', 'audit_A_mass_minus', 'audit_A_mass_plus']
def own(record, lens):
    return math.fsum(v for k, v in record['native_chi2'].items()
                     if k != ('lensB' if lens == 'A' else 'lensA'))

result = {}
for name in names:
    lens = 'B' if name == 'audit_B' else 'A'
    base = records['broader']['baseline'][name]
    refined = records['broader']['selected_reference_settings'][name]
    assert base['point'] == refined['point']
    assert all(math.isfinite(v) for v in refined['native_chi2'].values())
    differences = {}
    for setting in ['seven', 'medium', 'lensing']:
        other_base = records[setting]['baseline'][name]
        other = records[setting]['selected_reference_settings'][name]
        assert base['point'] == other_base['point'] == other['point']
        assert base['native_chi2'] == other_base['native_chi2']
        differences[setting] = own(refined, lens) - own(other, lens)
    result[name] = {
        'point': base['point'],
        'own_joint_broader_minus_default': own(refined, lens) - own(base, lens),
        'own_joint_broader_minus_controls': differences,
        'elapsed_seconds': refined['elapsed_seconds'],
    }
mass_changes = {}
for setting, rr in records.items():
    mass_changes[setting] = {}
    for name in ['audit_A_mass_minus', 'audit_A_mass_plus']:
        point = rr['selected_reference_settings'][name]['point']
        source = rr['selected_reference_settings']['audit_A']['point']
        assert all(point[k] == source[k] for k in source if k != 'mnu_sample')
        assert math.isclose(abs(point['mnu_sample'] - source['mnu_sample']), .001,
                            rel_tol=0, abs_tol=1e-16)
        delta = own(rr['selected_reference_settings'][name], 'A') - own(
            rr['selected_reference_settings']['audit_A'], 'A')
        mass_changes[setting][name] = delta
default = records['broader']['baseline']
fits_path = ROOT / 'runs/20261003_math_review_cosmological_cmb_desi_warm/fits.json'
fits = json.loads(fits_path.read_text())
source_errors = {}
for lens in ['A', 'B']:
    assert default['audit_' + lens]['point'] == fits['lens' + lens]['point']
    error = own(default['audit_' + lens], lens) + 2 * fits['lens' + lens]['loglike']
    assert abs(error) < 1e-9
    source_errors[lens] = error
mass_changes['default'] = {
    name: own(default[name], 'A') - own(default['audit_A'], 'A')
    for name in ['audit_A_mass_minus', 'audit_A_mass_plus']
}
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'four_completed_fixed_coordinate_native_comparisons',
    'baseline_components_equal_all_prior_controls': True,
    'warm_source_objective_errors': source_errors,
    'warm_fits_sha256': hashlib.sha256(fits_path.read_bytes()).hexdigest(),
    'posterior_accuracy_certified': False,
    'interval_error_certified': False,
    'source_sha256': {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
    'results': result,
    'A_mass_offsets_own_joint_chi2_changes': mass_changes,
    'A_mass_change_broader_minus_medium': {
        name: mass_changes['broader'][name] - mass_changes['medium'][name]
        for name in mass_changes['broader']
    },
}
(HERE / 'completed_comparison_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'results': result, 'mass_changes': mass_changes}, indent=2))
