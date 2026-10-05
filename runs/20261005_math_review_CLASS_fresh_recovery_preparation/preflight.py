"""Replay a preserved terminal row under the guarded recovery target before launch."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

import classy
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import run_cobaya as launcher
from verify_chain_targets import compare_native_row
from cobaya.model import get_model

seed = int(sys.argv[1])
folder = HERE / f'seed{seed}'
entry = json.loads((folder / 'preparation_receipt.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for path, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert sha(ROOT / entry['config']) == entry['config_sha256']
assert sha(ROOT / entry['source_chain']) == entry['source_chain_sha256']
assert sha(ROOT / entry['proposal']) == entry['proposal_sha256']
assert os.environ['OMP_NUM_THREADS'] == entry['OMP_NUM_THREADS']
cfg = yaml.safe_load((ROOT / entry['config']).read_text())
backend = launcher._validate_native_backend(cfg)
assert backend['module'] == entry['module'] and backend['module_sha256'] == entry['module_sha256']
bad = deepcopy(cfg)
bad['notes']['classy_backend']['module_sha256'] = '0' * 64
try:
    launcher._validate_native_backend(bad)
except ValueError:
    pass
else:
    raise AssertionError('Wrong guarded CLASS contract accepted.')
header = list(entry['source_row'])
row = np.array([float(entry['source_row'][k]) for k in header])
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
with get_model(model_cfg, stop_at_error=True) as model:
    result = compare_native_row(header, row, model, 1e-9, 0)
    arrays = {k: np.asarray(v, dtype=float) for k, v in model.provider.get_Cl(ell_factor=False, units='muK2').items()}
    assert all(np.isfinite(a).all() for a in arrays.values())
assert all(abs(v) <= 1e-9 for v in result['fresh_minus_recorded'].values())
with (folder / 'native_provider_arrays.npz').open('xb') as f:
    np.savez_compressed(f, **arrays)
module = Path(importlib.import_module(classy.Class.__module__).__file__).resolve()
with (folder / 'native_preflight_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed, 'parent_seed': entry['parent_seed'],
        'config_sha256': entry['config_sha256'], 'module_sha256': sha(module), 'loaded_CLASS_version': classy.__version__,
        'initial_point': entry['initial_point'], 'selected_terminal_row_native_match': True,
        'native_check': result, 'provider_arrays_sha256': sha(folder / 'native_provider_arrays.npz'),
        'actual_launcher_guard_checked': True, 'wrong_guarded_contract_refused': True,
        'scope': 'Selected preserved terminal row; no exact resume, global target equivalence or convergence theorem.'},
        f, indent=2, allow_nan=False)
    f.write('\n')
print(seed, 'preserved row matches recovery native target', result['fresh_minus_recorded'], flush=True)
