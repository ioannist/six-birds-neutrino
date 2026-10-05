"""Exercise the actual toy bundle CLI without fitting or sampling cosmology."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources = [ROOT / "runs/20261003_math_review_toy_audit" / name for name in ("lensA", "lensB")]
source_files = [path / name for path in sources for name in ("config.yaml", "bestfit.json")]
bound = [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in source_files]
records = []
for mode in ("dominant_whitened", "full_residual"):
    outdir = HERE / ("cli_" + mode)
    command = [sys.executable, str(ROOT / "scripts/run_template_rewrite.py"),
               "--runA", str(sources[0]), "--runB", str(sources[1]),
               "--template", mode, "--outdir", str(outdir)]
    with (HERE / (mode + "_stdout.txt")).open("x") as stdout, (HERE / (mode + "_stderr.txt")).open("x") as stderr:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr)
    record = {"mode": mode, "command": command, "actual_exit_code": result.returncode,
              "utc": datetime.now(timezone.utc).isoformat()}
    with (HERE / (mode + "_completion.json")).open("x") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
    if result.returncode:
        raise SystemExit(result.returncode)
    payload = json.loads((outdir / "metrics.json").read_text(),
                         parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    for direction in ("B_given_A", "A_given_B"):
        d = payload[direction]
        assert d["chi2_before"] > 0 and 0 <= d["chi2_after"] <= d["chi2_before"]
        if mode == "full_residual":
            assert d["chi2_after"] == 0 and d["fraction_removed"] == 1 and d["a_star"] == 1
    record["metrics_sha256"] = sha(outdir / "metrics.json")
    records.append(record)
for file in bound:
    assert sha(ROOT / file["path"]) == file["sha256"]
with (HERE / "cli_controls_receipt.json").open("x") as output:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(), "records": records,
               "source_files": bound, "original_source_bundles_unchanged": True,
               "fitting_or_cosmological_sampling_launched": False,
               "strict_JSON_outputs_verified": True}, output, indent=2)
    output.write("\n")
print("Actual toy rewrite CLI passed both modes and both directions; no scientific claim promotion.")
