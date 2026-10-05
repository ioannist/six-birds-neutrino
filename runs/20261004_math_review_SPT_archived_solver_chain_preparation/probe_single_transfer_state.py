"""Compare ordinary and one-state transfer caching after intervening cosmologies."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'src'))
from cobaya.model import get_model
import camb

version = importlib.metadata.version('camb')
assert version in ('1.6.5', '2.0.4')
calls = [json.loads(s) for s in (HERE/'sampler_trajectory_trace/posterior_calls.jsonl').read_text().splitlines()]
config = yaml.safe_load((HERE/'sampler_trajectory_trace/input.yaml').read_text())
config = {k: config[k] for k in ['theory','likelihood','params','packages_path']}
config['theory']['camb']['version'] = version
records = []
for size in [3, 1]:
    for name, indices in [('slow_return',[0,1,35]), ('late_window',[0,32,33,34,35])]:
        with get_model(config, stop_at_error=True) as model:
            helper = model.theory['camb.transfers']
            helper.set_cache_size(size)
            values = []
            for index in indices:
                post = model.logposterior(calls[index]['point'], cached=True)
                values.append({'call':index,'loglikes':[float(v) for v in post.loglikes]})
            fresh = [float(v) for v in model.logposterior(calls[35]['point'], cached=False).loglikes]
            record = {'case':name,'transfer_cache_size':size,'values':values,
                      'fresh_loglikes':fresh,
                      'cached_minus_fresh_chi2':[-2*(a-b) for a,b in zip(values[-1]['loglikes'],fresh)]}
            records.append(record)
            print(version, size, name, record['cached_minus_fresh_chi2'], flush=True)
native = Path(camb.baseconfig.camblib._name).resolve()
out = {'utc':datetime.now(timezone.utc).isoformat(),'CAMB_version':version,
       'Cobaya_version':importlib.metadata.version('cobaya'),'records':records,
       'native_path':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
       'scope':'private selected-point cache control; no production or live sampler changes'}
with (HERE/('single_transfer_state_'+version+'_receipt.json')).open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
