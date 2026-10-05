"""Check every current frozen precision target and resulting decision gate."""
from datetime import datetime, timezone
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from extract_mnu_limits import _load_chains_raw
from sbt_spt_audit.mcmc import holding_time_population_sd

cohorts={
 'SPT_A': ('20261004_math_review_spt_chain_snapshots_fourteenth_A','chain_A'),
 'SPT_B': ('20261004_math_review_spt_chain_snapshots_thirteenth_B','chain_B'),
 'quad_A': ('20261004_math_review_guarded_CLASS_second_diagnostics','quad_A'),
 'medium_A': ('20261004_math_review_guarded_CLASS_second_diagnostics','medium_A'),
 'quad_B': ('20261004_math_review_guarded_CLASS_third_B_diagnostics','quad_B'),
 'medium_B': ('20261004_math_review_guarded_CLASS_third_B_diagnostics','medium_B')}
records=[];sources=[]
for cohort,(bundle,stem) in cohorts.items():
 path=ROOT/'runs'/bundle/(stem+'_diagnostics.json')
 result=json.loads(path.read_text());sources.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 for name,d in result['diagnostics'].items():
  chains=[c for prefix in result['prefixes'] for c in _load_chains_raw(Path(prefix),name,.2)]
  values=np.concatenate([v for v,w in chains]);weights=np.concatenate([w for v,w in chains]);weights/=weights.max()
  mean=np.average(values,weights=weights)
  before=float(np.sqrt(np.average((values-mean)**2,weights=weights)))
  after=holding_time_population_sd(chains)
  assert np.isclose(before,after,rtol=1e-12,atol=0),(cohort,name,before,after)
  if name in ['mnu','mnu_sample']:
   limit=d['quantile_mcse_limit'];scope='unchanged_absolute_mass_target'
  else:
   assert np.isclose(.05*before,d['quantile_mcse_limit'],rtol=1e-12,atol=0)
   limit=.05*after;scope='full_history_population_SD_relative_target'
  finite=all(d[k] is not None and isfinite(d[k]) for k in ['rank_folded_split_rhat','bulk_ess','tail_ess_05_95','quantile_ess','quantile_mcse'])
  gates={
   'separate_starts':d['n_chains']>=2,
   'finite':finite,
   'Rhat':d['rank_folded_split_rhat']<=1.01,
   'bulk_ESS':d['bulk_ess']>=400,
   'tail_ESS':d['tail_ess_05_95']>=400,
   'quantile_ESS':d['quantile_ess']>=400,
   'MCSE':0<d['quantile_mcse']<=limit,
   'chronological_drift':d['quantile_half_difference']<=4*max(d['quantile_mcse'],limit),
   'equalized_selection':abs(d['quantile_full_draws']-d['quantile_retained_draws'])<=2*max(d['quantile_mcse'],limit)}
  old=dict(gates);old['MCSE']=0<d['quantile_mcse']<=d['quantile_mcse_limit'];old['chronological_drift']=d['quantile_half_difference']<=4*max(d['quantile_mcse'],d['quantile_mcse_limit']);old['equalized_selection']=abs(d['quantile_full_draws']-d['quantile_retained_draws'])<=2*max(d['quantile_mcse'],d['quantile_mcse_limit'])
  assert old==gates and all(gates.values())==d['diagnostic_thresholds_pass']
  records.append({'cohort':cohort,'parameter':name,'before_SD':before,'after_SD':after,'before_limit':d['quantile_mcse_limit'],'after_limit':limit,'precision_scope':scope,'all_gate_decisions_unchanged':True,'diagnostic_thresholds_pass':all(gates.values())})
assert len(records)==54
out={'utc':datetime.now(timezone.utc).isoformat(),'scope':'all_54_parameters_in_latest_six_frozen_cohorts','records':records,'source_reports':sources,'SD_relative_tolerance':1e-12,'all_gates_unchanged':True,'no_fresh_ArviZ_rerun_claimed':True,'MCSE_and_rank_algorithm_unchanged':True,'native_targets_and_sampler_settings_unchanged':True,'mass_absolute_precision_targets_unchanged':True,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE/'impact_receipt.json').open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('All 54 parameter SDs agree within 1e-12; every individual gate decision is unchanged.')
