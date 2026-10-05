"""Review immutable completed outputs; do not rerun their producers."""
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
records = []
wrong_selection_witnesses = []
for group, ordinal in [('old_A3200', 'eighth'), ('old_B4095', 'eighth'),
                       ('current_A3200', 'ninth')]:
    before = ROOT / f'runs/20261005_math_review_fresh_CAMB_{ordinal}_{group}_diagnostics'
    after = Path(str(before) + '_v2')
    original = json.loads((before / 'snapshot_receipt.json').read_text())
    snapshot = json.loads((after / 'snapshot_receipt.json').read_text())
    old = {f['seed']: f for f in original['families']}
    new = {f['seed']: f for f in snapshot['families']}
    assert len(old) == len(new) == 4 and old.keys() == new.keys()
    native = json.loads((after / 'native_rows_verification.json').read_text())
    native_by_seed = {f['seed']: f for f in native['records']}
    assert native_by_seed.keys() == new.keys()
    execution = json.loads((after / 'execution_receipt.json').read_text())
    assert execution['actual_terminal_exit_code'] == 0
    assert len(execution['stages']) == 3
    assert all(s['exit_code'] == 0 for s in execution['stages'])
    contract_path = ROOT / 'runs/20261004_math_review_fresh_CAMB_weighted_summary_diagnostic_preparation/assessment_contract.json'
    assert sha(contract_path) == snapshot['contract_sha256']
    contract = json.loads(contract_path.read_text())
    for seed, family in new.items():
        earlier = Path(old[seed]['snapshot'])
        later = Path(family['snapshot'])
        assert sha(earlier) == old[seed]['snapshot_sha256']
        assert sha(later) == family['snapshot_sha256']
        raw = later.read_bytes()
        assert raw.startswith(earlier.read_bytes())
        rows = np.loadtxt(BytesIO(raw), ndmin=2)
        assert len(rows) == family['stored_rows']
        header = raw.decode().splitlines()[0].lstrip('#').split()
        assert len(header) == len(set(header)) == rows.shape[1]
        entry = native_by_seed[seed]
        assert entry['file_sha256'] == sha(later)
        expected = np.unique(np.linspace(0, len(rows)-1,
                            min(len(rows), contract['native_rows_per_family']), dtype=int)).tolist()
        actual = [c['row_index'] for c in entry['checks']]
        assert actual == expected and len(actual) == 3
        incorrect = [0, len(rows)//2, len(rows)-1]
        if actual != incorrect:
            wrong_selection_witnesses.append({'group': group, 'seed': seed,
                'stored_rows': len(rows), 'actual_indices': actual,
                'incorrect_previous_audit_indices': incorrect})
        for check in entry['checks']:
            row = rows[check['row_index']]
            assert all(float(row[header.index(k)]).hex() == float(v).hex()
                       for k, v in check['point'].items())
            assert all(v == 0.0 for v in check['fresh_minus_recorded'].values())
        records.append({'group': group, 'seed': seed, 'snapshot_sha256': sha(later),
                        'selected_indices': actual, 'prefix_preserved': True,
                        'binary64_point_binding': True, 'all_component_errors_zero': True})
    review = json.loads((after / 'self_review_receipt.json').read_text())
    assert review['snapshot_receipt_sha256'] == sha(after / 'snapshot_receipt.json')
    assert review['native_row_verification_sha256'] == sha(after / 'native_rows_verification.json')
    assert review['diagnostics_sha256'] == sha(after / 'diagnostics.json')
    assert review['next_minimum_history'] == (6*snapshot['minimum_retained_represented_steps']+4)//5
    assert review['posterior_convergence_or_uniform_accuracy_proved'] is False

assert wrong_selection_witnesses
failure_path = HERE / 'checkpoint_audit_initial_assertion_failure_receipt.json'
with failure_path.open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'attempt': 'previous inline audit; AssertionError before scope receipt was written',
        'cause': 'Audit used n//2 instead of floor((n-1)/2) for middle of three linspace indices when n is even.',
        'witnesses': wrong_selection_witnesses,
        'original_native_receipts_modified': False,
        'correction': 'Bind by seed and use the contract and exact native verifier selection.'}, f, indent=2)
    f.write('\n')

runtime = json.loads((HERE / 'all_runtime_verification.json').read_text())
runtime_review = json.loads((HERE / 'self_review_receipt.json').read_text())
assert runtime_review['runtime_sha256'] == sha(HERE / 'all_runtime_verification.json')
assert runtime['registered_sampler_families'] == 48
assert runtime['owned_live_samplers'] == 44 and runtime['terminal_sampler_families'] == 4
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
assert state['latest_observed_total_live_sampler_count'] == 44
assert state['native_failure_sigma_candidate_production_adopted'] is False
assert state['posterior_convergence_verified'] is False
assert subprocess.check_output(['git', 'diff', '9f36b14', '--name-only', '--',
                                'scripts', 'src', 'tests', 'lean'], cwd=ROOT) == b''
assert subprocess.check_output(['git', 'diff', 'ffdaf4b', '--name-only', '--',
                                'paper', 'docs/findings/canonical_results.json'], cwd=ROOT) == b''
with (HERE / 'checkpoint_scope_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'review_type': 'distinct_self_review_not_independent_agent',
        'records': records, 'selected_native_points_bound': 36,
        'native_verifier_source_sha256': sha(ROOT / 'runs/20261004_math_review_fresh_CAMB_weighted_summary_diagnostic_preparation/verify_native_rows.py'),
        'runtime_receipt_sha256': sha(HERE / 'all_runtime_verification.json'),
        'runtime_observation_is_historical': True,
        'sigma_candidate_production_adopted': False,
        'uniform_numerical_error_or_posterior_certificate': False,
        'core_paper_canonical_unchanged': True}, f, indent=2)
    f.write('\n')
print('36 selected native points bound; completed prefixes preserved; scope checked.')
