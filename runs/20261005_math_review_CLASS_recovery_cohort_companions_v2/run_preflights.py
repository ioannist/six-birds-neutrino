"""Run all six native controls with at most two concurrent native workers."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
entries = json.loads((HERE / 'preparation_receipt.json').read_text())['entries']


def run(entry):
    folder = HERE / f'seed{entry["seed"]}'
    env = dict(os.environ, OMP_NUM_THREADS=entry['OMP_NUM_THREADS'],
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    command = [sys.executable, str(HERE / 'preflight.py'), str(entry['seed'])]
    with (folder / 'preflight_stdout.txt').open('x') as out, (folder / 'preflight_stderr.txt').open('x') as err:
        proc = subprocess.run(command, env=env, stdout=out, stderr=err)
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': entry['seed'],
              'command': command, 'actual_terminal_exit_code': proc.returncode}
    with (folder / 'preflight_execution_receipt.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(entry['seed'], 'native control exited', proc.returncode, flush=True)
    return result


with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(run, entries))
with (HERE / 'preflight_execution_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'records': results,
               'all_native_control_workers_terminal': True, 'maximum_concurrent_native_controls': 2,
               'samplers_launched': 0}, f, indent=2)
    f.write('\n')
sys.exit(0 if all(r['actual_terminal_exit_code'] == 0 for r in results) else 1)
