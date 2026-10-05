"""Independently recount files and integrate the piecewise likelihood exactly."""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
r=json.loads((HERE/'upper_prior_receipt.json').read_text())
for s in r['source_files']:
 assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256']
checks=[]
for cohort in r['current_frozen_cohorts']:
 report_path=next(s['path'] for s in r['source_files'] if s['path'].endswith('_diagnostics.json') and
                  (('chain_A' in s['path'] and cohort['cohort']=='SPT_A') or
                   ('chain_B' in s['path'] and cohort['cohort']=='SPT_B') or
                   (cohort['cohort'] in ['quad_A','quad_B','medium_A','medium_B'] and Path(s['path']).name==cohort['cohort']+'_diagnostics.json')))
 report=json.loads((ROOT/report_path).read_text());values=[];weights=[]
 for prefix in report['prefixes']:
  paths=sorted(Path(prefix).parent.glob(Path(prefix).name+'.*.txt'))
  assert len(paths)==1
  lines=paths[0].read_text().splitlines();names=lines[0].lstrip('#').split();ix=names.index(cohort['sampled_mass_parameter'])
  rows=[line.split() for line in lines[1:] if line.strip() and not line.startswith('#')]
  for row in rows[len(rows)//5:]:
   weight=F(row[0]);assert weight>0 and weight.denominator==1
   values.append(float(row[ix]));weights.append(int(weight))
 assert min(values)==cohort['observed_min_eV'] and max(values)==cohort['observed_max_eV']
 assert sum(weights)==cohort['represented_postburn_steps']
 assert not any(x>=4.5 for x in values)
 checks.append({'cohort':cohort['cohort'],'minimum':min(values),'maximum':max(values),'represented_steps':sum(weights),'integer_holding_time_recount_matches':True})

# Distinct readout: find a continuous quantile by accumulating rectangle mass.
segments=[(F(0),F(1,5),F(47,10)),(F(5),F(6),F(3,50))]
def quantile(U,p):
 clipped=[(a,min(U,b),d) for a,b,d in segments if a<min(U,b)]
 total=sum((d*(b-a) for a,b,d in clipped),F(0));threshold=p*total;used=F(0)
 for a,b,d in clipped:
  mass=d*(b-a)
  if used+mass>=threshold:return a+(threshold-used)/d,total
  used+=mass
 raise AssertionError('Positive integrated mass did not attain the requested CDF.')
p=F(19,20);q5,z5=quantile(F(5),p);q6,z6=quantile(F(6),p)
assert q5==F(19,100) and q6==F(31,6)
assert z5==F(47,50) and z6==1
assert q5<1 and q6>5
# Tail-bound audit on exact rational test distributions, including atoms.
# Conditioning keeps every mass at or below U; no atom-free premise is needed.
for U in [F(1),F(5)]:
 atoms=[(F(0),F(1,10)),(F(1),F(1,5)),(F(5),F(3,5)),(F(6),F(1,10))]
 keep=sum((w for x,w in atoms if x<=U),F(0));epsilon=1-keep
 errors=[]
 for t in [F(-1),F(0),F(1),F(5),F(6),F(7)]:
  full=sum((w for x,w in atoms if x<=t),F(0))
  restricted=sum((w for x,w in atoms if x<=min(t,U)),F(0))/keep
  errors.append(abs(full-restricted));assert errors[-1]<=epsilon
 assert max(errors)==epsilon
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review','source_hashes_and_integer_recounts':checks,'continuous_quantile_integrated_by_rectangle_accumulation':{'q95_upper_5_fraction':str(q5),'q95_upper_6_fraction':str(q6),'normalizer_upper_5_fraction':str(z5),'normalizer_upper_6_fraction':str(z6)},'tail_CDF_bound_rational_controls_include_atoms':True,'counterexample_is_actual_cosmological_posterior_claimed':False,'historical_and_current_prior_targets_changed':False,'all_non_SPT_cohorts_retained_as_provisional':True,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'upper_prior_receipt_sha256':hashlib.sha256((HERE/'upper_prior_receipt.json').read_bytes()).hexdigest()}
with (HERE/'self_review_receipt.json').open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Exact file recounts, continuous quantile counterexample and general tail-CDF bound controls verified.')
