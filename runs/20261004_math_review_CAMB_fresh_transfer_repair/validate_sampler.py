"""Check actual finite MCMC saved rows with the production fresh-transfer adapter."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cobaya.model import get_model
from cobaya.run import run
from sbt_spt_audit.boltzmann import FreshCAMBTransfers,configure_fresh_camb_transfers
import camb

version=importlib.metadata.version('camb')
assert version in ['1.6.5','2.0.4']
native=Path(camb.baseconfig.camblib._name).resolve()
stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
launch={'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'process_start_ticks':int(stat[19]),
        'CAMB_version':version,'Cobaya_version':importlib.metadata.version('cobaya'),
        'native_path':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
        'implementation_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
             [Path(__file__),ROOT/'src/sbt_spt_audit/boltzmann.py',ROOT/'src/sbt_spt_audit/samplers.py']},
        'inference_chain':False,'existing_inference_sampler_modified':False}
with (HERE/('sampler_'+version+'_launch.json')).open('x') as h:h.write(json.dumps(launch,indent=2)+'\n')
prep=ROOT/'runs/20261004_math_review_SPT_archived_solver_chain_preparation'
records=[]
for lens,seed in [('A',1604),('B',1608)]:
    output=HERE/('sampler_'+version+'_'+lens)
    output.mkdir()
    cfg=yaml.safe_load((prep/('seed'+str(seed))/'input.yaml').read_text())
    cfg['theory']['camb']['version']=version
    cfg.pop('notes',None)  # This diagnostic declares its actual native build above.
    configure_fresh_camb_transfers(cfg)
    options=deepcopy(cfg['sampler']['mcmc']);options['max_samples']=2
    cfg['sampler']={'sbt_spt_audit.samplers.FullPrecisionMCMC':options}
    cfg['output']=str(output/'chains'/'finite_probe')
    (output/'input.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    _,sampler=run(cfg,no_mpi=True,stop_at_error=True)
    assert isinstance(sampler.model.theory['camb.transfers'],FreshCAMBTransfers)
    path=output/'chains'/'finite_probe.1.txt'
    header=path.read_text().splitlines()[0].lstrip('#').split()
    rows=np.atleast_2d(np.loadtxt(path))
    assert rows.shape==sampler.collection.data.shape
    assert np.array_equal(rows,sampler.collection.data.to_numpy(dtype=np.float64))
    reference={k:deepcopy(cfg[k]) for k in ['theory','likelihood','params','packages_path']}
    reference['theory']['camb'].pop('class')
    checks=[]
    with get_model(reference,stop_at_error=True) as model:
        for index,row in enumerate(rows):
            values=dict(zip(header,row))
            point={p:float(values[p]) for p in model.parameterization.sampled_params()}
            fresh=model.logposterior(point,cached=False)
            expected={'minuslogpost':-float(fresh.logpost),'minuslogprior':-float(sum(fresh.logpriors)),
                      'chi2':-2*float(sum(fresh.loglikes))}
            expected.update({f'chi2__{n}':-2*float(v) for n,v in zip(model.likelihood,fresh.loglikes)})
            errors={n:float(v-values[n]) for n,v in expected.items()}
            checks.append({'row':index,'point':point,'fresh_minus_stored':errors,
                           'exactly_equal':all(v==0 for v in errors.values()),
                           'within_fixed_1e_minus9':all(abs(v)<=1e-9 for v in errors.values())})
    records.append({'lens':lens,'seed':seed,'stored_rows':len(rows),'checks':checks,
                    'chain':str(path.relative_to(ROOT)),'chain_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'sampler_transfer_helper_class':type(sampler.model.theory['camb.transfers']).__name__,
                    'ordinary_sampler_options_except_finite_sample_cap':True,
                    'proposal_blocks':[[str(p) for p in b] for b in sampler.blocks]})
    print(version,lens,'finite sampler rows',len(rows),'all within1e-9',all(c['within_fixed_1e_minus9'] for c in checks),flush=True)
out={'utc':datetime.now(timezone.utc).isoformat(),'records':records,'CAMB_version':version,
     'native_path':str(native),'native_sha256':launch['native_sha256'],
     'production_adapter_sha256':launch['implementation_sha256']['src/sbt_spt_audit/boltzmann.py'],
     'scope':'actual short native MCMC row reproduction on both SPT recipes; excluded from posterior diagnostics',
     'sampler_resize_reintroduced_cached_transfer_reuse':False,
     'all_rows_match_fresh_within_predeclared_1e_minus9':all(c['within_fixed_1e_minus9'] for r in records for c in r['checks'])}
with (HERE/('sampler_'+version+'_receipt.json')).open('x') as h:h.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
