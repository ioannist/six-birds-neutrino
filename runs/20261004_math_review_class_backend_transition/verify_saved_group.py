"""Re-evaluate fresh guarded sampler endpoints through the actual native model."""
from datetime import datetime, timezone
import hashlib
import importlib
from io import BytesIO
import json
from pathlib import Path
import sys

import classy
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from cobaya.model import get_model
from verify_chain_targets import compare_native_row

group = sys.argv[1]
folder = HERE / 'fresh_saved_rows' / group
snapshot = json.loads((folder / 'snapshot_receipt.json').read_text())
module = Path(importlib.import_module(classy.Class.__module__).__file__)
module_sha = hashlib.sha256(module.read_bytes()).hexdigest()
assert module_sha == '7a5d736220b3d236f3dc7c89944d025fe3e4c7cb4c8e4473ef807c898fc71539'
records = []
for entry in snapshot['records']:
    chain = ROOT / entry['snapshot']
    raw = chain.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['chain_sha256']
    header = raw.splitlines()[0].decode().lstrip('#').split()
    rows = np.atleast_2d(np.loadtxt(BytesIO(raw)))
    assert len(rows) == entry['stored_rows'] >= 2
    config = (chain.parents[1] / 'resolved.yaml').read_bytes()
    assert hashlib.sha256(config).hexdigest() == entry['snapshot_config_sha256']
    cfg = yaml.safe_load(config)
    cfg.pop('output')
    with get_model(cfg, stop_at_error=True) as model:
        assert type(model.theory['classy'].classy) is classy.Class
        actual = dict(model.theory['classy'].extra_args)
        assert all(actual[name] == value for name, value in cfg['theory']['classy']['extra_args'].items())
        assert actual['l_max_scalars'] == 4095 and len(model.likelihood) == 6
        checks = [dict(row_index=int(index), **compare_native_row(header, rows[index], model, atol=1e-7, rtol=1e-10))
                  for index in [0, len(rows)-1]]
    records.append({'seed': entry['seed'], 'chain_sha256': entry['chain_sha256'],
                    'initialized_native_extra_args': actual, 'checks': checks})
    print(f"New seed {entry['seed']} first/last native checks pass.", flush=True)
result = {'utc': datetime.now(timezone.utc).isoformat(), 'group': group,
          'scope': 'selected_fresh_guarded_saved_rows_all_native_components',
          'module_sha256': module_sha, 'records': records,
          'atol': 1e-7, 'rtol': 1e-10,
          'snapshot_receipt_sha256': hashlib.sha256((folder / 'snapshot_receipt.json').read_bytes()).hexdigest(),
          'every_transition_verified': False, 'posterior_convergence_certified': False,
          'uniform_numerical_accuracy_certified': False}
with (folder / 'native_target_verification.json').open('x') as handle:
    handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
