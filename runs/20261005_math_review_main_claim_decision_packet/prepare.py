"""Make the two material claim choices concrete without adopting or editing either."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
state = read(ROOT / 'runs/20261003_math_review_validation/review_state.json')
headline_path = 'runs/20261004_math_review_SPT_headline_magnitude_audit/headline_magnitude_receipt.json'
paired_path = 'runs/20261004_math_review_spt_chain_snapshots_fifteenth_B/paired_SPT_readout.json'
local_path = 'runs/20261003_math_review_cosmological_cmb_desi_accuracy_improved_source/comparison_verification.json'
range_path = 'runs/20261003_math_review_localization_range_check/range_verification.json'
headline, paired, local, ranges = [read(ROOT / p) for p in [headline_path, paired_path, local_path, range_path]]
assert not local['global_optimum_certified'] and not local['independent_chi_square_blocks_or_causal_attribution']
assert paired['all_seven_fixed_gates_pass_both_targets']
assert 'native evaluation qualification suspended' in state['pending_decision']
assert all(not e['posterior_qualified'] for e in state['fresh_CAMB_production_assessments'].values())
source_paths = [headline_path, paired_path, local_path, range_path,
                'docs/findings/canonical_results.json', 'paper/sections/abstract.tex',
                'paper/sections/conclusion.tex', 'lean/trunc_gauss_proof/TruncGaussProof/Audit.lean']
assessments = {}
for group, e in state['fresh_CAMB_production_assessments'].items():
    source_paths += [e['diagnostics'], e['native_verification'], e['self_review']]
    d = read(ROOT / e['diagnostics'])
    m = d['diagnostics']['mnu']
    assessments[group] = {'diagnostics': e['diagnostics'], 'minimum_saved_postburn_history': e['minimum_saved_postburn_history'],
        'next_minimum_history': e['next_minimum_history'], 'all_parameter_gate_sets_pass': d['all_diagnostic_thresholds_pass'],
        'mass_quantile_MCSE_eV': m['quantile_mcse'], 'mass_quantile_MCSE_limit_eV': m['quantile_mcse_limit'],
        'mass_rank_Rhat': m['rank_folded_split_rhat'], 'posterior_qualified': False}
packet = {'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Concrete main-claim options for user discussion; no manuscript edit or adopted numerical revision.',
    'magnitude': {
        'original_canonical_shift_eV': headline['canonical_exact_p95_shift_eV'],
        'original_archived_chain_diagnostics': {k: {'chains': v['n_chains'], 'scalar_split_Rhat': v['mnu_split_rhat'],
            'scalar_ESS_proxy': v['mnu_ess'], 'posterior_qualified': False} for k, v in headline['original_chain_diagnostic_sources'].items()},
        'historical_current_stack_shift_eV': paired['A_minus_B_retained_p95_eV'],
        'historical_current_stack_shift_scope': 'Passed the then-fixed empirical gates; numerical-target qualification was subsequently suspended after cache defects. This is not a current qualified replacement number.',
        'fresh_validated_policy_comparisons': assessments,
        'current_qualified_numeric_replacement_available': False,
        'restoration_route': 'Complete unchanged all-parameter gates on separately bound archived/current solver and cutoff targets; verify native evaluations and compare declared targets before assigning the original magnitude discrepancy to sampling. Preserve the wider-prior sigma-time candidate and CLASS precision cohorts separately.',
        'future_narrowing_route': 'Retain the reproducible lens-swap audit mechanism, mark the original 0.109 eV empirical magnitude unsupported, and state a numerical tightening only for a specifically identified qualified target once such evidence exists. Do not promote the suspended near-0.030 eV readout.',
        'restoration_of_original_point109_guaranteed': False},
    'localization': {
        'range': local['range_convention'],
        'full_CMB_same_source_pair': local['results'],
        'SPT_only_B_given_A': ranges['results']['cosmological_spt_desi']['B_given_A']['signed_totals_effective_ell_2000_inclusive_3000_exclusive'],
        'strongest_current_scope': 'Signed high-ell allocation depends on baseline and transfer direction: the recorded SPT-only forward allocation is TT-dominated, while the same-pair full-CMB forward allocation is EE-dominated and its reverse is TT-dominated.',
        'broad_full_CMB_TT_dominance_established': False,
        'restoration_route': 'A broader TT statement needs a prespecified baseline/direction/domain and controlled new evidence explaining the observed EE-dominated forward cases. More chain history alone does not change these finite signed allocations.',
        'future_narrowing_route': 'State TT dominance for the supported SPT-only/directional controls and explicitly report the full-CMB EE forward allocation. Retain directional mismatch and staging audits; do not interpret signed correlated allocations as independent chi-square blocks or causal root-cause proof.',
        'global_profile_optimality_or_pure_packaging_causality_proved': False},
    'mathematical_content_retained': ['Gaussian product, physical-gate CDF/quantile and boundary-mode results under their explicit hypotheses.',
        'Directional likelihood accounting under actual extremality or best-found scope, with correlated signed localization.',
        'Conditional quantitative transfer results retain their CDF-error, positive-slope, domain and law hypotheses; no cosmological uniform-error bridge is silently supplied.'],
    'proposed_strategy': 'Continue the already authorized restoration cohorts while preparing a scoped localization recommendation for discussion. Do not silently adopt either material change.',
    'material_claim_revision_adopted': False, 'paper_or_canonical_modified': False,
    'sources': [{'path': p, 'sha256': sha(ROOT / p)} for p in sorted(set(source_paths))]}
with (HERE / 'decision_packet.json').open('x') as f:
    json.dump(packet, f, indent=2, allow_nan=False)
    f.write('\n')
print('Two concrete claim routes recorded; suspended readouts are not promoted to qualified replacements.')
