"""Verify that the added header premise is the sole reader behavior change."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
before = ast.parse((HERE / 'before_extract_mnu_limits.py').read_text())
current = ast.parse((ROOT / 'scripts/extract_mnu_limits.py').read_text())

class RemoveAddedPremise(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id == '_require_chain_columns':
            return ast.copy_location(ast.Name(id='_require_unique_names', ctx=node.ctx), node)
        return node

old_functions = {f.name: f for f in before.body if isinstance(f, ast.FunctionDef)}
new_functions = {f.name: f for f in current.body if isinstance(f, ast.FunctionDef)}
assert set(new_functions)-set(old_functions) == {'_require_chain_columns'}
for name, original in old_functions.items():
    transformed = RemoveAddedPremise().visit(new_functions[name])
    assert ast.dump(transformed) == ast.dump(original), name
assert json.loads((HERE / 'before_test_completion.json').read_text())['exit_code'] == 1
assert '5 failed, 2 passed' in (HERE / 'before_tests_stdout.txt').read_text()
assert json.loads((HERE / 'math_check_completion.json').read_text())['exit_code'] == 0
full = (HERE / 'math_check_stdout.txt').read_text()
assert '193 passed' in full and 'Build completed successfully' in full
axioms = re.findall(r'depends on axioms: \[(.*?)\]', full, re.S)
assert len(axioms) == 83
assert all(set(a.strip() for a in group.split(',')) <=
           {'propext', 'Classical.choice', 'Quot.sound'} for group in axioms)
replay = json.loads((HERE / 'report_replay_receipt.json').read_text())
assert replay['reader_source_sha256'] == sha(ROOT / 'scripts/extract_mnu_limits.py')
assert len(replay['records']) == 7
for record in replay['records']:
    before_path, after_path = ROOT / record['original'], ROOT / record['replayed']
    assert sha(before_path) == record['original_sha256'] and sha(after_path) == record['replayed_sha256']
    assert json.loads(before_path.read_text()) == json.loads(after_path.read_text())
assert not subprocess.check_output(['git', 'diff', 'ffdaf4b', '--name-only', '--',
                                    'paper', 'docs/findings/canonical_results.json'], cwd=ROOT)
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                       'reviewer': 'distinct_self_review_not_independent_agent',
                       'only_added_reader_premise': 'a declared first chain column is weight',
                       'valid_header_reader_AST_unchanged_after_removing_guard': True,
                       'before_failure_controls': 5,
                       'unheaded_and_minusloglike_GetDist_controls_preserved': True,
                       'full_Python_tests': 193, 'public_Lean_axiom_outputs': 83,
                       'seven_latest_full_diagnostic_reports_unchanged': True,
                       'source_sha256': {'scripts/extract_mnu_limits.py': sha(ROOT / 'scripts/extract_mnu_limits.py'),
                                         'tests/test_math_repairs.py': sha(ROOT / 'tests/test_math_repairs.py')},
                       'self_review_script_sha256': sha(__file__),
                       'posterior_convergence_or_uniform_accuracy_certified': False,
                       'paper_or_canonical_results_changed': False}, indent=2) + '\n')
print('Weight-column self-review passes: sole added header premise, 193 tests, 83 Lean exports, seven unchanged reports.')
