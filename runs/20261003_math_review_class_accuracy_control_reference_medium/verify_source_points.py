"""Compare the two completed source coordinates; local mass offsets are pending."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
paths = {
    "reference_medium": HERE / "source_points_progress_snapshot.json",
    "reference": ROOT / "runs/20261003_math_review_class_accuracy_control_reference/metrics.json",
    "medium": ROOT / "runs/20261003_math_review_class_accuracy_control_medium/metrics.json",
}
data = {k: json.loads(p.read_text()) for k, p in paths.items()}
records = {
    k: v if k == "reference_medium" else v["records"]
    for k, v in data.items()
}


def own(record, lens):
    other = "lensB" if lens == "A" else "lensA"
    return math.fsum(v for k, v in record["native_chi2"].items() if k != other)


results = {}
for lens in ["A", "B"]:
    label = "audit_" + lens
    baseline = records["reference_medium"]["baseline"][label]
    selected = records["reference_medium"]["selected_reference_settings"][label]
    assert baseline["point"] == selected["point"]
    assert selected["spectrum_ell_max"] == {"tt": 4095, "ee": 4095}
    assert all(math.isfinite(v) for v in selected["native_chi2"].values())
    differences = {}
    for name in ["reference", "medium"]:
        other_base = records[name]["baseline"][label]
        other = records[name]["selected_reference_settings"][label]
        assert baseline["point"] == other_base["point"] == other["point"]
        assert baseline["native_chi2"] == other_base["native_chi2"]
        assert set(selected["native_chi2"]) == set(other["native_chi2"])
        differences[name] = {
            "native_components": {
                k: v - other["native_chi2"][k]
                for k, v in selected["native_chi2"].items()
            },
            "own_joint_chi2": own(selected, lens) - own(other, lens),
            "runtime_ratio": selected["elapsed_seconds"] / other["elapsed_seconds"],
        }
    results[label] = {
        "point": selected["point"],
        "elapsed_seconds": selected["elapsed_seconds"],
        "reference_medium_minus_controls": differences,
    }
receipt = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "scope": "two_completed_fixed_source_coordinates_local_mass_offsets_pending",
    "source_sha256": {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
    "baseline_native_components_equal_prior_controls": True,
    "results": results,
    "posterior_accuracy_certified": False,
    "interval_error_certified": False,
}
(HERE / "source_points_comparison.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
