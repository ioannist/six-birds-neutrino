"""Reproduce erased/altered subnormal variances and compare ordinary solves."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from sbt_spt_audit.metrics import covariance_solve, quadratic_contributions

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("review_before_metrics", HERE / "before_metrics.py")
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)
cases = []
for units in [1, 3, 17]:
    variance = units * np.nextafter(0., 1.)
    covariance, residual = np.array([[variance]]), np.array([variance])
    native = float(cho_solve(cho_factor(covariance, lower=True), residual)[0])
    try:
        old = {"value": float(before.covariance_solve(covariance, residual)[0])}
    except ValueError as exc:
        old = {"error": str(exc)}
    with np.errstate(under="raise", over="raise", invalid="raise"):
        new = float(covariance_solve(covariance, residual)[0])
    contribution = float(quadratic_contributions(residual, covariance)[0])
    assert abs(new - 1) < 2e-14 and new == native
    assert contribution == variance and covariance[0, 0] == variance
    assert "error" in old or abs(old["value"]-new) > .01
    cases.append({"subnormal_units": units, "variance": variance, "before": old,
                  "after": new, "native_Cholesky_solve": native, "allocation": contribution})
rng = np.random.default_rng(20261004)
controls = []
for n in range(2, 12):
    m = rng.normal(size=(n, n))
    c = m @ m.T + np.eye(n)
    r = rng.normal(size=n)
    for rounded in [False, True]:
        candidate = c.copy()
        if rounded:
            candidate[0, 1] = np.nextafter(candidate[0, 1], np.inf)
        old = before.covariance_solve(candidate, r)
        new = covariance_solve(candidate, r)
        assert np.array_equal(old, new)
        np.testing.assert_array_equal(before.quadratic_contributions(r, candidate),
                                      quadratic_contributions(r, candidate))
        controls.append({"dimension": n, "roundoff_asymmetry": rounded,
                         "solve_and_allocations_bit_identical": True})
out = {"utc": datetime.now(timezone.utc).isoformat(), "subnormal_cases": cases,
       "ordinary_controls": controls,
       "scope": "selected representable Cholesky solves and exact-symmetric projection repair",
       "input_matrix_mutated": False, "uniform_float_error_certificate": False}
(HERE / "repair_verification.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
print("Three subnormal failures repaired; 20 ordinary and roundoff-asymmetric controls bit-identical.")
