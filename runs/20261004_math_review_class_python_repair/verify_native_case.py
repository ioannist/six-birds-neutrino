"""Verify one exact archived coordinate using the separately built Python backend."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import time

import classy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('case', choices=['seed505_default', 'seed505_quadrature', 'seed701_intermediate'])
args = parser.parse_args()
manifest = json.loads((HERE / 'preparation_manifest.json').read_text())
module = Path(importlib.import_module(classy.Class.__module__).__file__)
assert module.parent == Path(manifest['package'])
source = ROOT / ('runs/20261004_math_review_class_tca_failure_seed701/failed_class_arguments.json'
                 if args.case == 'seed701_intermediate' else
                 'runs/20261004_math_review_class_tca_failure_seed505/failed_class_arguments.json')
arguments = dict(json.loads(source.read_text())['translated_class_arguments'])
if args.case == 'seed505_quadrature':
    arguments['tol_ncdm_bg'] = 1e-8
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'case': args.case,
           'arguments': arguments, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
           'module': str(module), 'module_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
           'omp_threads': os.environ.get('OMP_NUM_THREADS'),
           'scope': 'fixed_coordinate_native_Python_backend_validation',
           'posterior_convergence_certified': False, 'uniform_numerical_accuracy_certified': False}
started = time.monotonic()
model = classy.Class()
model.set(arguments)
model.compute()
spectra = model.lensed_cl(arguments['l_max_scalars'])
assert all(np.isfinite(values).all() for values in spectra.values())
assert int(spectra['ell'][-1]) == arguments['l_max_scalars']
file = HERE / (args.case + '_spectra.npz')
assert not file.exists()
np.savez_compressed(file, **spectra)
receipt['spectra_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
receipt['spectrum_ell_max'] = int(spectra['ell'][-1])
receipt['tables'] = {}
for name, table in [('background', model.get_background()), ('thermodynamics', model.get_thermodynamics())]:
    assert all(np.isfinite(values).all() for values in table.values())
    receipt['tables'][name] = {key: {'rows': int(values.size), 'nonfinite': 0,
                                   'array_sha256': hashlib.sha256(values.tobytes()).hexdigest()}
                               for key, values in table.items()}
    if name == 'thermodynamics':
        file = HERE / (args.case + '_thermodynamics.npz')
        np.savez_compressed(file, **table)
        receipt['thermodynamics_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
if args.case == 'seed505_quadrature':
    original = ROOT / 'runs/20261004_math_review_class_tca_failure_seed505/background_quadrature_omp4.npz'
    with np.load(original) as archive:
        assert set(archive.files) == set(spectra)
        equal = {key: bool(np.array_equal(spectra[key], archive[key])) for key in archive.files}
        discrepancies = {key: float(np.max(np.abs(spectra[key] - archive[key]))) for key in archive.files}
    receipt['original_spectra_sha256'] = hashlib.sha256(original.read_bytes()).hexdigest()
    receipt['arrays_equal_original_exactly'] = equal
    receipt['max_absolute_array_discrepancy'] = discrepancies
    assert all(equal.values())
model.struct_cleanup()
model.empty()
receipt['elapsed_seconds'] = time.monotonic() - started
receipt['succeeded'] = True
(HERE / (args.case + '_receipt.json')).write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps({'case': args.case, 'succeeded': True, 'elapsed_seconds': receipt['elapsed_seconds']}))
