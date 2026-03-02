#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import yaml


def now_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def import_optional(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SPT discovery + finite loglike smoke eval.")
    parser.add_argument("--outdir", type=str, default=None)
    parser.add_argument("--spt2018_id", type=str, default=None)
    parser.add_argument("--sptd1_id", type=str, default=None)
    return parser.parse_args()


def discover_ids(candl_data_mod: Any | None, spt_data_mod: Any | None) -> tuple[str | None, str | None]:
    spt2018 = None
    sptd1 = None
    if candl_data_mod is not None:
        s = getattr(candl_data_mod, "shortcuts", {})
        if isinstance(s, dict):
            entry = s.get("SPT-3G 2018 TT/TE/EE")
            if isinstance(entry, dict):
                target = entry.get("multifreq") or entry.get("index")
                if isinstance(target, str):
                    spt2018 = f"candl_data.{target}"
    if spt_data_mod is not None:
        s = getattr(spt_data_mod, "shortcuts", {})
        if isinstance(s, dict):
            entry = s.get("SPT-3G D1 TnE")
            if isinstance(entry, dict):
                target = entry.get("multifreq") or entry.get("index")
                if isinstance(target, str):
                    sptd1 = f"spt_candl_data.{target}"
    return spt2018, sptd1


def resolve_dataset_expr(expr: str) -> tuple[str, str, str]:
    parts = expr.split(".")
    if len(parts) != 2:
        raise ValueError(f"dataset expression must be module.attr, got: {expr}")
    module_name, attr_name = parts
    mod = importlib.import_module(module_name)
    dataset_path = getattr(mod, attr_name)
    if not isinstance(dataset_path, str):
        raise TypeError(f"{expr} did not resolve to a string path")
    return module_name, attr_name, dataset_path


def find_test_case(dataset_expr: str, module_name: str) -> tuple[Path, dict[str, Any]]:
    mod = importlib.import_module(module_name)
    data_path = getattr(mod, "data_path", None)
    if not isinstance(data_path, str):
        raise FileNotFoundError(f"{module_name} has no data_path for test discovery")
    tests_dir = Path(data_path) / "tests"
    if not tests_dir.exists():
        raise FileNotFoundError(f"tests directory not found: {tests_dir}")

    for test_yaml in sorted(tests_dir.glob("*.yaml")):
        payload = yaml.safe_load(test_yaml.read_text(encoding="utf-8"))
        if payload.get("data_set_file") == dataset_expr:
            return test_yaml, payload
    raise FileNotFoundError(f"no test yaml found for {dataset_expr} in {tests_dir}")


def build_params(test_yaml: Path, payload: dict[str, Any]) -> dict[str, Any]:
    test_spec = np.loadtxt(test_yaml.parent / str(payload["test_spectrum"]))
    pars_for_like = deepcopy(payload["param_values"])
    pars_for_like["Dl"] = {}
    for i, spec in enumerate(["ell", "TT", "TE", "EE", "BB", "pp", "kk"]):
        pars_for_like["Dl"][spec] = test_spec[:, i]
    return pars_for_like


def evaluate_from_test_vector(
    candl_mod: Any,
    dataset_path: str,
    payload: dict[str, Any],
    pars_for_like: dict[str, Any],
) -> tuple[str, float, float]:
    is_lensing = bool(payload.get("lensing", False))
    like_cls = candl_mod.LensLike if is_lensing else candl_mod.Like
    like_obj = like_cls(dataset_path, feedback=False)
    chi2 = float(like_obj.chi_square(pars_for_like))
    logl = float(like_obj.log_like(pars_for_like))
    return str(getattr(like_obj, "name", "unknown")), chi2, logl


def write_env(outdir: Path, repo_root: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    outdir = (
        Path(args.outdir).resolve()
        if args.outdir
        else repo_root / "runs" / f"{now_stamp()}_candl_spt_smoke"
    )
    outdir.mkdir(parents=True, exist_ok=False)

    lines: list[str] = []

    def log(msg: str) -> None:
        print(msg)
        lines.append(msg)

    log(f"run_bundle: {outdir}")

    candl_mod, candl_err = import_optional("candl")
    candl_data_mod, candl_data_err = import_optional("candl_data")
    spt_data_mod, spt_data_err = import_optional("spt_candl_data")
    camb_mod, camb_err = import_optional("camb")
    classy_mod, classy_err = import_optional("classy")
    cobaya_mod, cobaya_err = import_optional("cobaya")

    log(f"candl_importable={candl_mod is not None}")
    log(f"candl_data_importable={candl_data_mod is not None}")
    log(f"spt_candl_data_importable={spt_data_mod is not None}")
    log(f"camb_importable={camb_mod is not None}")
    log(f"classy_importable={classy_mod is not None}")
    log(f"cobaya_importable={cobaya_mod is not None}")

    if candl_mod is None:
        log(f"candl_import_error={candl_err}")
    if candl_data_mod is None:
        log(f"candl_data_import_error={candl_data_err}")
    if spt_data_mod is None:
        log(f"spt_candl_data_import_error={spt_data_err}")
    if camb_mod is None:
        log(f"camb_import_error={camb_err}")
    if classy_mod is None:
        log(f"classy_import_error={classy_err}")
    if cobaya_mod is None:
        log(f"cobaya_import_error={cobaya_err}")

    auto_2018, auto_d1 = discover_ids(candl_data_mod, spt_data_mod)
    spt2018_id = args.spt2018_id or auto_2018
    sptd1_id = args.sptd1_id or auto_d1
    log(f"spt2018_id={spt2018_id}")
    log(f"sptd1_id={sptd1_id}")

    metrics: dict[str, Any] = {
        "candl_importable": candl_mod is not None,
        "candl_data_importable": candl_data_mod is not None,
        "spt_candl_data_importable": spt_data_mod is not None,
        "camb_importable": camb_mod is not None,
        "classy_importable": classy_mod is not None,
        "cobaya_importable": cobaya_mod is not None,
        "spt2018_id_guess": spt2018_id,
        "sptd1_id_guess": sptd1_id,
        "spt2018": {},
        "sptd1": {},
        "errors": {},
    }

    for key, dataset_expr in [("spt2018", spt2018_id), ("sptd1", sptd1_id)]:
        if candl_mod is None:
            metrics["errors"][key] = "candl not importable"
            continue
        if not dataset_expr:
            metrics["errors"][key] = "dataset id not found"
            continue
        try:
            module_name, _, dataset_path = resolve_dataset_expr(dataset_expr)
            test_yaml, payload = find_test_case(dataset_expr, module_name)
            pars_for_like = build_params(test_yaml, payload)
            like_name, chi2, logl = evaluate_from_test_vector(
                candl_mod, dataset_path, payload, pars_for_like
            )
            finite = math.isfinite(chi2) and math.isfinite(logl)
            log(f"{key}: like={like_name}")
            log(f"{key}: test_yaml={test_yaml}")
            log(f"{key}: chi2={chi2}")
            log(f"{key}: loglike={logl}")
            log(f"{key}: finite={finite}")
            metrics[key] = {
                "dataset_expr": dataset_expr,
                "dataset_path": dataset_path,
                "test_yaml": str(test_yaml),
                "like_name": like_name,
                "chi2": chi2,
                "loglike": logl,
                "finite": finite,
            }
        except Exception as exc:  # noqa: BLE001
            msg = f"{type(exc).__name__}: {exc}"
            log(f"{key}: error={msg}")
            metrics["errors"][key] = msg

    write_env(outdir, repo_root)
    (outdir / "stdout.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    summary = [
        "# candl SPT Discovery + Smoke Eval",
        "",
        f"- run bundle: `{outdir}`",
        f"- spt2018 id: `{spt2018_id}`",
        f"- sptd1 id: `{sptd1_id}`",
        f"- spt2018 finite: `{metrics.get('spt2018', {}).get('finite')}`",
        f"- sptd1 finite: `{metrics.get('sptd1', {}).get('finite')}`",
        "",
        "Errors:",
    ]
    if metrics["errors"]:
        for comp, err in metrics["errors"].items():
            summary.append(f"- `{comp}`: `{err}`")
    else:
        summary.append("- none")
    (outdir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
