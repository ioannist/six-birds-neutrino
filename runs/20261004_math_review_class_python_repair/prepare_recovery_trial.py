"""Prepare a fresh guarded-backend trial from the failed family's last saved point."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
archive = ROOT / 'runs/20261004_math_review_class_tca_failure_seed701'
source_config = archive / 'recovery_segment/resume_input.yaml'
parent = yaml.safe_load(source_config.read_text())
assert parent['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] == 901
chain = next((archive / 'seed701/chains').glob('*.txt'))
raw = chain.read_bytes()
termination = json.loads((archive / 'termination_receipt.json').read_text())
assert hashlib.sha256(raw).hexdigest() == termination['archive_sha256'][str(chain.relative_to(archive))]
rows = np.atleast_2d(np.loadtxt(chain))
header = raw.splitlines()[0].decode().lstrip('#').split()
assert len(rows) == termination['complete_source_saved_rows'] == 152
assert np.isfinite(rows).all() and (rows[:, 0] > 0).all() and (rows[:, 0] == np.floor(rows[:, 0])).all()
values = dict(zip(header, rows[-1]))
config = deepcopy(parent)
config.pop('resume')
config.pop('output')
config['run_name'] = 'math_guarded_dragging_A_seed1201'
sampled = [name for name, block in config['params'].items() if isinstance(block, dict) and 'prior' in block]
assert len(sampled) == 10
for name in sampled:
    value = float(values[name])
    block = config['params'][name]
    assert block['prior']['min'] <= value <= block['prior']['max']
    block['ref'] = value
sampler = config['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
sampler['seed'] = 1201
source_covariance = next((archive / 'seed701/chains').glob('*.covmat'))
covariance = HERE / 'recovery_initial.covmat'
covariance.write_bytes(source_covariance.read_bytes())
np.linalg.cholesky(np.loadtxt(covariance))
sampler['covmat'] = str(covariance)
assert sampler['drag'] is True and sampler['temperature'] == 1
assert sampler['oversample_thin'] is False and sampler['oversample_power'] == .4
assert sampler['Rminus1_stop'] == .01 and sampler['Rminus1_cl_stop'] == .05
assert sampler['Rminus1_cl_level'] == .95 and sampler['max_samples'] == 20000
config['notes']['numerical_solver'] = 'Requires the manifest-verified separate CLASS3.4.0 finite-Jacobian backend. Same seven precision settings and physical likelihood/priors; distinct solver build, fresh output and RNG stream. Do not pool with unmodified-backend histories.'
config['notes']['warm_start_fit'] = 'Fixed last archived seed701/901 point; initialization only, not a guarded-backend posterior draw.'
config['notes']['proposal_scope'] = 'Archived static proposal initialization only; not a posterior covariance certificate.'
path = HERE / 'A_seed1201.yaml'
path.write_text(yaml.safe_dump(config, sort_keys=False))
assert config['likelihood'] == parent['likelihood'] and config['theory'] == parent['theory']
for name in config['params']:
    a, b = deepcopy(config['params'][name]), deepcopy(parent['params'][name])
    if isinstance(a, dict):
        a.pop('ref', None); b.pop('ref', None)
    assert a == b, name
native_cfg = deepcopy(config)
native_cfg.pop('output', None)
(HERE / 'parent_target_check_config.yaml').write_text(yaml.safe_dump(native_cfg, sort_keys=False))
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': 1201, 'parent_family_seed': 701,
           'parent_active_segment_seed': 901, 'parent_chain': str(chain.relative_to(ROOT)),
           'parent_chain_sha256': hashlib.sha256(raw).hexdigest(), 'parent_row_index': len(rows)-1,
           'fixed_initial_point': {name: float(values[name]) for name in sampled},
           'config_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
           'initial_covariance_sha256': hashlib.sha256(covariance.read_bytes()).hexdigest(),
           'same_physical_target_and_precision_settings_verified': True,
           'new_backend_same_numerical_target_as_unmodified_backend_asserted': False,
           'historical_prefix_appended': False, 'posterior_convergence_certified': False,
           'outdir': 'runs/20261004_math_review_guarded_dragging_chain_A_seed1201'}
(HERE / 'recovery_preparation_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Fresh seed1201 config prepared; physical target, precision, and stopping settings retained.')
