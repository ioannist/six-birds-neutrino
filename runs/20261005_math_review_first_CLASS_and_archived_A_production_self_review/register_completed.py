"""Record actual observed terminal executions; keep numerical targets separate."""
from datetime import datetime, timezone
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state_path = ROOT / "runs/20261003_math_review_validation/review_state.json"
read = lambda p: json.loads(Path(p).read_text())
def write_new(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")

state = read(state_path)
records = [
    ("fresh_CLASS_recovery_production_assessments", "fresh_recovery_quad_A",
     "runs/20261005_math_review_CLASS_fresh_first_quad_A_diagnostics", 2761, "mnu_sample"),
    ("fresh_CAMB_production_assessments", "old_A3200",
     "runs/20261005_math_review_fresh_CAMB_eleventh_old_A3200_diagnostics_v2", 14948, "mnu"),
]
for key, group, relative, session, mass_name in records:
    folder = ROOT / relative
    stages = []
    for stage in ("verify_native_rows.py", "run_diagnostic.py", "verify_snapshot.py"):
        completion = folder / (stage + ".completion.json")
        assert read(completion)["exit_code"] == 0
        stages.append({"stage": stage, "actual_exit_code": 0,
                       "completion": str(completion.relative_to(ROOT))})
    write_new(folder / "execution_receipt.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "managed_session": session,
        "exit_code": 0, "all_verification_workers_terminal": True,
        "terminal_observation": "write_stdin returned actual managed exit_code 0",
        "stages": stages})
    snapshot = read(folder / "snapshot_receipt.json")
    review = read(folder / "self_review_receipt.json")
    native = read(folder / "native_rows_verification.json")
    diagnostics = read(folder / "diagnostics.json")
    mass = diagnostics["diagnostics"][mass_name]
    differences = [value for record in native["records"] for check in record["checks"]
                   for value in check["fresh_minus_recorded"].values()]
    assert differences and max(map(abs, differences)) == 0
    assert not diagnostics["all_diagnostic_thresholds_pass"]
    state[key][group] = {
        "root": relative, "native_verification": relative + "/native_rows_verification.json",
        "diagnostics": relative + "/diagnostics.json", "self_review": relative + "/self_review_receipt.json",
        "execution_receipt": relative + "/execution_receipt.json", "managed_session": session,
        "all_three_verification_stages_exit_code": 0,
        "minimum_saved_postburn_history": snapshot["minimum_retained_represented_steps"],
        "next_minimum_history": review["next_minimum_history"], "selected_native_rows": 12,
        "maximum_native_component_error": 0.0,
        "all_parameter_gate_sets_pass": False,
        "passing_parameters": [name for name, d in diagnostics["diagnostics"].items()
                               if d["diagnostic_thresholds_pass"]],
        "mass_parameter": mass_name, "mass_Rhat": mass["rank_folded_split_rhat"],
        "mass_bulk_ESS": mass["bulk_ess"], "mass_tail_ESS": mass["tail_ess_05_95"],
        "mass_MCSE_eV": mass["quantile_mcse"], "posterior_qualified": False,
        "solver_version": native["solver_version"]}
    if "loaded_CLASS_version" in native:
        state[key][group]["loaded_CLASS_version"] = native["loaded_CLASS_version"]
state["fresh_CLASS_recovery_active_diagnostic_workflow"]["production_assessments_completed"] = 1
initial = ROOT / "runs/20261005_math_review_registered80_CLASS_first_production_initial_checkpoint"
write_new(initial / "execution_receipt.json", {
    "utc": datetime.now(timezone.utc).isoformat(), "observer_managed_session": 57371,
    "observer_actual_terminal_exit_code": 0, "self_review_direct_exit_code": 0,
    "growth_scope_direct_reconstruction_exit_code": 0, "all_verification_workers_terminal": True})
state_path.write_text(json.dumps(state, indent=2, allow_nan=False) + "\n")
print("Registered first CLASS and eleventh archived-CAMB assessments; neither qualifies.")
