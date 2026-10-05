"""Exercise native replay, diagnostics and self-review on one control snapshot."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
group = sys.argv[1]
assert group in json.loads((HERE / 'assessment_contract.json').read_text())['groups']
out = HERE / group
for stage in ['verify_native_rows.py', 'run_diagnostic.py', 'verify_snapshot.py']:
    command = [sys.executable, str(HERE / stage), str(out)]
    with (out / (stage + '.stdout.txt')).open('x') as stdout, (out / (stage + '.stderr.txt')).open('x') as stderr:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr)
    with (out / (stage + '.completion.json')).open('x') as f:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'command': command,
                   'actual_exit_code': result.returncode}, f, indent=2)
        f.write('\n')
    print(stage, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
