"""Selected-point diagnostic ablations, never a posterior fallback policy."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback

import camb
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
prep = ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation'
entry = json.loads((prep / 'reproduction_contract.json').read_text())['entries'][str(args.seed)]
for path, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert sha(entry['module']) == entry['module_sha256']
assert sha(entry['wrapper']) == entry['wrapper_sha256']
resolved = ROOT / entry['run_dir'] / 'resolved.yaml'
assert sha(resolved) == entry['effective_config_sha256']
cfg = yaml.safe_load(resolved.read_text())
point = json.loads((prep / f'seed{args.seed}/failed_proposal.json').read_text())['sampled']
folder = HERE / f'seed{args.seed}_nonlinear_ablation'
folder.mkdir(exist_ok=False)
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
with get_model(model_cfg, stop_at_error=True) as model:
    try:
        model.logposterior(point, cached=False)
    except ValueError as error:
        assert str(error) == 'provider spectrum tt must be finite and 1D.'
    else:
        raise AssertionError('Captured point no longer produces the original exception.')
    _, native = model.provider.get_CAMB_transfers()
    baseline = native.Params.copy()
    original = {
        'unlensed_scalar': native.get_unlensed_scalar_cls(lmax=4095, raw_cl=True, CMB_unit='muK'),
        'lensed_scalar': native.get_lensed_scalar_cls(lmax=4095, raw_cl=True, CMB_unit='muK'),
        'lens_potential': native.get_lens_potential_cls(lmax=4095, raw_cl=True, CMB_unit='muK'),
    }

records = []
for variant in ['original_mead2020', 'linear_lensing', 'mead2016', 'takahashi']:
    params = baseline.copy()
    if variant == 'linear_lensing':
        params.NonLinear = camb.model.NonLinear_none
    elif variant != 'original_mead2020':
        params.NonLinearModel.set_params(halofit_version=variant)
    before, after = str(baseline), str(params)
    with (folder / f'{variant}_params.txt').open('x') as f:
        f.write(after + '\n')
    record = {'variant': variant, 'NonLinear': str(params.NonLinear),
              'halofit_version': str(params.NonLinearModel.halofit_version),
              'parameters_sha256': sha(folder / f'{variant}_params.txt')}
    if variant == 'original_mead2020':
        assert before == after
    arrays = {}
    try:
        result = camb.get_results(params)
        for label, method in [('unlensed_scalar', result.get_unlensed_scalar_cls),
                              ('lensed_scalar', result.get_lensed_scalar_cls),
                              ('lens_potential', result.get_lens_potential_cls)]:
            arr = method(lmax=4095, raw_cl=True, CMB_unit='muK')
            arrays[label] = arr
            record[label] = {'shape': list(arr.shape), 'all_finite': bool(np.isfinite(arr).all()),
                             'nan_count': int(np.isnan(arr).sum()), 'inf_count': int(np.isinf(arr).sum()),
                             'equal_to_original_with_nan': bool(np.array_equal(arr, original[label], equal_nan=True))}
        record['status'] = 'arrays_returned'
    except Exception as error:
        record.update(status='exception', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
    with (folder / f'{variant}_arrays.npz').open('xb') as f:
        np.savez_compressed(f, **arrays)
    record['arrays_sha256'] = sha(folder / f'{variant}_arrays.npz')
    with (folder / f'{variant}_receipt.json').open('x') as f:
        f.write(json.dumps(record, indent=2, allow_nan=False) + '\n')
    records.append(record)
    print(args.seed, variant, {k: v.get('all_finite') for k, v in record.items() if isinstance(v, dict)}, flush=True)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': args.seed, 'sampled': point,
       'native_module_sha256': entry['module_sha256'], 'original_resolved_sha256': sha(resolved),
       'records': records, 'scope': 'selected-point native nonlinear-lensing ablations only',
       'production_target_changed': False, 'posterior_qualified': False,
       'ablation_is_solver_repair_or_uniform_support_proof': False}
with (folder / 'ablation_summary.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
