"""Record an isolated one-row sampler trajectory to diagnose native reproduction."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
import camb
from cobaya.model import Model
from cobaya.run import run

entry=json.loads((HERE/'seed1604/preparation_receipt.json').read_text())
assert importlib.metadata.version('camb')=='1.6.5' and importlib.metadata.version('cobaya')=='3.6.1'
module=Path(camb.baseconfig.camblib._name).resolve()
assert str(module)==entry['module'] and hashlib.sha256(module.read_bytes()).hexdigest()==entry['module_sha256']
out=HERE/'sampler_trajectory_trace';out.mkdir()
cfg=yaml.safe_load((ROOT/entry['config']).read_text())
options=deepcopy(cfg['sampler']['mcmc']);options['max_samples']=1
cfg['sampler']={'sbt_spt_audit.samplers.FullPrecisionMCMC':options}
cfg['output']=str(out/'chains'/'trace_seed1604')
cfg['notes']['diagnostic_scope']='Isolated finite sampler-state trace, excluded from posterior evidence.'
(out/'input.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
(HERE/'sampler_trace_launch_receipt.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
    'pid':os.getpid(),'process_start_ticks':int(stat[19]),'module':str(module),'module_sha256':entry['module_sha256'],
    'seed':1604,'max_samples':1,'isolated_output':str(out.relative_to(ROOT)),
    'scientific_samplers_modified':False,'count_as_inference_chain':False},indent=2)+'\n')
original=Model.logposterior
counter=0
def scalar(v):
    f=float(v)
    return f if math.isfinite(f) else None
def traced(self,params_values,*args,**kwargs):
    global counter
    result=original(self,params_values,*args,**kwargs)
    values=dict(params_values) if isinstance(params_values,dict) else dict(zip(self.parameterization.sampled_params(),params_values))
    record={'call':counter,'point':{n:scalar(v) for n,v in values.items()},
        'logposterior':scalar(result.logpost),'loglikes':None if result.loglikes is None else [scalar(v) for v in result.loglikes],
        'likelihood_names':list(self.likelihood),'cached_kwarg':kwargs.get('cached','default'),
        'return_derived_kwarg':kwargs.get('return_derived','default')}
    with (out/'posterior_calls.jsonl').open('a') as handle:
        handle.write(json.dumps(record,allow_nan=False)+'\n')
    counter+=1
    return result
Model.logposterior=traced
run(cfg,no_mpi=True,stop_at_error=True)
(HERE/'sampler_trace_completion.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
    'posterior_calls_traced':counter,'scope':'one_row_sampler_state_probe_not_posterior_evidence'},indent=2)+'\n')
