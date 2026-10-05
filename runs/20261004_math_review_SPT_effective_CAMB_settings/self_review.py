"""Adversarial scope and exact binary64 accounting pass over the native controls."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
comparison = json.loads((HERE/'comparison_receipt.json').read_text())
selection = json.loads((HERE/'selection_receipt.json').read_text())
exact = {}
for target in ['A', 'B']:
    native = json.loads((HERE/target/'evaluation_receipt.json').read_text())
    configs = [yaml.safe_load((HERE/target/style/'input.yaml').read_text()) for style in ['original_style','restoration_style']]
    for name in configs[0]['params']:
        for key in ['prior','value','drop']:
            assert configs[0]['params'][name].get(key) == configs[1]['params'][name].get(key)
    assert configs[0]['likelihood'] == configs[1]['likelihood']
    report = comparison['reports'][target]
    for s in ['original_style','restoration_style']:
        r = native['records'][s]
        assert 'tau' in r['sampled_scalar_inputs'] and 'tau' not in r['fixed_scalar_defaults']
        assert any('tau' in p['parameters'] for p in r['internal_prior_policy']['retained_factors'])
        request = max(r['requested_Cl'].values())
        config_lmax = configs[['original_style','restoration_style'].index(s)]['theory']['camb']['extra_args'].get('lmax',0)
        assert r['effective_CAMB_extra_args']['lmax'] == max(request, config_lmax)
    deltas = {}
    for label in selection['records'][target]['points']:
        a,b = [native['records'][s]['evaluations'][label] for s in ['original_style','restoration_style']]
        fraction_delta = Fraction(b['chi2_total'])-Fraction(a['chi2_total'])
        reported = report['native_chi2_differences'][label]['total_chi2_restoration_minus_original_style']
        assert float(fraction_delta) == reported
        deltas[label] = str(fraction_delta)
        if target == 'B':
            assert fraction_delta == 0 and a['chi2_components'] == b['chi2_components']
            for spectrum in ['tt','te','ee','bb']:
                with np.load(HERE/target/'original_style'/(label+'_spectra.npz')) as ca, np.load(HERE/target/'restoration_style'/(label+'_spectra.npz')) as cb:
                    assert np.array_equal(ca[spectrum],cb[spectrum])
    response_delta = (Fraction(native['records']['restoration_style']['evaluations']['restoration_median_mass_plus_001']['chi2_total'])
        -Fraction(native['records']['restoration_style']['evaluations']['restoration_median']['chi2_total'])
        -Fraction(native['records']['original_style']['evaluations']['restoration_median_mass_plus_001']['chi2_total'])
        +Fraction(native['records']['original_style']['evaluations']['restoration_median']['chi2_total']))
    assert float(response_delta) == report['mass_response_change']
    exact[target] = {'exact_binary64_total_chi2_differences': deltas,
                     'exact_binary64_mass_response_change': str(response_delta)}
assert report['current_versions']['cobaya'] == '3.6.2'
assert all(v['archived_versions'] == {'archived_CAMB':'1.6.5','archived_Cobaya':'3.6.1'} for v in comparison['reports'].values())
assert not comparison['historical_lmax_directly_observed']
assert not comparison['actual_original_stack_replayed']
assert not comparison['posterior_quantile_sensitivity_or_uniform_accuracy_certified']
runtime = json.loads((HERE/'runtime_observation.json').read_text())
growth = json.loads((HERE/'growth_observation.json').read_text())
assert runtime['owned_live_samplers'] == 28
assert not any(v['assessment_due'] for v in growth['progress'].values())
# Directly compare tracked scientific claims with the requested pre-review checkpoint.
import subprocess
diff = subprocess.run(['git','diff','ffdaf4b','--','paper','docs/findings/canonical_results.json'],
                      cwd=ROOT, check=True, capture_output=True)
assert not diff.stdout
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type':'distinct_self_review_not_independent_review',
       'exact_recomputations': exact, 'prior_and_likelihood_definitions_match_within_target':True,
       'sampled_tau_and_fixed_nuisance_defaults_distinguished':True,
       'B_selected_native_likelihoods_and_supported_spectra_bit_identical':True,
       'A_selected_native_target_changes_nonzero':True,
       'original_CAMB_1p6p5_and_Cobaya_3p6p1_not_replayed':True,
       'historical_lmax_inference_conditional_on_likelihood_support_and_negotiation':True,
       'pointwise_controls_do_not_bound_posterior_quantile_change':True,
       'original_chain_coordinates_unqualified_for_quantile_claims':True,
       'material_revision_decisions_still_pending':True,
       'no_posterior_gates_relaxed_or_native_sampler_changed':True,
       'paper_and_canonical_results_unchanged':True,
       'comparison_receipt_sha256':hashlib.sha256((HERE/'comparison_receipt.json').read_bytes()).hexdigest()}
with (HERE/'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Exact likelihood differences, native B identity and conditional historical scope verified.')
