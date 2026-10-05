"""Challenge the file-selection repair and check full-report preservation."""
import ast
from datetime import datetime,timezone
import hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=(HERE/'before_extract_mnu_limits.py').read_text()
a='        chain_candidates = sorted(prefix.parent.glob(f"{prefix.name}.*.txt"))\n        if not chain_candidates:\n            single = Path(str(prefix) + ".txt")\n            if single.exists():\n                chain_candidates = [single]\n'
b='    chain_files = sorted(p for p in prefix.parent.glob(f"{prefix.name}.*.txt")\n                         if p.name[len(prefix.name)+1:-4].isdigit())\n    if not chain_files:\n        single = Path(str(prefix) + ".txt")\n        if single.exists():\n            chain_files = [single]\n'
assert before.count(a)==before.count(b)==1
expected=ast.parse(before.replace(a,'        chain_candidates = _chain_files(prefix)\n').replace(b,'    chain_files = _chain_files(prefix)\n'))
current=ast.parse((ROOT/'scripts/extract_mnu_limits.py').read_text())
helpers=[n for n in current.body if isinstance(n,ast.FunctionDef) and n.name=='_chain_files']
assert len(helpers)==1
current.body.remove(helpers[0])
assert ast.dump(current)==ast.dump(expected), 'Change extends beyond shared file selection'
assert sha(HERE/'before_controls.py')==sha(ROOT/'tests/test_chain_file_selection.py')
assert json.loads((HERE/'before_test_completion.json').read_text())['exit_code']==1
assert '8 failed, 1 passed' in (HERE/'before_tests_stdout.txt').read_text()
assert json.loads((HERE/'math_check_completion.json').read_text())['exit_code']==0
full=(HERE/'math_check_stdout.txt').read_text()
assert '202 passed' in full and 'Build completed successfully' in full
axioms=re.findall(r'depends on axioms: \[(.*?)\]',full,re.S)
assert len(axioms)==83
assert all(set(a.strip() for a in group.split(',')) <= {'propext','Classical.choice','Quot.sound'} for group in axioms)
proof=json.loads((HERE/'report_replay_receipt.json').read_text())
assert proof['all_requested_reports_identical'] and proof['latest_reports_count']==len(proof['records'])==9
assert proof['reader_source_sha256']==sha(ROOT/'scripts/extract_mnu_limits.py')
state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
expected_reports={str(Path(p)/(c+'_diagnostics.json')) for c,p in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items()}
expected_reports|={v['diagnostics'] for v in state['fresh_CAMB_production_assessments'].values()}
assert expected_reports=={r['original'] for r in proof['records']}
for r in proof['records']:
 old,new=ROOT/r['original'],ROOT/r['replayed']
 assert sha(old)==r['original_sha256'] and sha(new)==r['replayed_sha256']
 assert json.loads(old.read_text())==json.loads(new.read_text())
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT)
with (HERE/'self_review_receipt.json').open('x') as f:
 f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'distinct_self_review_not_independent_agent','only_reader_change':'shared regular numbered or single-file selection for header and data','all_other_AST_unchanged':True,'before_failures':8,'new_controls':9,'full_Python_tests':202,'public_Lean_axiom_outputs':83,'all_nine_latest_full_reports_identical':True,'reader_source_sha256':sha(ROOT/'scripts/extract_mnu_limits.py'),'self_review_script_sha256':sha(__file__),'posterior_convergence_or_uniform_accuracy_certified':False,'paper_or_canonical_changed':False},indent=2)+'\n')
print('File-selection self-review passes: eight before failures, 202 tests, 83 Lean outputs, nine unchanged reports.')
