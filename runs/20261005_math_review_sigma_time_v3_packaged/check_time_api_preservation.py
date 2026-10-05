"""Bind explicit-tolerance, no-zero and empty-array controls to private builds."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import camb
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('variant', choices=['baseline', 'normalized'])
args = parser.parse_args()
sample = json.loads((ROOT / 'runs/20261005_math_review_sigma_time_endpoint_candidate_v3/selection_receipt.json').read_text())['records'][0]['point']
p = camb.set_params(H0=sample['H0'], ombh2=sample['omegabh2'], omch2=sample['omegach2'],
    mnu=sample['mnu'], tau=sample['tau'], As=np.exp(sample['logA'])*1e-10, ns=sample['ns'],
    num_massive_neutrinos=3, nnu=3.046)
bg = camb.get_background(p)
records = []
for maximum in [1., 10., 100.]:
    for count in [2, 5, 11, 31, 61]:
        zs = np.r_[np.geomspace(maximum, .001, count), 1e-12, 0.]
        for tolerance in [1e-4, 1e-6, 1e-8]:
            times = bg.conformal_time(zs, presorted=False, tol=tolerance)
            records.append({'kind': 'explicit_tolerance', 'z_max': maximum, 'count': count,
                            'tolerance': tolerance, 'times_hex': [float(t).hex() for t in times]})
        nonzero_times = bg.conformal_time(zs[:-1], presorted=False)
        records.append({'kind': 'no_zero_default', 'z_max': maximum, 'count': count,
                        'times_hex': [float(t).hex() for t in nonzero_times]})
empty = bg.conformal_time(np.array([]), presorted=False)
assert empty.shape == (0,)
with (HERE / f'{args.variant}_time_api_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'variant': args.variant,
        'module': str(camb.baseconfig.camblib._name),
        'module_sha256': hashlib.sha256(Path(camb.baseconfig.camblib._name).read_bytes()).hexdigest(),
        'point': sample, 'records': records, 'empty_array_preserved': True}, f, indent=2)
    f.write('\n')
print(args.variant, len(records), 'time API controls and empty array captured')
