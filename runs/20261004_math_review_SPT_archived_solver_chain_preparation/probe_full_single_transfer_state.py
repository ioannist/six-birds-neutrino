"""Replay the full traced history with one-state transfer caching, then fresh points."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'src'))
from cobaya.model import get_model
import camb

version = importlib.metadata.version('camb')
assert version in ['1.6.5','2.0.4']
calls_path = HERE/'sampler_trajectory_trace/posterior_calls.jsonl'
calls = [json.loads(s) for s in calls_path.read_text().splitlines()]
config = yaml.safe_load((HERE/'sampler_trajectory_trace/input.yaml').read_text())
config = {k:config[k] for k in ['theory','likelihood','params','packages_path']}
config['theory']['camb']['version'] = version

def values(post):
    return {'loglikes':[float(v) if math.isfinite(v) else None for v in post.loglikes],
            'logpriors':[float(v) if math.isfinite(v) else None for v in post.logpriors],
            'logpost':float(post.logpost) if math.isfinite(post.logpost) else None}

cached = []
with get_model(config,stop_at_error=True) as model:
    helper = model.theory['camb.transfers']
    helper.set_cache_size(1)
    for call in calls:
        cached.append(values(model.logposterior(call['point'],cached=True)))
        assert helper._states.maxlen == 1
        print(version,'one-state replay',call['call'],cached[-1]['loglikes'],flush=True)
fresh = []
with get_model(config,stop_at_error=True) as model:
    for call in calls:
        fresh.append(values(model.logposterior(call['point'],cached=False)))
        print(version,'full fresh baseline',call['call'],fresh[-1]['loglikes'],flush=True)
records = [{'call':c['call'],'point':c['point'],'one_state_cached':a,'full_fresh':b,
            'exactly_equal':a==b,
            'cached_minus_fresh_chi2':[-2*(x-y) for x,y in zip(a['loglikes'],b['loglikes'])]}
           for c,a,b in zip(calls,cached,fresh)]
native = Path(camb.baseconfig.camblib._name).resolve()
out = {'utc':datetime.now(timezone.utc).isoformat(),'CAMB_version':version,
       'Cobaya_version':importlib.metadata.version('cobaya'),'records':records,
       'all_recorded_points_match_full_fresh_exactly':all(r['exactly_equal'] for r in records),
       'trace_sha256':hashlib.sha256(calls_path.read_bytes()).hexdigest(),
       'native_path':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
       'scope':'37-point private cache repair prototype; no production or inference sampler modifications; not uniform accuracy certification'}
with (HERE/('full_single_transfer_state_'+version+'_receipt.json')).open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('all37 exact:',out['all_recorded_points_match_full_fresh_exactly'],flush=True)
