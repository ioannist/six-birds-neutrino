"""Preserve settled outputs and record deliberate interruption, not scientific failure."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
def write_new(path, value):
    with Path(path).open("x") as output:
        json.dump(value, output, indent=2, allow_nan=False)
        output.write("\n")

state_path = ROOT / "runs/20261003_math_review_validation/review_state.json"
state = read(state_path)
requests = [json.loads(line) for line in (HERE / "stop_requests_v2.jsonl").read_text().splitlines()]
observations = {entry["seed"]: entry for entry in read(HERE / "managed_terminal_observations.json")}
last = read(HERE / "seed1501_second_terminal_observation.json")
assert observations[1501]["result"]["session_id"] == last["managed_session"]
observations[1501] = {"seed": 1501, "session": last["managed_session"],
                      "result": {"exit_code": last["actual_terminal_exit_code"]}}
keys = ["guarded_solver_posterior_trials", "guarded_quadrature_posterior_chains",
        "guarded_medium_posterior_chains", "guarded_grid12_posterior_trials",
        "fresh_CAMB_posterior_chains", "upper_prior_posterior_chains",
        "native_candidate_posterior_chains", "guarded_CLASS_fresh_recovery_trials",
        "CLASS_recovery_companion_posterior_chains", "CLASS_fresh_B_posterior_chains"]
entries = {entry["seed"]: entry for key in keys for entry in state[key]}
prior = read(HERE / "combined_runtime_verification.json")
prior_by_seed = {record["seed"]: record for record in prior["records"]}
helper = ROOT / "runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py"
assert sha(helper) == "962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620"
spec = importlib.util.spec_from_file_location("shutdown_identity", helper)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
final_records = []
for request in requests:
    seed = request["seed"]
    entry = entries[seed]
    observed = observations[seed]
    assert observed["session"] == request["managed_session"]
    exit_code = observed["result"]["exit_code"]
    assert exit_code in (130, 143)
    absent = identity.observe_retired_identity(request["pid"], request["process_start_ticks"])
    assert absent["original_identity_absent"]
    folder = HERE / f"seed{seed}"
    outputs = folder / "outputs"
    outputs.mkdir(parents=True)
    run = ROOT / request["run_dir"]
    files = []
    for source in sorted(run.rglob("*")):
        if not source.is_file():
            continue
        assert not source.is_symlink()
        destination = outputs / source.relative_to(run)
        destination.parent.mkdir(parents=True, exist_ok=True)
        digest = sha(source)
        shutil.copy2(source, destination)
        assert sha(source) == sha(destination) == digest
        files.append({"source": str(source.relative_to(ROOT)),
                      "frozen": str(destination.relative_to(ROOT)), "sha256": digest})
    assert files
    chain = next((outputs / "chains").glob("*.1.txt"))
    raw = chain.read_bytes()
    complete = raw[:raw.rfind(b"\n") + 1]
    weights = [Fraction(line.split()[0]) for line in complete.decode().splitlines()
               if line.strip() and not line.startswith("#")]
    assert weights and all(w > 0 and w.denominator == 1 for w in weights)
    retained = sum(weights[len(weights) // 5:])
    assert retained.denominator == 1
    receipt = {
        "utc": datetime.now(timezone.utc).isoformat(), "registered_entry": dict(entry),
        "last_verified_live_identity": prior_by_seed[seed], "identity_observation": absent,
        "exit_code": exit_code, "managed_session": observed["session"],
        "exit_reason": "user_directed_claim_restoration_stop",
        "stop_request": request, "native_failure_established": False,
        "terminal_output_files": files, "stored_chain_rows": len(weights),
        "incomplete_trailing_chain_bytes": len(raw) - len(complete),
        "retained_represented_steps": int(retained), "posterior_qualified": False,
        "scientific_claim_disproved_by_interruption": False,
        "exact_PRNG_resume_asserted": False}
    terminal_path = folder / "terminal_receipt.json"
    write_new(terminal_path, receipt)
    if seed in (2201, 2202):
        entry["parent_terminal_receipt"] = entry["terminal_receipt"]
        entry["parent_terminal_receipt_sha256"] = entry["terminal_receipt_sha256"]
    entry.update({"status": "terminal_user_directed_claim_restoration_stop",
                  "terminal_receipt": str(terminal_path.relative_to(ROOT)),
                  "terminal_receipt_sha256": sha(terminal_path),
                  "terminal_exit_code": exit_code, "posterior_qualified": False})
    final_records.append({"seed": seed, "pid": request["pid"],
        "process_start_ticks": request["process_start_ticks"],
        "status": entry["status"], "terminal_receipt": entry["terminal_receipt"],
        "terminal_receipt_sha256": entry["terminal_receipt_sha256"],
        "identity_observation": absent, "exit_code": exit_code,
        "retained_represented_steps": int(retained), "posterior_qualified": False})
for record in prior["records"]:
    if record["status"] == "live_same_owned_native_identity":
        continue
    terminal = read(ROOT / record["terminal_receipt"])
    assert sha(ROOT / record["terminal_receipt"]) == record["terminal_receipt_sha256"]
    for file in terminal["terminal_output_files"]:
        assert sha(ROOT / file["source"]) == sha(ROOT / file["frozen"]) == file["sha256"]
    absent = identity.observe_retired_identity(record["pid"], record["process_start_ticks"])
    assert absent["original_identity_absent"]
    final_records.append(dict(record, identity_observation=absent))
assert len(final_records) == len({r["seed"] for r in final_records}) == 80
by_seed = {r["seed"]: r for r in final_records}
growth = {}
for group, old in prior["growth_by_cohort"].items():
    subset = [by_seed[seed] for seed in old["seeds"]]
    growth[group] = {"seeds": old["seeds"],
        "minimum_saved_postburn_history": min(r["retained_represented_steps"] for r in subset),
        "last_declared_history_trigger": old["next_assessment_trigger"],
        "terminal_family_seeds": old["seeds"], "assessment_eligible": False,
        "due": False, "sampling_campaign_withdrawn": True}
final_path = HERE / "final_runtime_verification.json"
write_new(final_path, {"utc": datetime.now(timezone.utc).isoformat(),
    "records": sorted(final_records, key=lambda r: r["seed"]), "registered_families": 80,
    "owned_live_samplers": 0, "terminal_families": 80, "user_directed_stops": 61,
    "known_native_failure_families": 4, "historical_exit_reason_unavailable_families": 15,
    "growth_by_cohort": growth, "prestop_runtime_sha256": sha(HERE / "combined_runtime_verification.json"),
    "original_headline_restoration_campaign_withdrawn": True,
    "interruption_is_not_scientific_evidence": True, "posterior_qualified": False})
state["latest_registered_runtime_observation"] = {
    "root": str(HERE.relative_to(ROOT)), "runtime": str(final_path.relative_to(ROOT)),
    "utc": read(final_path)["utc"], "registered_families": 80, "owned_live_samplers": 0,
    "user_directed_stopped_families": sorted(r["seed"] for r in requests),
    "terminal_native_failure_families": [2003, 2004, 2007, 2008],
    "terminal_exit_reason_unavailable_families": [r["seed"] for r in final_records
        if r["status"] == "terminal_exit_reason_unavailable_preserved"],
    "declared_cohorts": 20, "due_eligible_cohorts": [],
    "restoration_sampling_campaign_withdrawn": True,
    "historical_CLASS_cohorts_pooled_with_fresh_recovery": False}
state["review_status"] = "evidence_led_mathematical_review_claim_restoration_sampling_withdrawn"
state["claim_restoration_sampling_campaign"] = {
    "status": "withdrawn_after_user_evidence_priority_instruction",
    "user_instruction": "[paraphrased] stop trying to justify original claims that are wrong or likely wrong",
    "original_0p109_eV_claim": "unsupported_and_not_admissible_as_a_result; not conclusively disproved by chain diagnostics",
    "broad_TT_dominance_claim": "contradicted_by_audited_full_CMB_forward_cases; recommend withdrawing broad scope",
    "historical_near_0p030_eV_replacement": "native_qualification_suspended; not admissible replacement",
    "further_sampling_to_recover_original_claims_authorized": False,
    "continue": "Audit retained mathematics and finite comparisons; recommend only evidence-supported claims.",
    "shutdown_evidence": str(final_path.relative_to(ROOT)), "paper_modified": False}
state["pending_decision"] = (
    "User directed dropping attempts to justify wrong or likely wrong original claims. "
    "Claim-restoration sampling withdrawn. Broad TT dominance is contradicted in audited full-CMB forward cases; "
    "original0.109eV magnitude remains unsupported rather than disproved. Historical near0.030eV remains suspended. "
    "Finish evidence-led claim inventory and remaining mathematical review; manuscript revision is a later phase.")
state_path.write_text(json.dumps(state, indent=2, allow_nan=False) + "\n")
print("All 61 deliberate stops terminal; all outputs frozen; 80 registrations accounted for, no live registered samplers.")
