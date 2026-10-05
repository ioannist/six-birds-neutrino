"""Evaluate selected native boundary points and reject a below-gate control."""
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_cobaya import _validate_classy_backend
from cobaya.model import get_model

PARENT = HERE.parent/'20261004_math_review_guarded_medium_fine_mass_response'
parent_receipt = json.loads((PARENT/'completion_verification.json').read_text())
for file in parent_receipt['files']:
    assert hashlib.sha256((ROOT/file['path']).read_bytes()).hexdigest()==file['sha256']
module = Path(importlib.import_module('classy._classy').__file__).resolve()
runtime={'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'status':'running_selected_native_gate_checks',
         'module':str(module),'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),
         'omp_threads':os.environ['OMP_NUM_THREADS']}
(HERE/'runtime_state.json').write_text(json.dumps(runtime,indent=2)+'\n')
records=[]
for lens in ['A','B']:
    source = PARENT/lens/'evaluation/baseline.yaml'
    cfg = yaml.safe_load(source.read_text())
    point = json.loads((PARENT/lens/'points.json').read_text())['quad_q50']
    point = dict(point,mnu_sample=0.)
    assert cfg['params']['mnu_sample']['prior']=={'min':0.,'max':5.}
    assert _validate_classy_backend(cfg)['module_sha256']==runtime['module_sha256']
    (HERE/f'input_{lens}.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    with get_model(cfg,stop_at_error=True) as model:
        assert set(point)==set(model.parameterization.sampled_params())
        start=time.monotonic()
        fresh=model.logposterior(point,cached=False)
        assert np.isfinite(fresh.logpost) and np.all(np.isfinite(fresh.logpriors))
        assert len(fresh.loglikes)==6 and np.all(np.isfinite(fresh.loglikes))
        pars=model.theory['classy'].classy.pars
        masses=[float(v) for v in str(pars['m_ncdm']).split(',')]
        assert masses==[0.,0.,0.] and pars['N_ncdm']==3
        derived=dict(zip(model.parameterization.derived_params(),fresh.derived))
        assert derived['mnu']==0.
        cl=model.provider.get_Cl(ell_factor=False,units='muK2')
        assert all(np.all(np.isfinite(cl[k])) for k in ['tt','te','ee','pp'])
        negative=dict(point,mnu_sample=-.001)
        rejected=model.logposterior(negative,cached=False)
        assert rejected.logpost == -np.inf and not len(rejected.loglikes)
        records.append({'lens':lens,'point':point,'derived_mnu':0.,'actual_native_m_ncdm':str(pars['m_ncdm']),
                        'actual_native_N_ncdm':pars['N_ncdm'],'native_chi2':{n:-2*float(v) for n,v in zip(model.likelihood,fresh.loglikes)},
                        'minuslogprior':-float(sum(fresh.logpriors)),'minuslogposterior':-float(fresh.logpost),
                        'negative_mass_control':{'mnu_sample':-.001,'prior_rejected_before_likelihood':True},
                        'elapsed_seconds':time.monotonic()-start,'source_config':str(source.relative_to(ROOT)),
                        'source_config_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    (HERE/'progress.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
    print(lens,'native zero-mass gate point finite; negative-mass control rejected before likelihood',flush=True)
(HERE/'metrics.json').write_text(json.dumps({'scope':'two_selected_native_zero_mass_points_and_below_gate_controls',
    'records':records,'boundary_mode_established':False,'posterior_convergence_certified':False,
    'uniform_numerical_accuracy_certified':False,'paper_modified':False},indent=2,allow_nan=False)+'\n')
runtime['status']='complete_selected_native_gate_checks_not_mode_certificate'
(HERE/'runtime_state.json').write_text(json.dumps(runtime,indent=2)+'\n')
