"""Reconstruct the headline differences and all current diagnostic gates."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import isfinite
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / 'headline_magnitude_receipt.json').read_text())
for source in receipt['sources']:
    assert hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest() == source['sha256']
canonical = json.loads((ROOT / 'docs/findings/canonical_results.json').read_text())['mnu_shift']['spt_only_plus_desi']
old = float(Fraction(canonical['run2018']['mnu_p95_upper']) - Fraction(canonical['runD1']['mnu_p95_upper']))
assert abs(old - receipt['canonical_exact_p95_shift_eV']) < 1e-14
pair = json.loads((ROOT / 'runs/20261004_math_review_spt_chain_snapshots_thirteenth_B/paired_SPT_readout.json').read_text())
retained = float(Fraction(pair['A']['p95_equalized_retained_eV']) - Fraction(pair['B']['p95_equalized_retained_eV']))
full = float(Fraction(pair['A']['p95_full_postburn_eV']) - Fraction(pair['B']['p95_full_postburn_eV']))
assert retained == receipt['latest_qualified_retained_p95_shift_eV']
assert full == receipt['latest_qualified_full_postburn_p95_shift_eV']
assert retained > 0 and full > 0 and retained < .3 * old and full < .3 * old
checks = {}
for label in ['A', 'B']:
    diagnostic_path = next(ROOT / f['path'] for f in pair['sources'] if f['path'].endswith(f'chain_{label}_diagnostics.json'))
    d = json.loads(diagnostic_path.read_text())
    assert len(d['seeds']) == 6 and len(d['diagnostics']) == 7
    outcomes = {}
    for parameter, x in d['diagnostics'].items():
        mcse, limit = x['quantile_mcse'], x['quantile_mcse_limit']
        gates = (x['n_chains'] == 6 and all(isfinite(x[k]) for k in ['rank_folded_split_rhat', 'bulk_ess', 'tail_ess_05_95', 'quantile_ess', 'quantile_mcse'])
                 and x['rank_folded_split_rhat'] <= 1.01 and min(x['bulk_ess'], x['tail_ess_05_95'], x['quantile_ess']) >= 400
                 and 0 < mcse <= limit and x['quantile_half_difference'] <= 4 * max(mcse, limit)
                 and abs(x['quantile_full_draws'] - x['quantile_retained_draws']) <= 2 * max(mcse, limit))
        assert gates == x['diagnostic_thresholds_pass'] and gates
        outcomes[parameter] = gates
    assert d['all_diagnostic_thresholds_pass']
    checks[label] = outcomes
for archived in receipt['original_chain_diagnostic_sources'].values():
    assert archived['n_chains'] == 1 and archived['mnu_split_rhat'] > 1.05 and archived['mnu_ess'] < 400
assert not receipt['all_difference_attributed_to_sampling_or_code_repairs']
assert receipt['claim_magnitude_material_revision_decision'] == 'pending_user_discussion_no_revision_adopted'
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_review',
       'headline_magnitude_receipt_sha256': hashlib.sha256((HERE / 'headline_magnitude_receipt.json').read_bytes()).hexdigest(),
       'self_review_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'endpoint_differences_recomputed_from_exact_binary64_fractions': True,
       'all_fourteen_current_parameter_gate_sets_reconstructed': checks,
       'original_sparse_chains_do_not_supply_diagnostic_qualification': True,
       'latest_A_and_B_assessments_have_distinct_times': True,
       'judgment': 'qualitative SPT-only tightening remains supported by qualified readouts; original headline magnitude is not restored',
       'material_claim_revision_adopted': False,
       'global_convergence_uniform_accuracy_or_cosmological_significance_proved': False}
with (HERE / 'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Headline magnitude and every current SPT diagnostic gate pass self-review.')
