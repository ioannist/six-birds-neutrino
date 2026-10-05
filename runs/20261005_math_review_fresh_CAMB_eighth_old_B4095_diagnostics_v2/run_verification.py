"""Execute native replay, diagnostics and snapshot verification sequentially."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKFLOW = ROOT / 'runs/20261004_math_review_fresh_CAMB_weighted_summary_diagnostic_preparation'
env = dict(os.environ, PYTHONPATH='/mnt/8tb/six-birds-ml/tmp/neutrino_spt_archived_solver_control_20261004/packages:' + str(ROOT / 'src'), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
for stage in ['verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py']:
    command = [sys.executable, str(WORKFLOW / stage), str(HERE)]
    with (HERE / (stage + '.stdout.txt')).open('x') as stdout, (HERE / (stage + '.stderr.txt')).open('x') as stderr:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
    with (HERE / (stage + '.completion.json')).open('x') as f:
        f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(), 'command':command, 'exit_code':result.returncode}, indent=2) + '\n')
    print(stage, 'exit', result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
