"""Interrupt only identity-verified owned samplers using reuse-safe pidfds."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = json.loads((ROOT / "runs/20261003_math_review_validation/review_state.json").read_text())
runtime_path = HERE / "combined_runtime_verification.json"
runtime = json.loads(runtime_path.read_text())
keys = ["guarded_solver_posterior_trials", "guarded_quadrature_posterior_chains",
        "guarded_medium_posterior_chains", "guarded_grid12_posterior_trials",
        "fresh_CAMB_posterior_chains", "upper_prior_posterior_chains",
        "native_candidate_posterior_chains", "guarded_CLASS_fresh_recovery_trials",
        "CLASS_recovery_companion_posterior_chains", "CLASS_fresh_B_posterior_chains"]
entries = {entry["seed"]: entry for key in keys for entry in state[key]}
live = [r for r in runtime["records"] if r["status"] == "live_same_owned_native_identity"]
assert len(entries) == 80 and len(live) == 61
receipt_path = HERE / "stop_requests.jsonl"
with receipt_path.open("x") as output:
    for record in live:
        pid, seed = record["pid"], record["seed"]
        event = {"utc": datetime.now(timezone.utc).isoformat(), "seed": seed,
                 "pid": pid, "process_start_ticks": record["process_start_ticks"],
                 "managed_session": entries[seed]["session"],
                 "run_dir": entries[seed]["run_dir"], "signal": "SIGINT",
                 "reason": "user instructed dropping attempts to justify unsupported or contradicted original claims",
                 "signal_sent": False}
        fd = None
        try:
            fd = os.pidfd_open(pid)
            proc = Path("/proc", str(pid))
            stat = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            assert stat[0] != "Z" and int(stat[19]) == record["process_start_ticks"]
            command = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode()
            assert command == record["command"]
            assert record["module"] in (proc / "maps").read_text()
            assert sha(record["module"]) == record["module_sha256"]
            event["owned_identity_revalidated"] = True
            signal.pidfd_send_signal(fd, signal.SIGINT)
            event["signal_sent"] = True
        except (OSError, AssertionError) as error:
            event["refusal"] = type(error).__name__ + ": " + str(error)
        finally:
            if fd is not None:
                os.close(fd)
        output.write(json.dumps(event, allow_nan=False) + "\n")
        output.flush()
events = [json.loads(line) for line in receipt_path.read_text().splitlines()]
assert len(events) == 61 and all(e["signal_sent"] for e in events)
with (HERE / "stop_request_summary.json").open("x") as output:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
               "prestop_runtime_sha256": sha(runtime_path),
               "stop_requests_sha256": sha(receipt_path),
               "owned_live_identities": 61, "SIGINT_requests_sent": 61,
               "historical_terminal_families_not_signaled": 19,
               "terminal_exits_not_inferred_from_signals": True,
               "posterior_qualification_unchanged": False}, output, indent=2)
    output.write("\n")
print("Sent SIGINT to all 61 revalidated owned samplers; terminal verification remains required.")
