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

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cobaya.model import get_model  # noqa: E402


REF_POINT = {
    "omegabh2": 0.02237,
    "omegach2": 0.1200,
    "H0": 67.36,
    "ns": 0.9649,
    "tau": 0.0544,
    "mnu": 0.06,
    "logA": 3.044,
    "A_planck": 1.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sanity-check Planck subset baseline config.")
    parser.add_argument("--config", required=True, type=str)
    parser.add_argument("--outdir", default=None, type=str)
    parser.add_argument("--packages_path", default="external/cobaya_packages", type=str)
    return parser.parse_args()


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def _write_env(outdir: Path) -> None:
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


def _spectra_from_like(name: str, like_obj: Any) -> list[str]:
    if hasattr(like_obj, "use_cl"):
        vals = getattr(like_obj, "use_cl")
        if isinstance(vals, (list, tuple)):
            return [str(v).upper() for v in vals]
    if hasattr(like_obj, "requested_cls_lmax"):
        req = getattr(like_obj, "requested_cls_lmax")
        if isinstance(req, dict):
            return [str(k).upper() for k in req.keys()]
    low = name.lower()
    if "lensing" in low:
        return ["PP"]
    return []


def _safe_float(value: Any) -> float | None:
    try:
        x = float(value)
    except Exception:
        return None
    return x if math.isfinite(x) else None


def _extract_lrange(name: str, like_obj: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "component": name,
        "class": f"{like_obj.__class__.__module__}.{like_obj.__class__.__name__}",
        "spectra": _spectra_from_like(name, like_obj),
    }

    # PlanckPlikLite-like native class with bin selection.
    if all(hasattr(like_obj, attr) for attr in ["blmin", "blmax", "used_bins"]):
        try:
            used_indices: list[int] = []
            for arr in getattr(like_obj, "used_bins"):
                if len(arr):
                    used_indices.extend(int(x) for x in np.asarray(arr, dtype=int).tolist())
            if used_indices:
                blmin = np.asarray(getattr(like_obj, "blmin"), dtype=int)
                blmax = np.asarray(getattr(like_obj, "blmax"), dtype=int)
                info["lmin"] = int(np.min(blmin[used_indices]))
                info["lmax"] = int(np.max(blmax[used_indices]))
                info["n_used_bins"] = int(len(used_indices))
                return info
        except Exception:
            pass

    # Low-l classes (native) often expose lmin/lmax or _lmin/_lmax.
    for lo_key, hi_key in [("lmin", "lmax"), ("_lmin", "_lmax")]:
        if hasattr(like_obj, lo_key) and hasattr(like_obj, hi_key):
            lo = getattr(like_obj, lo_key)
            hi = getattr(like_obj, hi_key)
            lo_f = _safe_float(lo)
            hi_f = _safe_float(hi)
            if lo_f is not None and hi_f is not None:
                info["lmin"] = int(lo_f)
                info["lmax"] = int(hi_f)
                return info

    # Clik-like classes expose per-spectrum requested lmax.
    if hasattr(like_obj, "requested_cls_lmax"):
        req = getattr(like_obj, "requested_cls_lmax")
        if isinstance(req, dict) and req:
            per_spec = {str(k).upper(): int(v) for k, v in req.items()}
            info["per_spectrum_lmax"] = per_spec
            info["lmin"] = 2
            info["lmax"] = int(max(per_spec.values()))
            return info

    # Fallback: scan a few common attribute names.
    for key in ["lmax", "l_max", "ellmax", "ell_max"]:
        if hasattr(like_obj, key):
            val = _safe_float(getattr(like_obj, key))
            if val is not None:
                info["lmax"] = int(val)
                break
    for key in ["lmin", "l_min", "ellmin", "ell_min"]:
        if hasattr(like_obj, key):
            val = _safe_float(getattr(like_obj, key))
            if val is not None:
                info["lmin"] = int(val)
                break

    return info


def _build_ref_point(config: dict[str, Any], model: Any) -> dict[str, float]:
    params_cfg = config.get("params", {}) if isinstance(config.get("params"), dict) else {}
    sampled = list(model.parameterization.sampled_params())

    point: dict[str, float] = {}
    for p in sampled:
        if p in REF_POINT:
            point[p] = float(REF_POINT[p])
            continue

        block = params_cfg.get(p)
        if isinstance(block, dict):
            ref = block.get("ref")
            if isinstance(ref, (int, float)):
                point[p] = float(ref)
                continue
            val = block.get("value")
            if isinstance(val, (int, float)):
                point[p] = float(val)
                continue
            prior = block.get("prior")
            if isinstance(prior, dict):
                lo = prior.get("min")
                hi = prior.get("max")
                if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
                    point[p] = 0.5 * (float(lo) + float(hi))
                    continue

        # Deterministic fallback.
        point[p] = 1.0
    return point


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    packages_path = Path(args.packages_path).expanduser().resolve()

    cfg = _load_yaml(config_path)
    run_name = cfg.get("run_name") if isinstance(cfg.get("run_name"), str) else config_path.stem
    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else REPO_ROOT / "runs" / f"{_stamp()}_planck_subset_sanity_{run_name}"
    )
    outdir.mkdir(parents=True, exist_ok=False)

    _write_env(outdir)
    (outdir / "inputs.yaml").write_text(
        yaml.safe_dump(
            {
                "config": str(config_path),
                "packages_path": str(packages_path),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    logs: list[str] = []

    def log(msg: str) -> None:
        print(msg)
        logs.append(msg)

    model = get_model(cfg, packages_path=str(packages_path), stop_at_error=True)
    point = _build_ref_point(cfg, model)

    like_out = model.loglikes(point, as_dict=True, return_derived=False)
    if not isinstance(like_out, dict):
        raise RuntimeError("Expected loglikes(as_dict=True) to return a dictionary")

    loglike_components = {k: float(v) for k, v in like_out.items()}
    loglike_total = float(sum(loglike_components.values()))

    planck_components: dict[str, Any] = {}
    for name, like_obj in model.likelihood.items():
        lname = str(name)
        llow = lname.lower()
        if "planck" in llow or "clik" in llow:
            planck_components[lname] = _extract_lrange(lname, like_obj)

    metrics = {
        "config": str(config_path),
        "packages_path": str(packages_path),
        "planck_components": planck_components,
        "loglike_components": loglike_components,
        "loglike_total": loglike_total,
    }

    log(f"config={config_path}")
    log(f"packages_path={packages_path}")
    log("planck_components:")
    for comp, info in planck_components.items():
        log(f"- {comp}: {info}")
    log(f"loglike_total={loglike_total}")

    (outdir / "stdout.txt").write_text("\n".join(logs) + "\n", encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (outdir / "summary.md").write_text(
        "\n".join(
            [
                f"- run_bundle: {outdir}",
                f"- config: {config_path}",
                f"- planck_components_n: {len(planck_components)}",
                f"- loglike_total: {loglike_total}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Run bundle: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
