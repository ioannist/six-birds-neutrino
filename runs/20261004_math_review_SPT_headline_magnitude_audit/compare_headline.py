"""Trace the manuscript's headline magnitude to qualified current readouts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
canonical_path = ROOT / 'docs/findings/canonical_results.json'
current_path = ROOT / 'runs/20261004_math_review_spt_chain_snapshots_thirteenth_B/paired_SPT_readout.json'
canonical = json.loads(canonical_path.read_text())['mnu_shift']['spt_only_plus_desi']
current = json.loads(current_path.read_text())
assert current['all_seven_fixed_gates_pass_both_targets']
assert not current['simultaneous_joint_snapshot'] and current['A_reused_not_reassessed']
sources = [canonical_path, current_path, ROOT / 'paper/tables/tab_mnu_shift.tex',
           ROOT / 'paper/sections/abstract.tex']
for source in current['sources']:
    path = ROOT / source['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256']
    sources.append(path)
diagnostics = {}
for label in ['spt2018_desi', 'sptd1_desi']:
    path = ROOT / f'runs/20261003_math_review_chain_diagnostics/{label}.json'
    diagnostics[label] = json.loads(path.read_text())
    sources.append(path)
old = canonical['shift']['delta_p95_upper']
assert abs(old - (canonical['run2018']['mnu_p95_upper'] - canonical['runD1']['mnu_p95_upper'])) < 1e-14
assert '0.109' in (ROOT / 'paper/tables/tab_mnu_shift.tex').read_text()
assert '10^{-1}' in (ROOT / 'paper/sections/abstract.tex').read_text()
retained = current['A_minus_B_retained_p95_eV']
full = current['A_minus_B_full_postburn_p95_eV']
assert retained == current['A']['p95_equalized_retained_eV'] - current['B']['p95_equalized_retained_eV']
assert full == current['A']['p95_full_postburn_eV'] - current['B']['p95_full_postburn_eV']
out = {'utc': datetime.now(timezone.utc).isoformat(),
       'scope': 'headline_magnitude_review_distinct_from_CMB_TT_localization_decision',
       'manuscript_table_rounded_shift_eV': .109,
       'canonical_exact_p95_shift_eV': old,
       'latest_qualified_retained_p95_shift_eV': retained,
       'latest_qualified_full_postburn_p95_shift_eV': full,
       'current_to_canonical_retained_shift_ratio': retained / old,
       'canonical_minus_current_retained_shift_eV': old - retained,
       'quantile_MCSE_quadrature_eV_assuming_independent_MC_errors': current['quadrature_combined_quantile_MCSE_eV_assuming_independent_MC_errors'],
       'new_readout_supports_direction_of_tightening': retained > 0 and full > 0,
       'new_readout_establishes_original_point109_magnitude': False,
       'latest_A_and_B_assessments_use_distinct_snapshot_times': True,
       'original_chain_diagnostic_sources': diagnostics,
       'all_difference_attributed_to_sampling_or_code_repairs': False,
       'uniform_CAMB_accuracy_or_pure_completion_causality_certified': False,
       'claim_magnitude_material_revision_decision': 'pending_user_discussion_no_revision_adopted',
       'next_action': 'finish another growth-qualified stability assessment before a numerical claim decision if user selects that route',
       'paper_or_canonical_results_modified': False,
       'sources': [{'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                   for path in sources]}
with (HERE / 'headline_magnitude_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps({k: out[k] for k in ['canonical_exact_p95_shift_eV', 'latest_qualified_retained_p95_shift_eV',
                                     'latest_qualified_full_postburn_p95_shift_eV', 'current_to_canonical_retained_shift_ratio']}, indent=2))
