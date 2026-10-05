"""Check current process ownership against pinned earlier process identities."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / "runs/20261003_math_review_validation/review_state.json").read_text())
previous_path = ROOT / "runs/20261004_math_review_class_backend_transition/runtime_verification.json"
previous = {e["seed"]: e for e in json.loads(previous_path.read_text())["records"]}
entries = [e for e in state["restoration_chains"] if e["kind"] == "spt_desi"]
entries += state["guarded_solver_posterior_trials"]
entries += state["guarded_quadrature_posterior_chains"]
entries += state["guarded_medium_posterior_chains"]
entries += state["guarded_grid12_posterior_trials"]
assert len(entries) == 29 and len({e["pid"] for e in entries}) == 29
original = Path("/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy/_classy.cpython-312-x86_64-linux-gnu.so")
assert hashlib.sha256(original.read_bytes()).hexdigest() == "38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a"
records = []
for entry in entries:
    proc = Path("/proc", str(entry["pid"]))
    seed = entry["seed"]
    if seed in (401, 402, 403, 404):
        assert not proc.exists()
        records.append({"seed": seed, "pid": entry["pid"], "status": "completed_scientific_process_absent"})
        continue
    if seed == 1501:
        launch_path = ROOT / entry["launch_receipt"]
        launch = json.loads(launch_path.read_text())
        assert launch["pid"] == entry["pid"] and launch["seed"] == seed
        previous[seed] = {"process_start_ticks": launch["process_start_ticks"],
                          "mapped_guarded_module": launch["module"]}
    stat = (proc / "stat").read_text().split()
    assert stat[2] != "Z" and int(stat[21]) == previous[seed]["process_start_ticks"]
    command = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode()
    if seed == 1501:
        assert "seed1501/launch_trial.py" in command
    else:
        assert command == previous[seed]["command"]
    run = ROOT / entry["run_dir"]
    assert not (run / "stderr.txt").read_bytes()
    native = previous[seed]["mapped_guarded_module"]
    if seed >= 1201:
        maps = (proc / "maps").read_text()
        assert native in maps and str(original) not in maps
        assert hashlib.sha256(Path(native).read_bytes()).hexdigest() == entry["native_module_sha256"]
    log = (run / "stdout.txt").read_text()
    progress = re.findall(r"Progress @ ([^\n]+) : (\d+) steps taken, and (\d+) accepted", log)
    record = {"seed": seed, "pid": entry["pid"], "status": "live_same_owned_identity",
              "process_start_ticks": int(stat[21]), "mapped_guarded_module": native,
              "stderr_empty": True}
    if progress:
        timestamp, steps, accepted = progress[-1]
        record["latest_progress"] = {"utc": timestamp, "steps": int(steps), "accepted": int(accepted)}
    records.append(record)
live = [r for r in records if r["status"] == "live_same_owned_identity"]
assert len(live) == 25
result = {"utc": datetime.now(timezone.utc).isoformat(), "records": records,
          "earlier_identity_receipt": str(previous_path.relative_to(ROOT)),
          "earlier_identity_receipt_sha256": hashlib.sha256(previous_path.read_bytes()).hexdigest(),
          "owned_live_samplers": 25, "SPT_live": 8, "SPT_diagnostic_families": 12,
          "guarded_CLASS_live": 17, "completed_SPT_families": [401, 402, 403, 404],
          "original_CLASS_inference_active": False,
          "grid12_trial_launch_receipt": str(launch_path.relative_to(ROOT)),
          "grid12_trial_launch_receipt_sha256": hashlib.sha256(launch_path.read_bytes()).hexdigest(), "posterior_convergence_certified": False}
with (HERE / "runtime_observation.json").open("x") as handle:
    handle.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
print("25 owned samplers verified: 8 SPT and 17 guarded CLASS; all 12 SPT families retained.")
