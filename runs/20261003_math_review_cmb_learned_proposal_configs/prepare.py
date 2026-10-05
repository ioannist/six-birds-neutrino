"""Prepare matched-target trials with archived learned proposals and fresh seeds."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
assert not (HERE / 'manifest.json').exists()
source_root = ROOT / 'runs/20261003_math_review_cmb_accuracy_chain_configs'
shape_root = ROOT / 'runs/20261003_math_review_cmb_proposal_shape_check'
shape_inputs = json.loads((shape_root / 'inputs.json').read_text())
sampler_name = 'sbt_spt_audit.samplers.FullPrecisionMCMC'
records = []
for lens, original_seed, seed in [('A', 601, 811), ('B', 603, 813)]:
    source = source_root / f'{lens}_seed{original_seed}.yaml'
    original = source.read_bytes()
    config = yaml.safe_load(original)
    covariance_source = shape_root / f'{lens}_learned_default.covmat'
    covariance = covariance_source.read_bytes()
    assert hashlib.sha256(covariance).hexdigest() == shape_inputs['records'][covariance_source.name]['sha256']
    matrix = np.loadtxt(BytesIO(covariance))
    names = covariance.splitlines()[0].decode().removeprefix('#').split()
    sampled = [name for name, options in config['params'].items()
               if isinstance(options, dict) and 'prior' in options]
    assert names == sampled and matrix.shape == (len(names), len(names))
    assert np.all(np.isfinite(matrix))
    widths = np.sqrt(np.diag(matrix))
    antisymmetry = float(np.max(np.abs(matrix - matrix.T) / np.outer(widths, widths)))
    assert antisymmetry < 1e-12
    np.linalg.cholesky((matrix + matrix.T) / 2)
    local_covariance = HERE / covariance_source.name
    local_covariance.write_bytes(covariance)
    trial = deepcopy(config)
    trial['run_name'] = f'math_accuracy_learned_proposal_{lens}_seed{seed}'
    trial['sampler'][sampler_name]['seed'] = seed
    trial['sampler'][sampler_name]['covmat'] = str(local_covariance)
    trial['notes']['proposal_scope'] = ('Archived covariance learned by an unconverged default-target chain; '
                                       'proposal initialization only, not a posterior covariance certificate.')
    reconstructed = deepcopy(trial)
    reconstructed['run_name'] = config['run_name']
    reconstructed['sampler'][sampler_name]['seed'] = original_seed
    reconstructed['sampler'][sampler_name]['covmat'] = config['sampler'][sampler_name]['covmat']
    reconstructed['notes']['proposal_scope'] = config['notes']['proposal_scope']
    assert reconstructed == config
    saved = yaml.safe_dump(trial, sort_keys=False).encode()
    output = HERE / f'{lens}_seed{seed}.yaml'
    output.write_bytes(saved)
    (HERE / f'{lens}_source_seed{original_seed}.yaml').write_bytes(original)
    records.append({'lens': lens, 'seed': seed, 'source_seed': original_seed,
                    'source_config': str(source.relative_to(ROOT)),
                    'source_config_sha256': hashlib.sha256(original).hexdigest(),
                    'trial_config': str(output.relative_to(ROOT)),
                    'trial_config_sha256': hashlib.sha256(saved).hexdigest(),
                    'covariance_source': str(covariance_source.relative_to(ROOT)),
                    'covariance_sha256': hashlib.sha256(covariance).hexdigest(),
                    'covariance_max_antisymmetry_in_correlation_units': antisymmetry,
                    'sampled_parameter_order': sampled,
                    'exact_configuration_reconstruction_pass': True,
                    'target_priors_and_initialization_distributions_unchanged': True,
                    'stopping_gates_unchanged': True})
manifest = {'utc': datetime.now(timezone.utc).isoformat(),
            'scope': 'matched_controlled_target_learned_proposal_trials', 'records': records,
            'allowed_changes': ['run_name', 'sampler.seed', 'sampler.covmat', 'notes.proposal_scope'],
            'existing_samplers_changed': False, 'posterior_covariance_certified': False,
            'efficiency_improvement_verified': False, 'posterior_convergence_verified': False}
(HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
print(json.dumps(records, indent=2))
