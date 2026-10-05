"""Check selected saved guarded-trial rows with fresh native likelihood evaluations."""
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

snapshot = HERE / 'guarded_initial_rows'
receipt = json.loads((snapshot / 'snapshot_receipt.json').read_text())
build = json.loads((HERE / 'build_verification_receipt.json').read_text())
module = Path(importlib.import_module(classy.Class.__module__).__file__)
assert str(module) == build['module']
assert hashlib.sha256(module.read_bytes()).hexdigest() == build['module_sha256'] == receipt['module_sha256']
config_bytes = (snapshot / 'resolved.yaml').read_bytes()
assert hashlib.sha256(config_bytes).hexdigest() == receipt['snapshot_config_sha256']
cfg = yaml.safe_load(config_bytes)
cfg.pop('output')
chain = next((snapshot / 'chains').glob('*.txt'))
raw = chain.read_bytes()
assert hashlib.sha256(raw).hexdigest() == receipt['chain_sha256']
header = raw.splitlines()[0].decode().lstrip('#').split()
rows = np.atleast_2d(np.loadtxt(BytesIO(raw)))
assert len(rows) == receipt['stored_rows'] >= 2
with get_model(cfg, stop_at_error=True) as model:
    assert type(model.theory['classy'].classy) is classy.Class
    actual_args = dict(model.theory['classy'].extra_args)
    assert all(actual_args[name] == value for name, value in cfg['theory']['classy']['extra_args'].items())
    assert actual_args['l_max_scalars'] == 4095 and len(model.likelihood) == 6
    checks = [dict(row_index=int(index), **compare_native_row(header, rows[index], model, atol=1e-7, rtol=1e-10))
              for index in [0, len(rows)-1]]
result = {'utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'selected_new_guarded_saved_rows_full_native_target',
          'module_sha256': build['module_sha256'], 'chain_sha256': receipt['chain_sha256'],
          'snapshot_config_sha256': receipt['snapshot_config_sha256'],
          'actual_initialized_native_extra_args': actual_args,
          'current_covariance_helper_source_sha256': {
              str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [ROOT / 'src/sbt_spt_audit/metrics.py', ROOT / 'src/sbt_spt_audit/likelihoods/desi_dr2_bao.py']},
          'atol': 1e-7, 'rtol': 1e-10, 'checks': checks,
          'every_transition_verified': False, 'posterior_convergence_certified': False,
          'uniform_numerical_accuracy_certified': False}
with (snapshot / 'native_target_verification.json').open('x') as handle:
    handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('Both selected guarded rows verified against all native components, prior, and posterior.')
