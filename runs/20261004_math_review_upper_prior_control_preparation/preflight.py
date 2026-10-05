"""Isolate the prior factor at selected points using two fresh native models."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import camb
import cobaya.theories.camb.camb as wrapper
from cobaya.model import get_model
from sbt_spt_audit.boltzmann import FreshCAMB

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt = json.loads((HERE / 'preparation_receipt.json').read_text())
assert all(os.environ[k] == '1' for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'])
for path, digest in receipt['implementation_sha256'].items(): assert sha(ROOT / path) == digest
module = Path(camb.baseconfig.camblib._name).resolve()
results = {}
for group, entry in receipt['groups'].items():
    expected = entry['expected_environment']
    assert str(module) == expected['module'] and sha(module) == expected['module_sha256']
    assert str(Path(wrapper.__file__).resolve()) == expected['wrapper'] and sha(wrapper.__file__) == expected['wrapper_sha256']
    assert importlib.metadata.version('camb') == expected['solver_version']
    assert importlib.metadata.version('cobaya') == expected['Cobaya_version']
    assert sha(ROOT / entry['source_config']) == entry['source_config_sha256']
    assert sha(ROOT / entry['native_baseline_verification']) == entry['native_baseline_verification_sha256']
    results[group] = {}
    for cap, record in entry['controls'].items():
        path = ROOT / record['path']; assert sha(path) == record['sha256']
        config = yaml.safe_load(path.read_text()); upper = float(cap)
        assert 'sampler' not in config and 'output' not in config
        original = deepcopy(config); original['theory']['camb'].pop('class')
        points = {}
        with get_model(config, stop_at_error=True) as model, get_model(original, stop_at_error=True) as reference:
            assert isinstance(model.theory['camb'], FreshCAMB)
            assert model.theory['camb'].extra_args == reference.theory['camb'].extra_args
            model.set_cache_size(50)
            for label, point in entry['points'].items():
                assert set(point) == set(model.parameterization.sampled_params())
                actual = model.logposterior(point, cached=True)
                native = reference.logposterior(point, cached=False)
                if point['mnu'] > upper:
                    assert np.isneginf(actual.logpost) and np.isneginf(native.logpost)
                    assert np.isneginf(sum(actual.logpriors)) and np.isneginf(sum(native.logpriors))
                    assert len(actual.loglikes) == len(native.loglikes) == 0
                    points[label] = {'point': point, 'status': 'outside_declared_mass_prior',
                                     'logposterior': None, 'native_likelihood_evaluated': False}
                    continue
                assert np.isfinite([actual.logpost, *actual.loglikes, *actual.logpriors]).all()
                assert actual.logpriors == native.logpriors and np.array_equal(actual.loglikes, native.loglikes)
                points[label] = {'point': point, 'status': 'finite_native_target', 'logposterior': float(actual.logpost),
                                 'logprior': float(sum(actual.logpriors)),
                                 'likelihood_components': {name: float(value) for name, value in zip(model.likelihood, actual.loglikes)},
                                 'upstream_forced_fresh_exact': True}
                print(group, cap, label, 'finite exact upstream replay', flush=True)
        results[group][cap] = points
        with (HERE / group / f'upper_{cap}' / 'native_points.json').open('x') as f:
            f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'group': group, 'upper_eV': upper,
                                'config_sha256': record['sha256'], 'points': points}, indent=2, allow_nan=False) + '\n')
comparisons = []
for group, caps in results.items():
    for cap in ['10', '20']:
        for label in ['original_reference', 'selected_latest_frozen_row']:
            base, changed = caps['5'][label], caps[cap][label]
            assert base['point'] == changed['point'] and base['likelihood_components'] == changed['likelihood_components']
            expected = -math.log(float(cap) / 5.0)
            prior_error = changed['logprior'] - base['logprior'] - expected
            posterior_error = changed['logposterior'] - base['logposterior'] - expected
            assert abs(prior_error) <= 1e-10 and abs(posterior_error) <= 1e-10
            comparisons.append({'group': group, 'upper_eV': float(cap), 'point_label': label,
                                'expected_log_density_shift': expected, 'prior_shift_error': prior_error,
                                'posterior_shift_error': posterior_error, 'likelihood_components_exactly_equal': True})
out = {'utc': datetime.now(timezone.utc).isoformat(), 'comparisons': comparisons,
       'module_sha256': sha(module), 'solver_version': importlib.metadata.version('camb'),
       'native_finite_points': sum(p['status'] == 'finite_native_target' for caps in results.values() for points in caps.values() for p in points.values()),
       'prior_rejected_points': sum(p['status'] == 'outside_declared_mass_prior' for caps in results.values() for points in caps.values() for p in points.values()),
       'maximum_prior_shift_error': max(abs(c['prior_shift_error']) for c in comparisons),
       'maximum_posterior_shift_error': max(abs(c['posterior_shift_error']) for c in comparisons),
       'scope': 'selected native factor isolation and extra-support evaluation only',
       'tail_probability_estimated': False, 'quantile_stability_estimated': False,
       'uniform_solver_accuracy_certified': False, 'samplers_launched': 0, 'paper_modified': False}
with (HERE / 'preflight_receipt.json').open('x') as f: f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'comparisons'}, indent=2), flush=True)
