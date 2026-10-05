"""Recount holding times and reconstruct every fixed decision gate."""
from datetime import datetime, timezone
import hashlib
import json
from math import ceil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / 'snapshot_receipt.json').read_text())
verified = json.loads((HERE / 'completion_verification.json').read_text())
for f in verified['files']:
    assert hashlib.sha256((ROOT / f['path']).read_bytes()).hexdigest() == f['sha256']
counts = {}
for f in receipt['files']:
    lines = (ROOT / f['snapshot']).read_text().splitlines()[1:]
    rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
    weights = [int(float(row[0])) for row in rows]
    assert all(float(row[0]) == w and w > 0 for row, w in zip(rows, weights))
    retained = sum(weights[len(rows) // 5:])
    assert retained == f['retained_represented_steps']
    counts.setdefault(f['group'], []).append(retained)
    previous = json.loads((ROOT / receipt['previous_snapshot_receipt']).read_text())
    prior = next(p for p in previous['files'] if p['source'] == f['source'])
    assert (ROOT / f['snapshot']).read_bytes().startswith((ROOT / prior['snapshot']).read_bytes())
gates = {}
for cohort, lengths in counts.items():
    assert len(lengths) == 4 and min(lengths) == receipt['draws_per_chain_by_cohort'][cohort]
    result = json.loads((HERE / (cohort + '_diagnostics.json')).read_text())
    outcomes = {}
    for name, d in result['diagnostics'].items():
        expected = (d['rank_folded_split_rhat'] <= 1.01 and d['bulk_ess'] >= 400
                    and d['tail_ess_05_95'] >= 400 and d['quantile_ess'] >= 400
                    and d['quantile_mcse'] <= d['quantile_mcse_limit'])
        assert expected == d['diagnostic_thresholds_pass']
        outcomes[name] = expected
    assert len(outcomes) == 10 and not any(outcomes.values())
    assert not result['all_diagnostic_thresholds_pass']
    gates[cohort] = {'retained_represented_steps': lengths, 'passing_parameters': [],
                     'next_minimum_history': ceil(min(lengths) * 1.2)}
runtime = json.loads((HERE / 'runtime_observation.json').read_text())
assert runtime['owned_live_samplers'] == 25 and runtime['guarded_CLASS_live'] == 17
out = {'utc': datetime.now(timezone.utc).isoformat(),
       'review_type': 'distinct_self_review_not_independent_review',
       'completion_verification_sha256': hashlib.sha256((HERE / 'completion_verification.json').read_bytes()).hexdigest(),
       'runtime_observation_sha256': hashlib.sha256((HERE / 'runtime_observation.json').read_bytes()).hexdigest(),
       'self_review_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'integer_recount_and_reconstructed_gates': gates,
       'all_sixteen_fresh_families_retained': True,
       'precision_cohorts_or_grid12_trial_pooled': False,
       'growth_gate_met_in_every_cohort': True,
       'convergence_or_uniform_accuracy_certified': False,
       'judgment': 'all four cohorts remain provisional; zero of ten parameters pass all unchanged gates'}
with (HERE / 'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps(gates, indent=2))
