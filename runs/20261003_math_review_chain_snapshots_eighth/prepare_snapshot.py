"""Archive complete prefixes of all twenty original replicas without overwriting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / "runs/20261003_math_review_validation/review_state.json").read_text())
assert not (HERE / "snapshot_receipt.json").exists()
assert len(state["restoration_chains"]) == 20
files, configs, groups = [], [], {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


for chain in state["restoration_chains"]:
    source = ROOT / chain["run_dir"]
    label = source.name.removeprefix("20261003_math_review_")
    destination = HERE / label
    assert not destination.exists()
    (destination / "chains").mkdir(parents=True)
    chains = list((source / "chains").glob("*.txt"))
    assert len(chains) == 1
    source_chain = chains[0]
    raw = source_chain.read_bytes()
    complete = raw[:raw.rfind(b"\n") + 1]
    assert complete
    snapshot = destination / "chains" / source_chain.name
    snapshot.write_bytes(complete)
    rows = sum(bool(line.strip()) and not line.lstrip().startswith(b"#")
               for line in complete.splitlines())
    files.append({"source": str(source_chain.relative_to(ROOT)),
                  "snapshot": str(snapshot.relative_to(ROOT)),
                  "source_bytes": len(raw), "complete_bytes": len(complete),
                  "sha256": digest(complete), "stored_rows": rows})
    for name in ["input.yaml", "resolved.yaml"]:
        original = (source / name).read_bytes()
        saved = original
        if name == "resolved.yaml":
            cfg = yaml.safe_load(original)
            prefix = Path(cfg["output"]).name
            assert source_chain.name == prefix + ".1.txt"
            cfg["output"] = str(destination / "chains" / prefix)
            saved = yaml.safe_dump(cfg, sort_keys=False).encode()
        target = destination / name
        target.write_bytes(saved)
        configs.append({"source": str((source / name).relative_to(ROOT)),
                        "snapshot": str(target.relative_to(ROOT)),
                        "source_sha256": digest(original),
                        "snapshot_sha256": digest(saved)})
    group = ("cmb_chain_" if chain["kind"] == "cmb_desi" else "chain_") + chain["lens"]
    groups.setdefault(group, []).append(destination)

commands = {}
for group, directories in groups.items():
    command = [sys.executable, str(ROOT / "scripts/diagnose_cobaya_chains.py")]
    for directory in sorted(directories):
        command += ["--run-dir", str(directory)]
    command += ["--burnin-frac", "0.2", "--quantile-mcse-limit",
                "0.001" if group.startswith("cmb_") else "0.005",
                "--relative-quantile-mcse-limit", "0.05",
                "--output", str(HERE / (group + "_diagnostics.json"))]
    commands[group] = command
receipt = {"utc": datetime.now(timezone.utc).isoformat(),
           "scope": "progress_diagnostics_no_bound_claim", "complete_lines_only": True,
           "files": files, "configurations": configs,
           "controlled_precision_chains_included": False,
           "diagnostic_commands": commands,
           "diagnostic_script_sha256": digest((ROOT / "scripts/diagnose_cobaya_chains.py").read_bytes())}
(HERE / "snapshot_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"snapshot_rows": {Path(f["source"]).parents[1].name: f["stored_rows"]
                                     for f in files}}, indent=2))
