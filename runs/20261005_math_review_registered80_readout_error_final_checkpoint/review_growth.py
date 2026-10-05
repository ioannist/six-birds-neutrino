"""Check growth obligations from sealed assessment inputs, without resetting a target."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import ceil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = read(ROOT / "runs/20261003_math_review_validation/review_state.json")
runtime_path = HERE / "combined_runtime_verification.json"
runtime = read(runtime_path)
baseline_path = ROOT / "runs/20261005_math_review_sigma_time_v3_checkpoint/all_runtime_verification.json"
baseline = read(baseline_path)
assert sha(baseline_path) == runtime["baseline_runtime_sha256"]
records = []
for group, observed in runtime["growth_by_cohort"].items():
    matches = [state.get(key, {})[group] for key in (
        "fresh_CAMB_production_assessments", "native_candidate_production_assessments",
        "fresh_CLASS_recovery_production_assessments") if group in state.get(key, {})]
    assert len(matches) <= 1
    binding = None
    if matches:
        assessment = matches[0]
        snapshot_path = ROOT / assessment["root"] / "snapshot_receipt.json"
        snapshot = read(snapshot_path)
        assert snapshot["group"] == group
        assert [f["seed"] for f in snapshot["families"]] == observed["seeds"]
        assert snapshot["minimum_retained_represented_steps"] == min(
            f["retained_represented_steps"] for f in snapshot["families"])
        trigger = ceil(Fraction(6, 5) * snapshot["minimum_retained_represented_steps"])
        assert trigger == assessment["next_minimum_history"]
        assert not assessment["posterior_qualified"]
        binding = {"path": str(snapshot_path.relative_to(ROOT)), "sha256": sha(snapshot_path)}
    else:
        trigger = baseline["growth_by_cohort"].get(group, {}).get("next_assessment_trigger", 1000)
        if group.startswith("fresh_recovery_"):
            assert trigger == state["fresh_CLASS_recovery_cohorts"][group]["first_history_trigger"] == 1000
        if group.startswith("sigma_time_v3_"):
            assert trigger == 1000
    assert observed["next_assessment_trigger"] == trigger
    assert observed["assessment_eligible"] == (not observed["terminal_family_seeds"])
    assert observed["due"] == (observed["assessment_eligible"] and
        observed["minimum_saved_postburn_history"] >= trigger)
    records.append({"group": group, "assessment_binding": binding, "trigger": trigger,
        "eligible": observed["assessment_eligible"], "due": observed["due"]})
assert len(records) == 20
assert len([r for r in records if r["assessment_binding"]]) == 9
with (HERE / "growth_scope_self_review_receipt.json").open("x") as f:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent",
        "runtime_sha256": sha(runtime_path), "records": records,
        "exact_ceiling_growth_reconstructed": True,
        "unassessed_candidate_and_CLASS_targets_keep_first_gate": True,
        "terminal_cohorts_ineligible_and_memberships_preserved": True,
        "posterior_qualified": False}, f, indent=2, allow_nan=False)
    f.write("\n")
print("All 20 cohort growth obligations reconstructed; nine production predecessor bindings checked.")
