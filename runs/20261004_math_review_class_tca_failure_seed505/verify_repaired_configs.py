"""Bind the explicit future configuration repair to the successful native replay."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model

repair = json.loads((HERE / 'background_quadrature_omp8.json').read_text())
intermediate = json.loads((HERE / 'intermediate_omp8.json').read_text())
assert repair['succeeded'] and intermediate['succeeded']
assert repair['declared_precision_overrides'] == {'tol_ncdm_bg': 1e-8}
assert repair['native_module_sha256'] == intermediate['native_module_sha256']
assert repair['input_sha256'] == intermediate['input_sha256']
for result in [repair, intermediate]:
    spectrum_path = ROOT / result['spectra_file']
    assert hashlib.sha256(spectrum_path.read_bytes()).hexdigest() == result['spectra_sha256']
    with np.load(spectrum_path) as spectra:
        assert spectra['ell'][-1] == 4095
        assert all(np.all(np.isfinite(spectra[name])) for name in spectra.files)
failed = json.loads((HERE / 'failed_class_arguments.json').read_text())
records = []
for name in ['cmb_spt2018_plancksubset_desi_mnu', 'cmb_sptd1_plancksubset_desi_mnu',
             'cmb_baseline_spt2018_plancksubset_mnu', 'cmb_baseline_sptd1_plancksubset_mnu']:
    path = ROOT / 'configs/neutrino' / (name + '.yaml')
    raw = path.read_bytes()
    config = yaml.safe_load(raw)
    old_bytes = subprocess.check_output(['git', 'show', '3f8ea9a:' + str(path.relative_to(ROOT))], cwd=ROOT)
    old = yaml.safe_load(old_bytes)
    reconstructed = deepcopy(config)
    assert reconstructed['theory']['classy']['extra_args'].pop('tol_ncdm_bg') == 1e-8
    reconstructed['notes'].pop('class_precision')
    assert reconstructed == old
    archived_old = HERE / (name + '_before.yaml')
    if archived_old.exists():
        assert archived_old.read_bytes() == old_bytes
    else:
        archived_old.write_bytes(old_bytes)
    model_config = deepcopy(config)
    model_config['packages_path'] = str(ROOT / 'external/cobaya_packages')
    with get_model(model_config, stop_at_error=True) as model:
        actual = dict(model.theory['classy'].extra_args)
        expected = dict(failed['native_extra_args'], tol_ncdm_bg=1e-8)
        assert set(actual.pop('output').split()) == set(expected.pop('output').split())
        coverage = actual['l_max_scalars']
        if coverage == 3200:
            native_path = HERE / 'canonical_background_quadrature_ell3200_omp8.json'
        else:
            assert coverage == 4095, (name, coverage)
            native_path = HERE / 'background_quadrature_omp8.json'
        native = json.loads(native_path.read_text())
        assert native['succeeded'] and native['spectrum_ell_max'] == coverage
        assert native['native_module_sha256'] == repair['native_module_sha256']
        assert native['input_sha256'] == repair['input_sha256']
        expected['l_max_scalars'] = coverage
        assert actual == expected, (name, actual, expected)
    records.append({'configuration': str(path.relative_to(ROOT)),
                    'old_configuration_sha256': hashlib.sha256(old_bytes).hexdigest(),
                    'new_configuration_sha256': hashlib.sha256(raw).hexdigest(),
                    'only_declared_precision_and_explanatory_note_changed': True,
                    'initialized_native_extra_args_match_successful_replay': True,
                    'initialized_native_l_max_scalars': coverage,
                    'native_replay_file': native_path.name,
                    'native_replay_sha256': hashlib.sha256(native_path.read_bytes()).hexdigest()})
output = HERE / 'configuration_repair_verification.json'
assert not output.exists()
output.write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'known_failure_point_and_future_configuration_repair_only',
    'records': records, 'native_successful_replay': 'background_quadrature_omp8.json',
    'native_successful_replay_sha256': hashlib.sha256((HERE / 'background_quadrature_omp8.json').read_bytes()).hexdigest(),
    'historical_runs_rewritten': False, 'stopped_default_chain_resumed': False,
    'uniform_numerical_accuracy_certified': False, 'posterior_convergence_verified': False},
    indent=2, allow_nan=False) + '\n')
print('All four initialized canonical configurations match the successful repair replay.')
