"""Recompute compressed weighted moments with exact rational arithmetic."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import ldexp, sqrt
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from extract_mnu_limits import _load_chains_raw
from sbt_spt_audit.mcmc import holding_time_population_sd

def rational_sd(values,weights):
 total=sum(int(w) for w in weights)
 first=Fraction(0);second=Fraction(0)
 for x,w in zip(values,weights):
  f=Fraction(float(x));n=int(w)
  assert n>0 and float(n)==float(w)
  first+=n*f;second+=n*f*f
 variance=second/total-(first/total)**2
 assert variance>=0
 if not variance:return 0.
 exponent=2*((variance.numerator.bit_length()-variance.denominator.bit_length())//2)
 scale=Fraction(2)**exponent
 return ldexp(sqrt(float(variance/scale)),exponent//2)

impact=json.loads((HERE/'impact_receipt.json').read_text())
checks=[]
for source in impact['source_reports']:
 p=ROOT/source['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256']
 report=json.loads(p.read_text())
 for name in report['diagnostics']:
  chains=[c for prefix in report['prefixes'] for c in _load_chains_raw(Path(prefix),name,.2)]
  v=np.concatenate([v for v,w in chains]);w=np.concatenate([w for v,w in chains])
  exact=rational_sd(v,w);actual=holding_time_population_sd(chains)
  assert np.isclose(exact,actual,rtol=1e-12,atol=0),(source['path'],name,exact,actual)
  checks.append({'source_report':source['path'],'parameter':name,'rational_moment_SD':exact,'scaled_expanded_SD':actual})
assert len(checks)==54
controls=[]
for magnitude in [1e200,1e-200,np.finfo(float).max]:
 x=np.array([-magnitude,magnitude]);w=np.ones(2)
 with np.errstate(all='ignore'):
  mean=np.average(x,weights=w);old=float(np.sqrt(np.average((x-mean)**2,weights=w)))
 exact=rational_sd(x,w);actual=holding_time_population_sd([(x,w)])
 assert np.isclose(exact,actual,rtol=2e-15,atol=0)
 controls.append({'values':[float(v) for v in x],'before_SD':old if np.isfinite(old) else 'nonfinite','rational_moment_SD':exact,'after_SD':actual})
probe=json.loads((HERE/'probe_receipt.json').read_text())
for record in probe['records']:
 for version in ['before','after']:
  p=HERE/(record['fixture']+'_'+version+'.json')
  assert hashlib.sha256(p.read_bytes()).hexdigest()==record[version+'_report_sha256']
large,tiny=[json.loads((HERE/(label+'_after.json')).read_text())['diagnostics']['x'] for label in ['large','tiny']]
ordinary=json.loads((HERE/'ordinary_after.json').read_text())['diagnostics']['x']
for power,result in [(700,large),(-700,tiny)]:
 assert result['rank_folded_split_rhat']==ordinary['rank_folded_split_rhat']
 assert result['bulk_ess']==ordinary['bulk_ess'] and result['quantile_ess']==ordinary['quantile_ess']
 for key in ['quantile_mcse_limit','quantile_mcse','quantile_full_draws','quantile_retained_draws']:
  assert np.isclose(result[key],np.ldexp(ordinary[key],power),rtol=1e-12,atol=0)
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review','method':'exact_binary64_Fraction_weighted_first_and_second_moments_then_scaled_square_root','latest_frozen_parameter_checks':checks,'analytic_extreme_controls':controls,'coordinate_scale_replay_preserves_diagnostics_and_precision_decisions':True,'rank_and_MCSE_algorithm_changed':False,'universal_floating_point_certificate_claimed':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'impact_receipt_sha256':hashlib.sha256((HERE/'impact_receipt.json').read_bytes()).hexdigest(),'probe_receipt_sha256':hashlib.sha256((HERE/'probe_receipt.json').read_bytes()).hexdigest()}
with (HERE/'self_review_receipt.json').open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Distinct self-review: all 54 SDs match exact weighted moments within 1e-12; scaled diagnostic readouts agree.')
