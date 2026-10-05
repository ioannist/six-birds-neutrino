"""Archive twenty replica families, using fresh segments after recorded restarts."""
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
    segment = complete
    boundary = None
    resume_input = None
    if chain.get('resume_seed'):
        recovery = ROOT / chain['recovery_dir']
        boundary = json.loads((recovery / 'segment_boundaries.json').read_text())['segments'][str(chain['seed'])]
        old_path = recovery / f"seed{chain['seed']}" / 'chains' / source_chain.name
        old = old_path.read_bytes()
        assert len(old) == boundary['historical_prefix_byte_count']
        assert digest(old) == boundary['historical_chain_sha256']
        assert complete.startswith(old)
        segment = complete.splitlines(keepends=True)[0] + complete[len(old):]
        assert segment.splitlines()[1:]
        resume_input = recovery / f"seed{chain['seed']}" / 'resume_input.yaml'
    snapshot = destination / "chains" / source_chain.name
    snapshot.write_bytes(segment)
    rows = sum(bool(line.strip()) and not line.lstrip().startswith(b"#")
               for line in segment.splitlines())
    files.append({"source": str(source_chain.relative_to(ROOT)),
                  "snapshot": str(snapshot.relative_to(ROOT)),
                  "source_bytes": len(raw), "complete_bytes": len(complete),
                  "snapshot_bytes": len(segment),
                  "sha256": digest(segment), "stored_rows": rows,
                  "source_complete_sha256": digest(complete),
                  "trajectory_scope": 'post_recovery_segment' if boundary else 'uninterrupted_saved_prefix',
                  "historical_saved_rows_excluded": boundary['historical_saved_rows'] if boundary else 0,
                  "original_seed": chain['seed'],
                  "active_segment_seed": chain.get('resume_seed', chain['seed'])})
    for name in ["input.yaml", "resolved.yaml"]:
        original = (source / name).read_bytes()
        saved = original
        if name == "resolved.yaml" or resume_input:
            cfg = yaml.safe_load(resume_input.read_bytes() if resume_input else original)
            if resume_input:
                assert cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] == chain['resume_seed']
                cfg.pop('resume', None)
            prefix = Path(cfg["output"]).name
            assert source_chain.name == prefix + ".1.txt"
            cfg["output"] = str(destination / "chains" / prefix)
            saved = yaml.safe_dump(cfg, sort_keys=False).encode()
        target = destination / name
        target.write_bytes(saved)
        configs.append({"source": str((source / name).relative_to(ROOT)),
                        "snapshot": str(target.relative_to(ROOT)),
                        "source_sha256": digest(original),
                        "snapshot_sha256": digest(saved),
                        "recovery_configuration_source": str(resume_input.relative_to(ROOT)) if resume_input else None,
                        "recovery_configuration_sha256": digest(resume_input.read_bytes()) if resume_input else None})
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
           "recorded_restarts_use_only_fresh_segments": True,
           "diagnostic_commands": commands,
           "diagnostic_script_sha256": digest((ROOT / "scripts/diagnose_cobaya_chains.py").read_bytes())}
(HERE / "snapshot_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"snapshot_rows": {Path(f["source"]).parents[1].name: f["stored_rows"]
                                     for f in files}}, indent=2))
