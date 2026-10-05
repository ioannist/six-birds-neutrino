"""Prepare a new numerical target and frozen pilot proposal without pooling."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from sbt_spt_audit.metrics import covariance_solve

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANCHOR = HERE.parent / '20261004_math_review_guarded_precision_factor_controls_B'
SCOUT = HERE.parent / '20261004_math_review_guarded_medium_proposal_scout'
assert not (HERE / 'preparation_receipt.json').exists()
anchor_proof = json.loads((ANCHOR / 'completion_verification.json').read_text())
for file in anchor_proof['files']:
    assert hashlib.sha256((ROOT / file['path']).read_bytes()).hexdigest() == file['sha256']
scout = json.loads((SCOUT / 'scout_receipt.json').read_text())
for file in scout['files']:
    assert hashlib.sha256((ROOT / file['snapshot']).read_bytes()).hexdigest() == file['sha256']
cfg_path = ANCHOR / 'grid_only/input.yaml'
cfg = yaml.safe_load(cfg_path.read_text())
expected = json.loads((ANCHOR / 'grid_only/evaluation/metrics.json').read_text())['records']['quad_q50']
point = expected['point']
names = [n for n, p in cfg['params'].items() if isinstance(p, dict) and 'prior' in p]
assert set(point) == set(names) == set(scout['pilot_records']['B']['parameters'])
covariance = SCOUT / 'pilot_B.covmat'
assert covariance.read_text().splitlines()[0].lstrip('#').split() == names
covariance_solve(np.loadtxt(covariance), np.zeros(len(names)))
options = cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
assert options['learn_proposal'] and options['temperature'] == 1
options['seed'] = 1501
options['covmat'] = str(covariance)
for name, value in point.items():
    cfg['params'][name]['ref'] = value
cfg['run_name'] = 'math_guarded_grid12_trial_B_seed1501'
cfg['notes']['numerical_control'] = 'Medium dynamics and grid12 angular sampling; new numerical target. Do not pool with quadrature or medium-grid25 histories.'
cfg['notes']['proposal_scope'] = 'Frozen first-diagnostic quad_B covariance, unconverged pilot, initialization only; not a posterior covariance certificate.'
cfg['notes']['warm_start_fit'] = 'Exact verified grid12 quad_q50 coordinate; initialization only, not a posterior draw from this target.'
cfg['notes']['initialization_scope'] = 'Fresh seed1501 and output; one precision/proposal trial, not independent-replica posterior evidence.'
cfg['notes']['sampler_scope'] = 'Independent fresh RNG and integer outer holding times; unchanged learn/stop rules. Existing numerical cohorts remain controls.'
cfg['notes']['solver_backend'] = 'Pinned guarded CLASS module and checked backend contract; same physical model and priors, distinct spectrum-grid numerical target.'
theory = cfg['theory']['classy']['extra_args']
assert theory['l_logstep'] == 1.013 and theory['l_linstep'] == 12
assert options['Rminus1_stop'] == .01 and options['Rminus1_cl_stop'] == .05
assert not (HERE / 'run').exists()
target = HERE / 'input.yaml'
target.write_text(yaml.safe_dump(cfg, sort_keys=False))
# Verify only proposal inputs and metadata differ from the native anchor config.
original = yaml.safe_load(cfg_path.read_text())
clean = lambda c: {n: {k: v for k, v in p.items() if k not in ['ref', 'proposal']}
                  if isinstance(p, dict) else p for n, p in c['params'].items()}
assert clean(original) == clean(cfg)
assert {k: original.get(k) for k in ['likelihood', 'theory', 'prior']} == {
    k: cfg.get(k) for k in ['likelihood', 'theory', 'prior']}
prior_sampler = deepcopy(original['sampler'])
prior_sampler['sbt_spt_audit.samplers.FullPrecisionMCMC'].update(seed=1501, covmat=str(covariance))
assert cfg['sampler'] == prior_sampler
selection = json.loads((ANCHOR / 'selection_receipt.json').read_text())
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'one_fresh_B_grid12_frozen_quad_pilot_trial',
           'seed': 1501, 'lens': 'B', 'outdir': str((HERE / 'run').relative_to(ROOT)),
           'config': str(target.relative_to(ROOT)), 'config_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
           'covariance': str(covariance.relative_to(ROOT)), 'covariance_sha256': hashlib.sha256(covariance.read_bytes()).hexdigest(),
           'initial_point': point, 'expected_native_chi2': expected['native_chi2'],
           'native_module_path': selection['native_module_path'], 'native_module_sha256': selection['native_module_sha256'],
           'physical_model_and_priors_unchanged': True, 'existing_chains_modified_or_restarted': False,
           'distinct_target_no_historical_prefix_append': True, 'pilot_efficiency_or_accuracy_certified': False,
           'sources': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in [cfg_path, ANCHOR / 'completion_verification.json',
                                 SCOUT / 'scout_receipt.json', SCOUT / 'pilot_B.covmat']]}
with (HERE / 'preparation_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('Fresh B grid12 trial prepared; native initial-point replay is required before launch.')
