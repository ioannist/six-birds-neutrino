"""Test the second failed coordinate with the live quadrature-only precision."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import time
import traceback

import classy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('backend', choices=['original', 'guarded'])
args = parser.parse_args()
source = ROOT / 'runs/20261004_math_review_class_tca_failure_seed701/failed_class_arguments.json'
arguments = dict(json.loads(source.read_text())['translated_class_arguments'])
removed = {name: arguments.pop(name) for name in
           ['tol_perturbations_integration', 'perturbations_sampling_stepsize',
            'tol_ncdm_synchronous', 'tol_ncdm_newtonian', 'l_logstep', 'l_linstep']}
assert arguments['tol_ncdm_bg'] == 1e-8 and arguments['l_max_scalars'] == 4095
module = Path(importlib.import_module(classy.Class.__module__).__file__)
expected_sha = ('38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a'
                if args.backend == 'original' else
                '7a5d736220b3d236f3dc7c89944d025fe3e4c7cb4c8e4473ef807c898fc71539')
assert hashlib.sha256(module.read_bytes()).hexdigest() == expected_sha
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'backend': args.backend,
           'arguments': arguments, 'removed_later_precision_settings': removed,
           'source_arguments_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
           'module': str(module), 'module_sha256': expected_sha,
           'omp_threads': os.environ.get('OMP_NUM_THREADS'),
           'scope': 'exact_second_failure_point_under_quadrature_only_precision',
           'posterior_convergence_certified': False,
           'uniform_numerical_accuracy_certified': False}
started = time.monotonic()
model = classy.Class()
model.set(arguments)
try:
    model.compute()
except classy.CosmoComputationError as error:
    receipt.update(compute_succeeded=False, error_type=type(error).__name__, error=str(error))
    (HERE / (args.backend + '_native_error.txt')).write_text(traceback.format_exc())
    assert args.backend == 'original'
    assert 'initial conditions' in str(error) and 'tca' in str(error)
else:
    receipt['compute_succeeded'] = True
    spectra = model.lensed_cl(4095)
    assert all(np.isfinite(value).all() for value in spectra.values())
    path = HERE / (args.backend + '_spectra.npz')
    np.savez_compressed(path, **spectra)
    receipt['spectra_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    thermo = model.get_thermodynamics()
    background = model.get_background()
    assert all(np.isfinite(value).all() for value in thermo.values())
    assert all(np.isfinite(value).all() for value in background.values())
    path = HERE / (args.backend + '_thermodynamics.npz')
    np.savez_compressed(path, **thermo)
    receipt['thermodynamics_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with np.load(ROOT / 'runs/20261004_math_review_class_python_repair/seed701_intermediate_thermodynamics.npz') as control:
        assert set(control.files) == set(thermo)
        equal = {name: bool(np.array_equal(control[name], thermo[name])) for name in control.files}
    receipt['thermodynamics_equal_guarded_seven_setting_control_exactly'] = equal
    assert all(equal.values())
    assert args.backend == 'guarded'
model.struct_cleanup()
model.empty()
receipt['elapsed_seconds'] = time.monotonic() - started
with (HERE / (args.backend + '_receipt.json')).open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps({'backend': args.backend, 'compute_succeeded': receipt['compute_succeeded'],
                  'elapsed_seconds': receipt['elapsed_seconds']}))
