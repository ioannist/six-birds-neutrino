"""Reconcile four completed native coordinates with archived target checks."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
paths = {
    "metrics": HERE / "metrics.json",
    "progress": HERE / "progress.json",
    "medium": HERE / "medium_progress_snapshot.json",
    "default": HERE / "default_target_verification.json",
    "points": HERE / "points.json",
    "launch": HERE / "launch_receipt.json",
    "runtime": HERE / "runtime_state.json",
}
data = {name: json.loads(path.read_text()) for name, path in paths.items()}
for name, digest in data["launch"]["input_sha256"].items():
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
assert data["runtime"]["status"] == "complete_sampled_sensitivity_control_not_error_certificate"
records = data["metrics"]["records"]
assert records == data["progress"]
expected = {"chain_A_q50", "chain_A_q95", "chain_B_q50", "chain_B_q95"}
assert set(data["points"]) == expected
assert set(records) == {"baseline", "selected_reference_settings"}
assert all(set(group) == expected for group in records.values())


def own(record, lens):
    other = "lensB" if lens == "A" else "lensA"
    return math.fsum(value for name, value in record["native_chi2"].items() if name != other)


results = {}
for label in sorted(expected):
    lens = label.split("_")[1]
    baseline = records["baseline"][label]
    broader = records["selected_reference_settings"][label]
    medium = data["medium"]["baseline"][label]
    default = data["default"]["records"][label]
    assert baseline["point"] == broader["point"] == medium["point"] == default["point"] == data["points"][label]
    assert baseline["native_chi2"] == medium["native_chi2"]
    assert set(broader["native_chi2"]) == set(baseline["native_chi2"]) == set(default["native_chi2"])
    assert all(math.isfinite(value) for record in [baseline, broader, default]
               for value in record["native_chi2"].values())
    assert baseline["spectrum_ell_max"] == broader["spectrum_ell_max"] == {"tt": 4095, "ee": 4095}
    native_change = {name: value - baseline["native_chi2"][name]
                     for name, value in broader["native_chi2"].items()}
    assert native_change == data["metrics"]["refined_minus_baseline"][label]["native_chi2_change"]
    results[label] = {
        "point": broader["point"],
        "native_broader_minus_medium": native_change,
        "own_joint_broader_minus_medium": own(broader, lens) - own(baseline, lens),
        "own_joint_broader_minus_default": own(broader, lens) - own(default, lens),
        "elapsed_seconds": broader["elapsed_seconds"],
    }
relative = {
    lens: {setting: results[f"chain_{lens}_q95"][f"own_joint_broader_minus_{setting}"]
                  - results[f"chain_{lens}_q50"][f"own_joint_broader_minus_{setting}"]
           for setting in ["medium", "default"]}
    for lens in ["A", "B"]
}
receipt = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "scope": "four_completed_archived_coordinate_native_comparisons",
    "source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for name, path in paths.items()},
    "launch_input_hashes_verified": True,
    "baseline_native_components_equal_archived_medium": True,
    "results": results,
    "tail_minus_median_numerical_correction_change": relative,
    "interpretation": "All sampled coordinates vary within each pair from unconverged archives; these are pointwise numerical corrections, not a mass-only effect or a quantile bias.",
    "posterior_accuracy_certified": False,
    "posterior_convergence_certified": False,
    "interval_error_certified": False,
}
(HERE / "completed_comparison_verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"results": results, "tail_minus_median": relative}, indent=2))
