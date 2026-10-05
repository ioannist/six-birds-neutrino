"""Witness distinct starts from frozen inputs instead of inferring them from chain count."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import isfinite
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
obstacle_path = HERE / "obstacle_receipt.json"
records = []
for bound in read(obstacle_path)["records"]:
    snapshot_path = ROOT / bound["snapshot_path"]
    assert sha(snapshot_path) == bound["snapshot_sha256"]
    snapshot = read(snapshot_path)
    starts, first_points, bindings = [], [], []
    assert len({f["seed"] for f in snapshot["families"]}) == 4
    for family in snapshot["families"]:
        chain = Path(family["snapshot"])
        folder = chain.parent.parent
        config_path = folder / "input.yaml"
        assert sha(chain) == family["snapshot_sha256"]
        assert sha(config_path) == family["source_input_sha256"]
        cfg = yaml.safe_load(config_path.read_text())
        names = sorted(name for name, value in cfg["params"].items()
                       if isinstance(value, dict) and "prior" in value)
        assert len(names) == 7 and "mnu" in names
        point = []
        for name in names:
            parameter = cfg["params"][name]
            ref = parameter["ref"]
            assert isinstance(ref, (int, float)) and isfinite(ref)
            value = Fraction(ref)
            assert Fraction(parameter["prior"]["min"]) <= value <= Fraction(parameter["prior"]["max"])
            point.append(value)
        starts.append(tuple(point))
        lines = chain.read_text().splitlines()
        header = lines[0].lstrip("#").split()
        row = next(line.split() for line in lines if line.strip() and not line.startswith("#"))
        first_points.append(tuple(Fraction(row[header.index(name)]) for name in names))
        bindings.append({"seed": family["seed"], "input_sha256": sha(config_path),
            "chain_sha256": sha(chain), "fixed_mass_ref_eV": cfg["params"]["mnu"]["ref"]})
    assert len(set(starts)) == len(set(first_points)) == 4
    records.append({"group": bound["group"], "bindings": bindings,
        "four_distinct_fixed_ref_points_in_recorded_prior": True,
        "four_distinct_first_saved_points": True})
assert len(records) == 9
with (HERE / "starts_witness_receipt.json").open("x") as f:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent",
        "obstacle_receipt_sha256": sha(obstacle_path), "records": records,
        "gate_named_separate_starts_checks_chain_count_only": True,
        "distinctness_witnessed_separately_from_actual_bound_inputs": True,
        "no_PRNG_independence_stationarity_or_prior_exploration_proof": True},
        f, indent=2, allow_nan=False)
    f.write("\n")
print("Nine targets have four distinct fixed refs and first saved points; independence remains unproved.")
