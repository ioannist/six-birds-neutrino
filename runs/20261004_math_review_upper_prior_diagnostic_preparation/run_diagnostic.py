"""Run declared gates only after the frozen target's selected native checks pass."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('snapshot',type=Path);args=parser.parse_args()
out=args.snapshot.resolve();receipt=json.loads((out/'snapshot_receipt.json').read_text())
native=json.loads((out/'native_rows_verification.json').read_text())
assert native['group']==receipt['group'] and len(native['records'])==4
assert all(len(r['checks'])==3 for r in native['records'])
contract=json.loads((HERE/'assessment_contract.json').read_text())
assert hashlib.sha256((HERE/'assessment_contract.json').read_bytes()).hexdigest()==receipt['contract_sha256']
for path,digest in contract['diagnostic_source_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
with (out/'diagnostic_stdout.txt').open('x') as stdout,(out/'diagnostic_stderr.txt').open('x') as stderr:
    result=subprocess.run(receipt['diagnostic_command'],cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=stdout,stderr=stderr)
with (out/'diagnostic_completion.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'command':receipt['diagnostic_command'],
        'exit_code':result.returncode},indent=2)+'\n')
raise SystemExit(result.returncode)
