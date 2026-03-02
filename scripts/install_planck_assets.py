#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_PATH = REPO_ROOT / "external" / "cobaya_packages"


CORE_TARGETS = [
    "planck_2018_lowl.TT",
    "planck_2018_lowl.EE_sroll2",
    "planck_2018_highl_plik.TT_lite_native",
]


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


def _run_install(target: str) -> dict[str, object]:
    cmd = [
        "cobaya-install",
        target,
        "--packages-path",
        str(PACKAGES_PATH),
        "--no-set-global",
    ]
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return {
        "target": target,
        "returncode": int(res.returncode),
        "ok": res.returncode == 0,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


def _run_pr4_fallback_yaml() -> dict[str, object]:
    tmp_yaml = REPO_ROOT / "runs" / ".tmp_planckpr4_install.yaml"
    tmp_yaml.write_text(
        "\n".join(
            [
                "likelihood:",
                "  planckpr4lensing:",
                "    package_install:",
                "      github_repository: carronj/planck_PR4_lensing",
                "      min_version: 1.0.2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    cmd = [
        "cobaya-install",
        str(tmp_yaml),
        "--packages-path",
        str(PACKAGES_PATH),
        "--no-set-global",
    ]
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    pr4_dir = PACKAGES_PATH / "code" / "planck_PR4_lensing" / "planckpr4lensing"
    ok = pr4_dir.exists()
    try:
        tmp_yaml.unlink()
    except OSError:
        pass
    return {
        "target": "planckpr4lensing (fallback yaml install)",
        "returncode": int(res.returncode),
        "ok": bool(ok),
        "stdout": res.stdout,
        "stderr": res.stderr,
        "verification_path": str(pr4_dir),
        "verification_exists": ok,
    }


def main() -> int:
    PACKAGES_PATH.mkdir(parents=True, exist_ok=True)

    outdir = REPO_ROOT / "runs" / f"{_stamp()}_planck_install"
    outdir.mkdir(parents=True, exist_ok=False)

    _write_env(outdir)

    results: list[dict[str, object]] = []
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    for target in CORE_TARGETS:
        status = _run_install(target)
        results.append({k: v for k, v in status.items() if k not in {"stdout", "stderr"}})
        stdout_lines.append(f"=== target: {target} rc={status['returncode']} ===")
        stdout_lines.append(str(status["stdout"]).rstrip())
        stderr_lines.append(f"=== target: {target} rc={status['returncode']} ===")
        stderr_lines.append(str(status["stderr"]).rstrip())

    pr4_status = _run_pr4_fallback_yaml()
    results.append({k: v for k, v in pr4_status.items() if k not in {"stdout", "stderr"}})
    stdout_lines.append(
        f"=== target: {pr4_status['target']} rc={pr4_status['returncode']} "
        f"verified={pr4_status.get('verification_exists')} ==="
    )
    stdout_lines.append(str(pr4_status["stdout"]).rstrip())
    stderr_lines.append(
        f"=== target: {pr4_status['target']} rc={pr4_status['returncode']} "
        f"verified={pr4_status.get('verification_exists')} ==="
    )
    stderr_lines.append(str(pr4_status["stderr"]).rstrip())

    (outdir / "stdout.txt").write_text("\n".join(stdout_lines) + "\n", encoding="utf-8")
    (outdir / "stderr.txt").write_text("\n".join(stderr_lines) + "\n", encoding="utf-8")

    succeeded = [r["target"] for r in results if r["ok"]]
    failed = [r["target"] for r in results if not r["ok"]]

    attempted_targets = CORE_TARGETS + [str(pr4_status["target"])]
    metrics = {
        "packages_path": str(PACKAGES_PATH),
        "attempted_targets": attempted_targets,
        "results": results,
        "succeeded_targets": succeeded,
        "failed_targets": failed,
    }
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    summary_lines = [
        f"- run_bundle: {outdir}",
        f"- packages_path: {PACKAGES_PATH}",
        f"- attempted: {len(attempted_targets)}",
        f"- succeeded: {len(succeeded)}",
        f"- failed: {len(failed)}",
        f"- succeeded_targets: {succeeded}",
        f"- failed_targets: {failed}",
    ]
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Run bundle: {outdir}")
    print(f"Succeeded: {succeeded}")
    print(f"Failed: {failed}")

    # Keep diagnostic tool non-fatal; caller decides if failures are blockers.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
