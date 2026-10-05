"""Verify each prepared target at its exact proposed initial point."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
import camb
import cobaya
from cobaya.model import get_model

parser=argparse.ArgumentParser();parser.add_argument('target',choices=['A','B']);args=parser.parse_args()
entries=[e for e in json.loads((HERE/'preparation_receipt.json').read_text())['entries'] if e['lens']==args.target]
assert importlib.metadata.version('camb')=='1.6.5' and importlib.metadata.version('cobaya')=='3.6.1'
module=Path(camb.baseconfig.camblib._name).resolve()
assert str(module)==entries[0]['module']
assert hashlib.sha256(module.read_bytes()).hexdigest()==entries[0]['module_sha256']
base=yaml.safe_load((ROOT/entries[0]['config']).read_text())
signature={k:base[k] for k in ['theory','likelihood']}
for e in entries:
    cfg=yaml.safe_load((ROOT/e['config']).read_text())
    assert signature=={k:cfg[k] for k in signature}
    for name,b in base['params'].items():
        assert {k:v for k,v in b.items() if k!='ref'}=={k:v for k,v in cfg['params'][name].items() if k!='ref'}
    assert e['initial_point']=={n:cfg['params'][n]['ref'] for n in e['initial_point']}
    assert hashlib.sha256((ROOT/e['config']).read_bytes()).hexdigest()==e['config_sha256']
model_cfg={k:base[k] for k in ['theory','likelihood','params','packages_path']}
CONTROL=ROOT/'runs/20261004_math_review_SPT_archived_solver_version_control'
native_control=json.loads((CONTROL/args.target/'evaluation_receipt.json').read_text())['records']['original_style']
with get_model(model_cfg,stop_at_error=True) as model:
    assert model.theory['camb'].extra_args==native_control['effective_CAMB_extra_args']
    for e in entries:
        point=e['initial_point']
        likes={n:float(v) for n,v in model.loglikes(point,as_dict=True,return_derived=False,cached=False).items()}
        prior=[float(v) for v in model.logpriors(point)]
        chi={n:-2*v for n,v in likes.items()}
        assert np.all(np.isfinite(list(chi.values())+prior))
        expected=native_control['evaluations'][e['initial_point_label']]
        assert chi==expected['chi2_components'] and prior==expected['logpriors']
        receipt={'utc':datetime.now(timezone.utc).isoformat(),'seed':e['seed'],'initial_point':point,
            'config_sha256':e['config_sha256'],'module_sha256':e['module_sha256'],
            'native_initial_point_verified':True,'chi2_components':chi,'logpriors':prior,
            'logposterior':sum(likes.values())+sum(prior),'archived_control_all_components_reproduced_exactly':True,
            'requested_effective_lmax':model.theory['camb'].extra_args['lmax'],
            'scientific_target_or_priors_changed_from_preparation':False,'historical_identity_or_convergence_certified':False}
        with (HERE/('seed'+str(e['seed']))/'initial_point_verification.json').open('x') as handle:
            handle.write(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
        print(e['seed'],'initial native point verified',flush=True)
