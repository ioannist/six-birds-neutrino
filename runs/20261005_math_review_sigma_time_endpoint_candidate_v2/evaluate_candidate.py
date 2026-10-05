"""Evaluate declared controls, preserving each success or native error separately."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
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
parser.add_argument('maximum', type=int, choices=[22, 24])
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
package = Path('/mnt/8tb/six-birds-ml/tmp/neutrino_CAMB204_sigma_time_endpoint_v2_20261005')
assert Path(camb.__file__).parent == package / 'camb'
prep = json.loads((ROOT / f'runs/20261005_math_review_sigma_limit{args.maximum}_candidate/source_preparation.json').read_text())
assert sha(package / 'fortran/halofit.f90') == prep['candidate_sha256']
module_sha = sha(package / 'camb/camblib.so')
contract = json.loads((ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation/reproduction_contract.json').read_text())['entries']['2003']
for path, digest in contract['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert sha(contract['module']) == contract['module_sha256']
assert sha(contract['wrapper']) == contract['wrapper_sha256']
resolved = ROOT / contract['run_dir'] / 'resolved.yaml'
assert sha(resolved) == contract['effective_config_sha256']
cfg = yaml.safe_load(resolved.read_text())
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
selection_path = HERE / 'selection_receipt.json'
selection = json.loads(selection_path.read_text())
folder = args.output.resolve()
folder.mkdir(exist_ok=False)
records = []
for index, selected in enumerate(selection['records']):
    assert sha(ROOT / selected['source_receipt']) == selected['source_receipt_sha256']
    point = selected['point']
    assert all(cfg['params'][name]['prior']['min'] < value < cfg['params'][name]['prior']['max']
               for name, value in point.items())
    record = {'selection_index': index, 'point': point, 'kind': selected['kind'],
              'native_error_is_posterior_rejection': False}
    try:
        # Fresh model per control prevents failed native state from entering the next control.
        with get_model(deepcopy(model_cfg), stop_at_error=True) as model:
            result = model.logposterior(point, cached=False)
            assert math.isfinite(result.logpost)
            cls = {key: np.asarray(value, dtype=float) for key, value in model.provider.get_Cl(ell_factor=False, units='muK2').items()}
            assert all(np.isfinite(a).all() for a in cls.values())
            path = folder / f'point{index}_provider_arrays.npz'
            with path.open('xb') as f:
                np.savez_compressed(f, **cls)
            record.update(status='finite_evaluation', logpost=float(result.logpost),
                          logpriors=list(map(float, result.logpriors)), loglikes=list(map(float, result.loglikes)),
                          provider_arrays=str(path.relative_to(ROOT)), provider_arrays_sha256=sha(path),
                          all_spectra_finite=True)
    except Exception as error:
        record.update(status='native_or_evaluation_error', exception_type=type(error).__name__,
                      error=str(error), traceback=traceback.format_exc())
    record['utc'] = datetime.now(timezone.utc).isoformat()
    with (folder / f'point{index}_receipt.json').open('x') as f:
        json.dump(record, f, indent=2, allow_nan=False)
        f.write('\n')
    records.append(record)
    print(args.maximum, index, record['status'], record.get('logpost', record.get('error')), flush=True)
assert sha(package / 'camb/camblib.so') == module_sha
out = {'utc': datetime.now(timezone.utc).isoformat(), 'maximum_sigma_refinement_level': args.maximum,
       'records': records, 'native_module': str(package / 'camb/camblib.so'), 'native_module_sha256': module_sha,
       'evaluation_config_sha256': sha(resolved), 'selection_receipt_sha256': sha(selection_path),
       'scope': selection['scope'], 'production_adopted': False, 'posterior_qualified': False}
with (folder / 'evaluation_receipt.json').open('x') as f:
    json.dump(out, f, indent=2, allow_nan=False)
    f.write('\n')
raise SystemExit(0 if all(r['status'] == 'finite_evaluation' for r in records) else 1)
