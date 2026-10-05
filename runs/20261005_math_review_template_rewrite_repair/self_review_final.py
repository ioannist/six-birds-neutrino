"""Check projection equations by exact 1D/2D covariance inversion, not whitening."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from math import isclose, sqrt
from pathlib import Path
import warnings

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

old = load("before_rewrite", HERE / "before_run_template_rewrite.py")
current_path = ROOT / "scripts/run_template_rewrite.py"
new = load("current_rewrite", current_path)
assert "allow_nan=False" in current_path.read_text()
def rational_precision(covariance):
    rows = [[Fraction(float(value)) for value in row] for row in covariance]
    if len(rows) == 1:
        return [[1 / rows[0][0]]]
    assert len(rows) == 2 and rows[0][1] == rows[1][0]
    a, b, c = rows[0][0], rows[0][1], rows[1][1]
    determinant = a * c - b * b
    assert a > 0 and determinant > 0
    return [[c / determinant, -b / determinant], [-b / determinant, a / determinant]]

def form(left, precision, right):
    return sum((Fraction(float(x)) * precision[i][j] * Fraction(float(y))
                for i, x in enumerate(left) for j, y in enumerate(right)), Fraction(0))

records = []
maximum_ordinary_change = 0.
for number in range(20):
    a, b = number % 7 + 1, number % 9 - 4
    covariance = np.array([[a + b * b, b], [b, 1.]], dtype=float)
    residual = np.array([number % 5 + 1., number % 3 + 1.])
    precision = rational_precision(covariance)
    for mode in ("full_residual", "dominant_whitened", "mode0", "mode1"):
        metrics, warning = new._direction_metrics(residual, np.zeros(2), np.zeros(2), covariance, mode)
        before_metrics, _ = old._direction_metrics(residual, np.zeros(2), np.zeros(2), covariance, mode)
        template, _ = new._template_vector(residual, covariance, mode)
        denominator = form(template, precision, template)
        numerator = form(template, precision, residual)
        before = form(residual, precision, residual)
        coefficient = numerator / denominator
        after = before - numerator * numerator / denominator
        assert after >= 0
        assert isclose(metrics["a_star"], float(coefficient), rel_tol=1e-12, abs_tol=1e-12)
        assert isclose(metrics["chi2_before"], float(before), rel_tol=1e-12, abs_tol=1e-12)
        assert isclose(metrics["chi2_after"], float(after), rel_tol=1e-12, abs_tol=1e-12)
        expected_cosine = float(numerator) / sqrt(float(denominator)) / sqrt(float(before))
        assert isclose(metrics["alignment_cos"], expected_cosine, rel_tol=1e-12, abs_tol=1e-12)
        for key, value in metrics.items():
            if value is None or key == "dominant_mode_index":
                continue
            difference = abs(value - before_metrics[key])
            maximum_ordinary_change = max(maximum_ordinary_change, difference)
            assert isclose(value, before_metrics[key], rel_tol=1e-12, abs_tol=1e-12)
        json.dumps(metrics, allow_nan=False)
        records.append({"covariance": covariance.tolist(), "residual": residual.tolist(), "mode": mode,
                        "rational_projection_gain": str(numerator * numerator / denominator),
                        "coefficient": metrics["a_star"], "chi2_before": metrics["chi2_before"],
                        "chi2_after": metrics["chi2_after"]})

extreme_records = []
for mode in ("full_residual", "dominant_whitened"):
    covariance, residual = np.array([[1e-320]]), np.array([1e-10])
    with np.errstate(all="raise"):
        metrics, _ = new._direction_metrics(residual, np.zeros(1), np.zeros(1), covariance, mode)
    expected = float(form(residual, rational_precision(covariance), residual))
    assert isclose(metrics["chi2_before"], expected, rel_tol=1e-14)
    assert metrics["chi2_after"] <= 1e-28 * expected
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        broken, _ = old._direction_metrics(residual, np.zeros(1), np.zeros(1), covariance, mode)
    assert not np.isfinite(broken["chi2_before"])
    json.dumps(metrics, allow_nan=False)
    extreme_records.append({"mode": mode, "exact_input_quadratic_rounded": expected,
                            "repaired": metrics, "old_nonfinite_failure_reproduced": True})

condition_metrics, condition_warnings = new._direction_metrics(
    np.array([1e-160, 0.]), np.zeros(2), np.zeros(2), np.diag([1e-320, 1.]), "full_residual")
assert condition_metrics["cond_cov"] is None and np.isfinite(condition_metrics["chi2_before"])
json.dumps(condition_metrics, allow_nan=False)
assert any("condition number" in message for message in condition_warnings)
for residual in (1e200, np.nan, 1e-200):
    try:
        new._direction_metrics(np.array([residual]), np.zeros(1), np.zeros(1), np.eye(1), "full_residual")
    except ValueError:
        pass
    else:
        raise AssertionError("Nonfinite/unrepresentable output accepted")

receipt = {"utc": datetime.now(timezone.utc).isoformat(),
    "reviewer": "distinct_self_review_not_independent_agent",
    "before_source_sha256": sha(HERE / "before_run_template_rewrite.py"),
    "current_source_sha256": sha(current_path),
    "independent_algorithm": "exact rational 1D/2D covariance inverse and weighted projection formula",
    "ordinary_controls": records, "ordinary_controls_count": len(records),
    "maximum_ordinary_metric_absolute_change": maximum_ordinary_change,
    "extreme_representable_quadratic_controls": extreme_records,
    "nonfinite_condition_number_reported_unknown": True,
    "unrepresentable_or_nonfinite_quadratics_refused": 3,
    "floating_Cholesky_accuracy_certificate": False,
    "residual_selected_full_template_removal_is_fitted_not_held_out_validation": True,
    "cosmological_posterior_or_claim_restoration_promoted": False}
with (HERE / "final_self_review_receipt.json").open("x") as output:
    json.dump(receipt, output, indent=2, allow_nan=False)
    output.write("\n")
print("Rewrite self-review passed: 80 rational projection controls, 2 extreme finite cases, invalid-output refusals.")
