#!/usr/bin/env python3
from __future__ import annotations

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

from sbt_spt_audit.candl_support import (  # noqa: E402
    get_required_params_and_defaults,
    instantiate_like_with_metadata,
    load_test_vector,
)


TARGETS = {
    "spt2018": "candl_data.SPT3G_2018_TTTEEE_multifreq",
    "sptd1": "spt_candl_data.SPT3G_D1_TnE_multifreq",
}


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
    outdir = REPO_ROOT / "runs" / f"{_stamp()}_candl_param_inspect"
    outdir.mkdir(parents=True, exist_ok=False)
    logs: list[str] = []
    metrics: dict[str, Any] = {}

    def log(msg: str) -> None:
        print(msg)
        logs.append(msg)

    for label, likelihood_id in TARGETS.items():
        log(f"[{label}] likelihood_id={likelihood_id}")
        tv = load_test_vector(likelihood_id)
        like_obj, like_meta = instantiate_like_with_metadata(
            dataset_path=tv.dataset_path,
            lensing=tv.lensing,
            ell_cuts=None,
        )
        required, defaults = get_required_params_and_defaults(like_obj)
        missing = [p for p in required if p not in defaults]
        sorted_required = sorted(required)
        first20 = sorted_required[:20]
        covers_all = len(missing) == 0
        log(f"[{label}] n_required={len(required)}")
        log(f"[{label}] first20={first20}")
        log(f"[{label}] defaults_cover_all={covers_all}")
        log(f"[{label}] missing={missing}")

        metrics[label] = {
            "likelihood_id": likelihood_id,
            "dataset_yaml_used": like_meta.dataset_yaml_used,
            "n_required": len(required),
            "required_first20_sorted": first20,
            "defaults_cover_all": covers_all,
            "missing": missing,
            "n_defaults": len(defaults),
        }

    _write_env(outdir)
    (outdir / "stdout.txt").write_text("\n".join(logs) + "\n", encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (outdir / "summary.md").write_text(
        yaml.safe_dump(
            {
                "run_bundle": str(outdir),
                "targets": TARGETS,
                "status": "ok",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    print(f"Run bundle: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
