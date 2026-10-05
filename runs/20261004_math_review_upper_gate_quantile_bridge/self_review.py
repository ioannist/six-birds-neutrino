"""Check old theorem preservation, explicit bridge premises and edge witnesses."""
from datetime import datetime,timezone
import hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=ROOT/'lean/trunc_gauss_proof/TruncGaussProof/UpperGate.lean'
audit=ROOT/'lean/trunc_gauss_proof/AuditAxioms.lean'
before=(HERE/'before_UpperGate.lean').read_text();current=source.read_text()
extract=lambda t: {m.group(1):m.group(0).strip() for m in re.finditer(r'^theorem (\w+)[\s\S]*?(?=\n/--|\nend TruncGaussProof)',t,re.M)}
old,new=extract(before),extract(current)
assert len(old)==9 and len(new)==15
for name,body in old.items():assert new[name]==body,name
added=set(new)-set(old)
expected={'upperConditionedLaw_quantile_lt_gate','upperConditionedLaw_quantile_cdf_displacement','upperConditionedLaw_quantile_lt_original','upperConditionedLaw_quantile_displacement_le','upperConditionedGaussian_quantile_lt_original','upperConditionedGaussian_quantile_strictMono_gate'}
assert added==expected
assert audit.read_text().startswith((HERE/'before_AuditAxioms.lean').read_text())
new_audits=audit.read_text()[len((HERE/'before_AuditAxioms.lean').read_text()):]
assert set(re.findall(r'#print axioms TruncGaussProof\.(\w+)',new_audits))==expected
assert (HERE/'attempt1_UpperGate.lean').read_bytes()==source.read_bytes()
assert json.loads((HERE/'attempt1_completion.json').read_text())['exit_code']==0
full=(HERE/'math_check_stdout.txt').read_text()
assert json.loads((HERE/'math_check_completion.json').read_text())['exit_code']==0
assert '202 passed' in full and 'Build completed successfully' in full
axioms=re.findall(r'depends on axioms: \[(.*?)\]',full,re.S)
assert len(axioms)==89
assert all(set(a.strip() for a in group.split(',')) <= {'propext','Classical.choice','Quot.sound'} for group in axioms)
for artifact in ['formal_attempt1','formal_attempt2','formal_attempt3']:
 assert json.loads((HERE/(artifact+'_completion.json')).read_text())['exit_code']==1
assert json.loads((HERE/'formal_attempt4_completion.json').read_text())['exit_code']==0
formal=HERE/'FormalSelfReview.lean'
assert formal.read_bytes()==(HERE/'formal_attempt4_source.lean').read_bytes()
assert not (HERE/'formal_attempt4_stdout.txt').read_bytes() and not (HERE/'formal_attempt4_stderr.txt').read_bytes()
assert len(re.findall(r'^example',formal.read_text(),re.M))==18
original_controls=(ROOT/'runs/20261004_math_review_finite_upper_gate_formalization/FormalSelfReview.lean').read_text().replace('import TruncGaussProof\n','import TruncGaussProof.UpperGate\n',1)
assert formal.read_text().startswith(original_controls)
strip_comments=lambda t:re.sub(r'--[^\n]*','',re.sub(r'/\-[\s\S]*?\-/','',t))
for f in [source,formal]:assert not re.search(r'\b(sorry|axiom|admit|unsafe)\b',strip_comments(f.read_text()))
bridge=new['upperConditionedLaw_quantile_displacement_le']
assert '(hc : 0 < c)' in bridge and '(hgrowth : c * (y - x) ≤ cdf ν y - cdf ν x)' in bridge
assert '(hU1 : cdf ν U < 1)' in bridge and '(hq0 : 0 < q)' in bridge and '(hq1 : q < 1)' in bridge
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT)
with (HERE/'self_review_receipt.json').open('x') as f:
 f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'distinct_self_review_not_independent_agent','nine_old_upper_gate_theorems_preserved':True,'new_public_theorems':sorted(added),'full_Python_tests':202,'public_Lean_axiom_outputs':89,'formal_controls':18,'old_formal_controls_retained':10,'actual_atomic_probability_laws':3,'small_tail_probability':.001,'arbitrarily_large_exact_p95_CDF_solution_displacement_proved':True,'coordinate_certificate_requires_explicit_positive_CDF_growth':True,'zero_tail_plateau_counterexample_proved':True,'Gaussian_quantile_existence_and_gate_order_realized':True,'generic_scope':'actual probability laws and exact CDF-equation quantiles; atoms permitted','Gaussian_scope':'arbitrary real mean, positive sigma and positive finite upper gates','cosmological_Gaussianity_or_prior_insensitivity_inferred':False,'numerical_inverse_CDF_accuracy_proved':False,'source_sha256':{str(source.relative_to(ROOT)):sha(source),str(audit.relative_to(ROOT)):sha(audit)},'formal_controls_sha256':sha(formal),'self_review_script_sha256':sha(__file__),'paper_or_canonical_changed':False},indent=2)+'\n')
print('Quantile bridge self-review passes: six new theorems, 18 formal controls, 202 tests and 89 standard-axiom outputs.')
