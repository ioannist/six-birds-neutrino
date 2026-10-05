"""Reconstruct helper changes, fixed gates and all four separate control reports."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep = json.loads((HERE / 'worker_preparation_receipt.json').read_text())
source = ROOT / prep['source']
production = json.loads((HERE / 'assessment_contract.json').read_text())
original = json.loads((source / 'assessment_contract.json').read_text())
assert sha(source / 'assessment_contract.json') == prep['source_contract_sha256']
assert sha(HERE / 'assessment_contract.json') == prep['assessment_contract_sha256']
keys = ['first_minimum_retained_represented_steps', 'burnin_fraction_of_stored_rows', 'later_growth_factor',
        'absolute_mass_quantile_MCSE_limit', 'relative_other_parameter_MCSE_limit',
        'native_replay_atol', 'native_replay_rtol', 'native_rows_per_family', 'diagnostic_source_sha256']
assert all(production[k] == original[k] for k in keys)
assert production['first_minimum_retained_represented_steps'] == 1000
assert not production['compatible_predecessor_contracts']
for name, digest in prep['source_helpers'].items():
    assert sha(source / name) == digest
    new = (HERE / name).read_text()
    reverse = new
    for before, after in reversed(prep['helper_changes'].get(name, [])):
        assert reverse.count(after) == 1
        reverse = reverse.replace(after, before, 1)
    assert reverse.encode() == (source / name).read_bytes()
    ast.parse(new)
controls = ROOT / 'runs/20261005_math_review_sigma_time_v3_prethreshold_workflow_controls'
test = json.loads((controls / 'assessment_contract.json').read_text())
reverse = deepcopy(test)
reverse['first_minimum_retained_represented_steps'] = production['first_minimum_retained_represented_steps']
reverse['scope'] = production['scope']
assert reverse == production
refusals = json.loads((HERE / 'prethreshold_refusals_receipt.json').read_text())
assert len(refusals['records']) == 4 and refusals['all_four_output_directories_absent']
records = []
for group, entries in production['groups'].items():
    assert len(entries) == 4 and len({e['seed'] for e in entries}) == 4
    assert len({e['module_sha256'] for e in entries}) == 1
    for e in entries:
        proof = json.loads((ROOT / e['first_saved_row_receipt']).read_text())
        assert proof['native_row_verified'] and proof['module_sha256'] == e['module_sha256']
        assert sha(ROOT / e['config']) == e['config_sha256']
    refusal = next(r for r in refusals['records'] if r['group'] == group)
    assert refusal['actual_exit_code'] == 3 and refusal['threshold'] == 1000 and not refusal['snapshot_written']
    root = controls / group
    for name in ['verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py']:
        assert json.loads((root / (name + '.completion.json')).read_text())['actual_exit_code'] == 0
    native = json.loads((root / 'native_rows_verification.json').read_text())
    result = json.loads((root / 'diagnostics.json').read_text())
    review = json.loads((root / 'self_review_receipt.json').read_text())
    assert native['group'] == group and len(native['records']) == 4
    assert all(len(r['checks']) == 3 for r in native['records'])
    error = max(abs(v) for r in native['records'] for c in r['checks'] for v in c['fresh_minus_recorded'].values())
    assert error <= production['native_replay_atol']
    assert not result['all_diagnostic_thresholds_pass']
    assert len(review['all_seven_parameter_gate_sets_reconstructed']) == 7
    assert review['diagnostics_sha256'] == sha(root / 'diagnostics.json')
    records.append({'group': group, 'native_rows': 12, 'maximum_native_component_error': error,
                    'complete_reports_reconstructed': True, 'production_assessment': False,
                    'control_snapshot_receipt_sha256': sha(root / 'snapshot_receipt.json')})
unsafe = json.loads((HERE / 'unsafe_transition_controls_receipt.json').read_text())
assert unsafe['cross_cap_previous']['actual_exit_code'] == 1 and unsafe['cross_cap_previous']['output_directory_absent']
assert unsafe['old_native_policy_contract_refused']['reason'] == 'Unknown predecessor assessment contract.'
wrong = json.loads((controls / 'wrong_native_environment_receipt.json').read_text())
assert wrong['actual_exit_code'] == 1 and wrong['existing_positive_native_proof_unchanged']
assert wrong['native_proof_sha256'] == sha(controls / 'sigma_time_v3_A4095_cap5/native_rows_verification.json')
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_not_independent_agent',
        'records': records, 'production_gate_fields_identical_to_baseline': True,
        'production_first_history_trigger': 1000, 'control_threshold_separately_labelled': 1,
        'all_four_prethreshold_refusals_verified': True, 'cross_cap_and_old_policy_predecessors_refused': True,
        'wrong_native_environment_refused': True, 'selected_native_rows_checked': 48,
        'maximum_native_component_error': max(r['maximum_native_component_error'] for r in records),
        'posterior_qualification_or_uniform_accuracy_certified': False, 'production_adopted': False},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('Candidate workflow reviewed:48 native rows, four complete control reports and unchanged production gates.')
