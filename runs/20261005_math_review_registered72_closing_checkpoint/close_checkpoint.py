"""Close completed recovery/diagnostic packets and retain every original registration."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
utc = lambda: datetime.now(timezone.utc).isoformat()


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


workflow = ROOT / 'runs/20261005_math_review_CLASS_fresh_recovery_diagnostic_preparation_v2'
controls = ROOT / 'runs/20261005_math_review_CLASS_fresh_recovery_prethreshold_controls'
review = read(workflow / 'preparation_self_review_receipt.json')
assert len(review['records']) == 2
assert sum(r['selected_native_rows'] for r in review['records']) == 24
write(workflow / 'execution_receipt.json', {'utc': utc(),
    'contract_preparation_direct_exit_code': 0, 'preparation_self_review_direct_exit_code': 0,
    'production_prethreshold_refusal_exit_codes': [3, 3], 'unsafe_predecessor_refusal_exit_codes': [1, 1],
    'two_control_workflows_complete': True, 'all_verification_workers_terminal': True,
    'production_assessments_completed': 0, 'posterior_qualified': False})
write(controls / 'execution_receipt.json', {'utc': utc(),
    'managed_workers': [{'group': 'fresh_recovery_quad_A', 'session': 81638, 'actual_terminal_exit_code': 0},
                        {'group': 'fresh_recovery_medium_A', 'session': 12617, 'actual_terminal_exit_code': 0}],
    'all_control_workers_terminal': True, 'native_rows_checked': 24,
    'maximum_native_component_error': 0.0, 'wrong_loaded_native_environment_refusal_exit_code': 1,
    'production_assessments_completed': 0})
runtime = read(HERE / 'combined_runtime_verification.json')
assert runtime['registered_families'] == 72 and runtime['owned_live_samplers'] == 57
assert runtime['terminal_families'] == 15 and len(runtime['growth_by_cohort']) == 18
assert not any(v['due'] for v in runtime['growth_by_cohort'].values())
write(HERE / 'execution_receipt.json', {'utc': utc(), 'managed_session': 76593,
    'actual_terminal_exit_code': 0, 'self_review_direct_exit_code': 0,
    'all_verification_workers_terminal': True, 'inference_workers_not_modified': True})
state_path = ROOT / 'runs/20261003_math_review_validation/review_state.json'
s = read(state_path)
rel = str(HERE.relative_to(ROOT))
unknown = sorted(r['seed'] for r in runtime['records'] if r['status'] == 'terminal_exit_reason_unavailable_preserved')
assert len(unknown) == 11
s['latest_registered_runtime_observation'] = {
    'root': rel, 'runtime': rel + '/combined_runtime_verification.json',
    'self_review': rel + '/self_review_receipt.json', 'utc': runtime['utc'],
    'registered_families': 72, 'owned_live_samplers': 57,
    'terminal_native_failure_families': [2003, 2004, 2007, 2008],
    'terminal_exit_reason_unavailable_families': unknown,
    'candidate_first_saved_native_rows_verified': 16, 'CLASS_recovery_first_saved_native_rows_verified': 8,
    'declared_cohorts': 18, 'due_eligible_cohorts': [], 'historical_CLASS_cohorts_pooled_with_fresh_recovery': False}
s['active_runtime_observer'] = rel + '/observe_registered_runtime.py'
wr = str(workflow.relative_to(ROOT))
s['fresh_CLASS_recovery_active_diagnostic_workflow'] = {
    'root': wr, 'contract': wr + '/assessment_contract.json',
    'self_review': wr + '/preparation_self_review_receipt.json',
    'first_history_trigger': 1000, 'later_growth_factor': [6, 5],
    'all_ten_sampled_parameter_gates_retained': True,
    'two_production_prethreshold_refusals_verified': True,
    'two_separate_control_workflows_complete': True, 'native_control_rows_checked': 24,
    'maximum_native_component_error': 0.0, 'production_assessments_completed': 0,
    'posterior_qualified': False}
s['CLASS_recovery_cohort_companion_preparation']['new_cohort_diagnostic_workflow_pending'] = False
s['native_failure_next_repair_obligation'] = (
    'Assess each of the four sigma_time_v3 candidate targets and two separate fresh CLASS recovery '
    'cohorts after its fixed saved-history gate. All eight fresh CLASS first rows are exact and '
    'both CLASS ten-parameter workflows are exercised in separate controls. Preserve all eleven '
    'CLASS unknown exits and four known CAMB native failures. Construct separately identified '
    'fresh B precision cohorts if needed for the broader posterior comparison; old medium_B and '
    'quad_B now retain unknown-exit families and are ineligible. Uniform physical accuracy, '
    'prior stability and both material main-claim discussions remain open.')
with state_path.open('w') as f:
    json.dump(s, f, indent=2, allow_nan=False)
    f.write('\n')
with (ROOT / 'docs/findings/math_review.md').open('a') as f:
    f.write('''

All six reviewed CLASS companions activate with new output prefixes and RNG
seeds2301-2306, at nice5 and the existing recovery anchors' OMP8/4 profiles.
Actual activation and a distinct recount verify PID/start ticks, command,
mapped native library, effective configuration and process environment.
Every first complete saved row is frozen and forced-fresh replayed against
the declared guarded CLASS target. All checked prior, posterior and individual
likelihood chi2 components match exactly. Combined selected-row self-review
also reconstructs exact holding times, source prefixes, binary64 coordinates,
configuration/backend bindings and the separate CMB type aggregate. All eight
fresh recovery first-row proofs, including anchors2201/2202, now exist.

The first72-registration observation encounters absent original CLASS seed1302.
A complete identity scan finds nine additional absent original identities:
1302/1303/1307/1308/1401/1402/1403/1404/1405. All nine managed handles report
Unknown process id; stderr is empty and no success summary exists. Their complete
output trees and launch receipts are frozen byte-for-byte, complete holding
histories are recounted, and last verified live identities are bound. Exit codes
and reasons remain unavailable; no numerical failure, prior rejection, successful
completion or exact-resume state is inferred. Checkpoints lack proposal/RNG state.
No old prefix is appended or restarted. All original four-family registrations
remain present. Old mediumA/B and quadA/B cohorts now retain unavailable-exit
families and remain assessment-ineligible; the fresh A recovery cohorts are separate.

A corrected72-registration observer requires first-row proofs, with temporary
pending permission restricted to the newly activated companion seeds. Its first
snapshot and distinct self-review account for57 live and15 terminal registrations:
four known wider-prior CAMB native failures and eleven CLASS unknown exits.
A fresh closing observation after all eight recovery row proofs preserves the
same counts, every original family and all eighteen declared cohorts. No eligible
cohort is due at that observation. Fresh B precision posterior designs remain
an open restoration obligation if required for the broader comparison.

The two fresh CLASS targets now have a separate snapshot/native/diagnostic
workflow. It preserves first-history threshold1000, later growth6/5, exact
integer holding histories, 20-percent stored-row burn-in, native replay tolerance
1e-9 with zero relative tolerance, and every existing rank/ESS/quantile precision,
chronological drift and equalized-selection gate. All ten sampled parameters
are checked, with absolute mass MCSE target0.001eV and other-parameter precision
relative to empirical posterior standard deviation. A short native-row count
refuses before output creation; it does not relax the three-row native obligation.
Both actual production attempts refuse insufficient history with exit3. Actual
cross-target and control-as-production predecessor attempts also refuse before
output. No historical target or control contract is declared compatible.

The initial CLASS contract preparation fails because a dotted import resolves
an exported class rather than the module, so __file__ is unavailable. The failed
packet is closed and preserved. Fresh v2 helpers explicitly import the module;
both complete separately frozen prethreshold controls then execute upstream
forced-fresh native replay, ten-parameter diagnostics and distinct self-review
with exit0. All24 selected native rows match exactly. Neither short control
qualifies. A real replay worker under the installed unguarded native environment
exits1 before model evaluation, leaving its existing positive native proof
unchanged. Recorded launch solver-version metadata remains absent; the loaded
replay module's v3.4.0 label is reported separately rather than substituted into
historical provenance. Uniform solver accuracy, posterior stationarity, prior
stability and both material main-claim discussions remain open. The paper and
canonical results are unchanged.
''')
previous = read(ROOT / 'runs/20261005_math_review_CLASS_recovery_cohort_companions_v3/checkpoint_manifest.json')
for e in previous['files']:
    assert sha(ROOT / e['path']) == e['sha256']
for e in previous['static_files']:
    if e['path'] in ['docs/findings/math_review.md', str(state_path.relative_to(ROOT))]:
        assert hashlib.sha256(subprocess.check_output(['git', 'show', 'b9d4d86:' + e['path']], cwd=ROOT)).hexdigest() == e['sha256']
    else:
        assert sha(ROOT / e['path']) == e['sha256']
assert not subprocess.check_output(['git', 'diff', 'ffdaf4b', '--name-only', '--', 'paper', 'docs/findings/canonical_results.json'], cwd=ROOT)
assert not subprocess.check_output(['git', 'diff', '9f36b14', '--name-only', '--', 'src', 'lean'], cwd=ROOT)
write(HERE / 'checkpoint_scope_self_review_receipt.json', {
    'utc': utc(), 'reviewer': 'distinct_self_review_not_independent_agent',
    'prior_checkpoint_artifact_hashes_preserved': True, 'six_companion_first_native_rows_exact': True,
    'two_CLASS_workflow_controls_complete': True, 'selected_control_native_rows': 24,
    'eleven_unknown_CLASS_exits_retained': True, 'four_known_CAMB_native_failures_retained': True,
    'registered_families': 72, 'live_at_closing_observation': 57,
    'paper_and_canonical_unchanged': True, 'math_and_Lean_unchanged': True,
    'posterior_or_uniform_accuracy_certified': False})
print('Closed fresh CLASS verification and workflows; all historical families and claim obligations retained.')
