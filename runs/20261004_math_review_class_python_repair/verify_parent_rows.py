"""Verify selected archived rows against the guarded full native likelihood target."""
from datetime import datetime, timezone
import hashlib
import importlib
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

build = json.loads((HERE / 'build_verification_receipt.json').read_text())
module = Path(importlib.import_module(classy.Class.__module__).__file__)
assert str(module) == build['module'] and hashlib.sha256(module.read_bytes()).hexdigest() == build['module_sha256']
preparation = json.loads((HERE / 'recovery_preparation_receipt.json').read_text())
chain = ROOT / preparation['parent_chain']
raw = chain.read_bytes()
assert hashlib.sha256(raw).hexdigest() == preparation['parent_chain_sha256']
header = raw.splitlines()[0].decode().lstrip('#').split()
rows = np.atleast_2d(np.loadtxt(chain))
cfg = yaml.safe_load((HERE / 'parent_target_check_config.yaml').read_text())
with get_model(cfg, stop_at_error=True) as model:
    assert type(model.theory['classy'].classy) is classy.Class
    assert list(model.parameterization.sampled_params()) == list(preparation['fixed_initial_point'])
    checks = [dict(row_index=int(index), **compare_native_row(header, rows[index], model, atol=1e-7, rtol=1e-10))
              for index in [0, len(rows)-1]]
result = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'selected_archived_rows_full_guarded_native_target',
          'module_sha256': build['module_sha256'], 'chain_sha256': preparation['parent_chain_sha256'],
          'atol': 1e-7, 'rtol': 1e-10, 'checks': checks,
          'config_sha256': hashlib.sha256((HERE / 'A_seed1201.yaml').read_bytes()).hexdigest(),
          'all_old_rows_same_numerical_target_asserted': False,
          'posterior_convergence_certified': False}
(HERE / 'parent_native_target_verification.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('Both selected parent rows verified against all native components, prior, and posterior.')
