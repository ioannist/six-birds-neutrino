"""Check the LDL certificate with exact integer principal determinants and refusals."""
import ast
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import lcm
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def determinant(a):
    # Bareiss integer elimination, distinct from the certificate's rational LDL.
    a = [row[:] for row in a]
    previous = 1
    for k in range(len(a) - 1):
        pivot = a[k][k]
        assert pivot != 0
        for i in range(k + 1, len(a)):
            for j in range(k + 1, len(a)):
                numerator = pivot * a[i][j] - a[i][k] * a[k][j]
                assert numerator % previous == 0
                a[i][j] = numerator // previous
            a[i][k] = 0
        previous = pivot
    return a[-1][-1]


def principal_minors(a):
    scale = lcm(*(x.denominator for row in a for x in row))
    integer = [[int(x * scale) for x in row] for row in a]
    return [Fraction(determinant([row[:k] for row in integer[:k]]), scale ** k)
            for k in range(1, len(a) + 1)]


def decode(d):
    return Fraction(int(d['numerator']), int(d['denominator']))


certificate_path = HERE / 'certificate.json'
certificate = json.loads(certificate_path.read_text())
records = []
for r in certificate['records']:
    proposal = ROOT / r['proposal']
    assert sha(proposal) == r['proposal_sha256']
    assert sha(ROOT / r['preparation_receipt']) == r['preparation_receipt_sha256']
    raw = [[Fraction.from_float(float(x)) for x in row] for row in np.loadtxt(proposal)]
    n = len(raw)
    symmetric = [[(raw[i][j] + raw[j][i]) / 2 for j in range(n)] for i in range(n)]
    delta = max(abs(raw[i][j] - symmetric[i][j]) for i in range(n) for j in range(n))
    assert decode(r['entrywise_perturbation_bound_exact']) == delta
    assert decode(r['maximum_raw_asymmetry_exact']) == 2 * delta
    assert r['parsed_binary64_matrix_exactly_symmetric'] == (delta == 0)
    margin = decode(r['positive_definiteness_margin_exact'])
    assert margin == n * delta
    shifted = [[symmetric[i][j] - (margin if i == j else 0)
                for j in range(n)] for i in range(n)]
    for matrix, key in [(symmetric, 'ldlt_positive_pivots'),
                        (shifted, 'shifted_ldlt_positive_pivots')]:
        minors = principal_minors(matrix)
        assert len(minors) == n and all(d > 0 for d in minors)
        previous = Fraction(1)
        for minor, pivot in zip(minors, r[key]):
            assert decode(pivot) == minor / previous
            previous = minor
    records.append({'group': r['group'], 'proposal_sha256': sha(proposal),
                    'twenty_principal_determinants_positive_exactly': True,
                    'raw_exact_symmetry': delta == 0})

# Exercise the actual certifier's mathematical hinge without rerunning its writer.
tree = ast.parse((HERE / 'certify.py').read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'ldlt')
namespace = {'Fraction': Fraction}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(HERE / 'certify.py'), 'exec'), namespace)
invalid = []
for name, a in [('singular', [[1, 0], [0, 0]]), ('indefinite', [[1, 2], [2, 1]])]:
    try:
        namespace['ldlt']([[Fraction(x) for x in row] for row in a])
    except AssertionError:
        invalid.append(name)
    else:
        raise AssertionError('A non-PD target passed the actual LDL hinge.')
assert len(records) == 4 and invalid == ['singular', 'indefinite']
with (HERE / 'self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': records,
        'certificate_sha256': sha(certificate_path), 'certifier_sha256': sha(HERE / 'certify.py'),
        'independent_arithmetic_algorithm': 'integer Bareiss principal determinants',
        'independent_human_or_agent_review': False,
        'actual_ldlt_non_positive_definite_controls_refused': invalid,
        'perturbation_argument': 'For symmetric E with entries bounded by delta, abs(x^T E x)<=delta*(sum abs(x_i))^2<=n*delta*||x||^2. Exact positive definiteness of S-n*delta*I implies S+E is positive definite. Triangle copies of represented M, including after simultaneous permutation, obey that bound.',
        'raw_covariance_files_or_sampler_configs_modified': False,
        'floating_normalization_or_sampling_invariance_or_posterior_qualification_proved': False},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('80 exact principal determinants checked; singular and indefinite targets refused.')
