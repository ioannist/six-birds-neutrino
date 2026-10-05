"""Challenge the one-state repair candidate with separate native models."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
summary=[]
for version,session in [('1.6.5',62205),('2.0.4',95688)]:
    path=HERE/('interleaved_models_'+version+'_receipt.json')
    r=json.loads(path.read_text())
    assert r['CAMB_version']==version
    assert [c['cache_size'] for c in r['records']]==[1,0]
    same=json.loads((HERE/('single_transfer_state_'+version+'_receipt.json')).read_text())
    reference=next(c for c in same['records'] if c['transfer_cache_size']==3 and c['case']=='slow_return')
    for c in r['records']:
        delta=[-2*(Fraction(a)-Fraction(b)) for a,b in zip(c['return_main_loglikes'],c['fresh_main_loglikes'])]
        assert [float(v) for v in delta]==c['cached_minus_fresh_chi2']
        assert delta[1]==0 and (delta[0]==0)==(c['cache_size']==0)
        if c['cache_size']==1:
            assert c['cached_minus_fresh_chi2']==reference['cached_minus_fresh_chi2']
        else:
            assert c['return_main_loglikes']==c['fresh_main_loglikes']
    summary.append({'CAMB_version':version,'session':session,'exit_code':0,
                    'one_state_candidate_fails_with_interleaved_model':True,
                    'zero_state_selected_control_matches_fresh_exactly':True,
                    'receipt':path.name,'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'measured_errors':[c['cached_minus_fresh_chi2'] for c in r['records']]})
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'records':summary,'one_state_full_single_model_results_remain_valid':True,
     'one_state_general_cache_repair_candidate_rejected':True,
     'zero_state_selected_two_model_controls_match_fresh_exactly':True,
     'specific_shared_state_cause_or_uniform_accuracy_certificate_established':False,
     'native_spectra_differences_separately_recorded':False,
     'production_cache_or_live_sampler_modified':False}
with (HERE/'interleaved_controls_self_review.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('One-state candidate fails the two-model challenge on both versions; selected zero-state controls pass.')
