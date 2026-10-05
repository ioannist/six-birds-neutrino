"""Replay the exact failed CLASS theory arguments in an isolated native process."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import time
import yaml

import classy
import numpy as np

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--precision-mode', choices=['default', 'earlier_start', 'background_quadrature', 'intermediate'], default='default')
parser.add_argument('--ell-max', type=int, default=None)
args = parser.parse_args()
assert not args.output.exists()
input_path = HERE / 'failed_class_arguments.json'
record = json.loads(input_path.read_text())
arguments = dict(record['translated_class_arguments'])
overrides = {}
precision_source_sha256 = None
if args.precision_mode == 'earlier_start':
    reference_path = HERE.parent / '20261003_math_review_class_accuracy_control_reference/precision_settings.json'
    reference = json.loads(reference_path.read_text())
    overrides['start_small_k_at_tau_c_over_tau_h'] = reference['settings']['start_small_k_at_tau_c_over_tau_h']
    precision_source_sha256 = hashlib.sha256(reference_path.read_bytes()).hexdigest()
elif args.precision_mode in ['background_quadrature', 'intermediate']:
    config_path = HERE.parent / '20261003_math_review_cmb_accuracy_chain_configs/A_seed601.yaml'
    extra = yaml.safe_load(config_path.read_text())['theory']['classy']['extra_args']
    for key in ['N_ncdm', 'N_ur', 'l_max_scalars']:
        assert extra[key] == arguments[key]
    overrides = {key: value for key, value in extra.items() if key not in ['N_ncdm', 'N_ur', 'l_max_scalars']}
    assert set(overrides) == {'tol_ncdm_bg', 'tol_perturbations_integration',
                             'perturbations_sampling_stepsize', 'tol_ncdm_synchronous',
                             'tol_ncdm_newtonian', 'l_logstep', 'l_linstep'}
    if args.precision_mode == 'background_quadrature':
        overrides = {'tol_ncdm_bg': overrides['tol_ncdm_bg']}
    precision_source_sha256 = hashlib.sha256(config_path.read_bytes()).hexdigest()
assert not set(overrides).intersection(arguments)
arguments.update(overrides)
if args.ell_max is not None:
    assert 2 <= args.ell_max <= record['translated_class_arguments']['l_max_scalars']
    arguments['l_max_scalars'] = args.ell_max
started = time.perf_counter()
result = {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
          'omp_threads': os.environ.get('OMP_NUM_THREADS'),
          'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
          'native_class_arguments': arguments,
          'precision_mode': args.precision_mode, 'declared_precision_overrides': overrides,
          'precision_source_sha256': precision_source_sha256,
          'coverage_override_l_max_scalars': args.ell_max,
          'scope': 'exact_failed_theory_point_replay_no_posterior_claim',
          'succeeded': False, 'posterior_convergence_verified': False}
model = classy.Class()
try:
    model.set(arguments)
    model.compute()
    spectra = model.lensed_cl(arguments['l_max_scalars'])
    assert all(np.all(np.isfinite(v)) for v in spectra.values())
    spectrum_file = args.output.with_suffix('.npz')
    assert not spectrum_file.exists()
    np.savez_compressed(spectrum_file, **spectra)
    result.update(succeeded=True, spectra_file=str(spectrum_file),
                  spectra_sha256=hashlib.sha256(spectrum_file.read_bytes()).hexdigest(),
                  spectrum_ell_max=int(spectra['ell'][-1]))
except Exception as error:
    result.update(error_type=type(error).__name__, error=str(error))
finally:
    model.struct_cleanup()
    model.empty()
module = importlib.import_module(classy.Class.__module__)
result['native_module_sha256'] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
result['elapsed_seconds'] = time.perf_counter() - started
args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps({k: result[k] for k in ['succeeded', 'omp_threads', 'elapsed_seconds']}))
raise SystemExit(0 if result['succeeded'] else 1)
