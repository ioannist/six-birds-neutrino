"""Verify all remaining inference identities after retiring old CAMB cache policy."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
old={r['seed']:r for r in json.loads((ROOT/'runs/20261004_math_review_fresh_CAMB_posterior_preparation/final_runtime_verification.json').read_text())['records']}
entries=[]
for key in ['guarded_solver_posterior_trials','guarded_quadrature_posterior_chains',
            'guarded_medium_posterior_chains','guarded_grid12_posterior_trials']:
    entries+=state[key]
records=[]
for e in entries+state['fresh_CAMB_posterior_chains']:
    seed=e['seed'];pid=e['pid'];proc=Path('/proc',str(pid))
    prior=e if seed>=1700 else old[seed]
    stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
    assert stat[0]!='Z' and int(stat[19])==prior['process_start_ticks']
    command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode()
    assert command==prior['command']
    module=e['module'] if seed>=1700 else prior['module']
    assert module in (proc/'maps').read_text() and sha(module)==e['native_module_sha256']
    run=ROOT/e['run_dir'];assert not (run/'stderr.txt').read_bytes()
    if seed>=1700:
        assert not (ROOT/f'runs/20261004_math_review_fresh_CAMB_posterior_preparation/seed{seed}/launcher_stderr.txt').read_bytes()
        assert sha(ROOT/e['config'])==e['config_sha256'] and sha(run/'resolved.yaml')==e['effective_config_sha256']
    progress=re.findall(r'Progress @ ([^\n]+) : (\d+) steps taken, and (\d+) accepted',(run/'stdout.txt').read_text())
    record={'seed':seed,'pid':pid,'process_start_ticks':prior['process_start_ticks'],'command':command,
            'module':module,'module_sha256':sha(module),'status':'live_same_owned_native_identity'}
    if progress:
        utc,steps,accepted=progress[-1];record['latest_progress']={'utc':utc,'steps':int(steps),'accepted':int(accepted)}
    records.append(record)
assert len(records)==len({r['pid'] for r in records})==40
retired=json.loads((ROOT/'runs/20261004_math_review_fresh_CAMB_posterior_preparation/old_policy_retirement_receipt.json').read_text())
identity_path = ROOT / 'runs/20261004_math_review_fresh_CAMB_posterior_preparation/runtime_before_preparation.json'
assert sha(identity_path) == 'd066a446fc5d25fb6cb6418071cb62a174649f3ab0cd6e9ca2cd9e2183f6d5ce'
identity_baseline = {r['seed']: r for r in json.loads(identity_path.read_text())['records']}
helper_path = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
assert sha(helper_path) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
import importlib.util
identity_spec = importlib.util.spec_from_file_location('review_retirement_identity', helper_path)
identity_module = importlib.util.module_from_spec(identity_spec)
identity_spec.loader.exec_module(identity_module)
retired_identity_observations = []
for retired_record in retired['records']:
    baseline = identity_baseline[retired_record['seed']]
    assert baseline['pid'] == retired_record['pid']
    if 'process_start_ticks' in retired_record:
        assert baseline['process_start_ticks'] == retired_record['process_start_ticks']
    retired_observation = identity_module.observe_retired_identity(retired_record['pid'], baseline['process_start_ticks'])
    assert retired_observation['original_identity_absent'], 'Original retired process identity remains present.'
    retired_identity_observations.append({'seed': retired_record['seed'], **retired_observation})
assert len(retired_identity_observations) == len({r['seed'] for r in retired_identity_observations}) == 16
with (HERE/'runtime_observation.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,'owned_live_samplers':40,
        'fresh_CAMB_SPT_live':20,'guarded_CLASS_live':20,'old_policy_CAMB_SPT_live':0,
        'all_16_old_policy_process_identities_absent':True, 'retired_identity_observations':retired_identity_observations,'posterior_convergence_certified':False},indent=2,allow_nan=False)+'\n')
print('40 inference samplers live with verified native identities: 20 fresh CAMB and 20 guarded CLASS.')
