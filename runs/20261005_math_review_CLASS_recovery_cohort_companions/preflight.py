"""Evaluate a fresh start with the real backend guard and finite native providers."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import run_cobaya as launcher
from cobaya.model import get_model

seed = int(sys.argv[1])
folder = HERE / f'seed{seed}'
entry = json.loads((folder / 'preparation_receipt.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert os.environ['OMP_NUM_THREADS'] == entry['OMP_NUM_THREADS']
for p, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / p) == digest
assert sha(ROOT / entry['config']) == entry['config_sha256']
cfg = yaml.safe_load((ROOT / entry['config']).read_text())
backend = launcher._validate_native_backend(cfg)
assert backend['module_sha256'] == entry['module_sha256'] and backend['module'] == entry['module']
bad = deepcopy(cfg)
bad['notes']['classy_backend']['module_sha256'] = '0' * 64
try:
    launcher._validate_native_backend(bad)
except ValueError:
    pass
else:
    raise AssertionError('Wrong native backend accepted.')
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
with get_model(model_cfg, stop_at_error=True) as model:
    result = model.logposterior(entry['initial_point'], cached=False)
    assert np.isfinite([result.logpost, *result.logpriors, *result.loglikes]).all()
    arrays = {k: np.asarray(v, dtype=float) for k, v in model.provider.get_Cl(ell_factor=False, units='muK2').items()}
    assert arrays and all(np.isfinite(a).all() for a in arrays.values())
    names = list(model.likelihood)
with (folder / 'native_provider_arrays.npz').open('xb') as f:
    np.savez_compressed(f, **arrays)
with (folder / 'native_preflight_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed,
        'config_sha256': entry['config_sha256'], 'module_sha256': entry['module_sha256'],
        'initial_point': entry['initial_point'], 'logpost': float(result.logpost),
        'logpriors': list(map(float, result.logpriors)),
        'loglikes': dict(zip(names, map(float, result.loglikes))),
        'provider_arrays_sha256': sha(folder / 'native_provider_arrays.npz'),
        'actual_launcher_guard_checked': True, 'wrong_native_contract_refused': True,
        'fresh_initial_point_finite': True,
        'scope': 'Selected finite native start; no historical target equivalence, every-transition or convergence certificate.'},
        f, indent=2, allow_nan=False)
    f.write('\n')
print(seed, 'guarded native point finite', result.logpost, flush=True)
