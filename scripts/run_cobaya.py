#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cobaya.run import run as cobaya_run  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Cobaya config and capture run bundle artifacts.")
    parser.add_argument("--config", required=True, type=str)
    parser.add_argument("--outdir", default=None, type=str)
    parser.add_argument("--seed", default=0, type=int)
    parser.add_argument("--packages_path", default="external/cobaya_packages", type=str)
    parser.add_argument("--max_samples_override", default=None, type=int)
    return parser.parse_args()


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level mapping")
    return data


def _run_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _resolve_outdir(config: dict[str, Any], explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    run_name = config.get("run_name", "run")
    if not isinstance(run_name, str) or not run_name.strip():
        run_name = "run"
    return REPO_ROOT / "runs" / f"{_stamp()}_cobaya_{run_name}"


def _inject_seed(config: dict[str, Any], seed: int) -> None:
    sampler = config.get("sampler")
    if not isinstance(sampler, dict):
        raise ValueError("config missing sampler mapping")
    if "mcmc" not in sampler or not isinstance(sampler["mcmc"], dict):
        raise ValueError("config must define sampler.mcmc mapping")
    sampler["mcmc"]["seed"] = int(seed)


def _inject_max_samples_override(config: dict[str, Any], max_samples: int | None) -> None:
    if max_samples is None:
        return
    if max_samples <= 0:
        raise ValueError("--max_samples_override must be > 0")
    sampler = config.get("sampler")
    if not isinstance(sampler, dict):
        raise ValueError("config missing sampler mapping")
    if "mcmc" not in sampler or not isinstance(sampler["mcmc"], dict):
        raise ValueError("config must define sampler.mcmc mapping")
    sampler["mcmc"]["max_samples"] = int(max_samples)


def _write_summary(outdir: Path, lines: list[str]) -> None:
    (outdir / "summary.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        config = _load_yaml(config_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to parse config: {exc}", file=sys.stderr)
        return 2

    outdir = _resolve_outdir(config, args.outdir)
    outdir.mkdir(parents=True, exist_ok=False)
    (outdir / "chains").mkdir(parents=True, exist_ok=True)

    run_name = config.get("run_name", "run") if isinstance(config.get("run_name"), str) else "run"
    chains_prefix = outdir / "chains" / run_name

    try:
        _run_env(outdir)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to capture env: {exc}", file=sys.stderr)
        return 1

    (outdir / "input.yaml").write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")

    resolved = deepcopy(config)
    resolved["output"] = str(chains_prefix)
    resolved["packages_path"] = str(Path(args.packages_path).expanduser().resolve())
    _inject_seed(resolved, args.seed)
    _inject_max_samples_override(resolved, args.max_samples_override)
    (outdir / "resolved.yaml").write_text(yaml.safe_dump(resolved, sort_keys=False), encoding="utf-8")

    stdout_path = outdir / "stdout.txt"
    stderr_path = outdir / "stderr.txt"

    success = False
    error_msg: str | None = None
    with stdout_path.open("w", encoding="utf-8") as f_out, stderr_path.open("w", encoding="utf-8") as f_err:
        with redirect_stdout(f_out), redirect_stderr(f_err):
            try:
                cobaya_run(resolved, no_mpi=True, stop_at_error=True)
                success = True
            except Exception as exc:  # noqa: BLE001
                error_msg = f"{type(exc).__name__}: {exc}"
                success = False
                print(error_msg, file=f_err)

    metrics_path = outdir / "metrics.json"
    extract_ok = False
    if success:
        extract = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "extract_mnu_limits.py"),
                "--run_dir",
                str(outdir),
                "--param",
                "mnu",
                "--output",
                str(metrics_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        (outdir / "extract_stdout.txt").write_text(extract.stdout, encoding="utf-8")
        (outdir / "extract_stderr.txt").write_text(extract.stderr, encoding="utf-8")
        extract_ok = extract.returncode == 0

    summary_lines = [
        f"- run_name: {run_name}",
        f"- config: {config_path}",
        f"- output_prefix: {chains_prefix}",
        f"- cobaya_success: {success}",
        f"- extraction_success: {extract_ok}",
        f"- metrics_path: {metrics_path if metrics_path.exists() else 'missing'}",
    ]
    if error_msg:
        summary_lines.append(f"- error: {error_msg}")
    _write_summary(outdir, summary_lines)

    print(f"Run bundle: {outdir}")
    if not success:
        return 1
    if not extract_ok:
        return 1

    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        print(
            "mnu summary:",
            f"median={metrics.get('mnu_median')}",
            f"p95={metrics.get('mnu_p95_upper')}",
            f"boundary={metrics.get('boundary_fraction')}",
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
