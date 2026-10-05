"""Fresh default-target bridge at the four selected chain coordinates."""
from pathlib import Path
import sys
import json
import hashlib
import datetime
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from run_cosmological_audit import get_model, write_json

out = Path(__file__).resolve().parent
source = ROOT / 'runs/20261003_math_review_camb_accuracy_control_matched_coverage/input.yaml'
cfg = yaml.safe_load(source.read_text())
points = json.loads((out / 'points.json').read_text())
selection = json.loads((out / 'selection_receipt.json').read_text())['selection']
records = {}
with get_model(cfg, stop_at_error=True) as model:
    names = set(model.parameterization.sampled_params())
    completion = [k for k in model.likelihood if k not in ['lensA', 'lensB']]
    for selected in selection:
        label = selected['label']
        point = points[label]
        assert set(point) == names
        file = ROOT / selected['source_chain']
        assert hashlib.sha256(file.read_bytes()).hexdigest() == selected['source_sha256']
        header = file.read_text().splitlines()[0].lstrip('#').split()
        row = np.atleast_2d(np.loadtxt(file))[selected['stored_row_zero_based']]
        assert point == {n: float(row[header.index(n)]) for n in names}
        lens = 'lens' + label.split('_')[1]
        native = model.loglikes(point, as_dict=True, return_derived=False, cached=False)
        chi2 = {k: -2 * float(v) for k, v in native.items()}
        assert np.all(np.isfinite(list(chi2.values())))
        fresh = sum(float(native[k]) for k in completion + [lens])
        stored = float(-row[header.index('minuslogpost')] + row[header.index('minuslogprior')])
        if not np.isclose(fresh, stored, atol=0.002, rtol=1e-6):
            raise ValueError(f'{label}: default native target does not reproduce the stored row.')
        records[label] = {'point': point, 'lens': lens, 'native_chi2': chi2,
                          'stored_loglike': stored, 'fresh_loglike': fresh,
                          'fresh_minus_stored_loglike': fresh - stored}
        print(label + ': default target verified', flush=True)
write_json(out / 'default_target_verification.json', {
    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'four_selected_rounded_chain_rows_pointwise_default_target_bridge',
    'config_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'points_sha256': hashlib.sha256((out / 'points.json').read_bytes()).hexdigest(),
    'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'loglike_atol': 0.002, 'loglike_rtol': 1e-6,
    'completion': completion, 'records': records,
    'posterior_accuracy_certified': False})
