"""Run the exact diagnostic command registered by the frozen snapshot."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
receipt=json.loads((HERE/'snapshot_receipt.json').read_text())
for group,command in receipt['diagnostic_commands'].items():
    with (HERE/(group+'_stdout.txt')).open('x') as stdout,(HERE/(group+'_stderr.txt')).open('x') as stderr:
        result=subprocess.run(command,stdout=stdout,stderr=stderr,check=False)
    with (HERE/(group+'_completion.json')).open('x') as handle:
        handle.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'command':command,'exit_code':result.returncode},indent=2)+'\n')
    if result.returncode: raise SystemExit(result.returncode)
    print(group,'diagnostic exit0',flush=True)
