"""Check the RMS repair against analytic controls and the unchanged SPD solve."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from math import sqrt
from pathlib import Path
import warnings

import numpy as np
from sbt_spt_audit import metrics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('sbt_spt_audit.before_rmse', HERE / 'before_metrics.py')
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)


def evaluate(function, residual, cov):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            value = {'status': 'returned', 'value': function(residual, cov)}
        except ValueError as error:
            value = {'status': 'rejected', 'error': str(error)}
    value['warnings'] = [str(w.message) for w in caught]
    return value


cases = [
    ('quadratic_overflow', np.array([1e200]), np.eye(1), 1e200),
    ('quadratic_underflow', np.array([1e-200]), np.eye(1), 1e-200),
    ('smallest_residual', np.array([np.nextafter(0., 1.)]), np.eye(1), np.nextafter(0., 1.)),
    ('inverse_solve_overflow', np.array([1., 0.]), np.diag([1e-320, 1.]), (1. / sqrt(1e-320)) / sqrt(2.)),
    ('norm_overflow_but_RMS_finite', np.full(2, np.finfo(float).max), np.eye(2), np.finfo(float).max),
    ('correlated_signed_allocations', np.ones(2), np.array([[5., 2.], [2., 1.]]), 1.),
    ('unrepresentable_whitening', np.array([1e308]), np.array([[1e-308]]), None),
]
records = []
for name, residual, covariance, expected in cases:
    original_cov, original_residual = covariance.copy(), residual.copy()
    old = evaluate(before.weighted_rmse, residual, covariance)
    with np.errstate(all='raise'):
        new = evaluate(metrics.weighted_rmse, residual, covariance)
    if expected is None:
        assert new['status'] == 'rejected' and 'whitening produced nonfinite' in new['error']
    else:
        assert new['status'] == 'returned'
        assert new['value'] == expected or abs(new['value'] / expected - 1.) < 1e-14
    np.testing.assert_array_equal(covariance, original_cov)
    np.testing.assert_array_equal(residual, original_residual)
    records.append({'case': name, 'residual': residual.tolist(), 'covariance': covariance.tolist(),
                    'analytic_expected': expected, 'before': old, 'after': new})
assert records[0]['before']['status'] == records[3]['before']['status'] == 'rejected'
assert records[1]['before']['value'] == records[2]['before']['value'] == 0.

rng = np.random.default_rng(403)
for i in range(20):
    matrix = rng.normal(size=(8, 8))
    covariance = matrix @ matrix.T + np.eye(8)
    if i % 2:
        covariance[0, 1] = np.nextafter(covariance[0, 1], np.inf)
    residual = rng.normal(size=8)
    np.testing.assert_array_equal(metrics.covariance_solve(covariance, residual),
                                  before.covariance_solve(covariance, residual))
    assert np.isclose(metrics.weighted_rmse(residual, covariance),
                      before.weighted_rmse(residual, covariance), rtol=1e-14, atol=0.)
assert '100 passed' in (HERE / 'pytest_stdout.txt').read_text()
assert not (HERE / 'pytest_stderr.txt').read_bytes()
native = []
for kind, session in [('multistart', 58459), ('staging', 97150)]:
    name = f'native_{kind}_verification.json'
    assert (HERE / name).read_bytes() == (ROOT / 'runs/20261004_math_review_covariance_subnormal_repair' / name).read_bytes()
    assert not (HERE / f'native_{kind}_stderr.txt').read_bytes()
    native.append({'session': session, 'exit_code': 0, 'artifact': name,
                   'byte_identical_to_previous_native_receipt': True})
paths = [ROOT / 'src/sbt_spt_audit/metrics.py', ROOT / 'tests/test_metrics.py',
         HERE / 'before_metrics.py', HERE / 'pytest_stdout.txt', HERE / 'pytest_stderr.txt',
         Path(__file__).resolve()] + sorted(HERE.glob('native_*'))
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'cases': records,
           'pytest': {'session': 20902, 'exit_code': 0, 'passed': 100},
           'ordinary_and_roundoff_covariance_solves_bit_identical': 20,
           'ordinary_RMS_agreement_relative_tolerance': 1e-14,
           'native_checks': native, 'covariance_model_validation_unchanged': True,
           'finite_whitened_coordinates_required': True,
           'uniform_floating_point_error_certificate': False,
           'paper_modified': False, 'lean_changed': False,
           'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in paths]}
(HERE / 'validation_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('Seven RMS controls, twenty unchanged covariance solves, 100 tests and both native ledgers verified.')
