"""Record already-closed workers and advance separately reviewed cohort pointers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
utc = datetime.now(timezone.utc).isoformat()
state_path = ROOT / 'runs/20261003_math_review_validation/review_state.json'
state = json.loads(state_path.read_text())
before = sha(state_path)
for group, session in [('current_A4095', 67445), ('current_B4095', 76002)]:
    relative = f'runs/20261004_math_review_fresh_CAMB_seventh_{group}_diagnostics'
    root = ROOT / relative
    stages = [json.loads((root / (n + '.completion.json')).read_text())
              for n in ['verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py']]
    assert all(r['exit_code'] == 0 for r in stages)
    assert not (root / 'verification_worker_stderr.txt').read_bytes()
    proof = json.loads((root / 'native_rows_verification.json').read_text())
    checks = [c for r in proof['records'] for c in r['checks']]
    assert len(checks) == 12
    errors = [abs(v) for c in checks for v in c['fresh_minus_recorded'].values()]
    assert max(errors) == 0
    review = json.loads((root / 'self_review_receipt.json').read_text())
    assert review['diagnostics_sha256'] == sha(root / 'diagnostics.json')
    assert review['native_row_verification_sha256'] == sha(root / 'native_rows_verification.json')
    assert review['snapshot_receipt_sha256'] == sha(root / 'snapshot_receipt.json')
    gates = review['all_seven_parameter_gate_sets_reconstructed']
    passing = [k for k, v in gates.items() if v['pass']]
    assert len(gates) == 7 and passing == []
    mass = json.loads((root / 'diagnostics.json').read_text())['diagnostics']['mnu']
    execution = {'utc': utc, 'managed_session': session, 'actual_terminal_exit_code': 0,
                 'stages': stages, 'all_diagnostic_workers_complete': True}
    with (root / 'execution_receipt.json').open('x') as f:
        f.write(json.dumps(execution, indent=2) + '\n')
    state['fresh_CAMB_production_assessments'][group] = {
        'root': relative, 'native_verification': relative + '/native_rows_verification.json',
        'diagnostics': relative + '/diagnostics.json', 'self_review': relative + '/self_review_receipt.json',
        'execution_receipt': relative + '/execution_receipt.json', 'managed_session': session,
        'all_three_verification_stages_exit_code': 0, 'selected_native_rows': 12,
        'maximum_native_component_error': 0.0,
        'minimum_saved_postburn_history': min(review['retained_represented_steps']),
        'next_minimum_history': review['next_minimum_history'], 'passing_parameters': passing,
        'all_parameter_gate_sets_pass': False, 'mass_Rhat': mass['rank_folded_split_rhat'],
        'mass_bulk_ESS': mass['bulk_ess'], 'mass_tail_ESS': mass['tail_ess_05_95'],
        'mass_MCSE_eV': mass['quantile_mcse'], 'posterior_qualified': False}

relative = 'runs/20261004_math_review_guarded_CLASS_eighth_quad_A_diagnostics'
root = ROOT / relative
completion = json.loads((root / 'quad_A_completion.json').read_text())
assert completion['exit_code'] == 0
review = json.loads((root / 'self_review_receipt.json').read_text())
verification = json.loads((root / 'completion_verification.json').read_text())
assert review['completion_verification_sha256'] == sha(root / 'completion_verification.json')
assert review['runtime_observation_sha256'] == sha(root / 'runtime_observation.json')
assert json.loads((root / 'runtime_observation.json').read_text())['owned_live_samplers'] == 40
mass = verification['cohort_mass_diagnostics']['quad_A']
assert not mass['all_parameter_gates_pass'] and mass['passing_parameter_count'] == 1
with (root / 'execution_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': utc, 'stages': [
        {'script': 'run_diagnostics.py', 'managed_session': 8982, 'exit_code': 0},
        {'script': 'observe_runtime.py', 'direct_exec_exit_code': 0},
        {'script': 'verify_snapshot.py', 'direct_exec_exit_code': 0},
        {'script': 'self_review.py', 'direct_exec_exit_code': 0}],
        'all_four_workers_terminal': True, 'posterior_convergence_certified': False}, indent=2) + '\n')
state['guarded_CLASS_latest_diagnostic_cohorts']['quad_A'] = mass
state['guarded_CLASS_latest_diagnostic_bundle_by_cohort']['quad_A'] = relative
for k in ['guarded_CLASS_next_diagnostic_minimum_represented_steps', 'guarded_CLASS_next_assessment_minimum_history']:
    state[k]['quad_A'] = 7353
state['guarded_CLASS_eighth_quad_A_diagnostics'] = relative + '/completion_verification.json'
state['guarded_CLASS_eighth_quad_A_managed_diagnostic'] = {
    'session': 8982, 'status': 'complete_exit0', 'exit_code': 0,
    'completion_receipt': relative + '/quad_A_completion.json',
    'execution_receipt': relative + '/execution_receipt.json',
    'self_review': relative + '/self_review_receipt.json',
    'minimum_saved_postburn_history': mass['draws_per_chain'], 'next_minimum_history': 7353,
    'all_parameter_gates_pass': False}

index = json.loads((HERE / 'terminal_reproduction_index.json').read_text())
for e in state['native_failure_diagnostic_reproductions']:
    r = next(r for r in index['records'] if r['seed'] == e['seed'])
    v = json.loads((ROOT / r['receipt']).read_text())
    assert sha(ROOT / r['receipt']) == r['receipt_sha256']
    e.update(status='terminal_exit1_captured_NaNs_all_original_saved_rows_preserved',
             terminal_exit_code=1, terminal_verification=r['receipt'], terminal_verification_sha256=r['receipt_sha256'],
             all_original_saved_rows_verified=v['original_saved_rows'], replay_saved_rows=v['replay_saved_rows'],
             original_unflushed_tail_or_failing_proposal_known=False,
             whole_failed_trajectory_verified=False, pool_with_posterior=False)
state['native_failure_diagnostic_reproductions_current_live_count'] = 0
state['native_failure_reproduction_scope'] = 'Both diagnostic replays terminal exit1; every original saved row preserved exactly (217 and225), but unsaved original tails unavailable. Captured prior-interior proposals yield NaNs; no posterior pooling or rejection.'
state['native_failure_reproduction_terminal_verification'] = str((HERE / 'terminal_reproduction_index.json').relative_to(ROOT))
state['fresh_CAMB_latest_qualified_readout'] = None
state_path.write_text(json.dumps(state, indent=2, allow_nan=False) + '\n')
with (HERE / 'assessment_state_update_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': utc, 'state_before_sha256': before, 'state_after_sha256': sha(state_path),
                        'completed_assessments': ['current_A4095_seventh', 'current_B4095_seventh', 'quad_A_eighth'],
                        'inference_live_count_unchanged': state['current_owned_live_sampler_count'],
                        'diagnostic_replays_current_live_count': 0,
                        'paper_or_canonical_changed': False}, indent=2) + '\n')
print('Recorded three completed assessments and both terminal diagnostic replays; no qualified posterior.')
