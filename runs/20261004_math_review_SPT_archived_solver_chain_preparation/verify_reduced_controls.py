"""Distinct self-review of completed controls; do not infer a general repair."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
load = lambda name: json.loads((HERE/name).read_text())
reduced = load('reduced_histories_receipt.json')
cases = {r['case']:r for r in reduced['records']}
assert len(cases) == 5
for name in ['initial_then_target','earlier_fast_then_target']:
    assert cases[name]['cached_minus_fresh_chi2'] == [0.,0.]
assert cases['slow_then_target']['cached_minus_fresh_chi2'] == [0.04844393913572276,0.]
for name in ['late_window','late_window_independent_copy']:
    assert cases[name]['cached_minus_fresh_chi2'] == [0.19519154827321472,0.]
copy = cases['late_window_independent_copy']
assert len(copy['getter_calls']) == len(copy['sequence'])+1
assert all(g['As_before_spectra']==2e-9 and g['ns_before_spectra']==.96 for g in copy['getter_calls'])
assert all(g['has_scalar_time_sources'] for g in copy['getter_calls'])
assert cases['late_window']['values'][-1]['transfer_state_params']==cases['initial_then_target']['values'][-1]['transfer_state_params']
assert all(c['helper_non_linear_sources'] for c in cases.values())
sources = ['reduced_histories_receipt.json','independent_transfer_copy_receipt.json',
           'ordered_replay_self_review.json','traced_points_replay_receipt.json']
summary = {}
for version in ['1.6.5','2.0.4']:
    name = 'single_transfer_state_'+version+'_receipt.json'
    sources.append(name)
    r = load(name)
    assert r['CAMB_version'] == version
    assert len(r['records']) == 4
    for case in r['records']:
        cached = case['values'][-1]['loglikes']
        expected = [-2*(Fraction(a)-Fraction(b)) for a,b in zip(cached,case['fresh_loglikes'])]
        assert [float(v) for v in expected] == case['cached_minus_fresh_chi2']
        assert expected[1] == 0
        assert (expected[0]==0) == (case['transfer_cache_size']==1)
    summary[version] = [{'case':c['case'],'cache_size':c['transfer_cache_size'],
                         'cached_minus_fresh_chi2':c['cached_minus_fresh_chi2']} for c in r['records']]
out = {'utc':datetime.now(timezone.utc).isoformat(),
       'review_type':'distinct_self_review_not_independent_review',
       'completed_sessions':{'reduced_histories':3073,'archived_cache_control':20404,'current_cache_control':24461},
       'all_exit_codes':0,'both_versions_selected_cache_return_failures_observed':True,
       'one_state_selected_controls_match_fresh_exactly':True,
       'independent_copy_override_invocation_confirmed_on_reduced_history':True,
       'native_transfer_copy_did_not_fix_selected_failure':True,'summary':summary,
       'specific_native_global_or_general_validated_repair_proved':False,
       'no_inference_history_modified_no_numerical_tolerance_relaxed':True,
       'input_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources}}
with (HERE/'reduced_controls_self_review.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Selected failures and candidate controls verified; full-history checks remain separate.')
