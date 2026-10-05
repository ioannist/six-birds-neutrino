"""Bind failure causes to actual gate receipts, without extrapolating convergence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = read(ROOT / "runs/20261003_math_review_validation/review_state.json")
groups = dict(state["fresh_CAMB_production_assessments"])
assert not (set(groups) & set(state["native_candidate_production_assessments"]))
groups.update(state["native_candidate_production_assessments"])
assert len(groups) == 9
records = []
for group, registered in sorted(groups.items()):
    folder = ROOT / registered["root"]
    snapshot_path = folder / "snapshot_receipt.json"
    native_path = ROOT / registered["native_verification"]
    diagnostic_path = ROOT / registered["diagnostics"]
    review_path = ROOT / registered["self_review"]
    execution_path = ROOT / registered["execution_receipt"]
    snapshot = read(snapshot_path)
    native, diagnostic, review, execution = map(read, (
        native_path, diagnostic_path, review_path, execution_path))
    assert snapshot["group"] == review["group"] == group
    assert review["snapshot_receipt_sha256"] == sha(snapshot_path)
    assert review["native_row_verification_sha256"] == sha(native_path)
    assert review["diagnostics_sha256"] == sha(diagnostic_path)
    assert execution["exit_code"] == 0 and execution["all_verification_workers_terminal"]
    assert len(execution["stages"]) == 3
    assert all(s["actual_exit_code"] == 0 for s in execution["stages"])
    native_checks = [c for r in native["records"] for c in r["checks"]]
    assert len(native_checks) == registered["selected_native_rows"] == 12
    assert max(abs(v) for c in native_checks for v in c["fresh_minus_recorded"].values()) == 0
    gates = review["all_seven_parameter_gate_sets_reconstructed"]
    assert set(gates) == set(diagnostic["diagnostics"]) and len(gates) == 7
    failures = {}
    for name, item in gates.items():
        assert len(item["gates"]) == 9
        assert all(type(value) is bool for value in item["gates"].values())
        assert item["pass"] == all(item["gates"].values())
        assert item["gates"]["MCSE"] == (
            diagnostic["diagnostics"][name]["quantile_mcse"] <=
            diagnostic["diagnostics"][name]["quantile_mcse_limit"])
        failures[name] = [key for key, value in item["gates"].items() if not value]
    assert not registered["posterior_qualified"]
    assert not diagnostic["all_diagnostic_thresholds_pass"]
    assert not all(item["pass"] for item in gates.values())
    mass = diagnostic["diagnostics"]["mnu"]
    assert mass["quantile_mcse_limit"] == 0.001
    assert mass["quantile_mcse"] == registered["mass_MCSE_eV"]
    assert mass["rank_folded_split_rhat"] == registered["mass_Rhat"]
    union = sorted({failure for failed in failures.values() for failure in failed})
    records.append({"group": group,
        "snapshot_path": str(snapshot_path.relative_to(ROOT)), "snapshot_sha256": sha(snapshot_path),
        "native_sha256": sha(native_path), "diagnostic_sha256": sha(diagnostic_path),
        "self_review_sha256": sha(review_path), "execution_sha256": sha(execution_path),
        "parameter_failed_gates": failures, "union_failed_gates": union,
        "only_precision_gates_fail_at_this_snapshot": union == ["MCSE"],
        "mass_failed_gates": failures["mnu"],
        "mass_Rhat": mass["rank_folded_split_rhat"],
        "mass_bulk_ESS": mass["bulk_ess"], "mass_tail_ESS": mass["tail_ess_05_95"],
        "mass_MCSE_eV": mass["quantile_mcse"], "required_mass_MCSE_eV": 0.001,
        "minimum_saved_postburn_history": registered["minimum_saved_postburn_history"],
        "next_history_trigger": registered["next_minimum_history"], "posterior_qualified": False})
with (HERE / "obstacle_receipt.json").open("x") as f:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(), "records": records,
        "nine_numerical_targets_kept_separate": True,
        "all_sixty_three_parameter_gate_sets_bound": True,
        "all_one_hundred_eight_selected_native_rows_exact": True,
        "passing_Rhat_or_drift_not_read_as_stationarity": True,
        "MCSE_estimates_not_uniform_or_certified_physical_error_bounds": True,
        "distinct_starts_not_read_as_PRNG_independence": True,
        "no_sampling_length_or_completion_time_extrapolation": True,
        "precision_limits_unchanged": True, "main_claim_revision_adopted": False},
        f, indent=2, allow_nan=False)
    f.write("\n")
for record in records:
    print(record["group"], "failed gates", record["union_failed_gates"])
