"""Preserve proposal-learning evidence without claiming an atomic sampler state."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import yaml
from sbt_spt_audit.metrics import covariance_solve

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
runtime = json.loads((HERE/'runtime_observation.json').read_text())
owned = {r['seed']:r for r in runtime['records']}
records = []
for entry in state['guarded_quadrature_posterior_chains']:
    source = ROOT/entry['run_dir']
    cfg = yaml.safe_load((source/'resolved.yaml').read_text())
    options = cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
    prefix = Path(cfg['output'])
    initial = Path(options['covmat'])
    launch = json.loads((source/'runtime_state.json').read_text())
    assert hashlib.sha256(initial.read_bytes()).hexdigest()==launch['covariance_sha256']
    destination = HERE/f"seed{entry['seed']}"
    destination.mkdir()
    files = []
    for path, name in [(initial,'initial.covmat'),(prefix.with_suffix('.covmat'),'current.covmat'),
                       (prefix.with_suffix('.updated.yaml'),'updated.yaml'),
                       (source/'runtime_state.json','launch_runtime_state.json'),
                       (source/'resolved.yaml','resolved.yaml'),(source/'stdout.txt','stdout_prefix.txt')]:
        raw = path.read_bytes()
        if name=='stdout_prefix.txt':
            raw = raw[:raw.rfind(b'\n')+1]
        (destination/name).write_bytes(raw)
        files.append({'source':str(path),'snapshot':str((destination/name).relative_to(ROOT)),
                      'sha256':hashlib.sha256(raw).hexdigest(),'utc':datetime.now(timezone.utc).isoformat()})
    log = (destination/'stdout_prefix.txt').read_text()
    tests = re.findall(r'Convergence of means: R-1 = ([\d.eE+-]+) after (\d+) accepted steps',log)
    assert tests
    update_count = log.count('Updated covariance matrix of proposal pdf.')
    current = np.atleast_2d(np.loadtxt(destination/'current.covmat'))
    old = np.atleast_2d(np.loadtxt(destination/'initial.covmat'))
    assert current.shape==old.shape
    covariance_solve(current,np.zeros(len(current)))
    changed = not np.allclose(current,old,rtol=5e-15,atol=1e-20)
    assert changed == (update_count>0)
    updated = yaml.safe_load((destination/'updated.yaml').read_text())['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
    assert updated['Rminus1_stop']==.01 and updated['Rminus1_cl_stop']==.05
    assert updated['learn_proposal_Rminus1_max']==2.
    assert owned[entry['seed']]['status']=='live_same_owned_identity'
    records.append({'seed':entry['seed'],'proposal_updates_in_log_snapshot':update_count,
                    'last_internal_mean_Rminus1':float(tests[-1][0]),'accepted_steps_at_last_internal_check':int(tests[-1][1]),
                    'current_covariance_changed_from_initial':changed,'current_covariance_finite_SPD':True,
                    'Rminus1_stop':.01,'Rminus1_cl_stop':.05,'learn_proposal_Rminus1_max':2.,'files':files})
assert len(records)==8
result={'utc':datetime.now(timezone.utc).isoformat(),'scope':'guarded_quadrature_internal_proposal_learning_progress_only',
        'files_individually_frozen_not_an_atomic_sampler_state':True,'records':records,
        'families_with_updates':sum(r['proposal_updates_in_log_snapshot']>0 for r in records),
        'sampler_rules_changed':False,'posterior_convergence_certified':False,
        'module_changed':False,'paper_modified':False}
(HERE/'learning_receipt.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(f"{result['families_with_updates']} of eight guarded quadrature families have learned new finite SPD proposals.")
