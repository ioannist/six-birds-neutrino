"""Reconstruct likelihood shape changes and retain historical replay limitations."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CURRENT=ROOT/'runs/20261004_math_review_SPT_effective_CAMB_settings'
r=json.loads((HERE/'comparison_receipt.json').read_text())
checks={}
for target in ['A','B']:
    a=json.loads((HERE/target/'evaluation_receipt.json').read_text())
    b=json.loads((CURRENT/target/'evaluation_receipt.json').read_text())
    shape={}
    for style in ['original_style','restoration_style']:
        ea,eb=a['records'][style]['evaluations'],b['records'][style]['evaluations']
        deltas={n:Fraction(eb[n]['chi2_total'])-Fraction(ea[n]['chi2_total']) for n in ea}
        summary=r['reports'][target]['same_style_solver_version_controls'][style]
        for n,delta in deltas.items():
            assert float(delta)==summary['changes'][n]['total_chi2_current_minus_archived_versions']
        plus,median='restoration_median_mass_plus_001','restoration_median'
        response_delta=deltas[plus]-deltas[median]
        assert float(response_delta)==summary['mass_response_change']
        assert response_delta != 0
        spread=max(deltas.values())-min(deltas.values())
        assert spread>0
        # A nonconstant chi-square offset implies a nonconstant likelihood ratio.
        shape[style]={'exact_binary64_mass_response_change':str(response_delta),
                      'selected_chi2_offset_range':float(spread),
                      'selected_log_likelihood_ratio_range':float(spread/2),
                      'likelihood_change_is_not_only_an_additive_constant':True}
    archived=r['reports'][target]['selected_archived_saved_row_replays']
    max_total=max(abs(v['fresh_minus_stored_total_chi2']) for v in archived.values())
    max_component=max(abs(d) for v in archived.values() for d in v['component_fresh_minus_stored_chi2'].values())
    # Empirical reproduction at rounded stored coordinates, not a certified rounding bound.
    assert max_total < 3e-5 and max_component < 7e-5
    if target=='B':
        for label in a['records']['original_style']['evaluations']:
            ea=a['records']['original_style']['evaluations'][label]
            eb=a['records']['restoration_style']['evaluations'][label]
            assert ea['chi2_components']==eb['chi2_components'] and ea['chi2_total']==eb['chi2_total']
            for name in ['tt','te','ee','bb']:
                with np.load(HERE/target/'original_style'/(label+'_spectra.npz')) as ca,np.load(HERE/target/'restoration_style'/(label+'_spectra.npz')) as cb:
                    assert np.array_equal(ca[name],cb[name])
    checks[target]={'solver_version_shape_controls':shape,
                    'max_observed_archived_row_total_chi2_replay_error':max_total,
                    'max_observed_archived_row_component_chi2_replay_error':max_component}
for source in r['current_control_sources']:
    assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
current=json.loads((CURRENT/'A/evaluation_receipt.json').read_text())['runtime']
assert hashlib.sha256(Path(current['CAMB_module']).read_bytes()).hexdigest()==current['CAMB_module_sha256']
assert hashlib.sha256(Path(current['Cobaya_CAMB_wrapper']).read_bytes()).hexdigest()==current['Cobaya_CAMB_wrapper_sha256']
assert not r['original_Python_environment_or_native_binary_reconstructed']
assert not r['old_likelihood_package_and_data_identity_certified']
assert not r['posterior_quantile_sensitivity_or_uniform_solver_accuracy_certified']
diff=subprocess.run(['git','diff','ffdaf4b','--','paper','docs/findings/canonical_results.json'],cwd=ROOT,check=True,capture_output=True)
assert not diff.stdout
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'checks':checks,'version_changes_alter_likelihood_ratios_at_selected_points':True,
     'current_qualified_posteriors_are_not_a_sampling_only_original_target_restoration':True,
     'no_amount_or_direction_of_old_target_quantile_change_certified':True,
     'rounded_archive_reproduction_is_pointwise_not_complete_historical_identity':True,
     'requires_converged_archived_solver_target_comparison_before_main_numerical_decision':True,
     'original_point109_magnitude_restored':False,'main_numerical_downgrade_adopted':False,
     'live_stack_native_and_wrapper_hashes_unchanged':True,'paper_and_canonical_unchanged':True,
     'comparison_receipt_sha256':hashlib.sha256((HERE/'comparison_receipt.json').read_bytes()).hexdigest()}
with (HERE/'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps(checks,indent=2))
