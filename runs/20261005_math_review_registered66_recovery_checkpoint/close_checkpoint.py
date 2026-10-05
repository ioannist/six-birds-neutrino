"""Reconcile completed receipts, retain failed attempts, and document exact scope."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
utc = lambda: datetime.now(timezone.utc).isoformat()
read = lambda p: json.loads(Path(p).read_text())


def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


roots = [ROOT / ('runs/20261005_math_review_' + name) for name in [
    'sigma_time_v3_diagnostic_preparation', 'sigma_time_v3_prethreshold_workflow_controls',
    'CLASS_fresh_recovery_preparation', 'CLASS_fresh_recovery_activation',
    'registered66_checkpoint', 'registered66_checkpoint_v2',
    'fresh_CAMB_ninth_current_A4095_diagnostics_v2',
    'fresh_CAMB_ninth_current_B4095_diagnostics_v2']]
closed = []
for root in roots:
    receipt = root / 'execution_receipt.json'
    assert receipt.exists()
    closed.append({'root': str(root.relative_to(ROOT)), 'execution_receipt_sha256': sha(receipt)})
runtime = read(HERE / 'combined_runtime_verification.json')
review = read(HERE / 'self_review_receipt.json')
assert review['runtime_sha256'] == sha(HERE / 'combined_runtime_verification.json')
assert runtime['registered_families'] == 66 and runtime['owned_live_samplers'] == 60
assert not any(g['due'] for g in runtime['growth_by_cohort'].values())
write_new(HERE / 'execution_receipt.json', {'utc': utc(),
    'runtime_managed_session': 16334, 'actual_terminal_exit_code': 0,
    'distinct_self_review_direct_exit_code': 0, 'all_verification_workers_terminal': True,
    'inference_workers_not_modified': True})
state_path = ROOT / 'runs/20261003_math_review_validation/review_state.json'
s = read(state_path)
rel = str(HERE.relative_to(ROOT))
s['latest_registered_runtime_observation'] = {
    'root': rel, 'runtime': rel + '/combined_runtime_verification.json',
    'self_review': rel + '/self_review_receipt.json', 'utc': runtime['utc'],
    'registered_families': 66, 'owned_live_samplers': 60,
    'terminal_native_failure_families': [2003, 2004, 2007, 2008],
    'terminal_exit_reason_unavailable_families': [1201, 1301],
    'candidate_first_saved_native_rows_verified': 16,
    'CLASS_recovery_first_saved_native_rows_verified': 2,
    'due_eligible_cohorts': [], 'recovery_trials_pooled_with_original_cohorts': False}
s['active_runtime_observer'] = rel + '/observe_registered_runtime.py'
with state_path.open('w') as f:
    json.dump(s, f, indent=2, allow_nan=False)
    f.write('\n')

text = '''

The four sigma_time_v3 targets now have a separate diagnostic workflow with
the same first-history gate1000, subsequent growth6/5, holding-time accounting,
20-percent stored-row burn-in and all existing acceptance thresholds. Four
actual production attempts refuse insufficient history before snapshot creation.
Separate prethreshold controls exercise native replay, seven-parameter diagnostics
and distinct self-review for every target: all48 selected native rows match
exactly, and no control posterior qualifies. Cross-cap predecessors, an old-policy
contract and a deliberately wrong loaded native module are rejected. The source
overlay's incomplete distribution metadata is checked through loaded version2.0.4
and SHA-bound original PKG-INFO; no installed-version value is invented.

Two fresh CLASS recovery trials use new seeds2201/2202 and new output prefixes,
starting at the last complete preserved rows of unknown-exit seeds1201/1301.
The preserved learned covariances are finite positive-definite proposal heuristics.
Likelihoods, priors, native arguments and each original sampler profile remain
unchanged. Checkpoints lack the complete proposal/RNG state for exact resume;
the original histories are neither appended nor pooled with these trials.
Both initial native controls match exactly and both guarded launchers reject
bad native identities. Actual activation checks PID/start ticks, command,
mapped module, effective configuration and OS priority. CLASS reportsv3.4.0,
its distribution3.4.0.1, and Cobaya3.6.2.

Both trials now produce a complete first saved row. The dragging trial2201
takes longer to save a row but remains the same owned live process; no failure
or causal performance explanation is inferred. Forced-fresh native replay gives
zero error for every individually checked prior, posterior and likelihood chi2
component. Distinct self-review reconstructs exact integer holding times,
binary64 points, source prefixes and backend/configuration bindings; it also
checks the CMB type aggregate separately from individual likelihood terms.
Two failed self-review assumptions are preserved: treating that aggregate as
another likelihood component, and expecting runtime class types in resolved
configuration. The corrected review derives types from actual imported classes.
These are selected-row certificates, not uniform accuracy or posterior convergence.

The ninth current_A4095 and current_B4095 assessments complete all three stages
with exit0 and all12 selected native rows exact per target. Their minimum
represented postburn histories are5172/5003, and their next history gates
are6207/6004. No parameter passes all gates for A; only omegach2 does for B.
Both targets remain unqualified. A failed preparation using a guessed prior
directory suffix is preserved; the successful preparations use saved state paths.

The first66-registration observer fails because parent terminal provenance was
mistaken for a recovery trial's own terminal status. Its failed receipt remains
preserved. The corrected observer checks explicit own terminal status, and a
fresh closing observation additionally requires both recovery first-row proofs.
It accounts for66 registrations:60 live, four known wider-prior native failures
and two preserved unknown CLASS exits. All sixteen original/candidate four-family
groups retain their membership; the two new recovery trials are listed separately.
No eligible group is currently due. Candidate minimum histories are269-297,
below the unchanged first-assessment gate1000. Constructing an explicitly declared
four-family CLASS recovery design remains open. Uniform physical accuracy,
prior stability and both material main-claim discussions remain open. The paper
and canonical results are unchanged.
'''
with (ROOT / 'docs/findings/math_review.md').open('a') as f:
    f.write(text)

previous = read(ROOT / 'runs/20261005_math_review_registered64_checkpoint/checkpoint_manifest.json')
for e in previous['files']:
    assert sha(ROOT / e['path']) == e['sha256']
for e in previous['static_files']:
    if e['path'] in ['docs/findings/math_review.md', 'runs/20261003_math_review_validation/review_state.json']:
        original = subprocess.check_output(['git', 'show', '5c16772:' + e['path']], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == e['sha256']
    else:
        assert sha(ROOT / e['path']) == e['sha256']
assert not subprocess.check_output(['git', 'diff', 'ffdaf4b', '--name-only', '--',
                                    'paper', 'docs/findings/canonical_results.json'], cwd=ROOT)
assert not subprocess.check_output(['git', 'diff', '9f36b14', '--name-only', '--', 'src', 'lean'], cwd=ROOT)
assert sha('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/camb/camblib.so') == \
    '306640a8948cd5246fc9b21e76525f6adebdff5ba3bc792a57d50bba67225ad5'
write_new(HERE / 'checkpoint_scope_self_review_receipt.json', {
    'utc': utc(), 'reviewer': 'distinct_self_review_not_independent_agent',
    'closed_verification_roots': closed, 'prior_checkpoint_artifact_hashes_preserved': True,
    'candidate_control_native_rows': 48, 'recovery_first_saved_native_rows': 2,
    'new_existing_CAMB_native_rows': 24, 'all_selected_native_component_errors': 0.0,
    'registered_families': 66, 'live_at_observation': 60, 'terminal_registrations_retained': 6,
    'all_new_production_CAMB_assessments_unqualified': True,
    'old_and_new_CLASS_histories_not_pooled': True,
    'paper_and_canonical_unchanged': True, 'math_and_Lean_unchanged': True,
    'production_native_unchanged': True, 'posterior_or_uniform_accuracy_certified': False})
print('Reconciled state, documented completed work and checked prior checkpoint preservation.')
