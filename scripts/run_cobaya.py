#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime
import hashlib
import importlib
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
from sbt_spt_audit.mcmc import mcmc_config_options  # noqa: E402
from sbt_spt_audit.boltzmann import configure_fresh_camb_transfers  # noqa: E402


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
    mcmc_config_options(config)["seed"] = int(seed)


def _inject_max_samples_override(config: dict[str, Any], max_samples: int | None) -> None:
    if max_samples is None:
        return
    if max_samples <= 0:
        raise ValueError("--max_samples_override must be > 0")
    mcmc_config_options(config)["max_samples"] = int(max_samples)


def _configure_chain_output(config: dict[str, Any]) -> None:
    # Preserve every MCMC option and the target, while making saved floating
    # point witnesses round-trip-safe. The resolved bundle records this choice.
    options = mcmc_config_options(config)
    config["sampler"] = {"sbt_spt_audit.samplers.FullPrecisionMCMC": options}


def _validate_classy_backend(config: dict[str, Any]) -> dict[str, Any] | None:
    """Enforce an explicitly declared native solver build before creating output."""
    notes = config.get("notes", {})
    requirement = notes.get("classy_backend") if isinstance(notes, dict) else None
    if requirement is None:
        return None
    if not isinstance(requirement, dict) or "classy" not in config.get("theory", {}):
        raise ValueError("classy_backend requires a declared CLASS theory and a backend contract.")
    if config["theory"]["classy"].get("path") not in (None, "global"):
        raise ValueError("The guarded CLASS contract requires the verified Python import; remove the conflicting theory path.")
    receipt_path = Path(requirement["build_receipt"]).expanduser()
    if not receipt_path.is_absolute():
        receipt_path = REPO_ROOT / receipt_path
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected = requirement["module_sha256"]
    if receipt["module_sha256"] != expected:
        raise ValueError("CLASS build receipt disagrees with the configured native module hash.")
    classy = importlib.import_module("classy")
    module_path = Path(importlib.import_module(classy.Class.__module__).__file__).resolve()
    actual = hashlib.sha256(module_path.read_bytes()).hexdigest()
    if actual != expected or module_path != Path(receipt["module"]).resolve():
        overlay = Path(receipt["module"]).resolve().parent.parent
        raise ValueError(
            "CLASS native backend does not match the declared verified guarded build. "
            f"Set PYTHONPATH to {overlay} before launching, or declare and validate a new build. "
            f"Loaded {module_path} with SHA256 {actual}."
        )
    return {"module": str(module_path), "module_sha256": actual,
            "build_receipt": str(receipt_path.resolve()),
            "build_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest()}


def _validate_native_backend(config: dict[str, Any]) -> dict[str, Any] | None:
    """Check declared build identity against the solver this process will use."""
    notes = config.get("notes", {})
    if not isinstance(notes, dict):
        return None
    contracts = [name for name in ("classy", "camb") if notes.get(name + "_backend") is not None]
    if not contracts:
        return None
    theory = config.get("theory", {})
    solvers = [name for name in ("classy", "camb") if name in theory]
    if len(contracts) != 1 or solvers != contracts:
        raise ValueError("Native backend contract requires one matching Boltzmann solver.")
    solver = contracts[0]
    if solver == "classy":
        backend = _validate_classy_backend(config)
        return {**backend, "solver": solver}
    requirement = notes["camb_backend"]
    options = theory["camb"] or {}
    if not isinstance(requirement, dict) or not isinstance(options, dict):
        raise ValueError("camb_backend requires a CAMB theory and a backend contract.")
    if options.get("path") not in (None, "global"):
        raise ValueError("The guarded CAMB contract requires the verified Python import; remove the conflicting theory path.")
    expected = requirement.get("module_sha256")
    version = requirement.get("solver_version")
    if (not isinstance(expected, str) or len(expected) != 64
            or any(c not in "0123456789abcdef" for c in expected)
            or not isinstance(version, str) or not version.strip()):
        raise ValueError("CAMB backend contract requires a native SHA256 and solver version.")
    if options.get("version", version) != version:
        raise ValueError("CAMB theory version disagrees with the native backend contract.")
    camb = importlib.import_module("camb")
    module_path = Path(camb.baseconfig.camblib._name).resolve()
    actual = hashlib.sha256(module_path.read_bytes()).hexdigest()
    if actual != expected or camb.__version__ != version:
        raise ValueError(
            "CAMB native backend does not match the declared build and version. "
            f"Loaded {module_path} with SHA256 {actual} and version {camb.__version__}."
        )
    return {"solver": solver, "module": str(module_path),
            "module_sha256": actual, "solver_version": camb.__version__}


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

    try:
        backend = _validate_native_backend(config)
        resolved = deepcopy(config)
        configure_fresh_camb_transfers(resolved)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed native solver configuration: {exc}", file=sys.stderr)
        return 2

    outdir = _resolve_outdir(config, args.outdir)
    outdir.mkdir(parents=True, exist_ok=False)
    (outdir / "chains").mkdir(parents=True, exist_ok=True)
    if backend is not None:
        (outdir / "solver_backend.json").write_text(json.dumps(backend, indent=2) + "\n", encoding="utf-8")

    run_name = config.get("run_name", "run") if isinstance(config.get("run_name"), str) else "run"
    chains_prefix = outdir / "chains" / run_name

    try:
        _run_env(outdir)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to capture env: {exc}", file=sys.stderr)
        return 1

    (outdir / "input.yaml").write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")

    if backend is not None:
        # Cobaya otherwise prefers a solver under packages_path. The checked
        # import is already loaded, and global loading preserves that identity.
        resolved["theory"][backend["solver"]]["path"] = "global"
    resolved["output"] = str(chains_prefix)
    resolved["packages_path"] = str(Path(args.packages_path).expanduser().resolve())
    _inject_seed(resolved, args.seed)
    _inject_max_samples_override(resolved, args.max_samples_override)
    _configure_chain_output(resolved)
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
        for warning in metrics.get("warnings", []):
            print(f"Diagnostic warning: {warning}")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
