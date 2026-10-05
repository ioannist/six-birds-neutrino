"""Isolate spectrum and likelihood history dependence on both SPT recipes."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
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

version=importlib.metadata.version('camb')
assert version in ['1.6.5','2.0.4']
prep=ROOT/'runs/20261004_math_review_SPT_archived_solver_chain_preparation'
calls=[json.loads(s) for s in (prep/'sampler_trajectory_trace/posterior_calls.jsonl').read_text().splitlines()]
records=[]
for lens,seed in [('A',1604),('B',1608)]:
    source=prep/('seed'+str(seed))/'input.yaml'
    config=yaml.safe_load(source.read_text())
    config={k:deepcopy(config[k]) for k in ['theory','likelihood','params','packages_path']}
    config['theory']['camb']['version']=version
    initial={p:float(v['ref']) for p,v in config['params'].items() if 'prior' in v}
    other={p:initial[p]+calls[1]['point'][p]-calls[0]['point'][p] for p in initial}
    target={p:initial[p]+calls[35]['point'][p]-calls[0]['point'][p] for p in initial}
    if lens=='A':
        # Preserve the exact recorded coordinates, avoiding subtract/add rounding.
        initial,other,target=[deepcopy(calls[i]['point']) for i in [0,1,35]]
    for size in [1,0]:
        with get_model(config,stop_at_error=True) as main, get_model(config,stop_at_error=True) as interfering:
            main.theory['camb.transfers'].set_cache_size(size)
            main.logposterior(initial,cached=True)
            interfering.logposterior(other,cached=False)
            returned=main.logposterior(target,cached=True)
            before={k:np.asarray(v).copy() for k,v in main.provider.get_Cl(ell_factor=True).items()}
            fresh=main.logposterior(target,cached=False)
            after={k:np.asarray(v).copy() for k,v in main.provider.get_Cl(ell_factor=True).items()}
            assert before.keys()==after.keys()
            spectra={}
            payload={}
            for k in before:
                assert before[k].shape==after[k].shape
                difference=before[k]-after[k]
                spectra[k]={'shape':list(before[k].shape),
                            'exactly_equal':bool(np.array_equal(before[k],after[k])),
                            'nonidentical_entries':int(np.count_nonzero(difference)),
                            'max_absolute_difference':float(np.max(np.abs(difference))),
                            'before_sha256':hashlib.sha256(before[k].tobytes()).hexdigest(),
                            'after_sha256':hashlib.sha256(after[k].tobytes()).hexdigest()}
                payload['returned_'+k]=before[k]
                payload['fresh_'+k]=after[k]
            arrays=HERE/f'native_spectra_{version}_{lens}_cache{size}.npz'
            assert not arrays.exists()
            np.savez_compressed(arrays,**payload)
            a,b=[float(v) for v in returned.loglikes],[float(v) for v in fresh.loglikes]
            record={'lens':lens,'transfer_cache_size':size,'initial':initial,'intervening':other,'target':target,
                    'returned_loglikes':a,'fresh_loglikes':b,'returned_logpriors':list(returned.logpriors),
                    'fresh_logpriors':list(fresh.logpriors),'cached_minus_fresh_chi2':[-2*(x-y) for x,y in zip(a,b)],
                    'spectra':spectra,'spectrum_units':'CAMB get_Cl ell_factor=True defaults; CMB microkelvin squared',
                    'arrays':arrays.name,'arrays_sha256':hashlib.sha256(arrays.read_bytes()).hexdigest(),
                    'config_source':str(source.relative_to(ROOT)),'config_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
            records.append(record)
            print(version,lens,size,record['cached_minus_fresh_chi2'],
                  'TTmax',spectra['tt']['max_absolute_difference'],flush=True)
native=Path(camb.baseconfig.camblib._name).resolve()
out={'utc':datetime.now(timezone.utc).isoformat(),'CAMB_version':version,
     'Cobaya_version':importlib.metadata.version('cobaya'),'records':records,
     'native_path':str(native),'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
     'scope':'selected two-model native spectrum isolation for both SPT targets; no production or inference changes'}
with (HERE/('native_spectra_'+version+'_receipt.json')).open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
