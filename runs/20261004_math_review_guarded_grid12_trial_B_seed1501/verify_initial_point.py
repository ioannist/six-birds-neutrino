"""Check actual native likelihood, prior and posterior before sampler launch."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import yaml
import classy._classy as native
from cobaya.model import get_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from run_cobaya import _validate_classy_backend

prep = json.loads((HERE / 'preparation_receipt.json').read_text())
cfg_path = ROOT / prep['config']
assert hashlib.sha256(cfg_path.read_bytes()).hexdigest() == prep['config_sha256']
module = Path(native.__file__).resolve()
assert module == Path(prep['native_module_path']).resolve()
assert hashlib.sha256(module.read_bytes()).hexdigest() == prep['native_module_sha256']
cfg = yaml.safe_load(cfg_path.read_text())
backend = _validate_classy_backend(cfg)
assert backend['module_sha256'] == prep['native_module_sha256']
assert not (HERE / 'initial_point_verification.json').exists()
runtime = {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
           'module': str(module), 'module_sha256': backend['module_sha256'],
           'status': 'running_native_initial_point_replay', 'OMP_NUM_THREADS': os.environ['OMP_NUM_THREADS']}
(HERE / 'initial_point_runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
start = time.monotonic()
with get_model(cfg, stop_at_error=True) as model:
    point = prep['initial_point']
    assert set(model.parameterization.sampled_params()) == set(point)
    post = model.logposterior(point, cached=False)
    assert np.isfinite(post.logpost) and np.all(np.isfinite(post.logpriors)) and np.all(np.isfinite(post.loglikes))
    likes = model.loglikes(point, as_dict=True, return_derived=False, cached=True)
    chi2 = {n: -2 * float(v) for n, v in likes.items()}
    assert set(chi2) == set(prep['expected_native_chi2']) and len(chi2) == 6
    discrepancy = {n: chi2[n] - prep['expected_native_chi2'][n] for n in chi2}
    assert max(map(abs, discrepancy.values())) <= 1e-8
    actual = model.theory['classy'].classy.pars
    assert actual['N_ncdm'] == 3
    masses = [float(v) for v in actual['m_ncdm'].split(',')]
    assert len(masses) == 3 and np.isclose(sum(masses), point['mnu_sample'], rtol=1e-13, atol=0)
result = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': prep['scope'],
          'module_sha256': prep['native_module_sha256'], 'config_sha256': prep['config_sha256'],
          'covariance_sha256': prep['covariance_sha256'], 'initial_point': point,
          'native_chi2': chi2, 'native_anchor_component_discrepancies': discrepancy,
          'native_logprior': list(map(float, post.logpriors)), 'native_logposterior': float(post.logpost),
          'CLASS_masses': masses, 'elapsed_seconds': time.monotonic() - start,
          'initial_point_finite_native_target_verified': True,
          'posterior_convergence_or_uniform_accuracy_certified': False}
(HERE / 'initial_point_verification.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
runtime['status'] = 'complete_native_initial_point_replay'
(HERE / 'initial_point_runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
print(json.dumps({'native_anchor_component_discrepancies': discrepancy,
                  'native_logposterior': result['native_logposterior']}, indent=2))
