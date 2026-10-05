"""Self-review the formal statement coverage, examples and transitive axiom gate."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
module=ROOT/'lean/trunc_gauss_proof/TruncGaussProof/GaussianGatedCDF.lean'
new=set(re.findall(r'^theorem (\w+)',module.read_text(),re.M))
assert new=={'truncatedGaussianLaw_eq_smul_restrict','truncatedGaussianLaw_real_apply','truncatedGaussianLaw_Ioc_cdf','truncatedGaussianLaw_cdf_of_nonneg','truncatedGaussianLaw_cdf_of_nonpos','truncatedGaussianLaw_cdf_strictMonoOn'}
public=set()
for path in (ROOT/'lean/trunc_gauss_proof/TruncGaussProof').glob('*.lean'):
 text=path.read_text();names=set(re.findall(r'^theorem (\w+)',text,re.M))
 assert not public.intersection(names)
 assert not re.search(r'^\s*(axiom|opaque)\b|\b(sorry|admit)\b',text,re.M)
 public.update(names)
assert len(public)==71
printed=set(re.findall(r'^#print axioms TruncGaussProof\.(\w+)',(ROOT/'lean/trunc_gauss_proof/AuditAxioms.lean').read_text(),re.M))
assert printed==public
output=(HERE/'math_check_stdout.txt').read_text()
assert '130 passed' in output and 'Build completed successfully' in output
axioms={n:set(re.split(r',\s*',a.strip())) if a.strip() else set() for n,a in re.findall(r"'TruncGaussProof\.(\w+)' depends on axioms: \[([^\]]*)\]",output)}
axioms={n:{a.strip() for a in values} for n,values in axioms.items()}
assert set(axioms)==public
allowed={'propext','Classical.choice','Quot.sound'}
assert all(a<=allowed for a in axioms.values())
assert len(re.findall(r'^example\b',(HERE/'GaussianGatedCDFReview.lean').read_text(),re.M))==10
for name in ['build_stderr.txt','formal_review_stdout.txt','formal_review_stderr.txt','math_check_stderr.txt']:
 assert not (HERE/name).read_bytes(),name
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'])
runtime=json.loads((HERE/'runtime_observation.json').read_text());assert runtime['owned_live_samplers']==28
phases=[{'session':30636,'phase':'first_measure_identity_restriction_commutation_missing','exit_code':1},{'session':78699,'phase':'two_measure_identity_theorems','exit_code':0},{'session':44579,'phase':'first_CDF_build_derived_Gaussian_finiteness_not_explicit','exit_code':1},{'session':61005,'phase':'full_six_theorem_build','exit_code':0},{'session':69772,'phase':'first_formal_review_zero_membership_elaboration','exit_code':1},{'session':32451,'phase':'ten_example_formal_review','exit_code':0},{'session':57060,'phase':'combined_make_math_check','exit_code':0}]
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review','scope':'integral_derived_gated_Gaussian_law_to_conditional_measure_interval_probabilities_and_CDF','new_exported_theorems':sorted(new),'total_exported_theorems_axiom_checked':71,'allowed_transitive_axioms':sorted(allowed),'Python_tests_passed':130,'formal_review_examples':10,'managed_phases':phases,'normalization_bridge':'derived Gaussian PDF identity plus actual Lebesgue withDensity, restriction and scalar multiplication; denominator positivity derived from integral normalizer','CDF_formula_for_nonnegative_x':'[Phi((x-mu)/sigma)-Phi(-mu/sigma)]/Phi(mu/sigma)','CDF_for_nonpositive_x':'zero_including_boundary','strictness_scope':'all real means and positive sigma, CDF strictly increasing on the physical half-line; no exact-real strictness asserted for rounded numerical readouts','interval_formula_scope':'0<=a<=b and sigma>0 for Ioc(a,b); arbitrary measurable conditional event identity also proved','quantile_scope':'at most one nonnegative coordinate for a specified CDF value; no quantile existence or numerical inverse algorithm claimed','zero_width_control':'constructed law has zero boundary atom while actual zero-variance Gaussian is Dirac; positive-sigma hypothesis is essential','finite_upper_gate_or_varying_prior_covered':False,'native_cosmological_Gaussianity_or_convergence_certified':False,'floating_point_accuracy_certified':False,'owned_live_samplers':28,'paper_modified':False,'scope_or_magnitude_revision_adopted':False,'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((ROOT/'lean/trunc_gauss_proof').rglob('*')) if p.is_file() and '.lake' not in p.parts and p.suffix=='.lean']+[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='validation_receipt.json']}
with (HERE/'validation_receipt.json').open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Verified six new derived theorems, ten formal controls, 130 Python tests and all 71 transitive axiom outputs.')
