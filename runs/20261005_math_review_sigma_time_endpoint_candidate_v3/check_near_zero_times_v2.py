"""Adversarial sorted-redshift controls using the actual Python ordering contract."""
from datetime import datetime, timezone
import json
from pathlib import Path
import camb
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sample = json.loads((ROOT / 'runs/20261005_math_review_sigma_limit22_candidate/selection_receipt.json').read_text())['records'][8]['point']
p = camb.set_params(H0=sample['H0'], ombh2=sample['omegabh2'], omch2=sample['omegach2'],
    mnu=sample['mnu'], tau=sample['tau'], As=np.exp(sample['logA'])*1e-10, ns=sample['ns'],
    num_massive_neutrinos=3, nnu=3.046)
bg = camb.get_background(p)
records = []
for maximum in [1., 10., 100.]:
    for count in [2, 5, 11, 31, 61]:
        zs = np.r_[np.geomspace(maximum, .001, count), 1e-12, 0.]
        ts = bg.conformal_time(zs, presorted=False)
        records.append({'z_max': maximum, 'grid_count': count,
            'previous_redshift': float(zs[-2]), 'previous_time': float(ts[-2]),
            'final_time': float(ts[-1]), 'tau0': float(bg.tau0),
            'monotone': bool(np.all(np.diff(ts) >= 0)), 'final_increment': float(ts[-1]-ts[-2])})
with (HERE / 'near_zero_time_controls_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
        'scope': 'Adversarial descending-redshift controls under initialized background.',
        'point': sample}, f, indent=2)
    f.write('\n')
print('Monotonicity failures:', sum(not r['monotone'] for r in records))
print(json.dumps([r for r in records if not r['monotone']][:2], indent=2))
