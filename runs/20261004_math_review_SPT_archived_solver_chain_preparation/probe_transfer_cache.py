"""Compare fast-parameter transfer reuse with a forced full recalculation."""
from datetime import datetime,timezone
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

e=json.loads((HERE/'seed1604/preparation_receipt.json').read_text())
first=HERE/'seed1604/first_saved_rows'
file,=(first/'chains').glob('*.1.txt')
lines=file.read_text().splitlines()
row=dict(zip(lines[0].lstrip('#').split(),lines[-1].split()))
point={n:float(row[n]) for n in e['initial_point']}
cfg=yaml.safe_load((first/'resolved.yaml').read_text())
cfg={k:cfg[k] for k in ['theory','likelihood','params','packages_path']}
version=importlib.metadata.version('camb')
assert version in ['1.6.5','2.0.4']
records={}
with get_model(cfg,stop_at_error=True) as model:
    for label,p,cached in [('initial',e['initial_point'],False),('fast_move_reused_transfer',point,True),('same_point_full_recalculation',point,False)]:
        likes={n:-2*float(v) for n,v in model.loglikes(p,as_dict=True,return_derived=False,cached=cached).items()}
        assert np.all(np.isfinite(list(likes.values())))
        cls=model.provider.get_Cl(ell_factor=False,units='muK2')
        np.savez_compressed(HERE/(version+'_'+label+'_spectra.npz'),**{n:np.array(cls[n],copy=True) for n in ['tt','te','ee','bb']})
        records[label]={'point':p,'cached':cached,'chi2_components':likes,'chi2_total':sum(likes.values())}
        print(version,label,likes,flush=True)
out={'utc':datetime.now(timezone.utc).isoformat(),'CAMB_version':version,'Cobaya_version':importlib.metadata.version('cobaya'),
     'native_module':str(Path(camb.baseconfig.camblib._name).resolve()),
     'native_module_sha256':hashlib.sha256(Path(camb.baseconfig.camblib._name).read_bytes()).hexdigest(),
     'records':records,'stored_row_chi2':float(row['chi2']),
     'reused_minus_fresh_total_chi2':records['fast_move_reused_transfer']['chi2_total']-records['same_point_full_recalculation']['chi2_total'],
     'reused_minus_stored_total_chi2':records['fast_move_reused_transfer']['chi2_total']-float(row['chi2']),
     'same_slow_coordinates_only_logA_and_ns_changed':all(point[n]==e['initial_point'][n] for n in point if n not in ['logA','ns']),
     'samplers_modified':False,'accuracy_or_posterior_quantile_certificate':False}
with (HERE/('transfer_cache_'+version+'_receipt.json')).open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
