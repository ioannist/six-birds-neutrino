"""Close completed verification packets and reconcile authoritative review state."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
utc = lambda: datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


state_path = ROOT / 'runs/20261003_math_review_validation/review_state.json'
s = read(state_path)
for group, session in [('current_A4095', 8104), ('current_B4095', 30564)]:
    root = ROOT / f'runs/20261005_math_review_fresh_CAMB_ninth_{group}_diagnostics_v2'
    stages = [read(root / f'{name}.completion.json') for name in
              ['verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py']]
    assert all(stage['exit_code'] == 0 for stage in stages)
    review = read(root / 'self_review_receipt.json')
    native = read(root / 'native_rows_verification.json')
    diagnostics = read(root / 'diagnostics.json')
    errors = [abs(v) for record in native['records'] for check in record['checks']
              for v in check['fresh_minus_recorded'].values()]
    count = sum(len(record['checks']) for record in native['records'])
    assert count == 12 and max(errors) == 0.0
    passing = [k for k, v in review['all_seven_parameter_gate_sets_reconstructed'].items() if v['pass']]
    assert not diagnostics['all_diagnostic_thresholds_pass']
    write_new(root / 'execution_receipt.json', {'utc': utc(), 'managed_session': session,
        'actual_terminal_exit_code': 0, 'stages': stages, 'all_diagnostic_workers_complete': True})
    rel = str(root.relative_to(ROOT))
    mass = diagnostics['diagnostics']['mnu']
    s['fresh_CAMB_production_assessments'][group] = {
        'root': rel, 'native_verification': rel + '/native_rows_verification.json',
        'diagnostics': rel + '/diagnostics.json', 'self_review': rel + '/self_review_receipt.json',
        'execution_receipt': rel + '/execution_receipt.json', 'managed_session': session,
        'all_three_verification_stages_exit_code': 0,
        'minimum_saved_postburn_history': min(review['retained_represented_steps']),
        'next_minimum_history': review['next_minimum_history'], 'selected_native_rows': count,
        'maximum_native_component_error': max(errors), 'all_parameter_gate_sets_pass': False,
        'passing_parameters': passing, 'mass_Rhat': mass['rank_folded_split_rhat'],
        'mass_bulk_ESS': mass['bulk_ess'], 'mass_tail_ESS': mass['tail_ess_05_95'],
        'mass_MCSE_eV': mass['quantile_mcse'], 'posterior_qualified': False}

activation = ROOT / 'runs/20261005_math_review_CLASS_fresh_recovery_activation'
review = read(activation / 'self_review_receipt.json')
assert len(review['records']) == 2
for e in s['guarded_CLASS_fresh_recovery_trials']:
    proof = activation / f'seed{e["seed"]}/first_saved_row/completion_receipt.json'
    d = read(proof)
    assert d['native_row_verified'] and max(map(abs, d['native_check']['fresh_minus_recorded'].values())) == 0
    e['first_saved_row_receipt'] = str(proof.relative_to(ROOT))
    e['first_saved_row_receipt_sha256'] = sha(proof)
    e['status'] = 'running_fresh_CLASS_recovery_first_saved_native_row_verified'
s['guarded_CLASS_fresh_recovery_preparation'].update({
    'first_saved_rows_pending': False, 'two_first_saved_native_rows_verified': True,
    'selected_row_self_review': str((activation / 'self_review_receipt.json').relative_to(ROOT))})
write_new(activation / 'execution_receipt.json', {
    'utc': utc(), 'first_saved_row_workers': [
        {'seed': 2201, 'managed_session': 67810, 'actual_terminal_exit_code': 0},
        {'seed': 2202, 'managed_session': 83138, 'actual_terminal_exit_code': 0}],
    'activation_verifier_direct_exit_code': 0, 'selected_row_self_review_direct_exit_code': 0,
    'preserved_self_review_attempt_exit_codes': [1, 1],
    'all_verification_workers_terminal': True, 'inference_workers_still_active': True})
previous_observer = ROOT / 'runs/20261005_math_review_registered66_checkpoint_v2'
write_new(previous_observer / 'execution_receipt.json', {'utc': utc(),
    'runtime_managed_session': 52128, 'actual_terminal_exit_code': 0,
    'self_review_direct_exit_code': 0, 'all_verification_workers_terminal': True})

# Prepare a fresh immutable runtime observation with the now-proven first rows.
source = previous_observer / 'observe_registered_runtime.py'
changes = [
    ("if 2100 <= e['seed'] < 2200:", "if e['seed'] >= 2100:"),
    ("assert not (ROOT / 'runs/20261005_math_review_sigma_time_v3_posterior_activation' / f'seed{e[\"seed\"]}' / 'launcher_stderr.txt').read_bytes()",
     "activation_name = 'sigma_time_v3_posterior_activation' if e['seed'] < 2200 else 'CLASS_fresh_recovery_activation'\n        assert not (ROOT / f'runs/20261005_math_review_{activation_name}' / f'seed{e[\"seed\"]}' / 'launcher_stderr.txt').read_bytes()"),
    ("assert chain is not None or e['seed'] >= 2200", "assert chain is not None"),
    ("assert (weights or e['seed'] >= 2200) and all(w > 0 and w.denominator == 1 for w in weights)",
     "assert weights and all(w > 0 and w.denominator == 1 for w in weights)")]
text = source.read_text()
for before, after in changes:
    assert text.count(before) == 1
    text = text.replace(before, after, 1)
with (HERE / 'observe_registered_runtime.py').open('x') as f:
    f.write(text)
with (HERE / 'self_review.py').open('xb') as f:
    f.write((previous_observer / 'self_review.py').read_bytes())
write_new(HERE / 'observer_preparation_receipt.json', {'utc': utc(),
    'source': str(source.relative_to(ROOT)), 'source_sha256': sha(source), 'changes': changes,
    'scope': 'Require complete saved-row proofs for both separate CLASS recovery trials; preserve every original cohort.'})
s['native_failure_next_repair_obligation'] = (
    'Assess each of four sigma_time_v3 cap5/cap20 candidate targets after its fixed history gate; '
    'production diagnostic workflow and 48 control native rows are verified. Both fresh CLASS recovery '
    'first rows replay exactly; construct a separately declared valid four-family recovery design '
    'without dropping original terminal registrations or pooling numerical targets. '
    'Uniform physical accuracy, prior stability and both material main-claim discussions remain open.')
with state_path.open('w') as f:
    json.dump(s, f, indent=2, allow_nan=False)
    f.write('\n')
print('Closed selected-row and CAMB packets; prepared fresh registered-family observation.')
