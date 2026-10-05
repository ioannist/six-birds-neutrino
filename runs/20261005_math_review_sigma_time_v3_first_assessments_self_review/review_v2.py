"""Reconstruct the three first production candidates without qualifying their transients."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import ceil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
state = read(ROOT / 'runs/20261003_math_review_validation/review_state.json')
contract_path = ROOT / 'runs/20261005_math_review_sigma_time_v3_diagnostic_preparation/assessment_contract.json'
contract = read(contract_path)
assert contract['first_minimum_retained_represented_steps'] == 1000
assert contract['absolute_mass_quantile_MCSE_limit'] == 0.001
assert contract['later_growth_factor'] == [6, 5]
records = []
for group in ['sigma_time_v3_A4095_cap5', 'sigma_time_v3_B4095_cap5', 'sigma_time_v3_B4095_cap20']:
    registered = state['native_candidate_production_assessments'][group]
    folder = ROOT / registered['root']
    prep = read(folder / 'worker_preparation_receipt.json')
    source = ROOT / prep['source']
    assert sha(source) == prep['source_sha256']
    expected = source.read_text()
    for before, after in prep['changes']:
        assert expected.count(before) == 1
        expected = expected.replace(before, after, 1)
    assert expected.encode() == (folder / 'run_verification.py').read_bytes()
    execution = read(folder / 'execution_receipt.json')
    assert execution['exit_code'] == 0 and execution['all_verification_workers_terminal']
    assert len(execution['stages']) == 3 and all(e['actual_exit_code'] == 0 for e in execution['stages'])
    snapshot = read(folder / 'snapshot_receipt.json')
    assert snapshot['group'] == group and snapshot['contract_sha256'] == sha(contract_path)
    assert snapshot['assessment_trigger'] == 1000 and snapshot['previous_snapshot_receipt'] is None
    assert snapshot['minimum_retained_represented_steps'] >= 1000
    assert registered['next_minimum_history'] == ceil(Fraction(6, 5) * snapshot['minimum_retained_represented_steps'])
    assert [e['seed'] for e in snapshot['families']] == [e['seed'] for e in contract['groups'][group]]
    native = read(folder / 'native_rows_verification.json')
    checks = [c for r in native['records'] for c in r['checks']]
    assert len(checks) == 12 and max(abs(v) for c in checks for v in c['fresh_minus_recorded'].values()) == 0
    d = read(folder / 'diagnostics.json')
    review = read(folder / 'self_review_receipt.json')
    assert set(review['all_seven_parameter_gate_sets_reconstructed']) == set(d['diagnostics'])
    assert len(d['diagnostics']) == 7
    assert not d['all_diagnostic_thresholds_pass'] and not registered['posterior_qualified']
    assert not any(v['diagnostic_thresholds_pass'] for v in d['diagnostics'].values())
    mass = d['diagnostics']['mnu']
    assert mass['rank_folded_split_rhat'] > 1.01 and mass['quantile_mcse'] > 0.001
    families = []
    for f in snapshot['families']:
        path = Path(f['snapshot'])
        assert sha(path) == f['snapshot_sha256']
        raw = path.read_bytes()
        assert raw.endswith(b'\n') and (ROOT / f['source']).read_bytes().startswith(raw)
        lines = raw.decode().splitlines()
        header = lines[0].lstrip('#').split()
        rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
        weights = [Fraction(r[0]) for r in rows]
        assert all(w > 0 and w.denominator == 1 for w in weights)
        assert sum(int(w) for w in weights[len(weights) // 5:]) == f['retained_represented_steps']
        mass_column, post_column = header.index('mnu'), header.index('minuslogpost')
        families.append({'seed': f['seed'], 'first_saved_mass_eV': float(rows[0][mass_column]),
            'last_saved_mass_eV': float(rows[-1][mass_column]),
            'first_saved_minuslogpost': float(rows[0][post_column]),
            'last_saved_minuslogpost': float(rows[-1][post_column])})
    records.append({'group': group, 'snapshot_sha256': sha(folder / 'snapshot_receipt.json'),
        'native_sha256': sha(folder / 'native_rows_verification.json'),
        'diagnostic_sha256': sha(folder / 'diagnostics.json'), 'self_review_sha256': sha(folder / 'self_review_receipt.json'),
        'represented_minimum': snapshot['minimum_retained_represented_steps'],
        'next_history_trigger': registered['next_minimum_history'], 'families': families,
        'unqualified_mass_Rhat': mass['rank_folded_split_rhat'],
        'unqualified_mass_MCSE_eV': mass['quantile_mcse'], 'posterior_qualified': False})
assert len(records) == 3
with (HERE / 'self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': records,
        'selected_native_rows_exact': 36, 'all_seven_parameter_gates_checked': True,
        'all_three_production_snapshots_refused_qualification': True,
        'high_start_transients_not_read_as_stationary_tail_or_prior_sensitivity': True,
        'historical_or_control_contracts_not_promoted': True, 'main_claim_revision_adopted': False},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('Three production candidates reviewed: 36 native rows exact; all seven parameters fail qualification.')
