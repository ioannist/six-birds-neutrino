"""Check replay equality at the failing point without hiding earlier differences."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'traced_points_replay_receipt.json').read_text())
assert r['traced_call_count']==37 and [c['call'] for c in r['records']]==list(range(37))
different=[c for c in r['records'] if c['replayed_loglikes']!=c['recorded_loglikes']]
assert [c['call'] for c in different]==[2,3]
for c in different:
    expected=[-2*(Fraction(a)-Fraction(b)) for a,b in zip(c['replayed_loglikes'],c['recorded_loglikes'])]
    assert [float(v) for v in expected]==c['replayed_minus_recorded_chi2_components']
    assert expected[1]==0
call=r['records'][35]
assert call['replayed_loglikes']==call['recorded_loglikes']
fresh=r['call35_fresh_loglikes_after_complete_history']
delta=[-2*(Fraction(a)-Fraction(b)) for a,b in zip(call['replayed_loglikes'],fresh)]
assert delta[0]!=0 and delta[1]==0
simple=json.loads((HERE/'posterior_path_transfer_cache_1.6.5_receipt.json').read_text())
assert simple['records']['fast_move_reused_transfer']['chi2_total']==-2*sum(fresh)
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'session':39092,'exit_code':0,'posterior_calls_replayed':37,'exactly_reproduced_call_count':35,
     'nonidentical_calls':different,'all37_exact_equality_assumption_rejected_before_sealing':True,
     'failing_call35_reproduced_exactly':True,
     'call35_cached_minus_fresh_component_chi2_exact_binary64':[str(v) for v in delta],
     'call35_cached_minus_fresh_total_chi2':float(sum(delta)),
     'fresh_matches_simple_initial_to_same_point_control':True,
     'preceding_calculation_state_dependence_observed_at_fixed_point':True,
     'speed_measurement_calls_required_to_reproduce_call35_failure':False,
     'all_sampler_preparation_states_equivalent_or_replayed':False,
     'specific_mutation_or_validated_repair_established':False,
     'no_tolerance_relaxed_no_native_or_inference_sampler_modified':True,
     'replay_receipt_sha256':hashlib.sha256((HERE/'traced_points_replay_receipt.json').read_bytes()).hexdigest()}
with (HERE/'ordered_replay_self_review.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('35 calls exact, calls2/3 differ; failing call35 exactly reproduced; cached-minus-fresh chi2',float(sum(delta)))
