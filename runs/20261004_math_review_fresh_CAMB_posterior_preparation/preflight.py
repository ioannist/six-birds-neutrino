"""Check exact native identity and selected likelihoods before inference."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
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
import cobaya.theories.camb.camb as wrapper
from cobaya.model import get_model
from sbt_spt_audit.boltzmann import FreshCAMB,FRESH_CAMB_CLASS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('group');args=parser.parse_args()
entries=[e for e in json.loads((HERE/'preparation_receipt.json').read_text())['entries'] if e['group']==args.group]
assert len(entries)==4
e0=entries[0]
assert importlib.metadata.version('camb')==e0['solver_version']
assert importlib.metadata.version('cobaya')==e0['Cobaya_version']
module=Path(camb.baseconfig.camblib._name).resolve()
assert str(module)==e0['module'] and sha(module)==e0['module_sha256']
assert str(Path(wrapper.__file__).resolve())==e0['wrapper'] and sha(wrapper.__file__)==e0['wrapper_sha256']
base=yaml.safe_load((ROOT/e0['config']).read_text())
control=json.loads((ROOT/e0['control']).read_text())['records'][e0['style']]
for e in entries:
    cfg=yaml.safe_load((ROOT/e['config']).read_text())
    assert sha(ROOT/e['config'])==e['config_sha256'] and sha(ROOT/e['control'])==e['control_sha256']
    assert {k:cfg[k] for k in ['theory','likelihood']}=={k:base[k] for k in ['theory','likelihood']}
    assert e['initial_point']=={n:cfg['params'][n]['ref'] for n in e['initial_point']}
    for name,b in base['params'].items():
        assert {k:v for k,v in b.items() if k!='ref'}=={k:v for k,v in cfg['params'][name].items() if k!='ref'}
    assert sha(ROOT/e['proposal']['path'])==e['proposal']['sha256']
    for path,digest in e['implementation_sha256'].items(): assert sha(ROOT/path)==digest
model_cfg={k:deepcopy(base[k]) for k in ['theory','likelihood','params','packages_path']}
# Independent upstream forced-fresh comparator for this exact numerical recipe.
upstream=deepcopy(model_cfg);upstream['theory']['camb'].pop('class')
with get_model(model_cfg,stop_at_error=True) as model, get_model(upstream,stop_at_error=True) as reference:
    assert isinstance(model.theory['camb'],FreshCAMB)
    assert model.theory['camb'].extra_args==reference.theory['camb'].extra_args==control['effective_CAMB_extra_args']
    model.set_cache_size(50)
    for e in entries:
        point=e['initial_point']
        actual=model.logposterior(point,cached=True)
        expected=reference.logposterior(point,cached=False)
        assert np.array_equal(actual.loglikes,expected.loglikes) and actual.logpriors==expected.logpriors
        chi={n:-2*float(v) for n,v in zip(model.likelihood,actual.loglikes)}
        previous=control['evaluations'][e['initial_point_label']]
        delta={n:chi[n]-previous['chi2_components'][n] for n in chi}
        assert np.isfinite(list(chi.values())+list(actual.logpriors)).all()
        assert list(actual.logpriors)==previous['logpriors'] and max(abs(v) for v in delta.values())<=1e-9
        proof={'utc':datetime.now(timezone.utc).isoformat(),'seed':e['seed'],'group':e['group'],
            'initial_point':point,'config_sha256':e['config_sha256'],'module_sha256':sha(module),
            'native_initial_point_verified':True,'chi2_components':chi,'logpriors':list(actual.logpriors),
            'logposterior':float(actual.logpost),'control_component_differences':delta,
            'selected_replay_tolerance':1e-9,'upstream_forced_fresh_likes_and_priors_exact':True,
            'FreshCAMB_class':FRESH_CAMB_CLASS,'sampler_cache_resize_challenge':50,
            'effective_CAMB_extra_args':model.theory['camb'].extra_args,'posterior_certified':False}
        with (HERE/f"seed{e['seed']}"/'initial_point_verification.json').open('x') as f:
            f.write(json.dumps(proof,indent=2,allow_nan=False)+'\n')
        print(e['seed'],'preflight exact to independent forced-fresh comparator; control deltas',delta,flush=True)
