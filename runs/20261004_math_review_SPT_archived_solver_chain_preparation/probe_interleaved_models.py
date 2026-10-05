"""Test whether the one-state candidate survives another native model's calculation."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import yaml

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'src'))
from cobaya.model import get_model
import camb

version=importlib.metadata.version('camb')
assert version in ['1.6.5','2.0.4']
calls=[json.loads(s) for s in (HERE/'sampler_trajectory_trace/posterior_calls.jsonl').read_text().splitlines()]
config=yaml.safe_load((HERE/'sampler_trajectory_trace/input.yaml').read_text())
config={k:config[k] for k in ['theory','likelihood','params','packages_path']}
config['theory']['camb']['version']=version
records=[]
for cache_size in [1,0]:
    with get_model(config,stop_at_error=True) as main, get_model(config,stop_at_error=True) as other:
        main.theory['camb.transfers'].set_cache_size(cache_size)
        initial=[float(v) for v in main.logposterior(calls[0]['point'],cached=True).loglikes]
        intervening=[float(v) for v in other.logposterior(calls[1]['point'],cached=False).loglikes]
        cached=[float(v) for v in main.logposterior(calls[35]['point'],cached=True).loglikes]
        fresh=[float(v) for v in main.logposterior(calls[35]['point'],cached=False).loglikes]
        r={'cache_size':cache_size,'initial_main_loglikes':initial,'intervening_other_loglikes':intervening,
           'return_main_loglikes':cached,'fresh_main_loglikes':fresh,
           'cached_minus_fresh_chi2':[-2*(a-b) for a,b in zip(cached,fresh)]}
        records.append(r)
        print(version,'interleaved',cache_size,r['cached_minus_fresh_chi2'],flush=True)
native=Path(camb.baseconfig.camblib._name).resolve()
out={'utc':datetime.now(timezone.utc).isoformat(),'CAMB_version':version,
     'Cobaya_version':importlib.metadata.version('cobaya'),'records':records,
     'native_path':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
     'scope':'private two-model history control; no production or inference sampler changes'}
with (HERE/('interleaved_models_'+version+'_receipt.json')).open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
