#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cobaya.model import get_model  # noqa: E402


DEFAULT_CONFIGS = [
    "configs/neutrino/cmb_spt2018_plancksubset_desi_mnu.yaml",
    "configs/neutrino/cmb_sptd1_plancksubset_desi_mnu.yaml",
]

REF_DEFAULTS = {
    "omegabh2": 0.02237,
    "omegach2": 0.1200,
    "H0": 67.36,
    "ns": 0.9649,
    "tau": 0.0544,
    "logA": 3.044,
    "A_planck": 1.0,
    "TT_tSZ_Amp": 2.0,
    "TT_kSZ_Amp": 2.0,
    "mnu": 0.06,
    "mnu_sample": 0.06,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate N5 configs at reference point (no MCMC).")
    parser.add_argument("--config", action="append", default=[], help="Config path (can be given multiple times)")
    parser.add_argument("--outdir", default=None, type=str)
    parser.add_argument("--packages_path", default="external/cobaya_packages", type=str)
    return parser.parse_args()


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def _run_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level mapping")
    return data


def _pick_ref_value(name: str, block: Any) -> float:
    if name in REF_DEFAULTS:
        return float(REF_DEFAULTS[name])

    if isinstance(block, dict):
        ref = block.get("ref")
        if isinstance(ref, (int, float)):
            return float(ref)
        val = block.get("value")
        if isinstance(val, (int, float)):
            return float(val)
        prior = block.get("prior")
        if isinstance(prior, dict):
            lo = prior.get("min")
            hi = prior.get("max")
            if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
                return 0.5 * (float(lo) + float(hi))

    return 1.0


def _build_point(config: dict[str, Any], model: Any) -> dict[str, float]:
    params_cfg = config.get("params") if isinstance(config.get("params"), dict) else {}
    point: dict[str, float] = {}
    for pname in model.parameterization.sampled_params():
        point[pname] = _pick_ref_value(str(pname), params_cfg.get(pname))
    return point


def _is_finite_dict(d: dict[str, Any]) -> bool:
    for v in d.values():
        try:
            x = float(v)
        except Exception:
            return False
        if not math.isfinite(x):
            return False
    return True


def _evaluate_one(config_path: Path, packages_path: Path) -> dict[str, Any]:
    cfg = _load_yaml(config_path)
    model = get_model(cfg, packages_path=str(packages_path), stop_at_error=True)
    point = _build_point(cfg, model)
    out = model.loglikes(point, as_dict=True, return_derived=False)
    if not isinstance(out, dict):
        raise RuntimeError("loglikes(as_dict=True) did not return dict")

    loglikes = {str(k): float(v) for k, v in out.items()}
    total = float(sum(loglikes.values()))
    finite_total = math.isfinite(total)
    finite_components = _is_finite_dict(loglikes)

    return {
        "config": str(config_path),
        "run_name": cfg.get("run_name", config_path.stem),
        "sampled_params": list(model.parameterization.sampled_params()),
        "ref_point": point,
        "loglike_components": loglikes,
        "loglike_total": total,
        "finite_total": finite_total,
        "finite_components": finite_components,
    }


def main() -> int:
    args = parse_args()
    configs = [Path(c).expanduser().resolve() for c in (args.config or DEFAULT_CONFIGS)]
    packages_path = Path(args.packages_path).expanduser().resolve()

    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else REPO_ROOT / "runs" / f"{_stamp()}_eval_cmb_plancksubset_desi"
    )
    outdir.mkdir(parents=True, exist_ok=False)

    _run_env(outdir)
    (outdir / "inputs.yaml").write_text(
        yaml.safe_dump(
            {
                "configs": [str(p) for p in configs],
                "packages_path": str(packages_path),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    logs: list[str] = []
    results: list[dict[str, Any]] = []
    failed = False

    for config_path in configs:
        try:
            res = _evaluate_one(config_path, packages_path)
            results.append(res)
            logs.append(f"config={config_path}")
            logs.append(f"  loglike_total={res['loglike_total']}")
            for name, val in res["loglike_components"].items():
                logs.append(f"  {name}={val}")
        except Exception as exc:  # noqa: BLE001
            failed = True
            logs.append(f"config={config_path}")
            logs.append(f"  ERROR: {type(exc).__name__}: {exc}")
            results.append(
                {
                    "config": str(config_path),
                    "error": f"{type(exc).__name__}: {exc}",
                    "finite_total": False,
                    "finite_components": False,
                }
            )

    (outdir / "stdout.txt").write_text("\n".join(logs) + "\n", encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")

    summary = [
        f"- run_bundle: {outdir}",
        f"- n_configs: {len(configs)}",
        f"- failed: {failed}",
    ]
    for res in results:
        summary.append(
            f"- {Path(res.get('config', 'unknown')).name}: finite_total={res.get('finite_total')}"
        )
    (outdir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print(f"Run bundle: {outdir}")
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
