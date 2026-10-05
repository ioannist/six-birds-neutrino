from datetime import datetime, timezone
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
preparation = json.loads((HERE / 'preparation_receipt.json').read_text())
source = ROOT / preparation['source']
observer = HERE / 'observe_all_runtime.py'
assert sha(source) == preparation['source_sha256'] and sha(observer) == preparation['observer_sha256']
reversed_text = observer.read_text()
for old, new in reversed(preparation['changes']):
    assert reversed_text.count(new) == 1
    reversed_text = reversed_text.replace(new, old, 1)
assert reversed_text.encode() == source.read_bytes()
old_ast, new_ast = ast.parse(source.read_text()), ast.parse(observer.read_text())
old_primary = next(n for n in old_ast.body if isinstance(n, ast.FunctionDef))
new_primary = next(n for n in new_ast.body if isinstance(n, ast.FunctionDef))
assert ast.dump(old_primary) == ast.dump(new_primary)
def wider_loop(tree):
    return next(n for n in tree.body if isinstance(n, ast.For) and ast.unparse(n.iter) == 'entries')
old_loop, new_loop = wider_loop(old_ast), wider_loop(new_ast)
assert isinstance(new_loop.body[0], ast.If)
assert ast.unparse(new_loop.body[0].test) == "e['seed'] in [2003, 2004]"
new_loop.body = new_loop.body[1:]
assert ast.dump(old_loop) == ast.dump(new_loop)
contracts = json.loads((HERE / 'terminal_contracts.json').read_text())
runtime_path = HERE / 'all_runtime_verification.json'
runtime = json.loads(runtime_path.read_text())
records = runtime['records']
assert len(records) == len({r['seed'] for r in records}) == len({r['pid'] for r in records}) == 48
live = [r for r in records if r['status'] == 'live_same_owned_native_identity']
terminal = [r for r in records if r['status'] == 'terminal_native_failure_preserved']
assert len(live) == runtime['owned_live_samplers'] == 46
assert len([r for r in live if r['seed'] < 2000]) == 40
assert len([r for r in live if r['seed'] >= 2000]) == 6
assert [r['seed'] for r in terminal] == [2003, 2004]
for r in terminal:
    key = str(r['seed'])
    path = ROOT / contracts['terminal_paths'][key]
    assert sha(path) == contracts['terminal_receipt_shas'][key] == r['terminal_receipt_sha256']
    assert sha(path.with_name('self_review_receipt.json')) == contracts['terminal_self_review_shas'][key]
    assert r['identity_observation']['original_identity_absent'] and r['exit_code'] == 1
    assert not r['posterior_qualified'] and not r['native_failure_is_posterior_rejection']
    review = json.loads(path.with_name('self_review_receipt.json').read_text())
    assert r['retained_represented_steps'] == review['retained_represented_steps']
growth = runtime['growth_by_cohort']
assert len(growth) == 12
for group in ['upper20_A4095', 'upper20_B4095']:
    subset = [r for r in records if r.get('group') == group]
    g = growth[group]
    assert len(subset) == len(g['seeds']) == 4
    assert set(g['seeds']) == {r['seed'] for r in subset}
    assert g['minimum_saved_postburn_history'] == min(r['retained_represented_steps'] for r in subset)
    eligible = all(r['status'] == 'live_same_owned_native_identity' for r in subset)
    assert g['assessment_eligible'] == eligible
    assert g['due'] == (eligible and g['minimum_saved_postburn_history'] >= g['next_assessment_trigger'])
assert growth['upper20_A4095']['terminal_family_seeds'] == [2003, 2004]
assert not growth['upper20_A4095']['assessment_eligible']
assert growth['upper20_B4095']['assessment_eligible']
assert not runtime['posterior_convergence_certified'] and not runtime['prior_insensitivity_certified']
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'observer_sha256': sha(observer), 'runtime_sha256': sha(runtime_path),
       'reverse_source_bytes_checked': True, 'primary40_AST_identical': True,
       'remaining_wider_prior_live_loop_AST_identical': True,
       'registered_families_checked': 48, 'live_identities_checked': 46, 'terminal_families_checked': 2,
       'all_four_A_families_retained': True, 'terminal_failure_blocks_A_qualification': True,
       'native_error_counted_as_prior_or_posterior_rejection': False,
       'diagnostic_gates_changed': False, 'posterior_or_prior_stability_certified': False}
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Status-aware self-review passed: 48 families, 46 live, two explicit terminal failures; original live checks preserved.')
