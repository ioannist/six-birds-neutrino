from datetime import datetime, timezone
import ast
import hashlib
import json
import os
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract = json.loads((HERE / 'reproduction_contract.json').read_text())
for path, digest in contract['worker_source_sha256'].items():
    assert sha(ROOT / path) == digest
controls = json.loads((HERE / 'controls_receipt.json').read_text())
assert controls['original_success_result_identity_preserved']
assert controls['original_argument_forwarding_exact'] and controls['original_exception_identity_rethrown']
assert not controls['failure_returned_as_posterior_rejection']
recording_ast = ast.parse((HERE / 'failure_recording.py').read_text())
function = next(n for n in recording_ast.body if isinstance(n, ast.FunctionDef))
original_try = function.body[0]
assert isinstance(original_try, ast.Try)
assert len(original_try.body) == 1 and isinstance(original_try.body[0], ast.Return)
assert ast.unparse(original_try.body[0].value) == 'original(model, values, *args, **kwargs)'
assert len(original_try.handlers) == 1 and isinstance(original_try.handlers[0].body[-1], ast.Raise)
assert original_try.handlers[0].body[-1].exc is None
records = []
for seed, entry in contract['entries'].items():
    folder = HERE / f'seed{seed}'
    launch_path = folder / 'launch_receipt.json'
    launch = json.loads(launch_path.read_text())
    assert launch['contract_sha256'] == sha(HERE / 'reproduction_contract.json')
    proc = Path('/proc', str(launch['pid']))
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert stat[0] != 'Z' and int(stat[19]) == launch['process_start_ticks']
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    assert command == f"/tmp/neutrino-math-review-venv/bin/python {HERE.relative_to(ROOT)}/launch_reproduction.py {seed} "
    assert os.getpriority(os.PRIO_PROCESS, launch['pid']) == 10
    assert entry['module'] in (proc / 'maps').read_text()
    run = ROOT / launch['run_dir']
    assert not (folder / 'launcher_stderr.txt').read_bytes() and not (run / 'stderr.txt').read_bytes()
    native = json.loads((run / 'solver_backend.json').read_text())
    assert native['module_sha256'] == entry['module_sha256']
    original_cfg = yaml.safe_load((ROOT / entry['run_dir'] / 'resolved.yaml').read_text())
    new_cfg = yaml.safe_load((run / 'resolved.yaml').read_text())
    original_output, new_output = original_cfg.pop('output'), new_cfg.pop('output')
    assert original_output != new_output
    assert original_cfg == new_cfg
    records.append({'seed': int(seed), 'pid': launch['pid'], 'process_start_ticks': int(stat[19]),
                    'command': command, 'launch_receipt_sha256': sha(launch_path),
                    'original_resolved_sha256': entry['effective_config_sha256'],
                    'reproduction_resolved_sha256': sha(run / 'resolved.yaml'),
                    'configuration_changes_other_than_output_path': False, 'scheduling_nice': 10})
replay = json.loads((HERE / 'terminal_rows_replay_receipt.json').read_text())
assert len(replay['records']) == 6 and replay['upstream_original_CAMB_forced_fresh']
assert max(abs(v) for r in replay['records'] for v in r['fresh_minus_recorded'].values()) == 0
assert not replay['posterior_qualified']
with (HERE / 'activation_self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                       'review_type': 'distinct_self_review_not_independent_agent', 'records': records,
                       'original_model_sampler_and_seed_unchanged': True,
                       'only_run_output_path_changed': True, 'successful_evaluation_path_AST_verified': True,
                       'original_exception_reraised_AST_verified': True,
                       'six_selected_original_stored_rows_upstream_fresh_exact': True,
                       'original_failed_trajectory_or_proposal_exactly_reproduced': False,
                       'trajectory_prefix_verification_pending': True, 'posterior_qualified': False},
                      indent=2, allow_nan=False) + '\n')
print('Two isolated diagnostic replays live; model/sampler/seed identical, six original stored rows exact upstream controls.')
