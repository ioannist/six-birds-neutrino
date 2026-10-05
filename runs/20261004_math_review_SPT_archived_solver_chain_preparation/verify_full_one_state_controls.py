"""Check both complete prototypes against their separately calculated baselines."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
trace=HERE/'sampler_trajectory_trace/posterior_calls.jsonl'
calls=[json.loads(s) for s in trace.read_text().splitlines()]
assert len(calls)==37
records=[]
for version,session in [('1.6.5',60727),('2.0.4',96473)]:
    path=HERE/('full_single_transfer_state_'+version+'_receipt.json')
    receipt=json.loads(path.read_text())
    assert receipt['trace_sha256']==hashlib.sha256(trace.read_bytes()).hexdigest()
    assert receipt['CAMB_version']==version and len(receipt['records'])==37
    assert receipt['all_recorded_points_match_full_fresh_exactly']
    for call,r in zip(calls,receipt['records']):
        assert r['call']==call['call'] and r['point']==call['point']
        assert r['one_state_cached']==r['full_fresh'] and r['exactly_equal']
        assert all(delta==0 for delta in r['cached_minus_fresh_chi2'])
    rejected=[r['call'] for r in receipt['records'] if r['full_fresh']['logpost'] is None]
    assert rejected==[14] and calls[14]['point']['mnu']<0
    assert len(receipt['records'][14]['full_fresh']['loglikes'])==0
    assert len(receipt['records'][35]['full_fresh']['loglikes'])==2
    if version=='1.6.5':
        earlier=json.loads((HERE/'traced_points_replay_receipt.json').read_text())
        assert receipt['records'][35]['full_fresh']['loglikes']==earlier['call35_fresh_loglikes_after_complete_history']
    records.append({'CAMB_version':version,'session':session,'exit_code':0,
                    'exact_posterior_result_count':37,'finite_native_likelihood_point_count':36,
                    'prior_rejected_point_count':1,'receipt':path.name,
                    'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'records':records,'candidate_preserves_selected_full_fresh_target_both_versions':True,
     'all37_results_exactly_equal_to_separate_model_fresh_baselines':True,
     'sampled_likelihoods_priors_and_posterior_totals_compared':True,
     'specific_native_global_or_universal_cache_safety_proved':False,
     'production_helper_guard_or_actual_sampler_repair_implemented':False,
     'interleaved_multiple_native_models_validated':False,
     'likelihood_tolerance_relaxed_or_posterior_claim_adopted':False}
with (HERE/'full_one_state_self_review.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Both complete 37-point controls match separate fresh baselines exactly; production integration remains.')
