"""Wait for a complete saved row, then run the declared native verification."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
launch = json.loads((HERE / 'launch_receipt.json').read_text())
source = HERE / f"run/chains/math_guarded_grid12_trial_B_seed{launch['seed']}.1.txt"
runtime_path = HERE / 'first_rows_check_runtime.json'
runtime = {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
           'sampler_pid': launch['pid'], 'sampler_start_ticks': launch['process_start_ticks'],
           'status': 'waiting_for_complete_saved_row'}
runtime_path.write_text(json.dumps(runtime, indent=2) + '\n')
while True:
    proc = Path('/proc', str(launch['pid']))
    stat = (proc / 'stat').read_text().split()
    assert stat[2] != 'Z' and int(stat[21]) == launch['process_start_ticks']
    if source.exists():
        raw = source.read_bytes()
        complete = raw[:raw.rfind(b'\n') + 1].splitlines()
        if len(complete) >= 2:
            break
    time.sleep(15)
snapshot = subprocess.run([sys.executable, str(HERE / 'snapshot_first_rows.py')], check=True)
folder = HERE / 'first_saved_rows'
environment = os.environ.copy()
environment.update(launch['environment'])
command = [sys.executable, str(HERE / 'verify_first_rows.py')]
runtime['status'] = 'running_native_saved_row_verification'
runtime_path.write_text(json.dumps(runtime, indent=2) + '\n')
with (folder / 'native_stdout.txt').open('x') as stdout, (folder / 'native_stderr.txt').open('x') as stderr:
    native = subprocess.run(command, env=environment, stdout=stdout, stderr=stderr)
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'command': command,
           'environment': launch['environment'], 'exit_code': native.returncode,
           'snapshot_command_exit_code': snapshot.returncode,
           'native_check_script_sha256': hashlib.sha256((HERE / 'verify_first_rows.py').read_bytes()).hexdigest(),
           'snapshot_script_sha256': hashlib.sha256((HERE / 'snapshot_first_rows.py').read_bytes()).hexdigest()}
with (folder / 'completion_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2) + '\n')
runtime['status'] = 'completed' if native.returncode == 0 else 'failed_native_saved_row_verification'
runtime_path.write_text(json.dumps(runtime, indent=2) + '\n')
sys.exit(native.returncode)
