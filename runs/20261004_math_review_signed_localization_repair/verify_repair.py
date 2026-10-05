"""Reproduce the archived localizer failure and compare repaired audit ledgers."""
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import warnings

import numpy as np

from sbt_spt_audit.localization import localize_quadratic_difference
from sbt_spt_audit.metrics import quadratic_contributions


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "sbt_spt_audit.review_before_localization", OUT / "before_localization.py")
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)


def describe(value):
    if isinstance(value, dict):
        return {k: describe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [describe(v) for v in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return str(value)
    return value


def evaluate(fn, *args, **kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            value = fn(*args, **kwargs)
            result = {"returned": describe(value)}
        except ValueError as exc:
            result = {"error": str(exc)}
    result["warnings"] = [str(w.message) for w in caught]
    return result


C = np.array([[5.0, 2.0], [2.0, 1.0]])
a, b = np.sqrt(5e307), np.sqrt(1.5e308)
train, best = np.array([a, a]), np.array([b, 0.0])
qt, qb = quadratic_contributions(train, C), quadratic_contributions(best, C)
exact = sum((Fraction(float(x)) for x in qt), Fraction(0)) - sum(
    (Fraction(float(x)) for x in qb), Fraction(0))
args = (C, train, best, ["TT", "TT"], [1000, 1000], [400, 3000])
old, new = evaluate(before.localize_quadratic_difference, *args), evaluate(
    localize_quadratic_difference, *args)
assert old["returned"][3]["deltaQ_full"] == "-inf"
assert old["returned"][3]["accounting_error"] == "nan"
assert new["returned"][3]["deltaQ_full"] == float(exact)
assert np.isfinite(new["returned"][3]["deltaQ_full"])
assert new["returned"][3]["accounting_error"] == 0.0
split = evaluate(localize_quadratic_difference, C, train, best,
                 ["TT", "EE"], [1000, 1000], [400, 3000])
assert "not representable" in split["error"]
shape_args = (np.eye(1), [1.0], [1.0, 1.0], ["TT", "TT"],
              [1000, 1000], [400, 3000])
old_shape = evaluate(before.localize_quadratic_difference, *shape_args,
                     best_cov=np.eye(2))
new_shape = evaluate(localize_quadratic_difference, *shape_args,
                     best_cov=np.eye(2))
assert "returned" in old_shape and "matching shape" in new_shape["error"]
comparisons = {}
for name, artifact in [
    ("20261003_math_review_profiled_multistart", "native_multistart_verification.json"),
    ("20261003_math_review_profiled_staging_multistart", "native_staging_verification.json"),
]:
    original = json.loads((ROOT / "runs" / name / "metrics.json").read_text())
    checked = json.loads((OUT / artifact).read_text())
    comparisons[name] = {}
    for direction, new_ledger in checked.items():
        original_ledger = original["localization"][direction]
        diffs = []
        for spectrum, cells in new_ledger["deltaQ_by_spec_ell"].items():
            old_cells = original_ledger["deltaQ_by_spec_ell"][spectrum]
            np.testing.assert_allclose(cells, old_cells, rtol=1e-10, atol=1e-7)
            diffs.extend(abs(x-y) for x,y in zip(cells, old_cells))
        identity = lambda rows: [(r["spec"], r["ell"]) for r in rows]
        assert identity(new_ledger["top_groups"]) == identity(original_ledger["top_groups"])
        native_error = abs(new_ledger["native_delta_chi2"] - new_ledger["reconstructed_delta_chi2"])
        comparisons[name][direction] = {
            "max_cell_change": max(diffs), "ranked_group_identities_unchanged": True,
            "native_reconstruction_absolute_error": native_error,
            "accounting_error": new_ledger["accounting"]["accounting_error"],
        }
result = {
    "finite_endpoint_Q_coordinate_difference_overflow": {
        "covariance_determinant": float(np.linalg.det(C)),
        "covariance_eigenvalues": np.linalg.eigvalsh(C).tolist(),
        "train_allocations": qt.tolist(), "best_allocations": qb.tolist(),
        "train_Q_exact_floating_allocation_sum": float(sum(map(Fraction, map(float, qt)))),
        "best_Q_exact_floating_allocation_sum": float(sum(map(Fraction, map(float, qb)))),
        "difference_exact_floating_allocation_sum": float(exact),
        "before": old, "after": new, "split_unrepresentable_group": split,
    },
    "dimension_broadcasting": {"before": old_shape, "after": new_shape},
    "native_audit_comparisons": comparisons,
    "scope": "selected floating endpoint allocations; no uniform solve-error certificate",
}
(OUT / "repair_verification.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
print("Archived failures reproduced; finite repair and native audit group comparisons pass.")
