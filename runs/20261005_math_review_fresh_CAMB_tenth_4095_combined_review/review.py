"""Reconstruct both expanded-history assessments without promoting either posterior."""
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
records = []
for group in ("current_A4095", "current_B4095"):
    registered = state["fresh_CAMB_production_assessments"][group]
    folder = ROOT / registered["root"]
    prep = read(folder / "worker_preparation_receipt.json")
    source = ROOT / prep["source"]
    assert sha(source) == prep["source_sha256"] and prep["changes"] == []
    assert source.read_bytes() == (folder / "run_verification.py").read_bytes()
    execution = read(folder / "execution_receipt.json")
    assert execution["exit_code"] == 0 and execution["all_verification_workers_terminal"]
    assert len(execution["stages"]) == 3
    assert all(s["actual_exit_code"] == 0 for s in execution["stages"])
    snapshot = read(folder / "snapshot_receipt.json")
    previous_path = Path(snapshot["previous_snapshot_receipt"])
    previous = read(previous_path)
    assert sha(previous_path) == snapshot["previous_snapshot_sha256"]
    assert snapshot["group"] == previous["group"] == group
    assert snapshot["predecessor_contract_compatibility_checked"]
    assert snapshot["contract_sha256"] == previous["contract_sha256"]
    trigger = ceil(Fraction(6, 5) * previous["minimum_retained_represented_steps"])
    assert snapshot["assessment_trigger"] == trigger
    assert snapshot["minimum_retained_represented_steps"] >= trigger
    assert registered["next_minimum_history"] == ceil(
        Fraction(6, 5) * snapshot["minimum_retained_represented_steps"])
    old = {f["seed"]: f for f in previous["families"]}
    for family in snapshot["families"]:
        raw = Path(family["snapshot"]).read_bytes()
        prior = Path(old[family["seed"]]["snapshot"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == family["snapshot_sha256"]
        assert hashlib.sha256(prior).hexdigest() == old[family["seed"]]["snapshot_sha256"]
        assert raw.startswith(prior) and (ROOT / family["source"]).read_bytes().startswith(raw)
        weights = [Fraction(line.split()[0]) for line in raw.decode().splitlines()
                   if line.strip() and not line.startswith("#")]
        assert all(w > 0 and w.denominator == 1 for w in weights)
        assert sum(weights[len(weights) // 5:]) == family["retained_represented_steps"]
    native = read(folder / "native_rows_verification.json")
    checks = [c for r in native["records"] for c in r["checks"]]
    assert len(checks) == 12
    assert max(abs(v) for c in checks for v in c["fresh_minus_recorded"].values()) == 0
    diagnostic = read(folder / "diagnostics.json")
    assert len(diagnostic["diagnostics"]) == 7
    assert not diagnostic["all_diagnostic_thresholds_pass"]
    assert not registered["posterior_qualified"]
    mass = diagnostic["diagnostics"]["mnu"]
    assert not mass["diagnostic_thresholds_pass"]
    assert mass["quantile_mcse"] > mass["quantile_mcse_limit"] == 0.001
    assert mass["bulk_ess"] == registered["mass_bulk_ESS"]
    assert mass["tail_ess_05_95"] == registered["mass_tail_ESS"]
    assert mass["rank_folded_split_rhat"] == registered["mass_Rhat"]
    assert mass["quantile_mcse"] == registered["mass_MCSE_eV"]
    records.append({"group": group, "snapshot_sha256": sha(folder / "snapshot_receipt.json"),
        "native_sha256": sha(folder / "native_rows_verification.json"),
        "diagnostic_sha256": sha(folder / "diagnostics.json"),
        "self_review_sha256": sha(folder / "self_review_receipt.json"),
        "previous_snapshot_sha256": sha(previous_path),
        "passing_parameters": registered["passing_parameters"],
        "mass_Rhat": mass["rank_folded_split_rhat"], "mass_MCSE_eV": mass["quantile_mcse"],
        "next_history_trigger": registered["next_minimum_history"], "posterior_qualified": False})
with (HERE / "self_review_receipt.json").open("x") as f:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent", "records": records,
        "all_four_family_predecessor_prefixes_checked_for_each_target": True,
        "exact_weighted_history_and_growth_checked": True,
        "selected_native_rows_exact": 24, "seven_parameter_diagnostics_checked": True,
        "both_posteriors_unqualified": True, "mass_limit_difference_not_promoted": True},
        f, indent=2, allow_nan=False)
    f.write("\n")
print("Both tenth 4095 assessments reviewed; 24 native rows exact, both posteriors unqualified.")
