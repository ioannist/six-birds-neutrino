"""Distinct closing pass: check actual bound sources and retained statement scope."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
audit = read(HERE / "completion_audit.json")
inventory = read(HERE / "source_inventory.json")
assert audit["review_completion_requirements_satisfied"]
assert len(audit["requirements"]) == 8
assert not audit["known_required_work_remaining_in_requested_review"]
assert not audit["original_empirical_claims_validated"]
assert audit["Python_tests_passed"] == 245 and audit["public_formal_declarations_covered"] == 97
assert sha(HERE / "source_inventory.json") == audit["source_inventory_sha256"]
assert sha(HERE / "statement_inventory.json") == audit["statement_inventory_sha256"]
checked = 0
for records in inventory.values():
    for record in records:
        assert sha(ROOT / record["path"]) == record["sha256"]
        checked += 1
state = read(ROOT / "runs/20261003_math_review_validation/review_state.json")
assert state["mathematical_review_completion"]["requested_review_complete"]
assert state["mathematical_review_completion"]["completion_audit"] == str((HERE / "completion_audit.json").relative_to(ROOT))
assert state["pytest_passed"] == 245
assert not state["SPT_headline_magnitude_revision_decision"]["current_qualified_numeric_replacement_available"]
assert state["SPT_headline_magnitude_revision_decision"]["historical_near_0p030_native_qualification_suspended"]
assert not state["claim_restoration_sampling_campaign"]["further_sampling_to_recover_original_claims_authorized"]
assert state["latest_registered_runtime_observation"]["owned_live_samplers"] == 0
disposition = read(ROOT / "runs/20261005_math_review_user_directed_restoration_shutdown/claim_disposition.json")
assert any("withdraw broad wording" in item["status"] for item in disposition["claims"])
assert any("unsupported" in item["status"] and "0.109" in item["claim"] for item in disposition["claims"])
assert not subprocess.check_output(["git", "diff", "ffdaf4b", "--name-only", "--",
                                    "paper", "docs/findings/canonical_results.json"], cwd=ROOT)
report = (ROOT / "docs/findings/math_review.md").read_text()
assert "original paper's empirical claims" in report
assert "final245-test successful" in report
assert "not independent external review" in report
assert "not a currently qualified replacement" in report
with (HERE / "final_self_review_receipt.json").open("x") as output:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent",
        "completion_audit_sha256": sha(HERE / "completion_audit.json"),
        "current_report_sha256": sha(ROOT / "docs/findings/math_review.md"),
        "current_state_sha256": sha(ROOT / "runs/20261003_math_review_validation/review_state.json"),
        "actual_bound_source_files_rechecked": checked,
        "requested_review_complete": True, "original_empirical_claims_validated": False,
        "no_current_numeric_replacement_smuggled": True,
        "paper_and_canonical_unchanged": True, "sampler_campaign_withdrawn": True,
        "later_manuscript_phase_explicitly_excluded": True}, output, indent=2)
    output.write("\n")
print(f"Closing self-review passed: {checked} source hashes, explicit retained/withdrawn scopes, no paper edit or sampling restart.")
