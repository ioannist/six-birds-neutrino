"""Measure failed saved-row reproduction without changing tolerance or samplers."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cobaya.model import get_model
import camb

entries=json.loads((HERE/'preparation_receipt.json').read_text())['entries']
records={}
def evaluate(model,e):
    folder=HERE/('seed'+str(e['seed']))/'first_saved_rows'
    file,=(folder/'chains').glob('*.1.txt')
    raw=file.read_text().splitlines()
    header=next(line for line in raw if line.startswith('#')).lstrip('#').split()
    row=dict(zip(header,raw[-1].split()))
    point={n:float(row[n]) for n in e['initial_point']}
    likes={n:float(v) for n,v in model.loglikes(point,as_dict=True,return_derived=False,cached=False).items()}
    priors=[float(v) for v in model.logpriors(point)]
    discrepancies={n:-2*v-float(row['chi2__'+n]) for n,v in likes.items()}
    discrepancies['total_chi2']=-2*sum(likes.values())-float(row['chi2'])
    discrepancies['logprior']=sum(priors)+float(row['minuslogprior'])
    discrepancies['logposterior']=sum(likes.values())+sum(priors)+float(row['minuslogpost'])
    assert np.all(np.isfinite(list(discrepancies.values())))
    return {'point':point,'discrepancies':discrepancies,'components':{n:-2*v for n,v in likes.items()},
            'frozen_chain_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
def config(e):
    cfg=yaml.safe_load((HERE/('seed'+str(e['seed']))/'first_saved_rows/resolved.yaml').read_text())
    return {k:cfg[k] for k in ['theory','likelihood','params','packages_path']}
for target in ['A','B']:
    cohort=[e for e in entries if e['lens']==target]
    with get_model(config(cohort[0]),stop_at_error=True) as shared:
        for e in cohort:
            records[str(e['seed'])]={'shared_model':evaluate(shared,e)}
            print(e['seed'],'shared model',records[str(e['seed'])]['shared_model']['discrepancies'],flush=True)
    for e in cohort:
        with get_model(config(e),stop_at_error=True) as fresh:
            records[str(e['seed'])]['fresh_model']=evaluate(fresh,e)
            print(e['seed'],'fresh model',records[str(e['seed'])]['fresh_model']['discrepancies'],flush=True)
out={'utc':datetime.now(timezone.utc).isoformat(),'records':records,'module':str(Path(camb.baseconfig.camblib._name).resolve()),
     'samplers_modified':False,'tolerance_relaxed':False,'unverified_rows_used_for_inference':False}
with (HERE/'saved_row_discrepancy_probe.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
