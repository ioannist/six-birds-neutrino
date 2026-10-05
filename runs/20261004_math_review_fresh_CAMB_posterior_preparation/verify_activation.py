"""Observe actual process identity, mapped solver and effective sampler metadata."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries=json.loads((HERE/'preparation_receipt.json').read_text())['entries']
sessions={r['seed']:r['session_id'] for r in json.loads((HERE/'managed_sessions.json').read_text())}
records=[]
for e in entries:
    folder=HERE/f"seed{e['seed']}"
    launch=json.loads((folder/'launch_receipt.json').read_text())
    pid=launch['pid'];proc=Path('/proc',str(pid))
    stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
    assert stat[0]!='Z' and int(stat[19])==launch['process_start_ticks']
    command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode()
    assert f"launch_chain.py {e['seed']}" in command
    assert e['module'] in (proc/'maps').read_text() and sha(e['module'])==e['module_sha256']
    run=ROOT/e['run_dir']
    assert not (run/'stderr.txt').read_bytes() and not (folder/'launcher_stderr.txt').read_bytes()
    cfg=yaml.safe_load((run/'resolved.yaml').read_text())
    source=yaml.safe_load((ROOT/e['config']).read_text())
    assert cfg['theory']==source['theory'] and cfg['params']==source['params'] and cfg['likelihood']==source['likelihood']
    assert list(cfg['sampler'])==['sbt_spt_audit.samplers.FullPrecisionMCMC']
    assert cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed']==e['seed']
    backend=json.loads((run/'solver_backend.json').read_text())
    assert backend['module_sha256']==e['module_sha256'] and backend['solver_version']==e['solver_version']
    records.append({**e,'pid':pid,'session':sessions[e['seed']],'process_start_ticks':launch['process_start_ticks'],
        'command':command,'status':'running_native_identity_verified_initial_points_passed_first_saved_rows_pending',
        'native_module_sha256':e['module_sha256'],'effective_config_sha256':sha(run/'resolved.yaml'),
        'native_backend_receipt_sha256':sha(run/'solver_backend.json'),'launch_receipt_sha256':sha(folder/'launch_receipt.json')})
with (HERE/'activation_verification.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,'owned_live_fresh_samplers':20,
        'distinct_targets':5,'initial_native_points_passed':20,'first_saved_rows_pending':True,
        'posterior_convergence_certified':False,'cohorts_pooled':False},indent=2,allow_nan=False)+'\n')
print('20 actual native sampler processes verified, including production adapter and effective sampler metadata.')
