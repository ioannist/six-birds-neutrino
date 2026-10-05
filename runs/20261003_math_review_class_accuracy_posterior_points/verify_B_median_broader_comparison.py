"""Verify the completed B median coordinate; its selected tail is still pending."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
paths = {
    "progress": HERE / "B_median_broader_progress_snapshot.json",
    "medium": HERE / "medium_progress_snapshot.json",
    "default": HERE / "default_target_verification.json",
    "selection": HERE / "points.json",
}
data = {name: json.loads(path.read_text()) for name, path in paths.items()}
label = "chain_B_q50"
baseline = data["progress"]["baseline"][label]
broader = data["progress"]["selected_reference_settings"][label]
medium = data["medium"]["baseline"][label]
default = data["default"]["records"][label]
assert baseline["point"] == broader["point"] == medium["point"] == default["point"]
assert broader["point"] == data["selection"][label]
assert baseline["native_chi2"] == medium["native_chi2"]
assert broader["spectrum_ell_max"] == {"tt": 4095, "ee": 4095}
assert set(broader["native_chi2"]) == set(baseline["native_chi2"]) == set(default["native_chi2"])
assert all(math.isfinite(value) for value in broader["native_chi2"].values())


def own(record):
    return math.fsum(value for name, value in record["native_chi2"].items() if name != "lensA")


receipt = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "scope": "completed_selected_B_median_coordinate_B_tail_pending",
    "source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for name, path in paths.items()},
    "baseline_native_components_equal_archived_medium": True,
    "point_label": label,
    "native_broader_record": broader,
    "native_broader_minus_medium": {
        name: value - baseline["native_chi2"][name]
        for name, value in broader["native_chi2"].items()
    },
    "own_joint_broader_minus_medium": own(broader) - own(baseline),
    "own_joint_broader_minus_default": own(broader) - own(default),
    "interpretation": "A test coordinate selected from an unconverged archive; no B tail-relative change or posterior bias is determined.",
    "posterior_accuracy_certified": False,
    "posterior_convergence_certified": False,
}
(HERE / "B_median_broader_comparison.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({key: receipt[key] for key in ["own_joint_broader_minus_medium",
                                             "own_joint_broader_minus_default"]}))
