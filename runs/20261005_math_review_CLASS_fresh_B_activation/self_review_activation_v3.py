"""Recount startup identities and helper changes in a distinct self-review."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
for r in read(HERE / 'worker_preparation_receipt.json')['records']:
    assert sha(ROOT / r['source']) == r['source_sha256']
    text = (ROOT / r['source']).read_text()
    for before, after in r['changes']:
        assert text.count(before) == 1
        text = text.replace(before, after, 1)
    assert text.encode() == (HERE / r['name']).read_bytes()
activation = read(HERE / 'activation_verification.json')
assert activation['owned_live_recovery_trials'] == 8
assert {e['seed'] for e in activation['records']} == set(range(2401, 2409))
records = []
for e in activation['records']:
    proc = Path('/proc', str(e['pid']))
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert stat[0] != 'Z' and int(stat[19]) == e['process_start_ticks']
    assert (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode() == e['command']
    assert e['module'] in (proc / 'maps').read_text() and sha(e['module']) == e['module_sha256']
    assert os.getpriority(os.PRIO_PROCESS, e['pid']) == 5
    environment = dict(item.split(b'=', 1) for item in (proc / 'environ').read_bytes().split(b'\0') if b'=' in item)
    assert environment[b'OMP_NUM_THREADS'].decode() == e['OMP_NUM_THREADS']
    assert environment[b'OPENBLAS_NUM_THREADS'] == environment[b'MKL_NUM_THREADS'] == b'1'
    run = ROOT / e['run_dir']
    assert sha(run / 'resolved.yaml') == e['effective_config_sha256']
    assert sha(run / 'solver_backend.json') == e['native_backend_receipt_sha256']
    assert not (run / 'stderr.txt').read_bytes() and not (HERE / f'seed{e["seed"]}/launcher_stderr.txt').read_bytes()
    cfg = yaml.safe_load((ROOT / e['config']).read_text())
    resolved = yaml.safe_load((run / 'resolved.yaml').read_text())
    assert all(cfg[k] == resolved[k] for k in ['theory', 'likelihood', 'params', 'sampler'])
    preparation = ROOT / 'runs/20261005_math_review_CLASS_fresh_B_preparation'
    launch_path = preparation / f'seed{e["seed"]}/launch_receipt.json'
    launch = read(launch_path)
    assert sha(launch_path) == e['launch_receipt_sha256']
    assert launch['pid'] == e['pid'] and launch['process_start_ticks'] == e['process_start_ticks']
    assert launch['fresh_rng_and_output'] and not launch['old_prefix_appended']
    assert launch['preparation_self_review_sha256'] == sha(preparation / 'preparation_self_review_receipt.json')
    records.append({'seed': e['seed'], 'pid': e['pid'], 'process_start_ticks': e['process_start_ticks'],
                    'launch_receipt_sha256': sha(launch_path)})
with (HERE / 'activation_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': records,
        'eight_live_owned_native_identities_reconstructed': True,
        'new_outputs_and_source_bindings_verified': True, 'activation_verifier_direct_exit_code': 0,
        'saved_row_and_posterior_qualification_are_separate_obligations': True}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Eight B identities and effective targets reconstructed; first-row replay remains separate.')
