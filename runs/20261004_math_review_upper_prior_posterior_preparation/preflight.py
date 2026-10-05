"""Replay the four distinct starts before launching each wider-prior cohort."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
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
from sbt_spt_audit.boltzmann import FreshCAMB, FRESH_CAMB_CLASS
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
parser = argparse.ArgumentParser(); parser.add_argument('group'); args = parser.parse_args()
entries = [e for e in json.loads((HERE / 'preparation_receipt.json').read_text())['entries'] if e['group'] == args.group]
assert len(entries) == 4
assert all(os.environ[k] == '1' for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'])
e0 = entries[0]
module = Path(camb.baseconfig.camblib._name).resolve()
assert str(module) == e0['module'] and sha(module) == e0['module_sha256']
assert str(Path(wrapper.__file__).resolve()) == e0['wrapper'] and sha(wrapper.__file__) == e0['wrapper_sha256']
assert importlib.metadata.version('camb') == e0['solver_version'] == '2.0.4'
assert importlib.metadata.version('cobaya') == e0['Cobaya_version'] == '3.6.2'
base = yaml.safe_load((ROOT / e0['config']).read_text())
for e in entries:
    assert sha(ROOT / e['config']) == e['config_sha256']
    assert sha(ROOT / e['control']) == e['control_sha256']
    assert sha(ROOT / e['proposal']['path']) == e['proposal']['sha256']
    for path, digest in e['implementation_sha256'].items(): assert sha(ROOT / path) == digest
    cfg = yaml.safe_load((ROOT / e['config']).read_text())
    assert cfg['theory'] == base['theory'] and cfg['likelihood'] == base['likelihood']
    for name, block in base['params'].items():
        assert {k: v for k, v in block.items() if k != 'ref'} == {k: v for k, v in cfg['params'][name].items() if k != 'ref'}
    assert e['initial_point'] == {n: cfg['params'][n]['ref'] for n in e['initial_point']}
model_cfg = {k: deepcopy(base[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in base}
upstream = deepcopy(model_cfg); upstream['theory']['camb'].pop('class')
with get_model(model_cfg, stop_at_error=True) as model, get_model(upstream, stop_at_error=True) as reference:
    assert isinstance(model.theory['camb'], FreshCAMB)
    assert model.theory['camb'].extra_args == reference.theory['camb'].extra_args
    model.set_cache_size(50)
    for e in entries:
        actual = model.logposterior(e['initial_point'], cached=True)
        native = reference.logposterior(e['initial_point'], cached=False)
        assert np.isfinite([actual.logpost, *actual.loglikes, *actual.logpriors]).all()
        assert np.array_equal(actual.loglikes, native.loglikes) and actual.logpriors == native.logpriors
        components = {n: float(v) for n, v in zip(model.likelihood, actual.loglikes)}
        previous = json.loads((ROOT / e['control']).read_text())['points'][e['initial_point_label']]
        assert previous['point'] == e['initial_point'] and previous['likelihood_components'] == components
        assert previous['logposterior'] == float(actual.logpost) and previous['logprior'] == float(sum(actual.logpriors))
        proof = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': e['seed'], 'group': e['group'],
                 'initial_point': e['initial_point'], 'config_sha256': e['config_sha256'], 'module_sha256': sha(module),
                 'native_initial_point_verified': True, 'likelihood_components': components, 'logpriors': list(actual.logpriors),
                 'logposterior': float(actual.logpost), 'previous_preflight_components_exact': True,
                 'upstream_forced_fresh_likes_and_priors_exact': True, 'FreshCAMB_class': FRESH_CAMB_CLASS,
                 'sampler_cache_resize_challenge': 50, 'effective_CAMB_extra_args': model.theory['camb'].extra_args,
                 'posterior_certified': False}
        with (HERE / f'seed{e["seed"]}' / 'initial_point_verification.json').open('x') as f:
            f.write(json.dumps(proof, indent=2, allow_nan=False) + '\n')
        print(e['seed'], 'initial point exact to previous preflight and forced-fresh upstream', flush=True)
