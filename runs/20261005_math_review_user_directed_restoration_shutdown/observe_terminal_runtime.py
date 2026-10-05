"""Recheck the complete terminal ledger; never relaunch or qualify a sampler."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
helper = ROOT / "runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py"
assert sha(helper) == "962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620"
spec = importlib.util.spec_from_file_location("terminal_identity", helper)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
ledger_path = HERE / "final_runtime_verification.json"
ledger = read(ledger_path)
state = read(ROOT / "runs/20261003_math_review_validation/review_state.json")
keys = ["guarded_solver_posterior_trials", "guarded_quadrature_posterior_chains",
        "guarded_medium_posterior_chains", "guarded_grid12_posterior_trials",
        "fresh_CAMB_posterior_chains", "upper_prior_posterior_chains",
        "native_candidate_posterior_chains", "guarded_CLASS_fresh_recovery_trials",
        "CLASS_recovery_companion_posterior_chains", "CLASS_fresh_B_posterior_chains"]
entries = {e["seed"]: e for key in keys for e in state[key]}
assert len(entries) == len(ledger["records"]) == ledger["registered_families"] == 80
assert ledger["owned_live_samplers"] == 0 and ledger["terminal_families"] == 80
requests = {e["seed"]: e for e in map(json.loads, (HERE / "stop_requests_v2.jsonl").read_text().splitlines())}
observations = {e["seed"]: e for e in read(HERE / "managed_terminal_observations.json")}
last = read(HERE / "seed1501_second_terminal_observation.json")
observations[1501] = {"session": last["managed_session"],
                      "result": {"exit_code": last["actual_terminal_exit_code"]}}
counts = {"user_directed": 0, "native_failure": 0, "historical_unavailable": 0}
preserved_files, recounted_histories = 0, 0
for record in ledger["records"]:
    entry = entries[record["seed"]]
    assert entry["status"].startswith("terminal_")
    path = ROOT / record["terminal_receipt"]
    assert sha(path) == entry["terminal_receipt_sha256"] == record["terminal_receipt_sha256"]
    terminal = read(path)
    assert terminal["exit_code"] == record["exit_code"]
    assert identity.observe_retired_identity(record["pid"], record["process_start_ticks"])["original_identity_absent"]
    for file in terminal["terminal_output_files"]:
        assert sha(ROOT / file["source"]) == sha(ROOT / file["frozen"]) == file["sha256"]
        preserved_files += 1
    if record["status"] == "terminal_user_directed_claim_restoration_stop":
        counts["user_directed"] += 1
        request, observed = requests[record["seed"]], observations[record["seed"]]
        assert request["signal_sent"] and request["owned_identity_revalidated"]
        assert request["managed_session"] == observed["session"] == terminal["managed_session"]
        assert observed["result"]["exit_code"] == terminal["exit_code"]
        assert terminal["exit_reason"] == "user_directed_claim_restoration_stop"
        assert not terminal["native_failure_established"]
        assert not terminal["scientific_claim_disproved_by_interruption"]
        assert not terminal["exact_PRNG_resume_asserted"]
        chain_file = next(f for f in terminal["terminal_output_files"]
                          if f["frozen"].endswith(".1.txt"))
        raw = (ROOT / chain_file["frozen"]).read_bytes()
        complete = raw[:raw.rfind(b"\n") + 1]
        weights = [Fraction(line.split()[0]) for line in complete.decode().splitlines()
                   if line.strip() and not line.startswith("#")]
        assert weights and all(w > 0 and w.denominator == 1 for w in weights)
        retained = sum(weights[len(weights) // 5:])
        assert retained == terminal["retained_represented_steps"] == record["retained_represented_steps"]
        assert len(weights) == terminal["stored_chain_rows"]
        recounted_histories += 1
        if record["seed"] in (2201, 2202):
            parent = read(ROOT / entry["parent_terminal_receipt"])
            assert parent["registered_entry"]["seed"] == entry["parent_seed"]
            assert sha(ROOT / entry["parent_terminal_receipt"]) == entry["parent_terminal_receipt_sha256"]
    elif record["status"] == "terminal_native_failure_preserved":
        counts["native_failure"] += 1
        assert record["seed"] in (2003, 2004, 2007, 2008) and terminal["exit_code"] == 1
    else:
        counts["historical_unavailable"] += 1
        assert record["status"] == "terminal_exit_reason_unavailable_preserved"
        assert terminal["exit_reason"] is None and terminal["exit_code"] is None
assert counts == {"user_directed": 61, "native_failure": 4, "historical_unavailable": 15}
assert recounted_histories == 61
for group, entry in ledger["growth_by_cohort"].items():
    assert len(entry["seeds"]) == 4 and entry["terminal_family_seeds"] == entry["seeds"]
    assert not entry["assessment_eligible"] and not entry["due"] and entry["sampling_campaign_withdrawn"]
assert len(ledger["growth_by_cohort"]) == 20
assessments = [record for key in ("fresh_CAMB_production_assessments", "native_candidate_production_assessments",
                                "fresh_CLASS_recovery_production_assessments") for record in state[key].values()]
assert len(assessments) == 10 and all(not r["posterior_qualified"] for r in assessments)
assert not state["claim_restoration_sampling_campaign"]["further_sampling_to_recover_original_claims_authorized"]
output = Path(sys.argv[1])
with output.open("x") as stream:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent",
        "terminal_ledger_sha256": sha(ledger_path), "counts": counts,
        "registered_families": 80, "owned_live_samplers": 0,
        "frozen_file_hashes_rechecked": preserved_files, "weighted_histories_recounted": recounted_histories,
        "declared_cohort_memberships_preserved": 20, "latest_production_assessments_unqualified": 10,
        "deliberate_interruption_not_scientific_disproof": True,
        "historical_terminal_causes_not_rewritten": True, "posterior_qualified": False}, stream, indent=2)
    stream.write("\n")
print("Terminal ledger verified: 61 deliberate stops, 4 native failures, 15 unavailable historical causes; no registered sampler live.")
