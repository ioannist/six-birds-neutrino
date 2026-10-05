"""Check exact failed inputs, numerical-only controls, and saved finite spectra."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
input_path = HERE / 'failed_class_arguments.json'
inputs = json.loads(input_path.read_text())
original = inputs['translated_class_arguments']
names = {'fresh_default_omp1': False, 'fresh_default_omp8': False,
         'earlier_start_omp8': False, 'intermediate_omp8': True,
         'background_quadrature_omp8': True, 'canonical_default_ell3200_omp8': False,
         'canonical_background_quadrature_ell3200_omp8': True}
records, modules = [], set()
for name, succeeded in names.items():
    path = HERE / (name + '.json')
    result = json.loads(path.read_text())
    assert result['succeeded'] is succeeded
    assert result['input_sha256'] == hashlib.sha256(input_path.read_bytes()).hexdigest()
    expected = dict(original)
    for key, value in result.get('declared_precision_overrides', {}).items():
        assert key not in original
        expected[key] = value
    if result.get('coverage_override_l_max_scalars') is not None:
        expected['l_max_scalars'] = result['coverage_override_l_max_scalars']
    assert result['native_class_arguments'] == expected
    modules.add(result['native_module_sha256'])
    if succeeded:
        spectra_path = ROOT / result['spectra_file']
        assert hashlib.sha256(spectra_path.read_bytes()).hexdigest() == result['spectra_sha256']
        with np.load(spectra_path) as spectra:
            assert int(spectra['ell'][-1]) == expected['l_max_scalars']
            assert all(np.all(np.isfinite(spectra[key])) for key in spectra.files)
    else:
        assert result['error_type'] == 'CosmoComputationError'
        assert 'scalar initial conditions assume tight-coupling approximation turned on' in result['error']
    records.append({'replay': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'succeeded': succeeded, 'exec_exit_code': 0 if succeeded else 1,
                    'omp_threads': result['omp_threads'], 'l_max_scalars': expected['l_max_scalars']})
assert len(modules) == 1
repair = json.loads((HERE / 'configuration_repair_verification.json').read_text())
assert len(repair['records']) == 4
for config in repair['records']:
    expected_coverage = 4095 if 'sptd1' in config['configuration'] else 3200
    expected_replay = ('background_quadrature_omp8.json' if expected_coverage == 4095
                       else 'canonical_background_quadrature_ell3200_omp8.json')
    assert config['initialized_native_l_max_scalars'] == expected_coverage
    assert config['native_replay_file'] == expected_replay
    assert config['native_replay_sha256'] == hashlib.sha256((HERE / config['native_replay_file']).read_bytes()).hexdigest()
    assert hashlib.sha256((ROOT / config['configuration']).read_bytes()).hexdigest() == config['new_configuration_sha256']
output = HERE / 'replay_comparison_verification.json'
assert not output.exists()
output.write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'exact_known_failure_and_explicit_numerical_repair_only', 'records': records,
    'all_physical_inputs_preserved': True, 'single_native_module_used': True,
    'all_four_canonical_configuration_replays_bound': True,
    'uniform_numerical_error_certified': False, 'posterior_accuracy_certified': False,
    'stopped_default_sampler_resumed': False}, indent=2, allow_nan=False) + '\n')
print('Four identical native failures and three successful numerical controls verified.')
