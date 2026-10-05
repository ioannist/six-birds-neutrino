"""Recount A histories, reconstruct gates, and pair with explicitly older B."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import ceil, hypot, isfinite
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
B = ROOT / 'runs/20261004_math_review_spt_chain_snapshots_thirteenth_B'
snapshot = json.loads((HERE / 'snapshot_receipt.json').read_text())
verification = json.loads((HERE / 'completion_verification.json').read_text())
a_result = json.loads((HERE / 'chain_A_diagnostics.json').read_text())
b_result = json.loads((B / 'chain_B_diagnostics.json').read_text())
assert verification['all_diagnostic_thresholds_pass'] and b_result['all_diagnostic_thresholds_pass']
counts = []
for f in snapshot['files']:
    lines = (ROOT / f['snapshot']).read_text().splitlines()[1:]
    rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
    weights = [int(float(row[0])) for row in rows]
    assert all(float(row[0]) == weight and weight > 0 for row, weight in zip(rows, weights))
    count = sum(weights[len(rows)//5:])
    assert count == f['retained_represented_steps']
    counts.append(count)
assert min(counts) == snapshot['current_draws_per_chain']
assert snapshot['growth_fraction'] >= .2
gates = {}
for lens, result in [('A', a_result), ('B', b_result)]:
    assert len(result['seeds']) == 6 and len(result['diagnostics']) == 7
    outcomes = {}
    for parameter, d in result['diagnostics'].items():
        p, limit = d['quantile_mcse'], d['quantile_mcse_limit']
        passed = (d['n_chains'] == 6 and all(isfinite(d[k]) for k in ['rank_folded_split_rhat', 'bulk_ess', 'tail_ess_05_95', 'quantile_ess', 'quantile_mcse'])
                  and d['rank_folded_split_rhat'] <= 1.01 and min(d['bulk_ess'], d['tail_ess_05_95'], d['quantile_ess']) >= 400
                  and 0 < p <= limit and d['quantile_half_difference'] <= 4 * max(p, limit)
                  and abs(d['quantile_full_draws'] - d['quantile_retained_draws']) <= 2 * max(p, limit))
        assert passed == d['diagnostic_thresholds_pass'] and passed
        outcomes[parameter] = passed
    gates[lens] = outcomes
a_cfg = yaml.safe_load((HERE / 'chain_A_seed301/resolved.yaml').read_text())
b_cfg = yaml.safe_load((B / 'chain_B_seed305/resolved.yaml').read_text())
priors = lambda cfg: {n: p['prior'] for n, p in cfg['params'].items() if isinstance(p, dict) and 'prior' in p}
assert priors(a_cfg) == priors(b_cfg) and a_cfg['theory'] == b_cfg['theory']
a, b = a_result['diagnostics']['mnu'], b_result['diagnostics']['mnu']
previous = json.loads((ROOT / 'runs/20261004_math_review_spt_chain_snapshots_twelfth_A/chain_A_diagnostics.json').read_text())['diagnostics']['mnu']
readout = lambda d: {'p95_equalized_retained_eV': d['quantile_retained_draws'],
                     'p95_full_postburn_eV': d['quantile_full_draws'], 'p95_MCSE_eV': d['quantile_mcse'],
                     'represented_draws_per_chain': d['draws_per_chain']}
canonical = json.loads((ROOT / 'docs/findings/canonical_results.json').read_text())['mnu_shift']['spt_only_plus_desi']['shift']['delta_p95_upper']
sources = [HERE / 'snapshot_receipt.json', HERE / 'completion_verification.json', HERE / 'chain_A_diagnostics.json',
           B / 'snapshot_receipt.json', B / 'completion_verification.json', B / 'chain_B_diagnostics.json',
           ROOT / 'docs/findings/canonical_results.json']
pair = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'fresh_A_fourteenth_and_reused_B_thirteenth_qualified_SPT_readouts',
        'A_snapshot_time': snapshot['utc'], 'B_snapshot_time': json.loads((B / 'snapshot_receipt.json').read_text())['utc'],
        'A_reused_not_reassessed': False, 'B_reused_not_reassessed': True, 'simultaneous_joint_snapshot': False,
        'all_seven_fixed_gates_pass_both_targets': True, 'A': readout(a), 'B': readout(b),
        'A_minus_B_retained_p95_eV': float(Fraction(a['quantile_retained_draws']) - Fraction(b['quantile_retained_draws'])),
        'A_minus_B_full_postburn_p95_eV': float(Fraction(a['quantile_full_draws']) - Fraction(b['quantile_full_draws'])),
        'quadrature_combined_quantile_MCSE_eV_assuming_independent_MC_errors': hypot(a['quantile_mcse'], b['quantile_mcse']),
        'A_retained_p95_change_from_twelfth_eV': a['quantile_retained_draws'] - previous['quantile_retained_draws'],
        'A_full_postburn_p95_change_from_twelfth_eV': a['quantile_full_draws'] - previous['quantile_full_draws'],
        'canonical_original_shift_eV': canonical,
        'same_CAMB_configuration_and_sampled_cosmological_prior_ranges': True,
        'dataset_bundle_and_fixed_nuisance_definitions_are_target_specific': True,
        'pure_completion_causality_or_cosmological_significance_established': False,
        'mathematical_MCMC_convergence_or_uniform_accuracy_certified': False,
        'material_claim_revision_adopted': False,
        'sources': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]}
with (HERE / 'paired_SPT_readout.json').open('x') as handle:
    handle.write(json.dumps(pair, indent=2, allow_nan=False) + '\n')
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_review',
       'six_A_families_integer_recounts': counts, 'all_fourteen_parameter_gate_sets_reconstructed': gates,
       'completed_A_families_retained': [401, 402], 'unchanged_targets_and_gates': True,
       'paired_readout_sha256': hashlib.sha256((HERE / 'paired_SPT_readout.json').read_bytes()).hexdigest(),
       'fresh_B_assessment_performed': False, 'next_A_assessment_minimum': ceil(1.2 * a['draws_per_chain']),
       'next_B_assessment_minimum': ceil(1.2 * b['draws_per_chain']),
       'self_review_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'runtime_observation_sha256': hashlib.sha256((HERE / 'runtime_observation.json').read_bytes()).hexdigest(),
       'paper_modified': False, 'scope_or_magnitude_revision_adopted': False}
with (HERE / 'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps({k: pair[k] for k in ['A_minus_B_retained_p95_eV', 'A_minus_B_full_postburn_p95_eV',
                                     'quadrature_combined_quantile_MCSE_eV_assuming_independent_MC_errors',
                                     'A_retained_p95_change_from_twelfth_eV']}, indent=2))
