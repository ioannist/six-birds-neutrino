"""Certify symmetric interpretations of four represented proposal matrices exactly."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def encode(q):
    return {'numerator': str(q.numerator), 'denominator': str(q.denominator)}


def ldlt(a):
    n = len(a)
    lower = [[Fraction(i == j) for j in range(n)] for i in range(n)]
    diagonal = []
    for i in range(n):
        for j in range(i):
            lower[i][j] = (a[i][j] - sum(lower[i][k] * lower[j][k] * diagonal[k]
                                         for k in range(j))) / diagonal[j]
        d = a[i][i] - sum(lower[i][k] ** 2 * diagonal[k] for k in range(i))
        assert d > 0
        diagonal.append(d)
    assert all(a[i][j] == sum(lower[i][k] * diagonal[k] * lower[j][k]
                              for k in range(n)) for i in range(n) for j in range(n))
    return diagonal


records = []
for group, root, seed in [
    ('medium_A', 'CLASS_fresh_recovery_preparation', 2201),
    ('quad_A', 'CLASS_fresh_recovery_preparation', 2202),
    ('medium_B', 'CLASS_fresh_B_preparation', 2401),
    ('quad_B', 'CLASS_fresh_B_preparation', 2405),
]:
    entry_path = ROOT / f'runs/20261005_math_review_{root}/seed{seed}/preparation_receipt.json'
    entry = json.loads(entry_path.read_text())
    path = ROOT / entry['proposal']
    assert sha(path) == entry['proposal_sha256']
    values = np.loadtxt(path)
    assert values.shape == (10, 10) and np.isfinite(values).all()
    # These rationals represent the parsed binary64 entries, not unrounded decimal reals.
    raw = [[Fraction.from_float(float(x)) for x in row] for row in values]
    n = len(raw)
    symmetric = [[(raw[i][j] + raw[j][i]) / 2 for j in range(n)] for i in range(n)]
    delta = max(abs(raw[i][j] - symmetric[i][j]) for i in range(n) for j in range(n))
    margin = n * delta
    shifted = [[symmetric[i][j] - (margin if i == j else 0)
                for j in range(n)] for i in range(n)]
    diagonal = ldlt(symmetric)
    shifted_diagonal = ldlt(shifted)
    # Any matrix made symmetric by copying either represented triangle differs from
    # S entrywise by at most delta. Its quadratic error is <= n*delta*||x||^2.
    # Since S-n*delta*I is PD by its exact LDL factorization, each such matrix is PD,
    # including choices made after simultaneously permuting rows and columns.
    records.append({'group': group, 'proposal': entry['proposal'], 'proposal_sha256': sha(path),
        'preparation_receipt': str(entry_path.relative_to(ROOT)), 'preparation_receipt_sha256': sha(entry_path),
        'dimension': n, 'parsed_binary64_matrix_exactly_symmetric': delta == 0,
        'maximum_raw_asymmetry_exact': encode(2 * delta),
        'symmetric_interpretation': '(M+transpose(M))/2 in exact rational arithmetic',
        'ldlt_positive_pivots': [encode(d) for d in diagonal],
        'entrywise_perturbation_bound_exact': encode(delta),
        'positive_definiteness_margin_exact': encode(margin),
        'shifted_ldlt_positive_pivots': [encode(d) for d in shifted_diagonal],
        'both_ldlt_factorizations_reconstruct_all_entries_exactly': True,
        'symmetric_triangle_copies_after_any_permutation_positive_definite': True,
        'original_raw_matrix_exact_symmetry_or_sampling_independence_asserted': False,
        'floating_correlation_normalization_roundoff_certified': False})
with (HERE / 'certificate.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
        'scope': 'Finite exact rational certificates for symmetric interpretations of fixed proposal inputs. No sampling, posterior, or solver-accuracy theorem.'},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('Four proposal interpretations certified by exact LDL; raw symmetry is reported separately.')
