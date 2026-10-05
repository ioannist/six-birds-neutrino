"""Adversarial scope check for exact weighted empirical summaries."""
import ast
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=ast.parse((HERE/'before_extract_mnu_limits.py').read_text())
current=ast.parse((ROOT/'scripts/extract_mnu_limits.py').read_text())
old_functions={n.name:n for n in before.body if isinstance(n,ast.FunctionDef)}
new_functions={n.name:n for n in current.body if isinstance(n,ast.FunctionDef)}
assert set(new_functions)-set(old_functions)=={'_integer_weight_masses','_weighted_boundary_fraction'}
old_boundary=[n.value for n in ast.walk(old_functions['main']) if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='boundary_fraction' for t in n.targets)
              and isinstance(n.value,ast.Call)]
assert len(old_boundary)==1
class RestoreBoundary(ast.NodeTransformer):
 def visit_Call(self,node):
  if isinstance(node.func,ast.Name) and node.func.id=='_weighted_boundary_fraction':return deepcopy(old_boundary[0])
  return self.generic_visit(node)
normalized=[]
for node in current.body:
 if isinstance(node,ast.ImportFrom) and node.module in ['fractions','operator']:continue
 if isinstance(node,ast.FunctionDef):
  if node.name in ['_integer_weight_masses','_weighted_boundary_fraction']:continue
  if node.name=='_weighted_hist_mode':node=deepcopy(old_functions[node.name])
  if node.name=='main':node=RestoreBoundary().visit(node)
 normalized.append(node)
current.body=normalized
assert ast.dump(current)==ast.dump(before),'Unexpected non-summary reader change'
assert json.loads((HERE/'before_test_completion.json').read_text())['exit_code']==1
assert '8 failed, 4 passed' in (HERE/'before_tests_stdout.txt').read_text()
assert json.loads((HERE/'before_extended_test_completion.json').read_text())['exit_code']==1
assert '9 failed, 4 passed' in (HERE/'before_extended_tests_stdout.txt').read_text()
assert json.loads((HERE/'math_check_completion.json').read_text())['exit_code']==0
full=(HERE/'math_check_stdout.txt').read_text()
assert '214 passed' in full and 'Build completed successfully' in full
axioms=re.findall(r'depends on axioms: \[(.*?)\]',full,re.S)
assert len(axioms)==89 and all(set(a.strip() for a in group.split(',')) <= {'propext','Classical.choice','Quot.sound'} for group in axioms)
assert json.loads((HERE/'final_python_completion.json').read_text())['exit_code']==0
assert '215 passed' in (HERE/'final_python_stdout.txt').read_text()
assert not subprocess.check_output(['git','diff','5dd1b64','--','lean'],cwd=ROOT)
public=json.loads((ROOT/'runs/20261004_math_review_upper_gate_quantile_bridge/self_review_receipt.json').read_text())
for path,digest in public['source_sha256'].items():assert sha(ROOT/path)==digest
replay=json.loads((HERE/'report_replay_receipt.json').read_text())
assert len(replay['records'])==9 and replay['all_requested_reports_identical']
for r in replay['records']:
 old,new=ROOT/r['original'],ROOT/r['replayed']
 assert sha(old)==r['original_sha256'] and sha(new)==r['replayed_sha256']
 assert json.loads(old.read_text())==json.loads(new.read_text())
production=json.loads((HERE/'production_summary_replay_receipt.json').read_text())
assert len(production['records'])==36 and production['maximum_histogram_mode_change_ULPs']==0
assert production['all_medians_p95_and_boundary_fractions_identical']
for r in production['records']:
 assert sha(ROOT/r['chain'])==r['chain_sha256']
 assert r['original']==r['repaired']
controls=json.loads((HERE/'exact_summary_controls_receipt.json').read_text())
assert controls['histogram_controls']==96 and controls['boundary_fraction_controls']==672
for e in [replay,production,controls]:assert e['reader_source_sha256']==sha(ROOT/'scripts/extract_mnu_limits.py')
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT)
with (HERE/'self_review_receipt.json').open('x') as f:
 f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'distinct_self_review_not_independent_agent','only_reader_changes':'exact binary64 weighted histogram-bin comparisons and boundary-event fractions; finite rounded edges/midpoints','all_other_reader_AST_unchanged':True,'before_failures':9,'new_regression_controls':13,'initial_combined_Python_tests':214,'final_Python_tests':215,'public_Lean_axiom_outputs':89,'Lean_sources_unchanged_between_checks':True,'histogram_Fraction_oracle_controls':96,'boundary_fraction_Fraction_oracle_controls':672,'nine_latest_full_reports_identical':True,'all_36_production_family_summaries_identical':True,'positive_event_or_complement_mass_lost_at_float_endpoint_refused':True,'reader_source_sha256':sha(ROOT/'scripts/extract_mnu_limits.py'),'self_review_script_sha256':sha(__file__),'floating_edge_geometry_uniform_accuracy_certified':False,'posterior_convergence_or_precision_certified':False,'paper_or_canonical_changed':False},indent=2)+'\n')
print('Weighted summary self-review passes: 215 Python tests, 89 unchanged Lean outputs, 768 exact controls, nine reports and 36 summaries unchanged.')
