"""Observe the same recovery identities until their startup files are ready."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREPARATION = ROOT / 'runs/20261005_math_review_CLASS_fresh_recovery_preparation'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries = json.loads((PREPARATION / 'preparation_receipt.json').read_text())['entries']
sessions = {e['seed']: e['session_id'] for e in json.loads((HERE / 'managed_sessions.json').read_text())}
records = []
for e in entries:
    launch_path = PREPARATION / f'seed{e["seed"]}/launch_receipt.json'
    launch = json.loads(launch_path.read_text())
    proc = Path('/proc', str(launch['pid']))
    run = ROOT / e['run_dir']
    deadline = time.monotonic() + 900
    while True:
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        assert stat[0] != 'Z' and int(stat[19]) == launch['process_start_ticks']
        command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
        assert f'launch.py {e["seed"]}' in command
        assert e['module'] in (proc / 'maps').read_text() and sha(e['module']) == e['module_sha256']
        if all((run / n).exists() for n in ['resolved.yaml', 'solver_backend.json', 'stderr.txt']):
            break
        assert time.monotonic() < deadline, 'Startup observation timeout; inspect same owned process, do not restart.'
        print(e['seed'], 'same owned identity waiting for startup files', flush=True)
        time.sleep(5)
    assert os.getpriority(os.PRIO_PROCESS, launch['pid']) == 5
    assert not (run / 'stderr.txt').read_bytes()
    assert not (HERE / f'seed{e["seed"]}/launcher_stderr.txt').read_bytes()
    source = yaml.safe_load((ROOT / e['config']).read_text())
    cfg = yaml.safe_load((run / 'resolved.yaml').read_text())
    for key in ['theory', 'likelihood', 'params', 'sampler']:
        assert cfg[key] == source[key]
    backend = json.loads((run / 'solver_backend.json').read_text())
    assert backend['module_sha256'] == e['module_sha256'] and backend['module'] == e['module']
    records.append({**e, 'pid': launch['pid'], 'process_start_ticks': launch['process_start_ticks'],
        'command': command, 'session': sessions[e['seed']], 'native_module_sha256': e['module_sha256'],
        'effective_config_sha256': sha(run / 'resolved.yaml'),
        'native_backend_receipt_sha256': sha(run / 'solver_backend.json'),
        'launch_receipt_sha256': sha(launch_path),
        'status': 'running_fresh_CLASS_recovery_initial_native_point_verified_first_saved_row_pending'})
with (HERE / 'activation_verification.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'records': records, 'owned_live_recovery_trials': 2,
        'fresh_outputs_and_rng_verified': True, 'old_prefixes_appended': False,
        'original_terminal_families_replaced_or_dropped': False, 'posterior_qualified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Two recovery process identities, mapped libraries and effective configurations verified.')
