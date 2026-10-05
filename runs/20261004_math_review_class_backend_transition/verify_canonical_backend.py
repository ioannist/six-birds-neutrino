"""Check canonical contracts against actual Cobaya theory initialization."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import sys

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
from run_cobaya import _validate_classy_backend
from cobaya.model import get_model

names = ['cmb_spt2018_plancksubset_desi_mnu', 'cmb_sptd1_plancksubset_desi_mnu',
         'cmb_baseline_spt2018_plancksubset_mnu', 'cmb_baseline_sptd1_plancksubset_mnu']
records = []
for name in names:
    path = ROOT / 'configs/neutrino' / (name + '.yaml')
    config = yaml.safe_load(path.read_text())
    backend = _validate_classy_backend(config)
    assert backend is not None
    conflicting = deepcopy(config)
    conflicting['theory']['classy']['path'] = '/different/native/backend'
    try:
        _validate_classy_backend(conflicting)
    except ValueError as exc:
        assert 'conflicting theory path' in str(exc)
    else:
        raise AssertionError('Conflicting solver path was accepted')
    config['theory']['classy']['path'] = 'global'
    with get_model(config, packages_path=str(ROOT / 'external/cobaya_packages'),
                   stop_at_error=True) as model:
        theory = model.theory['classy']
        assert type(theory.classy) is importlib.import_module('classy').Class
        module = Path(importlib.import_module(type(theory.classy).__module__).__file__).resolve()
        assert str(module) == backend['module']
        assert hashlib.sha256(module.read_bytes()).hexdigest() == backend['module_sha256']
        records.append({'config': str(path.relative_to(ROOT)),
                        'config_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'backend': backend,
                        'actual_theory_path': theory.path,
                        'initialized_likelihoods': list(model.likelihood),
                        'conflicting_theory_path_rejected': True})
result = {'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
          'scope': 'actual_Cobaya_initialization_without_likelihood_evaluation_or_sampling',
          'runner_sha256': hashlib.sha256((ROOT / 'scripts/run_cobaya.py').read_bytes()).hexdigest(),
          'evaluator_sha256': hashlib.sha256((ROOT / 'scripts/eval_cmb_plancksubset_desi.py').read_bytes()).hexdigest()}
with (HERE / 'canonical_cobaya_initialization.json').open('x') as handle:
    handle.write(json.dumps(result, indent=2) + '\n')
print('All four actual canonical Cobaya models use the verified native Class type.')
