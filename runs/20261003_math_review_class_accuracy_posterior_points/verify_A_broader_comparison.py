"""Check the two completed A coordinates; B and convergence remain pending."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
paths = {
    "progress": HERE / "A_broader_progress_snapshot.json",
    "medium": HERE / "medium_progress_snapshot.json",
    "default": HERE / "default_target_verification.json",
    "selection": HERE / "points.json",
}
data = {k: json.loads(p.read_text()) for k, p in paths.items()}


def own(record):
    return math.fsum(v for k, v in record["native_chi2"].items() if k != "lensB")


results = {}
for label in ["chain_A_q50", "chain_A_q95"]:
    baseline = data["progress"]["baseline"][label]
    broader = data["progress"]["selected_reference_settings"][label]
    medium = data["medium"]["baseline"][label]
    default = data["default"]["records"][label]
    assert baseline["point"] == broader["point"] == medium["point"] == default["point"]
    assert broader["point"] == data["selection"][label]
    assert baseline["native_chi2"] == medium["native_chi2"]
    assert broader["spectrum_ell_max"] == {"tt": 4095, "ee": 4095}
    assert set(broader["native_chi2"]) == set(baseline["native_chi2"]) == set(default["native_chi2"])
    assert all(math.isfinite(v) for v in broader["native_chi2"].values())
    results[label] = {
        "point": broader["point"],
        "native_broader_minus_medium": {
            k: v - baseline["native_chi2"][k]
            for k, v in broader["native_chi2"].items()
        },
        "own_joint_broader_minus_medium": own(broader) - own(baseline),
        "own_joint_broader_minus_default": own(broader) - own(default),
        "elapsed_seconds": broader["elapsed_seconds"],
    }
receipt = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "scope": "two_completed_selected_A_coordinates_B_reference_evaluations_pending",
    "source_sha256": {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
    "baseline_native_components_equal_archived_medium": True,
    "results": results,
    "A_tail_minus_median_numerical_correction_change": {
        setting: results["chain_A_q95"]["own_joint_broader_minus_" + setting]
        - results["chain_A_q50"]["own_joint_broader_minus_" + setting]
        for setting in ["medium", "default"]
    },
    "interpretation": "All sampled coordinates vary between the two points; this does not identify a pure mass effect or a quantile bias.",
    "posterior_accuracy_certified": False,
    "posterior_convergence_certified": False,
}
(HERE / "A_broader_comparison.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
