"""Reconstruct the first CLASS and expanded archived-CAMB production obligations."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import isfinite
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = read(ROOT / "runs/20261003_math_review_validation/review_state.json")
specs = [
    ("fresh_CLASS_recovery_production_assessments", "fresh_recovery_quad_A", 10, "mnu_sample",
     "all_sampled_parameter_gate_sets_reconstructed",
     "runs/20261005_math_review_CLASS_fresh_recovery_diagnostic_preparation_v2"),
    ("fresh_CAMB_production_assessments", "old_A3200", 7, "mnu",
     "all_seven_parameter_gate_sets_reconstructed",
     "runs/20261004_math_review_fresh_CAMB_weighted_summary_diagnostic_preparation"),
]
records = []
for key, group, count, mass_name, gate_field, workflow in specs:
    registered = state[key][group]
    folder = ROOT / registered["root"]
    snapshot_path = folder / "snapshot_receipt.json"
    snapshot, native, diagnostics, reviewed, execution, prep = map(read, (
        snapshot_path, folder / "native_rows_verification.json", folder / "diagnostics.json",
        folder / "self_review_receipt.json", folder / "execution_receipt.json",
        folder / "worker_preparation_receipt.json"))
    source = ROOT / prep["source"]
    assert sha(source) == prep["source_sha256"]
    prepared = source.read_text()
    for before, after in prep["changes"]:
        assert prepared.count(before) == 1
        prepared = prepared.replace(before, after, 1)
    assert prepared.encode() == (folder / "run_verification.py").read_bytes()
    assert execution["exit_code"] == 0 and execution["all_verification_workers_terminal"]
    assert len(execution["stages"]) == 3 and all(s["actual_exit_code"] == 0 for s in execution["stages"])
    contract_path = ROOT / workflow / "assessment_contract.json"
    contract = read(contract_path)
    assert snapshot["group"] == native["group"] == reviewed["group"] == group
    assert snapshot["contract_sha256"] == sha(contract_path)
    assert [f["seed"] for f in snapshot["families"]] == [f["seed"] for f in contract["groups"][group]]
    lengths, refs = [], []
    for family in snapshot["families"]:
        path = Path(family["snapshot"])
        raw = path.read_bytes()
        assert sha(path) == family["snapshot_sha256"]
        assert (ROOT / family["source"]).read_bytes().startswith(raw)
        weights = [Fraction(line.split()[0]) for line in raw.decode().splitlines()
                   if line.strip() and not line.startswith("#")]
        assert all(w > 0 and w.denominator == 1 for w in weights)
        lengths.append(sum(weights[len(weights) // 5:]))
        assert lengths[-1] == family["retained_represented_steps"]
        cfg_path = path.parent.parent / "input.yaml"
        assert sha(cfg_path) == family["source_input_sha256"]
        cfg = yaml.safe_load(cfg_path.read_text())
        sampled = sorted(name for name, item in cfg["params"].items()
                         if isinstance(item, dict) and "prior" in item)
        assert len(sampled) == count and set(sampled) == set(diagnostics["diagnostics"])
        point = []
        for name in sampled:
            parameter = cfg["params"][name]
            value = Fraction(parameter["ref"])
            assert Fraction(parameter["prior"]["min"]) <= value <= Fraction(parameter["prior"]["max"])
            point.append(value)
        refs.append(tuple(point))
    assert len(set(refs)) == 4
    minimum = int(min(lengths))
    assert minimum == snapshot["minimum_retained_represented_steps"] == registered["minimum_saved_postburn_history"]
    assert registered["next_minimum_history"] == (6 * minimum + 4) // 5
    if count == 10:
        assert snapshot["previous_snapshot_receipt"] is None and snapshot["assessment_trigger"] == 1000
        assert native["loaded_CLASS_version"] == "v3.4.0" and native["solver_version"] is None
    else:
        previous_path = Path(snapshot["previous_snapshot_receipt"])
        assert sha(previous_path) == snapshot["previous_snapshot_sha256"]
        previous = read(previous_path)
        assert previous["group"] == group and previous["contract_sha256"] == snapshot["contract_sha256"]
        assert snapshot["assessment_trigger"] == (6 * previous["minimum_retained_represented_steps"] + 4) // 5
        old = {f["seed"]: f for f in previous["families"]}
        for family in snapshot["families"]:
            old_path = Path(old[family["seed"]]["snapshot"])
            assert sha(old_path) == old[family["seed"]]["snapshot_sha256"]
            assert Path(family["snapshot"]).read_bytes().startswith(old_path.read_bytes())
    assert minimum >= snapshot["assessment_trigger"]
    checks = [c for r in native["records"] for c in r["checks"]]
    assert len(checks) == 12 and all(isfinite(value) and value == 0
        for check in checks for value in check["fresh_minus_recorded"].values())
    gates = reviewed[gate_field]
    assert len(gates) == count and set(gates) == set(diagnostics["diagnostics"])
    for name, d in diagnostics["diagnostics"].items():
        if "error" in d:
            assert not d["diagnostic_thresholds_pass"] and not gates[name]["pass"]
            continue
        p, limit = d["quantile_mcse"], d["quantile_mcse_limit"]
        rebuilt = {"separate_starts": d["n_chains"] >= 2,
            "finite": all(d[k] is not None and isfinite(d[k]) for k in (
                "rank_folded_split_rhat", "bulk_ess", "tail_ess_05_95", "quantile_ess", "quantile_mcse")),
            "Rhat": d["rank_folded_split_rhat"] <= 1.01,
            "bulk_ESS": d["bulk_ess"] >= 400, "tail_ESS": d["tail_ess_05_95"] >= 400,
            "quantile_ESS": d["quantile_ess"] >= 400, "MCSE": 0 < p <= limit,
            "chronological_drift": d["quantile_half_difference"] <= 4 * max(p, limit),
            "equalized_selection": abs(d["quantile_full_draws"] - d["quantile_retained_draws"]) <= 2 * max(p, limit)}
        assert rebuilt == gates[name]["gates"] and all(rebuilt.values()) == d["diagnostic_thresholds_pass"]
    assert diagnostics["diagnostics"][mass_name]["quantile_mcse_limit"] == 0.001
    assert not diagnostics["all_diagnostic_thresholds_pass"] and not registered["posterior_qualified"]
    records.append({"group": group, "snapshot_sha256": sha(snapshot_path),
        "contract_sha256": sha(contract_path), "native_sha256": sha(folder / "native_rows_verification.json"),
        "diagnostic_sha256": sha(folder / "diagnostics.json"), "sampled_parameter_count": count,
        "next_history_trigger": registered["next_minimum_history"],
        "fixed_ref_distinctness_witnessed_separately": True, "posterior_qualified": False})
with (HERE / "self_review_receipt.json").open("x") as f:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent", "records": records,
        "seventeen_numeric_gate_sets_reconstructed": True, "eight_weighted_histories_recounted": True,
        "selected_native_rows_exact": 24, "first_CLASS_production_contract_not_control_promotion": True,
        "CLASS_absent_solver_metadata_not_filled_with_loaded_version": True,
        "targets_and_historical_failed_cohorts_not_pooled": True,
        "starts_not_PRNG_independence_or_stationarity": True,
        "MCSE_not_substituted_for_Readout_absolute_error_inputs": True}, f, indent=2, allow_nan=False)
    f.write("\n")
print("First CLASS and archived A assessments reviewed: 17 gate sets, 24 exact native rows; neither qualifies.")
