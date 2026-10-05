"""Inspect native tables before perturbations, at the exact archived failure point."""
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import time

import classy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'runs/20261004_math_review_class_tca_failure_seed505/failed_class_arguments.json'
arguments = json.loads(SOURCE.read_text())['translated_class_arguments']
native_module_path = Path(importlib.import_module(classy.Class.__module__).__file__)
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'native_background_and_thermodynamics_before_perturbations_at_one_fixed_point',
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'native_module': str(native_module_path),
    'native_module_sha256': hashlib.sha256(native_module_path.read_bytes()).hexdigest(),
    'active_inference_library_changed': False,
    'posterior_accuracy_certified': False,
    'cases': {},
}
for mode in ('default', 'background_quadrature'):
    effective = dict(arguments)
    if mode == 'background_quadrature':
        effective['tol_ncdm_bg'] = 1e-8
    model = classy.Class()
    model.set(effective)
    started = time.monotonic()
    model.compute(['thermodynamics'])
    tables = {'background': model.get_background(), 'thermodynamics': model.get_thermodynamics()}
    case = {'arguments': effective, 'elapsed_seconds': time.monotonic() - started, 'tables': {}}
    for name, table in tables.items():
        file = HERE / f'{mode}_{name}.npz'
        np.savez_compressed(file, **table)
        z = np.asarray(table['z'])
        columns = {}
        for key, values in table.items():
            values = np.asarray(values)
            finite = np.isfinite(values)
            bad_z = z[~finite]
            columns[key] = {
                'rows': int(values.size), 'nonfinite_count': int((~finite).sum()),
                'finite_min': float(values[finite].min()) if finite.any() else None,
                'finite_max': float(values[finite].max()) if finite.any() else None,
                'nonfinite_z_min': float(bad_z.min()) if bad_z.size else None,
                'nonfinite_z_max': float(bad_z.max()) if bad_z.size else None,
            }
        case['tables'][name] = {'file': file.name, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                               'columns': columns}
    receipt['cases'][mode] = case
    model.struct_cleanup()
    model.empty()
(HERE / 'native_table_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps({mode: {name: {key: col['nonfinite_count'] for key, col in data['columns'].items()
                               if col['nonfinite_count']} for name, data in case['tables'].items()}
                  for mode, case in receipt['cases'].items()}, indent=2))
