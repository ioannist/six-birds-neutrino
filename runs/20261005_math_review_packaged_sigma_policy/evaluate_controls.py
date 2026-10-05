"""Same-configuration low-mass evaluations in isolated native variants."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
import yaml
import camb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model

parser = argparse.ArgumentParser()
parser.add_argument('variant', choices=['packaged14'])
args = parser.parse_args()
paths = {'packaged14': Path('/mnt/8tb/six-birds-ml/tmp/neutrino_CAMB204_packaged_sigma_policy_20261005/camb-2.0.4')}
package = paths[args.variant]
assert Path(camb.__file__).parent == package / 'camb'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract = json.loads((ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation/reproduction_contract.json').read_text())['entries']['2003']
for path, digest in contract['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert sha(contract['module']) == contract['module_sha256']
assert sha(contract['wrapper']) == contract['wrapper_sha256']
resolved = ROOT / contract['run_dir'] / 'resolved.yaml'
assert sha(resolved) == contract['effective_config_sha256']
cfg = yaml.safe_load(resolved.read_text())
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
selection = json.loads((HERE / 'selection_receipt.json').read_text())
folder = HERE / args.variant
folder.mkdir(exist_ok=False)
records = []
with get_model(model_cfg, stop_at_error=True) as model:
    for index, selected in enumerate(selection['records']):
        assert sha(ROOT / selected['source_native_receipt']) == selected['source_native_receipt_sha256']
        point = selected['point']
        assert all(cfg['params'][name]['prior']['min'] < value < cfg['params'][name]['prior']['max']
                   for name, value in point.items())
        result = model.logposterior(point, cached=False)
        assert math.isfinite(result.logpost)
        cls = {key: np.asarray(value, dtype=float) for key, value in model.provider.get_Cl(ell_factor=False, units='muK2').items()}
        assert all(np.isfinite(a).all() for a in cls.values())
        path = folder / f'point{index}_provider_arrays.npz'
        with path.open('xb') as f:
            np.savez_compressed(f, **cls)
        records.append({'selection_index': index, 'point': point, 'logpost': float(result.logpost),
                        'logpriors': list(map(float, result.logpriors)), 'loglikes': list(map(float, result.loglikes)),
                        'provider_arrays': str(path.relative_to(ROOT)), 'provider_arrays_sha256': sha(path),
                        'all_spectra_finite': True})
        print(args.variant, index, result.logpost, flush=True)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'variant': args.variant, 'records': records,
       'native_module': str(package / 'camb/camblib.so'), 'native_module_sha256': sha(package / 'camb/camblib.so'),
       'evaluation_config_sha256': sha(resolved), 'selection_receipt_sha256': sha(HERE / 'selection_receipt.json'),
       'scope': selection['scope'], 'production_adopted': False, 'posterior_qualified': False}
with (folder / 'evaluation_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
