"""Freeze a completed SPT family without replacing ensemble convergence checks."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / "runs/20261003_math_review_validation/review_state.json").read_text())
entry = next(e for e in state["restoration_chains"] if e["seed"] == 404)
assert entry["pid"] == 2333851 and entry["exec_session"] == 26652
assert not Path("/proc", str(entry["pid"])).exists()
source = ROOT / entry["run_dir"]
log = (source / "stdout.txt").read_text()
assert "The run has converged!" in log
assert "Sampling complete after 18760 accepted steps." in log
assert not (source / "stderr.txt").read_bytes()
assert not (source / "extract_stderr.txt").read_bytes()
checkpoint = yaml.safe_load(next((source / "chains").glob("*.checkpoint")).read_text())
assert checkpoint["sampler"]["mcmc"]["converged"] is True
assert (source / "metrics.json").exists()
target = HERE / "seed404"
assert not target.exists()
files = []
for original in sorted(source.rglob("*")):
    if not original.is_file():
        continue
    raw = original.read_bytes()
    frozen = target / original.relative_to(source)
    frozen.parent.mkdir(parents=True, exist_ok=True)
    frozen.write_bytes(raw)
    assert original.read_bytes() == raw == frozen.read_bytes()
    files.append({"source": str(original.relative_to(ROOT)),
                  "archive": str(frozen.relative_to(ROOT)),
                  "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
chain = next((target / "chains").glob("*.1.txt"))
raw = chain.read_bytes()
assert raw.endswith(b"\n")
rows = np.atleast_2d(np.loadtxt(BytesIO(raw)))
assert len(rows) == 18760 and np.all(np.isfinite(rows))
assert np.all(rows[:, 0] > 0) and np.all(rows[:, 0] == np.floor(rows[:, 0]))
receipt = {
    "utc": datetime.now(timezone.utc).isoformat(), "seed": 404,
    "scientific_pid": entry["pid"], "managed_session": entry["exec_session"],
    "managed_exit_code": 0, "scientific_process_absent": True,
    "reason": "configured_Cobaya_internal_mean_and_bound_stopping_test",
    "accepted_samples": len(rows), "checkpoint": checkpoint,
    "complete_output_bundle_preserved": True, "files": files,
    "retain_family_in_next_twelve_family_SPT_assessment": True,
    "independent_ensemble_gates_changed": False,
    "independent_ensemble_convergence_verified": False,
    "posterior_bound_replacement_authorized_by_this_completion": False,
}
with (HERE / "completion_receipt.json").open("x") as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
print("B404 exit zero; 18,760-row complete bundle frozen; ensemble gates retained.")
