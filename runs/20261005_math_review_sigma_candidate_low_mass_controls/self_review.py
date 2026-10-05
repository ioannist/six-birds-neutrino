from datetime import datetime, timezone
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep = json.loads((HERE / 'preparation_receipt.json').read_text())
source, observer = ROOT / prep['source'], HERE / 'observe_all_runtime.py'
assert sha(source) == prep['source_sha256'] and sha(observer) == prep['observer_sha256']
reverse = observer.read_text()
for old, new in reversed(prep['changes']):
    assert reverse.count(new) == 1
    reverse = reverse.replace(new, old, 1)
assert reverse.encode() == source.read_bytes()
old_tree, new_tree = ast.parse(source.read_text()), ast.parse(observer.read_text())
old_primary = next(n for n in old_tree.body if isinstance(n, ast.FunctionDef))
new_primary = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef))
assert ast.dump(old_primary) == ast.dump(new_primary)
def loop(tree):
    return next(n for n in tree.body if isinstance(n, ast.For) and ast.unparse(n.iter) == 'entries')
old_loop, new_loop = loop(old_tree), loop(new_tree)
old_loop.body = old_loop.body[1:]
new_loop.body = new_loop.body[1:]
assert ast.dump(old_loop) == ast.dump(new_loop)
runtime_path = HERE / 'all_runtime_verification.json'
runtime = json.loads(runtime_path.read_text())
records = runtime['records']
assert len(records) == len({r['seed'] for r in records}) == len({r['pid'] for r in records}) == 48
live = [r for r in records if r['status'] == 'live_same_owned_native_identity']
terminal = [r for r in records if r['status'] == 'terminal_native_failure_preserved']
assert len(live) == runtime['owned_live_samplers'] == 44
assert len([r for r in live if r['seed'] < 2000]) == runtime['primary_owned_live_samplers'] == 40
assert len([r for r in live if r['seed'] >= 2000]) == runtime['upper_prior_owned_live_samplers'] == 4
assert [r['seed'] for r in terminal] == [2003, 2004, 2007, 2008]
contracts = {e['seed']: e for e in prep['terminal_contracts']}
assert set(contracts) == {r['seed'] for r in terminal}
for r in terminal:
    c = contracts[r['seed']]
    path = ROOT / c['terminal_receipt']
    assert sha(path) == c['terminal_receipt_sha256'] == r['terminal_receipt_sha256']
    assert sha(path.with_name('self_review_receipt.json')) == c['terminal_self_review_sha256']
    original = json.loads(path.read_text())
    for file in original['terminal_output_files']:
        assert sha(ROOT / file['source']) == sha(ROOT / file['frozen']) == file['sha256']
    review = json.loads(path.with_name('self_review_receipt.json').read_text())
    assert r['retained_represented_steps'] == review['retained_represented_steps']
    assert r['identity_observation']['original_identity_absent'] and r['exit_code'] == 1
    assert not r['posterior_qualified'] and not r['native_failure_is_posterior_rejection']
growth = runtime['growth_by_cohort']
assert len(growth) == 12
for group, terminal_seeds in [('upper20_A4095', [2003, 2004]), ('upper20_B4095', [2007, 2008])]:
    subset = [r for r in records if r.get('group') == group]
    g = growth[group]
    assert len(subset) == len(g['seeds']) == 4
    assert set(g['seeds']) == {r['seed'] for r in subset}
    assert g['minimum_saved_postburn_history'] == min(r['retained_represented_steps'] for r in subset)
    assert g['terminal_family_seeds'] == terminal_seeds
    assert not g['assessment_eligible'] and not g['due']
assert not runtime['posterior_convergence_certified'] and not runtime['prior_insensitivity_certified']
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'observer_sha256': sha(observer), 'runtime_sha256': sha(runtime_path),
       'reverse_source_bytes_checked': True, 'primary40_AST_identical': True,
       'remaining_wider_prior_live_loop_AST_identical': True,
       'registered_families_checked': 48, 'live_identities_checked': 44, 'terminal_families_checked': 4,
       'all_four_A_and_all_four_B_families_retained': True,
       'terminal_failure_blocks_both_wider_prior_qualifications': True,
       'native_error_counted_as_prior_or_posterior_rejection': False,
       'diagnostic_gates_changed': False, 'posterior_or_prior_stability_certified': False}
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Status-aware review passed: 48 registered families, 44 live, four explicit terminal failures; both wider-prior cohorts incomplete.')
