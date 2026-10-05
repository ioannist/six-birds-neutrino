"""Execute native replay, diagnostics and snapshot verification sequentially."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKFLOW = ROOT / 'runs/20261005_math_review_CLASS_fresh_recovery_diagnostic_preparation_v2'
contract = json.loads((WORKFLOW / 'assessment_contract.json').read_text())
snapshot = json.loads((HERE / 'snapshot_receipt.json').read_text())
entry = contract['groups'][snapshot['group']][0]
env = dict(os.environ, PYTHONPATH=str(Path(entry['module']).parent.parent) + ':' + str(ROOT / 'src'),
           OMP_NUM_THREADS=entry['OMP_NUM_THREADS'], OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
for stage in ['verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py']:
    command = [sys.executable, str(WORKFLOW / stage), str(HERE)]
    with (HERE / (stage + '.stdout.txt')).open('x') as stdout, (HERE / (stage + '.stderr.txt')).open('x') as stderr:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
    with (HERE / (stage + '.completion.json')).open('x') as f:
        f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(), 'command':command, 'exit_code':result.returncode}, indent=2) + '\n')
    print(stage, 'exit', result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
