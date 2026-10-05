"""Fresh component, prior, and posterior replay of four precise archived rows."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from run_cosmological_audit import get_model, write_json, SPT

cfg = yaml.safe_load((HERE / 'default_input.yaml').read_text())
points = json.loads((HERE / 'points.json').read_text())
selected = json.loads((HERE / 'selection_receipt.json').read_text())['selection']
records = {}
with get_model(cfg, stop_at_error=True) as model:
    names = set(model.parameterization.sampled_params())
    for selection in selected:
        label = selection['label']
        source = ROOT / selection['source_chain']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == selection['source_sha256']
        header = source.read_text().splitlines()[0].lstrip('#').split()
        row = np.atleast_2d(np.loadtxt(source))[selection['stored_row_zero_based']]
        stored = dict(zip(header, row))
        point = points[label]
        assert set(point) == names
        assert point == {name: float(stored[name]) for name in names}
        posterior = model.logposterior(point, cached=False)
        native = dict(zip(model.likelihood, map(float, posterior.loglikes)))
        own_lens = 'lens' + label.split('_')[1]
        own_components = [k for k in native if k not in ['lensA', 'lensB']] + [own_lens]
        native_chi2 = {k: -2 * v for k, v in native.items()}
        expected = {('chi2__' + (SPT if k == own_lens else k)): native_chi2[k]
                    for k in own_components}
        prior = math.fsum(map(float, posterior.logpriors))
        own_loglike = math.fsum(native[k] for k in own_components)
        expected.update(chi2=-2 * own_loglike, minuslogprior=-prior,
                        minuslogpost=-own_loglike-prior)
        errors = {}
        for name, value in expected.items():
            assert np.isfinite(value)
            if not np.isclose(value, stored[name], atol=1e-7, rtol=1e-10):
                raise ValueError(f'{label} {name}: fresh {value} != stored {stored[name]}')
            errors[name] = value - float(stored[name])
        records[label] = {'point': point, 'own_lens': own_lens,
                          'native_chi2': native_chi2,
                          'fresh_minus_recorded': errors,
                          'own_joint_chi2': -2 * own_loglike}
        print(label + ': all native components, prior, and posterior verified', flush=True)
write_json(HERE / 'default_target_verification.json', {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'four_selected_precise_rows_pointwise_native_target_consistency',
    'atol': 1e-7, 'rtol': 1e-10,
    'source_sha256': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                      for name in ['default_input.yaml', 'points.json',
                                   'selection_receipt.json', 'default_bridge_runner.py']},
    'records': records, 'posterior_convergence_certified': False,
    'numerical_accuracy_certified': False,
})
