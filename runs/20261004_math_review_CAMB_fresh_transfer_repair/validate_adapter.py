"""Compare the production adapter against upstream forced-fresh targets."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cobaya.model import get_model
from sbt_spt_audit.boltzmann import FreshCAMB,FreshCAMBTransfers,configure_fresh_camb_transfers
import camb

version=importlib.metadata.version('camb')
assert version in ['1.6.5','2.0.4']
prep=ROOT/'runs/20261004_math_review_SPT_archived_solver_chain_preparation'
trace=prep/'sampler_trajectory_trace/posterior_calls.jsonl'
calls=[json.loads(s) for s in trace.read_text().splitlines()]
def values(post):
    finite=lambda v:float(v) if math.isfinite(v) else None
    return {'loglikes':[finite(v) for v in post.loglikes],
            'logpriors':[finite(v) for v in post.logpriors],'logpost':finite(post.logpost)}

records=[]
interleaved=[]
configs=[]
for lens,seed in [('A',1604),('B',1608)]:
    source=prep/('seed'+str(seed))/'input.yaml'
    cfg=yaml.safe_load(source.read_text())
    cfg={k:cfg[k] for k in ['theory','likelihood','params','packages_path']}
    cfg['theory']['camb']['version']=version
    reference=deepcopy(cfg)
    configure_fresh_camb_transfers(cfg)
    reverted=deepcopy(cfg);reverted['theory']['camb'].pop('class')
    assert reverted==reference
    candidate=[]
    with get_model(cfg,stop_at_error=True) as model:
        assert isinstance(model.theory['camb'],FreshCAMB)
        helper=model.theory['camb.transfers']
        assert isinstance(helper,FreshCAMBTransfers)
        model.set_cache_size(50)  # Sampler-style resizing must preserve fresh handling.
        for call in calls:
            candidate.append(values(model.logposterior(call['point'],cached=True)))
            print(version,lens,'adapter history',call['call'],flush=True)
    baseline=[]
    with get_model(reference,stop_at_error=True) as model:
        for call in calls:
            baseline.append(values(model.logposterior(call['point'],cached=False)))
            print(version,lens,'upstream fresh',call['call'],flush=True)
    for call,a,b in zip(calls,candidate,baseline):
        records.append({'lens':lens,'call':call['call'],'point':call['point'],
                        'adapter_cached':a,'upstream_forced_fresh':b,'exactly_equal':a==b})
    with get_model(cfg,stop_at_error=True) as main,get_model(reference,stop_at_error=True) as other:
        main.logposterior(calls[0]['point'],cached=True)
        other.logposterior(calls[1]['point'],cached=False)
        result=values(main.logposterior(calls[35]['point'],cached=True))
        cls={k:np.asarray(v).copy() for k,v in main.provider.get_Cl(ell_factor=True).items()}
        fresh=values(main.logposterior(calls[35]['point'],cached=False))
        fresh_cls=main.provider.get_Cl(ell_factor=True)
        interleaved.append({'lens':lens,'adapter_return':result,'adapter_forced_fresh':fresh,
                            'posterior_results_exactly_equal':result==fresh,
                            'spectra_exactly_equal':all(np.array_equal(v,fresh_cls[k]) for k,v in cls.items())})
    configs.append({'lens':lens,'source':str(source.relative_to(ROOT)),
                    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'adapter_config':cfg,'reference_config':reference})
native=Path(camb.baseconfig.camblib._name).resolve()
out={'utc':datetime.now(timezone.utc).isoformat(),'CAMB_version':version,
     'Cobaya_version':importlib.metadata.version('cobaya'),'records':records,'interleaved':interleaved,
     'all74_selected_results_exact':all(r['exactly_equal'] for r in records),'configs':configs,
     'trace_sha256':hashlib.sha256(trace.read_bytes()).hexdigest(),'native_path':str(native),
     'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
     'production_adapter_sha256':hashlib.sha256((ROOT/'src/sbt_spt_audit/boltzmann.py').read_bytes()).hexdigest(),
     'scope':'both SPT recipes, 37 selected points each, sampled priors and components; not uniform accuracy or posterior qualification'}
with (HERE/('adapter_'+version+'_receipt.json')).open('x') as h:
    h.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(version,'all74 exact',out['all74_selected_results_exact'],'interleaving',interleaved,flush=True)
