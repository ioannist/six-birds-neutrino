"""Replay every latest frozen cohort report with the repaired chain selection."""
from datetime import datetime,timezone
import hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
selected=[]
for group,root in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items():
 selected.append((group,Path(root),group+'_completion.json',group+'_diagnostics.json'))
for group,assessment in state['fresh_CAMB_production_assessments'].items():
 selected.append((group,Path(assessment['root']),'diagnostic_completion.json','diagnostics.json'))
assert len(selected)==9
records=[]
for group,root,completion,report in selected:
 command=json.loads((ROOT/root/completion).read_text())['command']
 output=HERE/(group+'_replayed_diagnostics.json')
 assert not output.exists()
 command[command.index('--output')+1]=str(output)
 with (HERE/(group+'_replay_stdout.txt')).open('x') as out,(HERE/(group+'_replay_stderr.txt')).open('x') as err:
  r=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=out,stderr=err)
 assert r.returncode==0,group
 original=ROOT/root/report
 assert json.loads(original.read_text())==json.loads(output.read_text()),group
 records.append({'group':group,'original':str(original.relative_to(ROOT)),'replayed':str(output.relative_to(ROOT)),'original_sha256':sha(original),'replayed_sha256':sha(output),'whole_report_equal':True,'exit_code':r.returncode})
 print(group,'whole report identical',flush=True)
with (HERE/'report_replay_receipt.json').open('x') as f:
 f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,'all_requested_reports_identical':True,'latest_reports_count':9,'reader_source_sha256':sha(ROOT/'scripts/extract_mnu_limits.py'),'physical_targets_or_diagnostic_gates_changed':False},indent=2)+'\n')
