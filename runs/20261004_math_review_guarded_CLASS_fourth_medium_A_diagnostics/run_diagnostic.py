"""Execute a declared diagnostic command and preserve its process result."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / "snapshot_receipt.json").read_text())
group = sys.argv[1]
command = receipt["diagnostic_commands"][group]
assert receipt["diagnostic_script_sha256"] == hashlib.sha256(
    (ROOT / "scripts/diagnose_cobaya_chains.py").read_bytes()).hexdigest()
assert not (HERE / (group + "_completion.json")).exists()
environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
                   OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
with (HERE / (group + "_diagnostic_stdout.txt")).open("w") as output:
    result = subprocess.run(command, cwd=ROOT, env=environment,
                            stdout=output, stderr=subprocess.STDOUT)
(HERE / (group + "_completion.json")).write_text(json.dumps({
    "utc": datetime.now(timezone.utc).isoformat(), "command": command,
    "exit_code": result.returncode,
}, indent=2) + "\n")
sys.exit(result.returncode)
