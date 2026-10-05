"""Check the native target at each archived post-recovery endpoint."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from cobaya.model import get_model
from verify_chain_targets import compare_native_row

seed = int(sys.argv[1])
receipt = json.loads((HERE / 'growth_snapshot_receipt.json').read_text())
entry = receipt['records'][str(seed)]
directory = HERE / 'resumed_saved_rows' / f'seed{seed}'
chain = directory / entry['chain_name']
raw = chain.read_bytes()
assert hashlib.sha256(raw).hexdigest() == entry['snapshot_sha256']
assert hashlib.sha256((directory / 'resolved.yaml').read_bytes()).hexdigest() == entry['snapshot_config_sha256']
old = HERE / f'seed{seed}' / 'chains' / entry['chain_name']
assert raw.startswith(old.read_bytes())
rows = np.atleast_2d(np.loadtxt(chain))
assert len(rows) == entry['snapshot_rows'] > entry['pre_resume_rows']
header = raw.decode().splitlines()[0].lstrip('#').split()
cfg = yaml.safe_load((directory / 'resolved.yaml').read_text())
with get_model(cfg, stop_at_error=True) as model:
    check = compare_native_row(header, rows[-1], model, atol=1e-7, rtol=1e-10)
result = {'scope': 'last_saved_post_recovery_row_native_target_only',
          'original_seed': seed, 'resume_seed': entry['resume_seed'],
          'row_index': len(rows) - 1, 'first_post_recovery_row_index': entry['pre_resume_rows'],
          'chain_sha256': entry['snapshot_sha256'], 'atol': 1e-7, 'rtol': 1e-10,
          'check': check, 'posterior_convergence_verified': False,
          'uninterrupted_rng_trajectory_reconstructed': False}
(directory / 'native_target_verification.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(f'Fresh post-recovery native endpoint verified: seed {seed}', flush=True)
