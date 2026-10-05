"""Reconstruct explicit terminal roles and parent-provenance roles separately."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep = json.loads((HERE / 'observer_preparation_receipt.json').read_text())
source = ROOT / prep['source']
assert sha(source) == prep['source_sha256']
reverse = (HERE / 'observe_registered_runtime.py').read_text()
expected = source.read_text()
for before, after in prep['changes']:
    assert before in expected
    expected = expected.replace(before, after)
assert reverse.encode() == expected.encode()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
keys = ['guarded_solver_posterior_trials', 'guarded_quadrature_posterior_chains', 'guarded_medium_posterior_chains',
        'guarded_grid12_posterior_trials', 'fresh_CAMB_posterior_chains', 'upper_prior_posterior_chains',
        'native_candidate_posterior_chains', 'guarded_CLASS_fresh_recovery_trials', 'CLASS_recovery_companion_posterior_chains', 'CLASS_fresh_B_posterior_chains']
entries = {e['seed']: e for key in keys for e in state[key]}
runtime_path = HERE / 'combined_runtime_verification.json'
runtime = json.loads(runtime_path.read_text())
records = {r['seed']: r for r in runtime['records']}
assert set(entries) == set(records) and len(records) == 80
live = [r for r in records.values() if r['status'] == 'live_same_owned_native_identity']
known = [r for r in records.values() if r['status'] == 'terminal_native_failure_preserved']
unknown = [r for r in records.values() if r['status'] == 'terminal_exit_reason_unavailable_preserved']
assert len(live) == runtime['owned_live_samplers'] == 65
assert len(known) + len(unknown) == runtime['terminal_families'] == 15
assert {r['seed'] for r in known} == {2003, 2004, 2007, 2008}
assert {r['seed'] for r in unknown} == {1201, 1301, 1302, 1303, 1307, 1308, 1401, 1402, 1403, 1404, 1405}
for r in known + unknown:
    entry = entries[r['seed']]
    assert entry['status'].startswith('terminal_')
    terminal_path = ROOT / entry['terminal_receipt']
    assert sha(terminal_path) == entry['terminal_receipt_sha256'] == r['terminal_receipt_sha256']
    terminal = json.loads(terminal_path.read_text())
    assert terminal['exit_code'] == r['exit_code']
    assert r['identity_observation']['original_identity_absent']
    for file in terminal['terminal_output_files']:
        assert sha(ROOT / file['source']) == sha(ROOT / file['frozen']) == file['sha256']
for seed, parent in [(2201, 1201), (2202, 1301)]:
    entry = entries[seed]
    assert not entry['status'].startswith('terminal_')
    assert records[seed]['status'] == 'live_same_owned_native_identity'
    terminal = json.loads((ROOT / entry['terminal_receipt']).read_text())
    assert terminal['registered_entry']['seed'] == parent == entry['parent_seed']
    assert entry['pid'] != terminal['registered_entry']['pid']
    assert entry['process_start_ticks'] != terminal['last_verified_live_identity']['process_start_ticks']
    assert sha(entry['module']) == entry['module_sha256'] == records[seed]['module_sha256']
    # This pair is a concrete counterexample to using parent receipt presence as process status.
    assert 'terminal_receipt' in entry
assert runtime['recovery_trials_by_target'] == {'medium_A': [2201], 'quad_A': [2202]}
assert runtime['fresh_recovery_cohorts_declared_but_not_qualified']
assert len(runtime['growth_by_cohort']) == 20
for group, g in runtime['growth_by_cohort'].items():
    assert len(g['seeds']) == 4
    if group.startswith('fresh_recovery_'):
        assert g['seeds'] == state['fresh_CLASS_recovery_cohorts'][group]['seeds']
    else:
        assert not ({2201, 2202} & set(g['seeds']))
    subset = [records[seed] for seed in g['seeds']]
    terminal = [r['seed'] for r in subset if r['status'] != 'live_same_owned_native_identity']
    assert g['terminal_family_seeds'] == terminal and g['assessment_eligible'] == (not terminal)
    assert g['minimum_saved_postburn_history'] == min(r['retained_represented_steps'] for r in subset)
    assert g['due'] == (not terminal and g['minimum_saved_postburn_history'] >= g['next_assessment_trigger'])
with (HERE / 'self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_not_independent_agent',
        'runtime_sha256': sha(runtime_path), 'registrations_reconstructed': 80, 'live_at_observation': 65,
        'known_native_failure_families': 4, 'unknown_exit_families': 11,
        'parent_receipt_as_own_terminal_status_counterexamples': [2201, 2202],
        'original_cohort_membership_preserved': True, 'historical_recovery_histories_not_pooled_and_fresh_cohorts_not_qualified': True,
        'terminal_causes_not_inferred': True, 'posterior_qualified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('80 registrations verified; original exits and separate fresh recovery cohorts retained.')
