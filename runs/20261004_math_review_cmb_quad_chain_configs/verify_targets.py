"""Verify the common repaired native target and unchanged stopping gates."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model

manifest = json.loads((HERE / 'manifest.json').read_text())
assert len(manifest['runs']) == 8
sampler_name = 'sbt_spt_audit.samplers.FullPrecisionMCMC'
records = []
for lens in ['A', 'B']:
    cohort = [entry for entry in manifest['runs'] if entry['lens'] == lens]
    assert len(cohort) == 4
    target = None
    for entry in cohort:
        path = ROOT / entry['config']
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry['config_sha256']
        config = yaml.safe_load(raw)
        stripped = deepcopy(config)
        for key in ['run_name', 'notes']:
            stripped.pop(key, None)
        stripped['sampler'][sampler_name].pop('seed')
        for block in stripped['params'].values():
            if isinstance(block, dict):
                block.pop('ref', None)
        if target is None:
            target = stripped
        else:
            assert stripped == target
        assert config['sampler'][sampler_name]['seed'] == entry['seed']
        assert {name: config['params'][name]['ref'] for name in entry['fixed_initial_point']} == entry['fixed_initial_point']
    model_config = yaml.safe_load((ROOT / cohort[0]['config']).read_text())
    model_config['packages_path'] = str(ROOT / 'external/cobaya_packages')
    with get_model(model_config, stop_at_error=True) as model:
        actual = dict(model.theory['classy'].extra_args)
        assert actual['N_ncdm'] == 3 and actual['N_ur'] == .00641
        assert actual['l_max_scalars'] == 4095 and actual['tol_ncdm_bg'] == 1e-8
        assert set(actual['output'].split()) == {'tCl', 'pCl', 'lCl'}
        assert actual['non_linear'] == 'hmcode' and actual['lensing'] == 'yes'
        assert set(actual) == {'N_ncdm', 'N_ur', 'l_max_scalars', 'tol_ncdm_bg', 'output', 'non_linear', 'lensing'}
        sampled = list(model.parameterization.sampled_params())
        assert sampled == list(cohort[0]['fixed_initial_point'])
        assert len(model.likelihood) == 6
    records.append({'lens': lens, 'replicas': 4, 'initialized_native_extra_args': actual,
                    'all_four_native_targets_identical_within_lens': True,
                    'sampled_parameter_order': sampled})
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'eight_new_configuration_and_native_target_contracts_before_sampling',
           'records': records, 'manifest_sha256': hashlib.sha256((HERE / 'manifest.json').read_bytes()).hexdigest(),
           'pool_with_other_precision_targets': False, 'posterior_convergence_verified': False,
           'posterior_accuracy_certified': False}
output = HERE / 'target_verification.json'
assert not output.exists()
output.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('Eight configs and both initialized native numerical targets verified.')
