"""Separate observed upper-gate support from prior-insensitivity evidence."""
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from extract_mnu_limits import _load_chains_raw
from sbt_spt_audit.mcmc import weighted_quantile

state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
cohorts={'SPT_A':(state['latest_SPT_A_diagnostic_bundle'],'chain_A'),
         'SPT_B':(state['latest_SPT_B_diagnostic_bundle'],'chain_B'),
         **{g:(b,g) for g,b in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items()}}
records=[];sources=[];n_families=0
for cohort,(bundle,stem) in cohorts.items():
 path=ROOT/bundle/(stem+'_diagnostics.json');report=json.loads(path.read_text());sources.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 name='mnu' if cohort.startswith('SPT') else 'mnu_sample'
 chains=[c for p in report['prefixes'] for c in _load_chains_raw(Path(p),name,.2)]
 n_families+=len(chains)
 for run in report['runs']:
  cfg_path=Path(run)/'resolved.yaml';cfg=yaml.safe_load(cfg_path.read_text());prior=cfg['params'][name]['prior']
  assert prior=={'min':0,'max':5},prior
  sources.append({'path':str(cfg_path.relative_to(ROOT)),'sha256':hashlib.sha256(cfg_path.read_bytes()).hexdigest()})
 for prefix in report['prefixes']:
  for p in Path(prefix).parent.glob(Path(prefix).name+'.*.txt'):
   sources.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 v=np.concatenate([v for v,w in chains]);w=np.concatenate([w for v,w in chains])
 assert np.all(v>=0) and np.all(v<=5) and np.all(w==np.floor(w)) and np.all(w>0)
 records.append({'cohort':cohort,'family_count':len(chains),'represented_postburn_steps':sum(int(x) for x in w),'sampled_mass_parameter':name,'prior_lower_eV':0,'prior_upper_eV':5,'observed_min_eV':float(v.min()),'observed_max_eV':float(v.max()),'descriptive_full_postburn_p95_eV':weighted_quantile(v,w,.95),'distance_of_largest_saved_mass_from_upper_gate_eV':5-float(v.max()),'represented_steps_at_or_above_4_5_eV':sum(int(weight) for x,weight in zip(v,w) if x>=4.5),'all_fixed_diagnostic_gates_pass':report['all_diagnostic_thresholds_pass'],'posterior_beyond_declared_prior_observed_or_certified':False})
assert n_families==28 and len(records)==6

# A single nonnegative likelihood shape, conditioned by two flat priors.
# L=47/10 on [0,1/5], L=3/50 on [5,6], zero elsewhere.
# Its integral is 1 on [0,6] and 47/50 on [0,5].
likelihood_segments=[(F(0),F(1,5),F(47,10)),(F(5),F(6),F(3,50))]
def area(U):
 return sum((max(F(0),min(b,U)-a)*d for a,b,d in likelihood_segments),F(0))
def cdf(x,U):
 return sum((max(F(0),min(b,U,x)-a)*d for a,b,d in likelihood_segments),F(0))/area(U)
old_upper,new_upper=F(5),F(6);old_q,new_q=F(19,100),F(31,6)
assert area(new_upper)==1 and area(old_upper)==F(47,50)
assert cdf(old_q,old_upper)==F(19,20) and cdf(new_q,new_upper)==F(19,20)
assert cdf(old_q,new_upper)==F(893,1000)
exact=lambda x:{'numerator':x.numerator,'denominator':x.denominator,'decimal':float(x)}
# Piecewise linear differences attain their extrema at the combined breakpoints.
breakpoints=[F(-1),F(0),F(1,5),F(5),F(6),F(7)]
errors=[abs(cdf(x,old_upper)-cdf(x,new_upper)) for x in breakpoints]
assert max(errors)==F(3,50)
counter={'scope':'analytic_counterexample_to_inferring_prior_insensitivity_from_small_conditional_p95_not_a_cosmological_likelihood','same_likelihood_segments':[{'lower':exact(a),'upper':exact(b),'density':exact(d)} for a,b,d in likelihood_segments],'posterior_normalizer_with_upper_5':exact(area(old_upper)),'posterior_normalizer_with_upper_6':exact(area(new_upper)),'p95_with_flat_prior_0_5_eV':exact(old_q),'p95_with_flat_prior_0_6_eV':exact(new_q),'CDF_with_upper_6_at_original_p95':exact(cdf(old_q,new_upper)),'removed_tail_probability_under_wider_prior':exact(F(3,50)),'supremum_CDF_error':exact(max(errors)),'inverse_quantile_definition':'infimum of coordinates where continuous posterior CDF reaches 19/20','constant_prior_normalization':'factor 1/U cancels in the posterior; the likelihood shape is unchanged'}
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'mathematical_scope_audit_with_exact_counterexample','manuscript_claim_location':'paper/sections/methods.tex:98','current_frozen_cohorts':records,'frozen_family_count':n_families,'source_files':sources,'counterexample':counter,'conditional_CDF_tail_bound':{'premises':'A specified wider posterior P and gate [0,U] with P([0,U])=1-epsilon>0; nonnegative support; an independently established tail probability epsilon','conclusion':'sup_x |F_conditioned(x)-F(x)| <= epsilon, with equality at U','derivation_below_gate':'F_conditioned(x)=F(x)/(1-epsilon); difference=F(x)*epsilon/(1-epsilon)<=epsilon because F(x)<=1-epsilon','derivation_above_gate':'F_conditioned(x)=1; difference=1-F(x)<=epsilon','coordinate_quantile_error_bound_from_this_alone':False,'tail_probability_estimated_from_chains_already_conditioned_on_upper_5':False},'strongest_current_observation':'no saved postburn mass is near the declared upper gate; posterior summaries remain conditional on the stated flat [0,5] prior','actual_cosmological_upper_prior_sensitivity_established':False,'native_model_variants_launched':False,'paper_modified':False,'scope_or_magnitude_revision_adopted':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE/'upper_prior_receipt.json').open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('28 frozen families checked across six cohorts; observed maximum',max(r['observed_max_eV'] for r in records),'eV.')
print('Exact fixed-likelihood counterexample: p95 moves from 19/100 to 31/6 eV when upper gate changes from 5 to 6.')
