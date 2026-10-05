"""Evaluate native CAMB/Candl targets without running or changing a sampler."""
import argparse
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'src'))
from cobaya.model import get_model
import camb
import cobaya.theories.camb.camb as wrapper
import cobaya
PREFIX = Path('/mnt/8tb/six-birds-ml/tmp/neutrino_spt_archived_solver_control_20261004/packages')
assert Path(camb.__file__).resolve().is_relative_to(PREFIX)
assert Path(cobaya.__file__).resolve().is_relative_to(PREFIX)
assert importlib.metadata.version('camb') == '1.6.5'
assert importlib.metadata.version('cobaya') == '3.6.1'

parser = argparse.ArgumentParser()
parser.add_argument('target', choices=['A', 'B'])
args = parser.parse_args()
points = json.loads((HERE/args.target/'points.json').read_text())
module = Path(camb.baseconfig.camblib._name).resolve()
runtime = {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
           'omp_threads': os.environ['OMP_NUM_THREADS'], 'CAMB_module': str(module),
           'CAMB_module_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
           'Cobaya_module': str(Path(cobaya.__file__).resolve()),
           'CAMB_Python_module': str(Path(camb.__file__).resolve()),
           'Cobaya_CAMB_wrapper': str(Path(wrapper.__file__).resolve()),
           'Cobaya_CAMB_wrapper_sha256': hashlib.sha256(Path(wrapper.__file__).read_bytes()).hexdigest(),
           'versions': {n: importlib.metadata.version(n) for n in
                        ['camb', 'cobaya', 'candl-like', 'candl-data', 'spt-candl-data']}}
records = {}
for style in ['original_style', 'restoration_style']:
    folder = HERE/args.target/style
    cfg = yaml.safe_load((folder/'input.yaml').read_text())
    with get_model(cfg, stop_at_error=True) as model:
        adapter = next(v for n, v in model.likelihood.items() if 'Candl' in n)
        theory = model.theory['camb']
        assert set(model.parameterization.sampled_params()) == set(next(iter(points.values())))
        assert set(adapter.input_params) <= set(point_name for point_name in next(iter(points.values())))
        record = {'requested_Cl': adapter.get_requirements()['Cl'],
                  'effective_CAMB_extra_args': dict(theory.extra_args),
                  'internal_prior_policy': adapter._internal_prior_policy,
                  'sampled_scalar_inputs': list(adapter.input_params),
                  'fixed_scalar_defaults': {n: float(adapter._base_params[n]) for n in adapter._scalar_parameters if n not in adapter.input_params},
                  'native_dataset_path': str(adapter._test_vector.dataset_path), 'evaluations': {}}
        for label, point in points.items():
            start = time.monotonic()
            likes = {n: float(v) for n, v in model.loglikes(point, as_dict=True, return_derived=False, cached=False).items()}
            priors = [float(v) for v in model.logpriors(point)]
            assert len(likes) == 2 and np.all(np.isfinite(list(likes.values())+priors))
            cl = model.provider.get_Cl(ell_factor=False, units='muK2')
            supported = {n: np.asarray(cl[n][:maximum+1]).copy() for n, maximum in record['requested_Cl'].items()}
            assert all(np.all(np.isfinite(a)) and len(a) == record['requested_Cl'][n]+1 for n, a in supported.items())
            np.savez_compressed(folder/(label+'_spectra.npz'), **supported)
            record['evaluations'][label] = {'point': point, 'chi2_components': {n: -2*v for n, v in likes.items()},
                'chi2_total': -2*sum(likes.values()), 'logpriors': priors,
                'logposterior': sum(likes.values())+sum(priors), 'elapsed_seconds': time.monotonic()-start}
            print(args.target, style, label, 'complete', flush=True)
        records[style] = record
with (HERE/args.target/'evaluation_receipt.json').open('x') as handle:
    handle.write(json.dumps({'runtime': runtime, 'records': records,
        'scope': 'selected_archived_version_control_on_current_Python_and_likelihood_stack_not_original_binary_replay'},
        indent=2, allow_nan=False)+'\n')
