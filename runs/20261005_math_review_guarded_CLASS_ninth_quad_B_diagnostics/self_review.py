"""Recount saved holding times and reconstruct every fixed diagnostic gate."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import ceil, isfinite
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / 'snapshot_receipt.json').read_text())
verified = json.loads((HERE / 'completion_verification.json').read_text())
for f in verified['files']:
    assert hashlib.sha256((ROOT / f['path']).read_bytes()).hexdigest() == f['sha256']
counts = {}
for f in receipt['files']:
    rows = [line.split() for line in (ROOT / f['snapshot']).read_text().splitlines()
            if line.strip() and not line.startswith('#')]
    fractions = [Fraction(row[0]) for row in rows]
    assert all(w.denominator == 1 and w > 0 for w in fractions)
    retained = sum(int(w) for w in fractions[len(rows) // 5:])
    assert retained == f['retained_represented_steps']
    counts.setdefault(f['group'], []).append(retained)
checks, gates = {}, {}
for cohort, lengths in counts.items():
    assert len(lengths) == 4 and min(lengths) == receipt['draws_per_chain_by_cohort'][cohort]
    result = json.loads((HERE / (cohort + '_diagnostics.json')).read_text())
    outcomes = {}
    for name, d in result['diagnostics'].items():
        p, limit = d['quantile_mcse'], d['quantile_mcse_limit']
        fixed = {
            'separate_starts': d['n_chains'] >= 2,
            'finite': all(d[k] is not None and isfinite(d[k]) for k in
                          ['rank_folded_split_rhat', 'bulk_ess', 'tail_ess_05_95', 'quantile_ess', 'quantile_mcse']),
            'Rhat': d['rank_folded_split_rhat'] <= 1.01,
            'bulk_ESS': d['bulk_ess'] >= 400,
            'tail_ESS': d['tail_ess_05_95'] >= 400,
            'quantile_ESS': d['quantile_ess'] >= 400,
            'MCSE': 0 < p <= limit,
            'chronological_drift': d['quantile_half_difference'] <= 4 * max(p, limit),
            'equalized_selection': abs(d['quantile_full_draws'] - d['quantile_retained_draws']) <= 2 * max(p, limit),
        }
        assert all(fixed.values()) == d['diagnostic_thresholds_pass']
        outcomes[name] = fixed
    assert len(outcomes) == 10
    passed = [n for n, c in outcomes.items() if all(c.values())]
    assert result['all_diagnostic_thresholds_pass'] == (len(passed) == 10)
    checks[cohort] = outcomes
    gates[cohort] = {'retained_represented_steps': lengths, 'passing_parameters': passed,
                     'next_minimum_history': ceil(Fraction(6, 5) * min(lengths))}
runtime = json.loads((HERE / 'runtime_observation.json').read_text())
assert runtime['owned_live_samplers'] == 40 and runtime['guarded_CLASS_live'] == 20
out = {'utc': datetime.now(timezone.utc).isoformat(),
       'review_type': 'distinct_self_review_not_independent_review',
       'completion_verification_sha256': hashlib.sha256((HERE / 'completion_verification.json').read_bytes()).hexdigest(),
       'runtime_observation_sha256': hashlib.sha256((HERE / 'runtime_observation.json').read_bytes()).hexdigest(),
       'self_review_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'all_ten_parameter_gate_sets_reconstructed': checks,
       'integer_recount_and_reconstructed_gates': gates,
       'all_four_quadrature_B_families_retained': True,
       'A_cohorts_reassessed': False, 'medium_B_reassessed': False,
       'precision_cohorts_or_grid12_pooled': False,
       'growth_gate_met_in_quadrature_B_cohort': True,
       'convergence_or_uniform_accuracy_certified': False}
with (HERE / 'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps(gates, indent=2))
