"""Reproduce finite additive-accounting failures and check the repaired contract."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

from sbt_spt_audit.metrics import blockwise_delta_chi2_from_loglike_blocks as repaired
from sbt_spt_audit.localization import _finite_signed_sum

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("before_metrics", HERE / "before_metrics.py")
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)
old = before.blockwise_delta_chi2_from_loglike_blocks
spec = importlib.util.spec_from_file_location("sbt_spt_audit.before_localization", HERE / "before_localization.py")
before_localizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before_localizer)

cases = [
    ("common_offset", {"large": -1e16, "small": -1.}, {"large": -1e16, "small": -2.}, -2.),
    ("insertion_order", {"a": -1e16, "b": -1., "c": -1.}, {"b": -1., "c": -1., "a": -1e16}, 0.),
    ("intermediate_overflow", {"a": -5e307, "b": -5e307, "c": 0., "d": 0.},
     {"a": 0., "b": 0., "c": -5e307, "d": -5e307}, 0.),
    ("unrepresentable_total", {"a": -5e307, "b": -5e307}, {"a": 0., "b": 0.}, None),
    ("rounded_blocks_hide_signal", {"a": -1e16, "b": 0.}, {"a": -1., "b": -1e16}, None),
    ("small_signal_within_tolerance", {"a": -1e16, "b": 0.}, {"a": -1e-14, "b": -1e16}, -2e-14),
]


def evaluate(function, train, test):
    try:
        return {"status": "returned", "result": function(train, test)}
    except ValueError as error:
        return {"status": "rejected", "error": str(error)}


records = []
for name, train, test, expected in cases:
    original_train, original_test = dict(train), dict(test)
    old_result, new_result = evaluate(old, train, test), evaluate(repaired, train, test)
    exact = sum((-2 * (Fraction(train[k]) - Fraction(test[k])) for k in train), Fraction(0))
    if expected is None:
        assert new_result["status"] == "rejected"
    else:
        assert new_result["status"] == "returned"
        assert new_result["result"]["total"] == float(exact) == expected
    if name in {"common_offset", "intermediate_overflow"}:
        assert old_result["status"] == "rejected"
    if name == "insertion_order":
        # Python 3.12's improved builtin float sum already passes this control.
        assert old_result["result"]["total"] == 0.
    if name in {"rounded_blocks_hide_signal", "small_signal_within_tolerance"}:
        assert old_result["result"]["total"] == 0.
    assert train == original_train and test == original_test
    records.append({"case": name, "train": train, "test": test,
                    "exact_aggregate_numerator": str(exact.numerator),
                    "exact_aggregate_denominator": str(exact.denominator),
                    "before": old_result, "after": new_result})

controls = [[1., -2., 3.], [1e308, 1e308, -1e308, -1e308], [5e307, -1e308], []]
for values in controls:
    assert _finite_signed_sum(values) == before_localizer._finite_signed_sum(values)
assert records[-1]["after"]["result"]["accounting_error"] == 2e-14
regular = repaired({"A": -120., "B": -35.}, {"A": -118., "B": -34.})
assert regular["total"] == 6. and regular["accounting_error"] == 0.
assert '94 passed' in (HERE / 'final_pytest_stdout.txt').read_text()
assert not (HERE / 'final_pytest_stderr.txt').read_bytes()
paths = [HERE / 'before_metrics.py', HERE / 'before_localization.py',
         ROOT / 'src/sbt_spt_audit/metrics.py', ROOT / 'src/sbt_spt_audit/localization.py',
         ROOT / 'src/sbt_spt_audit/_numerics.py', ROOT / 'tests/test_metrics.py',
         HERE / 'final_pytest_stdout.txt', HERE / 'final_pytest_stderr.txt', Path(__file__).resolve()]
result = {"utc": datetime.now(timezone.utc).isoformat(), "cases": records,
          "pytest_passed": 94, "pytest_session": 79238, "pytest_exit_code": 0,
          "shared_localizer_controls_unchanged": True,
          "scope": "generic_helper_for_actual_additive_loglike_terms_only",
          "correlated_covariance_subblocks_declared_additive": False,
          "native_likelihood_rerun_for_this_refactor": False,
          "lean_changed": False,
          "files": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                    for p in paths]}
(HERE / 'validation_receipt.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('Six accounting controls verified; four shared signed-sum controls unchanged; 94-test receipt verified.')
