"""Wait on the same owned processes until the unchanged growth gate allows freezing."""
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
prior_path = ROOT / 'runs/20261004_math_review_guarded_CLASS_third_B_diagnostics/snapshot_receipt.json'
prior = json.loads(prior_path.read_text())
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
entries = [e for e in state['guarded_quadrature_posterior_chains'] if e['lens'] == 'B']
owned = {r['seed']: r for r in prior['runtime_observations']}
assert {e['seed'] for e in entries} == {1305, 1306, 1307, 1308}
assert not (HERE / 'snapshot_receipt.json').exists()
command = [sys.executable, str(HERE / 'prepare_snapshot.py')]
launch = {
    'utc': datetime.now(timezone.utc).isoformat(), 'worker_pid': os.getpid(),
    'worker_process_start_ticks': int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]),
    'owned_sampler_pids': {str(e['seed']): e['pid'] for e in entries},
    'previous_snapshot_receipt': str(prior_path.relative_to(ROOT)),
    'previous_snapshot_receipt_sha256': hashlib.sha256(prior_path.read_bytes()).hexdigest(),
    'prepare_script_sha256': hashlib.sha256((HERE / 'prepare_snapshot.py').read_bytes()).hexdigest(),
    'growth_threshold_represented_steps': 2123, 'samplers_modified_or_restarted': False,
}
with (HERE / 'growth_wait_launch_receipt.json').open('x') as handle:
    handle.write(json.dumps(launch, indent=2) + '\n')
while True:
    for entry in entries:
        proc = Path('/proc', str(entry['pid']))
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        assert fields[0] != 'Z' and int(fields[19]) == owned[entry['seed']]['process_start_ticks']
        assert (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode() == owned[entry['seed']]['command']
        module = json.loads((ROOT / entry['run_dir'] / 'runtime_state.json').read_text())['module']
        assert module in (proc / 'maps').read_text()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    record = {'utc': datetime.now(timezone.utc).isoformat(), 'owned_sampler_identities_verified_live': True,
              'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    with (HERE / 'growth_wait_observations.jsonl').open('a') as handle:
        handle.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    if result.returncode == 0:
        with (HERE / 'growth_wait_completion.json').open('x') as handle:
            handle.write(json.dumps({'utc': record['utc'], 'exit_code': 0,
                                    'snapshot_frozen': True, 'samplers_modified_or_restarted': False}, indent=2) + '\n')
        break
    assert result.returncode == 3, result
    time.sleep(45)
