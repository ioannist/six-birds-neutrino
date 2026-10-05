"""Distinct recount of registered identities, terminal preservation and cohort eligibility."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
runtime_path = HERE / 'combined_runtime_verification.json'
runtime = json.loads(runtime_path.read_text())
keys = ['guarded_solver_posterior_trials', 'guarded_quadrature_posterior_chains',
        'guarded_medium_posterior_chains', 'guarded_grid12_posterior_trials',
        'fresh_CAMB_posterior_chains', 'upper_prior_posterior_chains', 'native_candidate_posterior_chains']
entries = {e['seed']: e for key in keys for e in state[key]}
records = {r['seed']: r for r in runtime['records']}
assert set(records) == set(entries) and len(records) == 64
live = [r for r in records.values() if r['status'] == 'live_same_owned_native_identity']
known = [r for r in records.values() if r['status'] == 'terminal_native_failure_preserved']
unknown = [r for r in records.values() if r['status'] == 'terminal_exit_reason_unavailable_preserved']
assert len(live) == runtime['owned_live_samplers'] == 58
assert len(known) + len(unknown) == runtime['terminal_families'] == 6
assert {r['seed'] for r in known} == {2003, 2004, 2007, 2008}
assert {r['seed'] for r in unknown} == {1201, 1301}
preserved = []
for r in known + unknown:
    e = entries[r['seed']]
    path = ROOT / r['terminal_receipt']
    assert sha(path) == r['terminal_receipt_sha256'] == e['terminal_receipt_sha256']
    terminal = json.loads(path.read_text())
    assert r['identity_observation']['original_identity_absent']
    assert not r['posterior_qualified'] and not r['native_error_is_posterior_rejection']
    assert r['exit_code'] == e['terminal_exit_code'] == terminal['exit_code']
    for f in terminal['terminal_output_files']:
        assert sha(ROOT / f['source']) == sha(ROOT / f['frozen']) == f['sha256']
    if r in unknown:
        assert terminal['registered_entry']['seed'] == r['seed']
        assert terminal['last_verified_live_identity']['pid'] == r['pid']
        assert terminal['last_verified_live_identity']['process_start_ticks'] == r['process_start_ticks']
        assert terminal['exit_reason'] is None and terminal['exit_code'] is None
        assert not terminal['native_failure_established'] and terminal['stderr_empty']
        assert not terminal['success_summary_present'] and not terminal['sampler_restarted']
        chain_record = next(f for f in terminal['terminal_output_files'] if f['source'].endswith('.1.txt'))
        raw = (ROOT / chain_record['frozen']).read_bytes()
        prefix = raw[:raw.rfind(b'\n') + 1]
        rows = [line.split() for line in prefix.decode().splitlines() if line.strip() and not line.startswith('#')]
        weights = [Fraction(row[0]) for row in rows]
        assert all(w > 0 and w.denominator == 1 for w in weights)
        assert len(weights) == terminal['complete_saved_rows']
        assert sum(int(w) for w in weights[len(weights) // 5:]) == r['retained_represented_steps']
        preserved.append({'seed': r['seed'], 'terminal_receipt_sha256': sha(path),
                          'complete_rows': len(weights), 'retained_represented_steps': r['retained_represented_steps']})
for r in live:
    e = entries[r['seed']]
    assert sha(r['module']) == r['module_sha256']
    assert r['pid'] == e['pid']
    if r['seed'] >= 2100:
        proof_path = ROOT / e['first_saved_row_receipt']
        assert sha(proof_path) == e['first_saved_row_receipt_sha256']
        proof = json.loads(proof_path.read_text())
        assert proof['native_row_verified'] and proof['module_sha256'] == r['module_sha256']
assert len(runtime['growth_by_cohort']) == 16
for group, g in runtime['growth_by_cohort'].items():
    assert len(g['seeds']) == 4
    subset = [records[seed] for seed in g['seeds']]
    terminal = [r['seed'] for r in subset if r['status'] != 'live_same_owned_native_identity']
    assert g['terminal_family_seeds'] == terminal
    assert g['assessment_eligible'] == (not terminal)
    assert g['minimum_saved_postburn_history'] == min(r['retained_represented_steps'] for r in subset)
    assert g['due'] == (not terminal and g['minimum_saved_postburn_history'] >= g['next_assessment_trigger'])
with (HERE / 'self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_not_independent_agent',
        'runtime_sha256': sha(runtime_path), 'registrations_reconstructed': 64, 'live_identities': 58,
        'known_native_failure_families': 4, 'unknown_exit_families': 2, 'unknown_exit_preservation_checks': preserved,
        'all_sixteen_candidate_first_rows_bound': True, 'all_sixteen_cohort_status_sets_reconstructed': True,
        'unknown_exit_reason_or_code_invented': False, 'native_error_is_posterior_rejection': False,
        'posterior_or_prior_stability_certified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('64 registrations recounted:58 live,4 known native failures,2 unknown exits; all cohorts status-aware.')
