"""Recompute every acceptance predicate from numeric diagnostics, not stored labels."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import isfinite
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt_path = HERE / "obstacle_receipt.json"
receipt = read(receipt_path)
records = []
for bound in receipt["records"]:
    snapshot_path = ROOT / bound["snapshot_path"]
    folder = snapshot_path.parent
    assert sha(snapshot_path) == bound["snapshot_sha256"]
    diagnostic_path, review_path = folder / "diagnostics.json", folder / "self_review_receipt.json"
    assert sha(diagnostic_path) == bound["diagnostic_sha256"]
    assert sha(review_path) == bound["self_review_sha256"]
    snapshot, diagnostic, review = map(read, (snapshot_path, diagnostic_path, review_path))
    assert snapshot["group"] == bound["group"]
    lengths = []
    for family in snapshot["families"]:
        path = Path(family["snapshot"])
        assert sha(path) == family["snapshot_sha256"]
        weights = [Fraction(line.split()[0]) for line in path.read_text().splitlines()
                   if line.strip() and not line.startswith("#")]
        assert all(w > 0 and w.denominator == 1 for w in weights)
        retained = sum(weights[len(weights) // 5:])
        assert retained == family["retained_represented_steps"]
        lengths.append(retained)
    assert len(lengths) == 4 and min(lengths) == bound["minimum_saved_postburn_history"]
    assert bound["next_history_trigger"] == (6 * int(min(lengths)) + 4) // 5
    failures = {}
    for name, d in diagnostic["diagnostics"].items():
        assert d["n_chains"] == 4 and d["draws_per_chain"] == min(lengths)
        p, limit = d["quantile_mcse"], d["quantile_mcse_limit"]
        assert isfinite(p) and isfinite(limit) and p > 0 and limit > 0
        numeric = {"separate_starts": d["n_chains"] >= 2,
            "finite": all(isfinite(d[key]) for key in (
                "rank_folded_split_rhat", "bulk_ess", "tail_ess_05_95", "quantile_ess", "quantile_mcse")),
            "Rhat": d["rank_folded_split_rhat"] <= 1.01,
            "bulk_ESS": d["bulk_ess"] >= 400, "tail_ESS": d["tail_ess_05_95"] >= 400,
            "quantile_ESS": d["quantile_ess"] >= 400, "MCSE": 0 < p <= limit,
            "chronological_drift": d["quantile_half_difference"] <= 4 * max(p, limit),
            "equalized_selection": abs(d["quantile_full_draws"] - d["quantile_retained_draws"])
                <= 2 * max(p, limit)}
        assert numeric == review["all_seven_parameter_gate_sets_reconstructed"][name]["gates"]
        assert all(numeric.values()) == d["diagnostic_thresholds_pass"]
        failures[name] = [key for key, value in numeric.items() if not value]
    assert failures == bound["parameter_failed_gates"]
    union = sorted({failure for values in failures.values() for failure in values})
    assert union == bound["union_failed_gates"]
    assert bound["only_precision_gates_fail_at_this_snapshot"] == (union == ["MCSE"])
    assert union and not bound["posterior_qualified"]
    records.append({"group": bound["group"], "failed_gate_union": union,
        "numeric_gate_sets_reconstructed": len(failures), "weighted_histories_recounted": 4})
assert len(records) == 9
assert [r["group"] for r in receipt["records"] if r["only_precision_gates_fail_at_this_snapshot"] == ["current_A4095"]
with (HERE / "self_review_receipt.json").open("x") as f:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent",
        "audit_source_sha256": sha(HERE / "audit.py"), "obstacle_receipt_sha256": sha(receipt_path),
        "records": records, "all_sixty_three_numeric_gate_sets_reconstructed": True,
        "all_thirty_six_weighted_histories_recounted": True,
        "only_current_A4095_has_precision_only_failures_at_bound_snapshot": True,
        "represented_numeric_checks_not_uniform_arithmetic_certificates": True,
        "no_stationarity_physical_accuracy_or_completion_time_inference": True},
        f, indent=2, allow_nan=False)
    f.write("\n")
print("63 numeric gate sets and 36 weighted histories reconstructed; only current_A4095 fails precision alone.")
