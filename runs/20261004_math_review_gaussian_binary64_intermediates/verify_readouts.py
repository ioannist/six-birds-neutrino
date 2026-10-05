"""Exercise the real readout with native and emulated binary64 intermediates."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import warnings

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
phase = sys.argv[1]
assert phase in ['before', 'after']
source = HERE / 'before_toy_truncated_gaussian.py' if phase == 'before' else ROOT / 'scripts/toy_truncated_gaussian.py'
spec = importlib.util.spec_from_file_location('checked_toy', source)
toy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toy)
native_type = np.longdouble
native_info = np.finfo(native_type)
records = []
for emulated in [False, True]:
    for sign in [1., -1.]:
        first = sign * np.finfo(float).max
        second = np.array([first, .5 * first, -first])
        expected = np.array([float((Fraction(float(first)) + Fraction(float(x))) / 2) for x in second])
        np.longdouble = np.float64 if emulated else native_type
        try:
            with warnings.catch_warnings(record=True) as seen:
                warnings.simplefilter('always')
                mean, sd = toy.combine_gaussians(first, 1., second, 1.)
        finally:
            np.longdouble = native_type
        finite = bool(np.isfinite(mean).all() and np.isfinite(sd).all())
        if phase == 'after':
            assert finite and np.array_equal(mean, expected)
            np.testing.assert_allclose(sd, 1 / np.sqrt(2), rtol=2e-16, atol=0)
            assert not seen
        records.append({'binary64_intermediate_emulation': emulated, 'first_mean_sign': sign,
                        'finite': finite, 'mean_display': [str(float(x)) for x in mean],
                        'expected_from_exact_input_fractions': expected.tolist(),
                        'warnings': [str(w.message) for w in seen]})
result = {'utc': datetime.now(timezone.utc).isoformat(), 'phase': phase,
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'native_intermediate_mantissa_bits': native_info.nmant,
          'native_intermediate_max_exponent': native_info.maxexp,
          'records': records, 'scope': 'finite_convex_mean_under_reduced_intermediate_range'}
with (HERE / (phase + '_verification.json')).open('x') as handle:
    handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps(result, indent=2, allow_nan=False))
