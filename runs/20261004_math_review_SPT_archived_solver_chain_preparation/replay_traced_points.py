"""Replay the recorded sampler evaluations in order without adding new draws."""
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cobaya.model import get_model
import camb

assert importlib.metadata.version('camb')=='1.6.5' and importlib.metadata.version('cobaya')=='3.6.1'
file=HERE/'sampler_trajectory_trace/posterior_calls.jsonl'
calls=[json.loads(line) for line in file.read_text().splitlines()]
cfg=yaml.safe_load((HERE/'sampler_trajectory_trace/input.yaml').read_text())
cfg={k:cfg[k] for k in ['theory','likelihood','params','packages_path']}
records=[]
with get_model(cfg,stop_at_error=True) as model:
    for call in calls:
        post=model.logposterior(call['point'],cached=True)
        values=None if post.loglikes is None else [float(v) if math.isfinite(v) else None for v in post.loglikes]
        differences=None if values is None or call['loglikes'] is None else [None if a is None or b is None else -2*(a-b) for a,b in zip(values,call['loglikes'])]
        records.append({'call':call['call'],'point':call['point'],'replayed_loglikes':values,
                        'recorded_loglikes':call['loglikes'],'replayed_minus_recorded_chi2_components':differences})
        print('replayed call',call['call'],differences,flush=True)
    last=calls[35]['point']
    fresh=model.logposterior(last,cached=False)
    fresh_values=[float(v) for v in fresh.loglikes]
out={'utc':datetime.now(timezone.utc).isoformat(),'records':records,'traced_call_count':len(calls),
     'trace_jsonl_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
     'call35_fresh_loglikes_after_complete_history':fresh_values,
     'native_module':str(Path(camb.baseconfig.camblib._name).resolve()),
     'speed_measurement_internal_calls_replayed':False,'samplers_modified':False,
     'scope':'recorded posterior evaluation sequence control; not a posterior readout or established cache repair'}
with (HERE/'traced_points_replay_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
