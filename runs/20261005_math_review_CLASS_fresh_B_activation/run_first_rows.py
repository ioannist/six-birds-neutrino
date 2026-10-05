"""Run eight first-row witnesses with at most two replay workers and retain exits."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
entries = {e['seed']: e for e in json.loads((HERE / 'activation_verification.json').read_text())['records']}
pending = [2405, 2406, 2407, 2408, 2401, 2402, 2403, 2404]
active, records = {}, []
while pending or active:
    while pending and len(active) < 2:
        seed = pending.pop(0)
        e = entries[seed]
        folder = HERE / f'seed{seed}'
        env = os.environ.copy()
        env.update(PYTHONPATH=str(Path(e['module']).parents[1]) + ':' + str(ROOT / 'src'),
                   OMP_NUM_THREADS=e['OMP_NUM_THREADS'], OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        command = ['/usr/bin/nice', '-n', '5', sys.executable, str(HERE / 'verify_first_row.py'), str(seed)]
        stdout = (folder / 'first_row_stdout.txt').open('xb')
        stderr = (folder / 'first_row_stderr.txt').open('xb')
        active[seed] = (subprocess.Popen(command, env=env, stdout=stdout, stderr=stderr), stdout, stderr, command)
    for seed, (p, out, err, command) in list(active.items()):
        code = p.poll()
        if code is None:
            continue
        out.close()
        err.close()
        r = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed,
             'command': command, 'actual_terminal_exit_code': code}
        with (HERE / f'seed{seed}/first_row_execution_receipt.json').open('x') as f:
            json.dump(r, f, indent=2, allow_nan=False)
            f.write('\n')
        records.append(r)
        del active[seed]
        print(seed, 'first-row worker terminal exit', code, flush=True)
    if active:
        time.sleep(1)
with (HERE / 'first_row_execution_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
        'all_first_row_workers_terminal': True, 'maximum_concurrent_replay_workers': 2,
        'posterior_qualified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
assert len(records) == 8 and all(r['actual_terminal_exit_code'] == 0 for r in records)
