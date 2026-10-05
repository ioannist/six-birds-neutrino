"""Wait for, freeze and natively replay each archived-version first saved row."""
from datetime import datetime,timezone
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

prep=json.loads((HERE/'preparation_receipt.json').read_text())
module=Path(camb.baseconfig.camblib._name).resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert importlib.metadata.version('camb')=='1.6.5' and importlib.metadata.version('cobaya')=='3.6.1'
assert sha(module)==prep['entries'][0]['module_sha256']
deadline=time.monotonic()+900
remaining={e['seed']:e for e in prep['entries']}
frozen=[]
while remaining:
    for seed,e in list(remaining.items()):
        folder=HERE/('seed'+str(seed))
        launch=json.loads((folder/'launch_receipt.json').read_text())
        proc=Path('/proc',str(launch['pid']))
        stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
        assert stat[0]!='Z' and int(stat[19])==launch['process_start_ticks']
        assert str(module) in (proc/'maps').read_text()
        run=ROOT/e['run_dir']
        assert not (run/'stderr.txt').read_bytes()
        source=run/'chains'/('archived_CAMB_'+e['lens']+'_seed'+str(seed)+'.1.txt')
        if not source.exists():
            continue
        raw=source.read_bytes();lines=raw.splitlines(keepends=True)
        first=next((i for i,line in enumerate(lines) if line.endswith(b'\n') and line.strip() and not line.startswith(b'#')),None)
        if first is None:
            continue
        raw=b''.join(lines[:first+1])
        cfg=yaml.safe_load((run/'resolved.yaml').read_text())
        backend={k:launch[k] for k in ['module','module_sha256','solver_version','Cobaya_version','wrapper_sha256']}
        backend['launch_receipt']=str((folder/'launch_receipt.json').relative_to(ROOT))
        backend['launch_receipt_sha256']=sha(folder/'launch_receipt.json')
        with (run/'solver_backend.json').open('x') as handle:
            handle.write(json.dumps(backend,indent=2)+'\n')
        out=folder/'first_saved_rows';(out/'chains').mkdir(parents=True)
        prefix=out/'chains'/source.name.removesuffix('.1.txt')
        frozen_file=Path(str(prefix)+'.1.txt');frozen_file.write_bytes(raw)
        (out/'input.yaml').write_bytes((run/'input.yaml').read_bytes())
        cfg['output']=str(prefix)
        (out/'resolved.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
        (out/'solver_backend.json').write_bytes((run/'solver_backend.json').read_bytes())
        updated=source.with_name(source.name.removesuffix('.1.txt')+'.updated.yaml')
        (out/'chains'/updated.name).write_bytes(updated.read_bytes())
        header=next(line for line in raw.decode().splitlines() if line.startswith('#')).lstrip('#').split()
        row=dict(zip(header,raw.decode().splitlines()[-1].split()))
        point={n:float(row[n]) for n in e['initial_point']}
        assert float(row['weight'])>0 and float(row['weight']).is_integer()
        frozen.append({'seed':seed,'lens':e['lens'],'source':str(source.relative_to(ROOT)),
            'frozen':str(frozen_file.relative_to(ROOT)),'snapshot_sha256':sha(frozen_file),
            'source_complete_prefix_matches':source.read_bytes().startswith(raw),
            'point':point,'holding_time':int(float(row['weight'])),'row':row,'out':str(out.relative_to(ROOT))})
        del remaining[seed]
        print(seed,'first complete row frozen',flush=True)
    if remaining:
        assert time.monotonic()<deadline,'Timed out waiting; samplers must be inspected without restart.'
        print('Waiting on same owned sampler identities:',sorted(remaining),flush=True)
        time.sleep(15)

checks=[]
for target in ['A','B']:
    records=[r for r in frozen if r['lens']==target]
    cfg=yaml.safe_load((ROOT/records[0]['out']/'resolved.yaml').read_text())
    model_cfg={k:cfg[k] for k in ['theory','likelihood','params','packages_path']}
    with get_model(model_cfg,stop_at_error=True) as model:
        for record in records:
            likes={n:float(v) for n,v in model.loglikes(record['point'],as_dict=True,return_derived=False,cached=False).items()}
            prior=[float(v) for v in model.logpriors(record['point'])]
            assert len(likes)==2 and np.all(np.isfinite(list(likes.values())+prior))
            row=record.pop('row')
            discrepancy={n:-2*v-float(row['chi2__'+n]) for n,v in likes.items()}
            discrepancy['total_chi2']=-2*sum(likes.values())-float(row['chi2'])
            discrepancy['logprior']=sum(prior)+float(row['minuslogprior'])
            discrepancy['logposterior']=sum(likes.values())+sum(prior)+float(row['minuslogpost'])
            assert max(abs(v) for v in discrepancy.values())<=1e-9
            proof={**record,'utc':datetime.now(timezone.utc).isoformat(),'native_row_replay_discrepancies':discrepancy,
                'native_row_replay_tolerance':1e-9,'module_sha256':sha(module),'native_row_verified':True,
                'requested_effective_lmax':model.theory['camb'].extra_args['lmax'],
                'original_environment_or_convergence_certified':False}
            with (ROOT/record['out']/'completion_receipt.json').open('x') as handle:
                handle.write(json.dumps(proof,indent=2,allow_nan=False)+'\n')
            checks.append(proof)
            print(record['seed'],'first saved row native replay verified',flush=True)
out={'utc':datetime.now(timezone.utc).isoformat(),'records':checks,'first_native_rows_verified':8,
     'actual_loaded_module':str(module),'module_sha256':sha(module),'worker_pid':os.getpid(),
     'scope':'selected_first_saved_rows_not_posterior_convergence_or_historical_identity',
     'histories_from_different_solver_targets_pooled':False,'paper_modified':False}
with (HERE/'saved_rows_verification.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
