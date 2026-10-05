"""Replay a captured failing proposal and inspect already-calculated native spectra."""
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model

parser = argparse.ArgumentParser()
parser.add_argument('seed', type=int, choices=[2003, 2004])
args = parser.parse_args()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
repro = ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation'
contract = json.loads((repro / 'reproduction_contract.json').read_text())
entry = contract['entries'][str(args.seed)]
capture = repro / f'seed{args.seed}/failed_proposal.json'
failed = json.loads(capture.read_text())
point = failed['sampled']
assert all(math.isfinite(v) for v in point.values())
for path, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert sha(entry['module']) == entry['module_sha256']
assert sha(entry['wrapper']) == entry['wrapper_sha256']
original = ROOT / entry['run_dir'] / 'resolved.yaml'
assert sha(original) == entry['effective_config_sha256']
cfg = yaml.safe_load(original.read_text())
sampled_names = {name for name, block in cfg['params'].items() if isinstance(block, dict) and 'prior' in block}
assert set(point) == sampled_names
assert all(cfg['params'][name]['prior']['min'] <= value <= cfg['params'][name]['prior']['max']
           for name, value in point.items())
folder = HERE / f'seed{args.seed}_phase_classification'
folder.mkdir(exist_ok=False)
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
out = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': args.seed, 'sampled': point,
       'capture': str(capture.relative_to(ROOT)), 'capture_sha256': sha(capture),
       'original_native_module_sha256': entry['module_sha256'], 'original_resolved_sha256': sha(original),
       'theory_class': cfg['theory']['camb']['class'], 'numerical_settings_changed': False,
       'scope': 'captured point replay and native-array phase inspection; no solver repair or posterior qualification'}
arrays = {}
def save_array(label, value):
    arr = np.asarray(value, dtype=float)
    arrays[label] = arr
    finite = arr[np.isfinite(arr)]
    return {'shape': list(arr.shape), 'all_finite': bool(np.isfinite(arr).all()),
            'nan_count': int(np.isnan(arr).sum()), 'inf_count': int(np.isinf(arr).sum()),
            'finite_min': float(finite.min()) if finite.size else None,
            'finite_max': float(finite.max()) if finite.size else None}
with get_model(model_cfg, stop_at_error=True) as model:
    try:
        result = model.logposterior(point, cached=False)
        out['isolated_point_status'] = 'finite_evaluation' if math.isfinite(result.logpost) else 'nonfinite_posterior_return'
        if math.isfinite(result.logpost):
            out['finite_target_components'] = {'logpost': float(result.logpost),
                                               'logpriors': list(map(float, result.logpriors)),
                                               'loglikes': list(map(float, result.loglikes))}
    except Exception as error:
        out['isolated_point_status'] = 'exception'
        out['exception_type'] = type(error).__name__
        out['error'] = str(error)
        out['traceback'] = traceback.format_exc()
    try:
        cls = model.provider.get_Cl(ell_factor=False, units='muK2')
        out['provider_spectra'] = {key: save_array('provider_' + key, value) for key, value in cls.items()}
    except Exception as error:
        out['provider_inspection_error'] = f'{type(error).__name__}: {error}'
    _transfer_params, native = model.provider.get_CAMB_transfers()
    params = native.Params
    out['native_parameters'] = {name: float(getattr(params, name)) for name in ['H0', 'ombh2', 'omch2', 'omnuh2', 'YHe', 'TCMB']}
    out['native_parameters']['NonLinear'] = str(params.NonLinear)
    out['native_parameters']['halofit_version'] = str(params.NonLinearModel.halofit_version)
    out['native_spectra'] = {}
    for label, method in [('unlensed_scalar', native.get_unlensed_scalar_cls),
                          ('lensed_scalar', native.get_lensed_scalar_cls),
                          ('lens_potential', native.get_lens_potential_cls)]:
        try:
            arr = method(lmax=cfg['theory']['camb']['extra_args']['lmax'], CMB_unit='muK', raw_cl=True)
            out['native_spectra'][label] = save_array(label, arr)
        except Exception as error:
            out['native_spectra'][label] = {'inspection_error': f'{type(error).__name__}: {error}'}
with (folder / 'native_arrays.npz').open('xb') as f:
    np.savez_compressed(f, **arrays)
out['native_arrays_sha256'] = sha(folder / 'native_arrays.npz')
with (folder / 'phase_classification.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(args.seed, 'isolated captured point:', out['isolated_point_status'], flush=True)
print(json.dumps(out['native_spectra'], indent=2), flush=True)
