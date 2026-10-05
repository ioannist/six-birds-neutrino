"""Evaluate one numerical factor with a pinned native CLASS module."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_cobaya import _validate_classy_backend
from cobaya.model import get_model
import classy
import classy._classy as native

parser = argparse.ArgumentParser()
parser.add_argument('variant',choices=['unit_grid'])
args = parser.parse_args()
selection = json.loads((HERE/'selection_receipt.json').read_text())
module = Path(native.__file__).resolve()
assert module==Path(selection['native_module_path']).resolve()
assert hashlib.sha256(module.read_bytes()).hexdigest()==selection['native_module_sha256']
folder = HERE/args.variant
cfg = yaml.safe_load((folder/'input.yaml').read_text())
points = json.loads((folder/'points.json').read_text())
backend = _validate_classy_backend(cfg)
assert backend['module_sha256']==selection['native_module_sha256']
header = (Path(classy.__file__).parent/'include/precisions.h').read_text()
allowed=set(re.findall(r'class_(?:precision|type)_parameter\(\s*(\w+)\s*,',header))
assert set(selection['changed_controls'][args.variant])<=allowed
out = folder/'evaluation'
out.mkdir()
runtime={'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'status':'running_numerical_factor_check',
         'module':str(module),'module_sha256':backend['module_sha256'],'omp_threads':os.environ['OMP_NUM_THREADS']}
(out/'runtime_state.json').write_text(json.dumps(runtime,indent=2)+'\n')
records={}
with get_model(cfg,stop_at_error=True) as model:
    names=set(model.parameterization.sampled_params())
    for label,point in points.items():
        assert set(point)==names and np.all(np.isfinite(list(point.values())))
        start=time.monotonic()
        likes=model.loglikes(point,as_dict=True,return_derived=False,cached=False)
        values={n:-2*float(v) for n,v in likes.items()}
        assert len(values)==6 and np.all(np.isfinite(list(values.values())))
        cl=model.provider.get_Cl(ell_factor=False,units='muK2')
        request=model.theory['classy'].requested()['Cl']
        saved={name:np.array(cl[name][:int(lmax)+1],copy=True) for name,lmax in request.items()}
        assert all(a.ndim==1 and len(a)==int(request[name])+1 and np.all(np.isfinite(a)) for name,a in saved.items())
        np.savez_compressed(out/(label+'_spectra.npz'),**saved)
        derived=model.theory['classy'].classy.get_current_derived_parameters(['ra_rec','conformal_age','tau_rec'])
        rescaling=derived['ra_rec']/(derived['conformal_age']-derived['tau_rec'])
        assert cfg['theory']['classy']['extra_args']['l_logstep']==1.0
        assert cfg['theory']['classy']['extra_args']['l_linstep']*rescaling>1.0
        records[label]={'native_geometry':derived,'angular_rescaling':rescaling,'point':point,'native_chi2':values,'elapsed_seconds':time.monotonic()-start,
                        'requested_spectrum_ell_max':{k:int(v) for k,v in request.items()}}
        (out/'progress.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
        print(args.variant,label,'completed',flush=True)
(out/'metrics.json').write_text(json.dumps({'scope':'two_selected_B_fixed_coordinates_unit_multipole_grid',
    'variant':args.variant,'records':records,'posterior_accuracy_certified':False,'interval_error_certified':False},indent=2,allow_nan=False)+'\n')
runtime['status']='complete_selected_factor_check_not_accuracy_certificate'
(out/'runtime_state.json').write_text(json.dumps(runtime,indent=2)+'\n')
