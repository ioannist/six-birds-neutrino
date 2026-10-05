"""Check the mathematical scaling, compatibility and actual validation scope."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source = ROOT / 'src/sbt_spt_audit/likelihoods/desi_dr2_bao.py'
before = ast.parse((HERE / 'before_desi_dr2_bao.py').read_text())
after = ast.parse(source.read_text())
function = lambda tree: next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                             and n.name == 'compute_observable_value')
old_function, new_function = function(before), function(after)
assignments = lambda fun: {n.targets[0].id: n.value for n in ast.walk(fun)
                           if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
old, new = assignments(old_function), assignments(new_function)
ordinary = next(n.value for n in ast.walk(new_function) if isinstance(n, ast.Assign)
                and isinstance(n.value, ast.BinOp) and isinstance(n.value.left, ast.BinOp)
                and isinstance(n.value.left.left, ast.Name) and n.value.left.left.id == 'product')

class ExpandProduct(ast.NodeTransformer):
    def visit_Name(self, node):
        return deepcopy(new['product']) if node.id == 'product' else node

expanded = ExpandProduct().visit(deepcopy(ordinary))
legacy = ast.BinOp(left=old['dv'], op=ast.Div(), right=ast.Name(id='rd', ctx=ast.Load()))
assert ast.dump(expanded) == ast.dump(legacy)
assert all(alias.name != 'cbrt' for node in after.body if isinstance(node, ast.ImportFrom)
           and node.module == 'math' for alias in node.names)
assert 'np.cbrt' in source.read_text()
assert 'requires-python = ">=3.9"' in (ROOT / 'pyproject.toml').read_text()

assert json.loads((HERE / 'before_test_completion.json').read_text())['exit_code'] == 1
assert '9 failed, 11 passed' in (HERE / 'before_tests_stdout.txt').read_text()
assert json.loads((HERE / 'after_test_completion.json').read_text())['exit_code'] == 0
assert '20 passed' in (HERE / 'after_tests_stdout.txt').read_text()
assert json.loads((HERE / 'final_python_completion.json').read_text())['exit_code'] == 0
assert '186 passed' in (HERE / 'final_python_stdout.txt').read_text()
assert not (HERE / 'final_python_stderr.txt').read_bytes()
assert json.loads((HERE / 'math_check_completion.json').read_text())['exit_code'] == 0
full = (HERE / 'math_check_stdout.txt').read_text()
assert '186 passed' in full and 'Build completed successfully' in full
axioms = re.findall(r'depends on axioms: \[(.*?)\]', full, re.S)
assert len(axioms) == 83
assert all(set(a.strip() for a in group.split(',')) <=
           {'propext', 'Classical.choice', 'Quot.sound'} for group in axioms)
assert not subprocess.check_output(['git', 'diff', '36a10cf', '--name-only', '--', 'lean'], cwd=ROOT)
assert not subprocess.check_output(['git', 'diff', 'ffdaf4b', '--name-only', '--',
                                    'paper', 'docs/findings/canonical_results.json'], cwd=ROOT)

control = json.loads((HERE / 'final_numerical_control_receipt.json').read_text())
assert control['production_source_sha256'] == sha(source)
assert control['controls_checked'] == len(control['controls']) == 108
assert control['maximum_relative_error'] <= 3e-15
native_checks = 0
for group in ['current_A3200', 'old_A3200']:
    assert json.loads((HERE / (group+'_final_native_completion.json')).read_text())['exit_code'] == 0
    result = json.loads((HERE / (group+'_final_native_invariance.json')).read_text())
    assert result['production_source_sha256'] == sha(source)
    assert result['native_atol'] == 1e-9 and result['native_rtol'] == 0
    assert len(result['checks']) == 2
    for check in result['checks']:
        assert check['ordinary_BAO_before_after_exact']
        assert max(abs(v) for v in check['native']['fresh_minus_recorded'].values()) <= 1e-9
        native_checks += 1
assert native_checks == 4
runtime = json.loads((HERE / 'runtime_observation.json').read_text())
assert runtime['owned_live_samplers'] == 40 and not runtime['posterior_convergence_certified']
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                       'reviewer': 'distinct_self_review_not_independent_agent',
                       'mathematical_scaling': 'z=mz*2^ez, DH=mh*2^eh, DM=mm*2^em, rd=mr*2^er; E=ez+eh+2em-3er=3q+r; DV/rd=cbrt(mz*mh*mm^2*2^r)/mr*2^q',
                       'fallback_scope': 'positive finite inputs with unusable intermediate product; zero numerator handled separately; nonrepresentable final output refused',
                       'ordinary_arithmetic_AST_matches_before': True,
                       'new_math_cbrt_dependency_removed': True,
                       'before_failing_regressions': 9,
                       'final_full_Python_tests': 186,
                       'fresh_Lean_public_axiom_outputs': 83,
                       'validation_scope': 'combined make check for initial cbrt attempt; final full Python suite, high-precision controls and native controls rerun after compatibility repair; Lean sources unchanged',
                       'final_high_precision_controls': 108,
                       'maximum_relative_control_error': control['maximum_relative_error'],
                       'final_native_rows_checked': native_checks,
                       'ordinary_native_BAO_vectors_identical': True,
                       'source_sha256': {str(source.relative_to(ROOT)): sha(source),
                                         'tests/test_desi_dr2_bao.py': sha(ROOT / 'tests/test_desi_dr2_bao.py')},
                       'self_review_script_sha256': sha(__file__),
                       'uniform_interval_error_or_posterior_convergence_certified': False,
                       'paper_or_canonical_results_changed': False}, indent=2, allow_nan=False) + '\n')
print('Final BAO range repair self-review passes: 186 Python tests, 83 unchanged Lean exports, 108 controls, four native rows.')
