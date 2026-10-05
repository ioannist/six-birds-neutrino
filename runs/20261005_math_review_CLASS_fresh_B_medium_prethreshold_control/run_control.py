"""Preserve real stage return codes for one separately frozen control target."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
group = sys.argv[1]
out = HERE / group
contract = json.loads((HERE / 'assessment_contract.json').read_text())
entry = contract['groups'][group][0]
env = dict(os.environ, OMP_NUM_THREADS=entry['OMP_NUM_THREADS'],
           OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
           PYTHONPATH=str(Path(entry['module']).parent.parent) + ':' + str(HERE.parents[1] / 'src'))
records = []
for name in ['verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py']:
    command = [sys.executable, str(HERE / name), str(out)]
    with (out / (name + '.stdout.txt')).open('x') as stdout, (out / (name + '.stderr.txt')).open('x') as stderr:
        result = subprocess.run(command, env=env, stdout=stdout, stderr=stderr)
    record = {'utc': datetime.now(timezone.utc).isoformat(), 'command': command,
              'actual_terminal_exit_code': result.returncode}
    with (out / (name + '.completion.json')).open('x') as f:
        json.dump(record, f, indent=2)
        f.write('\n')
    records.append(record)
    print(group, name, 'exit', result.returncode, flush=True)
    if result.returncode:
        break
with (out / 'execution_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
        'all_control_workers_terminal': True, 'production_assessments_completed': 0}, f, indent=2)
    f.write('\n')
sys.exit(0 if len(records) == 3 and all(r['actual_terminal_exit_code'] == 0 for r in records) else 1)
