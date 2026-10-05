"""Exercise actual native launch contracts and fresh transfer controls per target."""
import argparse
from email.parser import BytesParser
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

import camb
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import run_cobaya as launcher
from cobaya.model import get_model
from sbt_spt_audit.boltzmann import FreshCAMB, FRESH_CAMB_CLASS

parser = argparse.ArgumentParser()
parser.add_argument('group')
args = parser.parse_args()
entries = [e for e in json.loads((HERE / 'preparation_receipt.json').read_text())['entries'] if e['group'] == args.group]
assert len(entries) == 4
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert all(os.environ[k] == '1' for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'])
assert os.environ['LD_LIBRARY_PATH'] == entries[0]['required_LD_LIBRARY_PATH']
assert camb.__version__ == '2.0.4'
pkg_info_path = Path(camb.__file__).resolve().parent.parent / 'PKG-INFO'
pkg_info = BytesParser().parsebytes(pkg_info_path.read_bytes())
assert pkg_info['Name'] == 'camb' and pkg_info['Version'] == camb.__version__
build_preparation = json.loads((ROOT / 'runs/20261005_math_review_sigma_time_v3_packaged/source_preparation.json').read_text())
metadata_entry = next(e for e in build_preparation['files'] if e['path'] == 'camb-2.0.4/PKG-INFO')
assert sha(pkg_info_path) == metadata_entry['prepared_sha256'] == metadata_entry['original_sha256']
assert importlib.metadata.version('cobaya') == '3.6.2'
base = yaml.safe_load((ROOT / entries[0]['config']).read_text())
for e in entries:
    assert sha(ROOT / e['config']) == e['config_sha256']
    assert sha(ROOT / e['policy']) == e['policy_sha256']
    assert sha(ROOT / e['build_receipt']) == e['build_receipt_sha256']
    assert sha(ROOT / e['proposal']['path']) == e['proposal']['sha256']
    for path, digest in e['implementation_sha256'].items():
        assert sha(ROOT / path) == digest
    cfg = yaml.safe_load((ROOT / e['config']).read_text())
    assert cfg['theory'] == base['theory'] and cfg['likelihood'] == base['likelihood']
    assert {k: {n: v for n, v in block.items() if n != 'ref'} for k, block in cfg['params'].items()} == {
        k: {n: v for n, v in block.items() if n != 'ref'} for k, block in base['params'].items()}
    assert e['initial_point'] == {name: cfg['params'][name]['ref'] for name in e['initial_point']}
    native = launcher._validate_native_backend(cfg)
    assert native['module'] == e['module'] and native['module_sha256'] == e['module_sha256']
    bad = deepcopy(cfg)
    bad['notes']['camb_backend']['module_sha256'] = '0' * 64
    try:
        launcher._validate_native_backend(bad)
    except ValueError as error:
        assert 'does not match' in str(error)
    else:
        raise AssertionError('Wrong native contract accepted.')
model_cfg = {k: deepcopy(base[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in base}
upstream = deepcopy(model_cfg)
upstream['theory']['camb'].pop('class')
with get_model(model_cfg, stop_at_error=True) as model, get_model(upstream, stop_at_error=True) as reference:
    assert isinstance(model.theory['camb'], FreshCAMB)
    assert model.theory['camb'].extra_args == reference.theory['camb'].extra_args
    model.set_cache_size(50)
    for e in entries:
        observed = model.logposterior(e['initial_point'], cached=True)
        arrays = {k: np.array(v, dtype=float, copy=True) for k, v in model.provider.get_Cl(ell_factor=False, units='muK2').items()}
        native = reference.logposterior(e['initial_point'], cached=False)
        reference_arrays = reference.provider.get_Cl(ell_factor=False, units='muK2')
        assert np.isfinite([observed.logpost, *observed.loglikes, *observed.logpriors]).all()
        assert observed.logpost == native.logpost and observed.logpriors == native.logpriors
        assert np.array_equal(observed.loglikes, native.loglikes)
        assert set(arrays) == set(reference_arrays)
        assert all(np.isfinite(a).all() and np.array_equal(a, reference_arrays[k]) for k, a in arrays.items())
        folder = HERE / f'seed{e["seed"]}'
        with (folder / 'initial_provider_arrays.npz').open('xb') as f:
            np.savez_compressed(f, **arrays)
        proof = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': e['seed'], 'group': e['group'],
            'initial_point': e['initial_point'], 'config_sha256': e['config_sha256'],
            'module_sha256': sha(e['module']), 'policy_sha256': e['policy_sha256'],
            'loaded_CAMB_version': camb.__version__, 'source_PKG_INFO_sha256': sha(pkg_info_path),
            'distribution_metadata_version': importlib.metadata.version('camb'),
            'native_initial_point_verified': True, 'likelihood_components': dict(zip(model.likelihood, map(float, observed.loglikes))),
            'logpriors': list(map(float, observed.logpriors)), 'logposterior': float(observed.logpost),
            'upstream_forced_fresh_likes_and_priors_exact': True, 'provider_arrays_exact': True,
            'provider_arrays_sha256': sha(folder / 'initial_provider_arrays.npz'), 'FreshCAMB_class': FRESH_CAMB_CLASS,
            'sampler_cache_resize_challenge': 50, 'actual_launcher_native_guard_checked': True,
            'wrong_module_hash_refused': True, 'posterior_certified': False}
        with (folder / 'initial_point_verification.json').open('x') as f:
            f.write(json.dumps(proof, indent=2, allow_nan=False) + '\n')
        print(e['seed'], 'finite start, exact forced-fresh native replay and launcher guard', flush=True)
