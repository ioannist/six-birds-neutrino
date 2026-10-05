"""Recompute the latest four frozen CLASS reports without modifying originals."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cohorts=[('quad_A','20261004_math_review_guarded_CLASS_fifth_quad_A_diagnostics'),
         ('quad_B','20261004_math_review_guarded_CLASS_sixth_quad_B_diagnostics'),
         ('medium_A','20261004_math_review_guarded_CLASS_fifth_medium_A_diagnostics'),
         ('medium_B','20261004_math_review_guarded_CLASS_fifth_medium_B_diagnostics')]
records=[]
for group,name in cohorts:
    source=ROOT/'runs'/name
    receipt=json.loads((source/'snapshot_receipt.json').read_text())
    command=list(receipt['diagnostic_commands'][group])
    original=Path(command[command.index('--output')+1]);assert original.is_relative_to(source)
    output=HERE/f'replayed_{group}_diagnostics.json';assert not output.exists()
    command[command.index('--output')+1]=str(output)
    with (HERE/f'replayed_{group}_stdout.txt').open('x') as stdout,(HERE/f'replayed_{group}_stderr.txt').open('x') as stderr:
        completed=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),
            OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=stdout,stderr=stderr)
    assert completed.returncode==0
    expected=json.loads(original.read_text());actual=json.loads(output.read_text())
    assert actual==expected
    records.append({'group':group,'original_report':str(original.relative_to(ROOT)),
        'original_sha256':sha(original),'replayed_report':str(output.relative_to(ROOT)),
        'replayed_sha256':sha(output),'reports_exactly_equal':True,'exit_code':0})
    print(group,'entire report unchanged',flush=True)
with (HERE/'latest_CLASS_replay_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,
        'all_four_latest_CLASS_reports_unchanged':True,'old_reports_overwritten':False,
        'native_models_and_diagnostic_algorithms_unchanged':True,'posterior_convergence_certified':False},indent=2,allow_nan=False)+'\n')
