"""Compare overflow controls with a separate high-precision calculation."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from itertools import product
from math import isfinite, ldexp
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from sbt_spt_audit.likelihoods.desi_dr2_bao import compute_observable_value

records = []
for sign in [-1, 1]:
    for mz, mh, mm in product([.51, .73, .99], repeat=3):
        for exponents in [(600*sign, 600*sign, -300*sign, 200*sign),
                          (600*sign, 600*sign, 600*sign, 800*sign)]:
            ez, eh, em, er = exponents
            z, dh, dm, rd = ldexp(mz, ez), ldexp(mh, eh), ldexp(mm, em), ldexp(.81, er)
            raw = z * dh * dm * dm
            assert not isfinite(raw) or raw == 0
            references = []
            for precision in [100, 180]:
                with localcontext() as ctx:
                    ctx.prec = precision
                    dz, drd, ddm, ddh = map(Decimal, [z, rd, dm, dh])
                    ratio_cubed = dz * ddh * ddm * ddm / (drd * drd * drd)
                    references.append(float(ratio_cubed ** (Decimal(1) / Decimal(3))))
            assert references[0] == references[1]
            actual = compute_observable_value('DV_over_rd', z, rd, dm, dh)
            error = abs(actual / references[1] - 1)
            assert error <= 3e-15
            records.append({'inputs': [z, rd, dm, dh], 'reference': references[1],
                            'actual': actual, 'relative_error': error})
assert len(records) == 108
with (HERE / 'final_numerical_control_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                       'controls': records, 'controls_checked': len(records),
                       'maximum_relative_error': max(r['relative_error'] for r in records),
                       'reference_precision_digits': [100, 180],
                       'reference_scope': 'high precision selected controls; no rigorous interval or global error certificate',
                       'production_source_sha256': hashlib.sha256((ROOT / 'src/sbt_spt_audit/likelihoods/desi_dr2_bao.py').read_bytes()).hexdigest(),
                       'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                      indent=2, allow_nan=False) + '\n')
print('108 high-precision overflow/underflow controls pass.')
