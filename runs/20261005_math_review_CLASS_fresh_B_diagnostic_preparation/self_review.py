"""Reconstruct unchanged thresholds, native evidence and actual refusal/control paths."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTROL = ROOT / 'runs/20261005_math_review_CLASS_fresh_B_prethreshold_controls'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())


def reverse_helpers(folder):
    receipt = read(folder / 'worker_preparation_receipt.json')
    for item in receipt['records']:
        source = ROOT / item['source']
        assert sha(source) == item['source_sha256']
        actual = (folder / item['name']).read_text()
        for before, after in reversed(item['changes']):
            assert actual.count(after) == 1
            actual = actual.replace(after, before, 1)
        assert actual.encode() == source.read_bytes()
    return receipt


receipt = reverse_helpers(HERE)
older = ROOT / receipt['original_adaptation_receipt']
assert sha(older) == receipt['original_adaptation_receipt_sha256']
reverse_helpers(older.parent)
contract = read(HERE / 'assessment_contract.json')
source = read(ROOT / 'runs/20261005_math_review_sigma_time_v3_diagnostic_preparation/assessment_contract.json')
for key in ['first_minimum_retained_represented_steps', 'burnin_fraction_of_stored_rows',
            'later_growth_factor', 'absolute_mass_quantile_MCSE_limit',
            'relative_other_parameter_MCSE_limit', 'native_replay_atol', 'native_replay_rtol',
            'native_rows_per_family', 'diagnostic_source_sha256']:
    assert contract[key] == source[key]
assert contract['first_minimum_retained_represented_steps'] == 1000
assert contract['compatible_predecessor_contracts'] == {}
state = read(ROOT / 'runs/20261003_math_review_validation/review_state.json')
assert set(contract['groups']) == set(state['CLASS_fresh_B_preparation']['cohorts'])
records = []
for group, entries in contract['groups'].items():
    assert [e['seed'] for e in entries] == state['CLASS_fresh_B_preparation']['cohorts'][group]['seeds']
    signatures = []
    for e in entries:
        cfg = yaml.safe_load((ROOT / e['config']).read_text())
        assert sha(ROOT / e['config']) == e['config_sha256']
        parameters = deepcopy(cfg['params'])
        for block in parameters.values():
            if isinstance(block, dict):
                block.pop('ref', None)
                block.pop('proposal', None)
        signatures.append((cfg['theory'], cfg['likelihood'], cfg.get('prior'), parameters))
        proof = ROOT / e['first_saved_row_receipt']
        d = read(proof)
        assert sha(proof) == e['first_saved_row_receipt_sha256']
        assert d['native_row_verified'] and d['module_sha256'] == e['module_sha256'] == sha(e['module'])
        assert sha(e['wrapper']) == e['wrapper_sha256']
        backend = read(ROOT / e['run_dir'] / 'solver_backend.json')
        assert backend.get('solver_version') is None and e['solver_version'] is None
        assert len([n for n, b in cfg['params'].items() if isinstance(b, dict) and 'prior' in b]) == 10
    assert all(s == signatures[0] for s in signatures)
    out = CONTROL / group
    stages = read(out / 'execution_receipt.json')['records']
    assert len(stages) == 3 and all(s['actual_terminal_exit_code'] == 0 for s in stages)
    native = read(out / 'native_rows_verification.json')
    assert native['solver_version'] is None
    assert native['loaded_CLASS_version'] == entries[0]['loaded_CLASS_version']
    checks = [c for r in native['records'] for c in r['checks']]
    assert len(checks) == 12
    errors = [abs(v) for c in checks for v in c['fresh_minus_recorded'].values()]
    assert max(errors) == 0.0
    review = read(out / 'self_review_receipt.json')
    assert review['sampled_parameter_count'] == 10
    assert len(review['all_sampled_parameter_gate_sets_reconstructed']) == 10
    assert not read(out / 'diagnostics.json')['all_diagnostic_thresholds_pass']
    records.append({'group': group, 'selected_native_rows': 12, 'maximum_native_component_error': max(errors),
                    'native_receipt_sha256': sha(out / 'native_rows_verification.json'),
                    'self_review_receipt_sha256': sha(out / 'self_review_receipt.json')})

controls = read(CONTROL / 'assessment_contract.json')
reconstructed = deepcopy(controls)
reconstructed['first_minimum_retained_represented_steps'] = contract['first_minimum_retained_represented_steps']
reconstructed['scope'] = contract['scope']
assert reconstructed == contract
for name in ['prepare_snapshot.py', 'verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py', 'contract_compatibility.py']:
    assert (CONTROL / name).read_bytes() == (HERE / name).read_bytes()
refusals = read(HERE / 'prethreshold_refusals_receipt.json')
assert len(refusals['records']) == 2 and all(r['actual_terminal_exit_code'] == 3 and not r['snapshot_created'] for r in refusals['records'])
transitions = read(HERE / 'unsafe_transition_controls_receipt.json')
assert len(transitions['records']) == 2 and all(r['actual_terminal_exit_code'] == 1 and not r['snapshot_created'] for r in transitions['records'])
wrong_module = read(CONTROL / 'wrong_native_environment_receipt.json')
assert wrong_module['actual_terminal_exit_code'] == 1 and wrong_module['existing_positive_native_proof_unchanged']
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': records,
        'all_thresholds_and_ten_parameter_coverage_reconstructed': True,
        'all_eight_native_first_row_bindings_checked': True,
        'recorded_unknown_version_not_replaced_by_installed_metadata': True,
        'two_production_prethreshold_refusals': True, 'two_unsafe_predecessors_refused': True,
        'wrong_loaded_native_environment_refused': True, 'production_assessments_completed': 0,
        'posterior_or_uniform_accuracy_certified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Two CLASS workflows reviewed: 24 selected native rows exact, all ten parameter gates retained.')
