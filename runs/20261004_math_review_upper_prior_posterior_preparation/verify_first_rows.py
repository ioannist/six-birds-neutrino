"""Freeze and replay each first complete row against independent fresh native theory."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
import camb
from cobaya.model import get_model
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('group');args=parser.parse_args()
entries=[e for e in json.loads((HERE/'preparation_receipt.json').read_text())['entries'] if e['group']==args.group]
assert len(entries)==4
module=Path(camb.baseconfig.camblib._name).resolve()
assert str(module)==entries[0]['module'] and sha(module)==entries[0]['module_sha256']
assert importlib.metadata.version('camb')==entries[0]['solver_version']
assert importlib.metadata.version('cobaya')==entries[0]['Cobaya_version']
remaining={e['seed']:e for e in entries};frozen=[]
deadline=time.monotonic()+1800
while remaining:
    for seed,e in list(remaining.items()):
        folder=HERE/f'seed{seed}'
        launch=json.loads((folder/'launch_receipt.json').read_text())
        proc=Path('/proc',str(launch['pid']))
        stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
        assert stat[0]!='Z' and int(stat[19])==launch['process_start_ticks']
        assert str(module) in (proc/'maps').read_text()
        run=ROOT/e['run_dir']
        assert not (run/'stderr.txt').read_bytes() and not (folder/'launcher_stderr.txt').read_bytes()
        source=run/'chains'/f'fresh_CAMB_{e["group"]}_seed{seed}.1.txt'
        if not source.exists():continue
        raw=source.read_bytes();lines=raw.splitlines(keepends=True)
        first=next((i for i,line in enumerate(lines) if line.endswith(b'\n') and line.strip() and not line.startswith(b'#')),None)
        if first is None:continue
        raw=b''.join(lines[:first+1])
        out=folder/'first_saved_rows';(out/'chains').mkdir(parents=True)
        destination=out/'chains'/source.name
        destination.write_bytes(raw)
        for name in ['input.yaml','resolved.yaml','solver_backend.json']:(out/name).write_bytes((run/name).read_bytes())
        updated=source.with_name(source.name.removesuffix('.1.txt')+'.updated.yaml')
        (out/'chains'/updated.name).write_bytes(updated.read_bytes())
        header=next(line for line in raw.decode().splitlines() if line.startswith('#')).lstrip('#').split()
        assert len(set(header))==len(header)
        values=raw.decode().splitlines()[-1].split();assert len(values)==len(header)
        row=dict(zip(header,values));assert np.isfinite([float(v) for v in values]).all()
        assert float(row['weight'])>0 and float(row['weight']).is_integer()
        assert source.read_bytes().startswith(raw)
        frozen.append({'seed':seed,'group':e['group'],'point':{n:float(row[n]) for n in e['initial_point']},
            'holding_time':int(float(row['weight'])),'source':str(source.relative_to(ROOT)),
            'frozen':str(destination.relative_to(ROOT)),'snapshot_sha256':sha(destination),'row':row,
            'complete_prefix_matches':True,'out':str(out.relative_to(ROOT))})
        del remaining[seed];print(seed,'first saved row frozen',flush=True)
    if remaining:
        assert time.monotonic()<deadline,'Observation timeout; inspect the same sampler, do not restart.'
        print('Waiting for first rows from owned processes',sorted(remaining),flush=True);time.sleep(15)

base=yaml.safe_load((ROOT/entries[0]['config']).read_text())
cfg={k:deepcopy(base[k]) for k in ['theory','likelihood','params','packages_path']}
upstream=deepcopy(cfg);upstream['theory']['camb'].pop('class')
checks=[]
with get_model(cfg,stop_at_error=True) as model,get_model(upstream,stop_at_error=True) as reference:
    model.set_cache_size(50)
    for record in frozen:
        expected=reference.logposterior(record['point'],cached=False)
        actual=model.logposterior(record['point'],cached=True)
        assert np.array_equal(actual.loglikes,expected.loglikes) and actual.logpriors==expected.logpriors
        row=record.pop('row')
        discrepancy={n:-2*float(v)-float(row['chi2__'+n]) for n,v in zip(reference.likelihood,expected.loglikes)}
        discrepancy['total_chi2']=-2*sum(expected.loglikes)-float(row['chi2'])
        discrepancy['logprior']=sum(expected.logpriors)+float(row['minuslogprior'])
        discrepancy['logposterior']=float(expected.logpost)+float(row['minuslogpost'])
        assert max(abs(v) for v in discrepancy.values())<=1e-9
        proof={**record,'utc':datetime.now(timezone.utc).isoformat(),'native_row_verified':True,
            'module_sha256':sha(module),'native_row_replay_discrepancies':discrepancy,'native_row_replay_tolerance':1e-9,
            'FreshCAMB_exact_to_independent_upstream_fresh':True,'sampler_cache_resize_challenge':50,
            'scope':'selected first saved row; no convergence or uniform accuracy certification'}
        with (ROOT/record['out']/'completion_receipt.json').open('x') as f:
            f.write(json.dumps(proof,indent=2,allow_nan=False)+'\n')
        checks.append(proof);print(record['seed'],'first native row verified',flush=True)
with (HERE/f'first_rows_{args.group}_verification.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'group':args.group,'records':checks,
        'first_saved_native_rows_verified':4,'worker_pid':os.getpid(),'posterior_certified':False},indent=2,allow_nan=False)+'\n')
