#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
import importlib
import json
from pathlib import Path
import pkgutil
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_PR4_PATH = REPO_ROOT / "external" / "cobaya_packages" / "code" / "planck_PR4_lensing"


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


def main() -> int:
    outdir = REPO_ROOT / "runs" / f"{_stamp()}_planck_like_list"
    outdir.mkdir(parents=True, exist_ok=False)

    lines: list[str] = []
    metrics: dict[str, object] = {}

    import cobaya
    import cobaya.likelihoods as likelihoods

    lines.append(f"cobaya_version={cobaya.__version__}")
    lines.append("available_planck_like_modules:")

    found = []
    for mod in pkgutil.walk_packages(likelihoods.__path__, likelihoods.__name__ + "."):
        name = mod.name
        if "planck" in name.lower() or "clik" in name.lower():
            short = name.replace("cobaya.likelihoods.", "")
            found.append(short)
    found = sorted(set(found))

    for name in found:
        lines.append(f"- {name}")

    # Optional external PR4 lensing package listing.
    pr4_classes: list[str] = []
    pr4_info: dict[str, object] = {"importable": False}
    try:
        pr4 = importlib.import_module("planckpr4lensing")
        pr4_info["importable"] = True
        pr4_info["version"] = getattr(pr4, "__version__", "unknown")
        for attr in dir(pr4):
            obj = getattr(pr4, attr)
            if isinstance(obj, type):
                pr4_classes.append(attr)
        pr4_classes = sorted(pr4_classes)
        lines.append(f"planckpr4lensing_importable=True version={pr4_info['version']}")
        lines.append("planckpr4lensing_classes:")
        for c in pr4_classes:
            lines.append(f"- {c}")
    except Exception as exc:  # noqa: BLE001
        pr4_info["error"] = f"{type(exc).__name__}: {exc}"
        lines.append(f"planckpr4lensing_importable=False error={pr4_info['error']}")

    if EXTERNAL_PR4_PATH.exists():
        lines.append(f"planckpr4lensing_external_path={EXTERNAL_PR4_PATH}")
        yaml_classes = sorted(p.stem for p in (EXTERNAL_PR4_PATH / "planckpr4lensing").glob("*.yaml"))
        if yaml_classes:
            lines.append("planckpr4lensing_external_yaml_classes:")
            for c in yaml_classes:
                lines.append(f"- {c}")
        metrics["planckpr4lensing_external_path"] = str(EXTERNAL_PR4_PATH)
        metrics["planckpr4lensing_external_yaml_classes"] = yaml_classes

    metrics["cobaya_version"] = cobaya.__version__
    metrics["planck_like_modules"] = found
    metrics["planckpr4lensing"] = pr4_info
    metrics["planckpr4lensing_classes"] = pr4_classes

    _write_env(outdir)
    (outdir / "stdout.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (outdir / "summary.md").write_text(
        "\n".join(
            [
                f"- run_bundle: {outdir}",
                f"- cobaya_version: {cobaya.__version__}",
                f"- n_planck_modules: {len(found)}",
                f"- planckpr4lensing_importable: {pr4_info['importable']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Run bundle: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
