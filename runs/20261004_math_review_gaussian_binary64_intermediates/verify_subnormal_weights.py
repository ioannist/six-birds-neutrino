"""Compare subnormal-weight readouts with exact binary64-input fractions."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
records = []
native_type = np.longdouble
for phase in ['before', 'after']:
    source = HERE / 'overflow_only_toy_truncated_gaussian.py' if phase == 'before' else ROOT / 'scripts/toy_truncated_gaussian.py'
    spec = importlib.util.spec_from_file_location('subnormal_' + phase, source)
    toy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(toy)
    for sign in [1., -1.]:
        expected = float(Fraction(sign * 1e300) * Fraction(1e-60) ** 2 /
                         (Fraction(1e-60) ** 2 + Fraction(1e100) ** 2))
        np.longdouble = np.float64
        try:
            actual, sigma = toy.combine_gaussians(0., 1e-60, sign * 1e300, 1e100)
            swapped, swapped_sigma = toy.combine_gaussians(sign * 1e300, 1e100, 0., 1e-60)
        finally:
            np.longdouble = native_type
        if phase == 'after':
            assert actual == swapped == expected
            assert sigma == swapped_sigma == 1e-60
        else:
            assert abs(float(actual) / expected - 1) > 1e-6
        records.append({'phase': phase, 'sign': sign,
                        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'actual': float(actual), 'swapped': float(swapped),
                        'exact_input_fraction_rounded': expected,
                        'relative_error': float(actual) / expected - 1})
with (HERE / 'subnormal_weight_verification.json').open('x') as handle:
    handle.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                            'scope': 'subnormal_nonzero_precision_weight_binary64_intermediate_emulation',
                            'records': records}, indent=2) + '\n')
print('Both signs and swapped constraints now match the exact rounded means.')
