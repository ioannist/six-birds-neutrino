"""Test copying native transfer objects before the spectrum calculation mutates them."""
from datetime import datetime,timezone
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

assert importlib.metadata.version('camb')=='1.6.5' and importlib.metadata.version('cobaya')=='3.6.1'
calls=[json.loads(line) for line in (HERE/'sampler_trajectory_trace/posterior_calls.jsonl').read_text().splitlines()]
cfg=yaml.safe_load((HERE/'sampler_trajectory_trace/input.yaml').read_text())
cfg={k:cfg[k] for k in ['theory','likelihood','params','packages_path']}
records=[]
with get_model(cfg,stop_at_error=True) as model:
    helper=model.theory['camb.transfers']
    original=helper.get_CAMB_transfers
    def independent_copy():
        params,results=original()
        return params.copy(),results.copy()
    helper.get_CAMB_transfers=independent_copy
    for call in calls:
        post=model.logposterior(call['point'],cached=True)
        values=None if post.loglikes is None else [float(v) if math.isfinite(v) else None for v in post.loglikes]
        records.append({'call':call['call'],'point':call['point'],'loglikes':values})
        print('independent-copy call',call['call'],values,flush=True)
    fresh=model.logposterior(calls[35]['point'],cached=False)
    fresh_values=[float(v) for v in fresh.loglikes]
    copied_values=records[35]['loglikes']
out={'utc':datetime.now(timezone.utc).isoformat(),'records':records,
     'call35_cached_copy_loglikes':copied_values,'call35_full_recalculation_loglikes':fresh_values,
     'call35_copy_minus_fresh_chi2_components':[-2*(a-b) for a,b in zip(copied_values,fresh_values)],
     'prototype_only_no_production_or_sampler_changes':True,
     'scope':'37 recorded-point object-isolation control; not a validated implementation or posterior readout'}
with (HERE/'independent_transfer_copy_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
