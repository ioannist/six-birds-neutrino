"""Reconstruct the selected-row evidence without running the native verifier again."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


activation = json.loads((HERE / 'activation_verification.json').read_text())
records = []
for entry in activation['records']:
    seed = entry['seed']
    out = HERE / f'seed{seed}/first_saved_row'
    receipt = out / 'completion_receipt.json'
    d = json.loads(receipt.read_text())
    frozen = ROOT / d['frozen']
    raw = frozen.read_bytes()
    assert raw.endswith(b'\n') and sha(frozen) == d['snapshot_sha256']
    lines = raw.decode().splitlines()
    header = lines[0].lstrip('#').split()
    rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
    assert len(rows) == 1 and len(header) == len(set(header)) == len(rows[0])
    values = dict(zip(header, rows[0]))
    assert np.isfinite([float(v) for v in values.values()]).all()
    weight = Fraction(values['weight'])
    assert weight.denominator == 1 and weight > 0 and int(weight) == d['holding_time']
    source = ROOT / d['source']
    assert source.read_bytes().startswith(raw)
    point = {k: float(values[k]) for k in entry['initial_point']}
    assert point == d['point'] == d['native_check']['point']
    input_cfg = yaml.safe_load((out / 'input.yaml').read_text())
    resolved = yaml.safe_load((out / 'resolved.yaml').read_text())
    prepared = ROOT / entry['config']
    assert sha(prepared) == entry['config_sha256'] == d['config_sha256']
    for key in ['theory', 'likelihood', 'params', 'sampler']:
        assert input_cfg[key] == yaml.safe_load(prepared.read_text())[key]
    for k, v in point.items():
        prior = input_cfg['params'][k]['prior']
        if 'min' in prior:
            assert prior['min'] < v < prior['max']
    backend = json.loads((out / 'solver_backend.json').read_text())
    assert backend['module_sha256'] == entry['module_sha256'] == d['module_sha256']
    assert sha(backend['module']) == backend['module_sha256']
    assert sha(backend['build_receipt']) == backend['build_receipt_sha256']
    errors = d['native_check']['fresh_minus_recorded']
    expected = {'minuslogpost', 'minuslogprior', 'chi2'} | {
        f'chi2__{name}' for name in resolved['likelihood']}
    assert set(errors) == expected and all(v == 0.0 for v in errors.values())
    # Cobaya also writes a type aggregate; it is not another likelihood term.
    cmb_names = [name for name, cfg in resolved['likelihood'].items()
                 if cfg.get('type') == 'CMB' or 'CMB' in (cfg.get('type') or [])]
    assert cmb_names
    assert abs(float(values['chi2__CMB']) - sum(
        float(values[f'chi2__{name}']) for name in cmb_names)) < 1e-10
    assert float(values['minuslogprior__0']) == float(values['minuslogprior'])
    assert d['native_check']['fresh_minuslogpost'] == float(values['minuslogpost'])
    assert d['native_row_verified'] and d['complete_source_prefix_preserved']
    assert not entry['exact_resume_asserted'] and not entry['old_prefix_appended']
    records.append({'seed': seed, 'parent_seed': entry['parent_seed'],
                    'receipt_sha256': sha(receipt), 'snapshot_sha256': sha(frozen),
                    'holding_time': int(weight), 'checked_components': sorted(errors),
                    'maximum_native_component_error': max(map(abs, errors.values()))})

assert sorted(e['seed'] for e in records) == [2201, 2202]
with (HERE / 'self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
               'reviewer': 'distinct_self_review_not_independent_agent',
               'activation_sha256': sha(HERE / 'activation_verification.json'),
               'records': records, 'complete_source_prefixes_reconstructed': True,
               'old_histories_pooled': False, 'exact_resume_asserted': False,
               'posterior_or_uniform_accuracy_certified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Both recovery selected-row receipts reconstructed; no posterior qualification.')
