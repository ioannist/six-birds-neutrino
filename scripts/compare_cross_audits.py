#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_INPUT_ERROR = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare baseline vs common-staging cross-audit bundles.")
    parser.add_argument("--baseline", required=True, type=str, help="Path to baseline cross-audit run bundle")
    parser.add_argument("--staging", required=True, type=str, help="Path to staging cross-audit run bundle")
    parser.add_argument("--outdir", type=str, default=None, help="Optional output run bundle path")
    return parser.parse_args()


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return EXIT_INPUT_ERROR


def _load_metrics(run_dir: Path) -> dict[str, Any]:
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing {metrics_path}")
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{metrics_path}: top-level JSON must be object.")
    return data


def _extract_values(metrics: dict[str, Any], label: str) -> tuple[str, dict[str, float]]:
    # Legacy cross-audit schema
    delta = metrics.get("delta_chi2")
    if isinstance(delta, dict) and "B_given_A" in delta and "A_given_B" in delta:
        return "legacy", {
            "unprofiled_B_given_A": float(delta["B_given_A"]),
            "unprofiled_A_given_B": float(delta["A_given_B"]),
        }

    # Profiled cross-audit schema
    b = metrics.get("B_given_A")
    a = metrics.get("A_given_B")
    if isinstance(b, dict) and isinstance(a, dict):
        needed = [
            "delta_chi2_unprofiled",
            "delta_chi2_profiled",
        ]
        if all(k in b for k in needed) and all(k in a for k in needed):
            return "profiled", {
                "unprofiled_B_given_A": float(b["delta_chi2_unprofiled"]),
                "unprofiled_A_given_B": float(a["delta_chi2_unprofiled"]),
                "profiled_B_given_A": float(b["delta_chi2_profiled"]),
                "profiled_A_given_B": float(a["delta_chi2_profiled"]),
            }
    raise ValueError(f"{label}: unsupported metrics schema.")


def _reduction_pct(baseline: float, staging: float) -> float | None:
    if baseline <= 0:
        return None
    return 100.0 * (baseline - staging) / baseline


def _write_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _plot_compare_profiled(
    outpath: Path,
    baseline_pb: float,
    baseline_pa: float,
    staging_pb: float,
    staging_pa: float,
) -> None:
    labels = ["Δχ²_profiled_{B|A}", "Δχ²_profiled_{A|B}"]
    x = np.arange(2)
    width = 0.36
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, [baseline_pb, baseline_pa], width=width, label="baseline")
    ax.bar(x + width / 2, [staging_pb, staging_pa], width=width, label="staging")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Δχ² (profiled)")
    ax.set_title("Profiled baseline vs common-staging")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def _plot_compare_legacy(
    outpath: Path,
    baseline_ba: float,
    baseline_ab: float,
    staging_ba: float,
    staging_ab: float,
) -> None:
    labels = ["Δχ²_{B|A}", "Δχ²_{A|B}"]
    x = np.arange(2)
    width = 0.36
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, [baseline_ba, baseline_ab], width=width, label="baseline")
    ax.bar(x + width / 2, [staging_ba, staging_ab], width=width, label="staging")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Δχ²")
    ax.set_title("Baseline vs common-staging cross-audit")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    baseline_dir = Path(args.baseline).resolve()
    staging_dir = Path(args.staging).resolve()
    if not baseline_dir.exists():
        return _fail(f"Invalid --baseline path: {baseline_dir}")
    if not staging_dir.exists():
        return _fail(f"Invalid --staging path: {staging_dir}")

    try:
        baseline_metrics = _load_metrics(baseline_dir)
        staging_metrics = _load_metrics(staging_dir)
        mode_b, vals_b = _extract_values(baseline_metrics, "baseline")
        mode_s, vals_s = _extract_values(staging_metrics, "staging")
        if mode_b != mode_s:
            raise ValueError(f"baseline/staging schema mismatch: {mode_b} vs {mode_s}")
        mode = mode_b
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Input/parse error: {exc}")

    outdir = (
        Path(args.outdir).resolve()
        if args.outdir
        else REPO_ROOT / "runs" / f"{_stamp()}_common_staging_compare"
    )
    outdir.mkdir(parents=True, exist_ok=False)
    figures_dir = outdir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    _write_env(outdir)

    payload: dict[str, Any] = {
        "mode": mode,
        "baseline": {"path": str(baseline_dir)},
        "staging": {"path": str(staging_dir)},
        "reduction_pct": {},
    }

    if mode == "profiled":
        for key in [
            "unprofiled_B_given_A",
            "unprofiled_A_given_B",
            "profiled_B_given_A",
            "profiled_A_given_B",
        ]:
            payload["baseline"][key] = vals_b[key]
            payload["staging"][key] = vals_s[key]
            payload["reduction_pct"][key] = _reduction_pct(vals_b[key], vals_s[key])

        fig_path = figures_dir / "delta_chi2_profiled_baseline_vs_staging.png"
        _plot_compare_profiled(
            fig_path,
            vals_b["profiled_B_given_A"],
            vals_b["profiled_A_given_B"],
            vals_s["profiled_B_given_A"],
            vals_s["profiled_A_given_B"],
        )
    else:
        payload["baseline"]["delta_chi2"] = {
            "B_given_A": vals_b["unprofiled_B_given_A"],
            "A_given_B": vals_b["unprofiled_A_given_B"],
        }
        payload["staging"]["delta_chi2"] = {
            "B_given_A": vals_s["unprofiled_B_given_A"],
            "A_given_B": vals_s["unprofiled_A_given_B"],
        }
        payload["reduction_pct"] = {
            "B_given_A": _reduction_pct(vals_b["unprofiled_B_given_A"], vals_s["unprofiled_B_given_A"]),
            "A_given_B": _reduction_pct(vals_b["unprofiled_A_given_B"], vals_s["unprofiled_A_given_B"]),
        }
        fig_path = figures_dir / "delta_chi2_baseline_vs_staging.png"
        _plot_compare_legacy(
            fig_path,
            vals_b["unprofiled_B_given_A"],
            vals_b["unprofiled_A_given_B"],
            vals_s["unprofiled_B_given_A"],
            vals_s["unprofiled_A_given_B"],
        )

    (outdir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary_lines = [
        "# Common Staging Comparison",
        "",
        f"- mode: `{mode}`",
        f"- baseline: `{baseline_dir}`",
        f"- staging: `{staging_dir}`",
        f"- figure: `{fig_path}`",
    ]
    if mode == "profiled":
        summary_lines.extend(
            [
                f"- baseline profiled B|A: `{vals_b['profiled_B_given_A']}`",
                f"- staging profiled B|A: `{vals_s['profiled_B_given_A']}`",
                f"- baseline profiled A|B: `{vals_b['profiled_A_given_B']}`",
                f"- staging profiled A|B: `{vals_s['profiled_A_given_B']}`",
                f"- reduction profiled B|A: `{payload['reduction_pct']['profiled_B_given_A']}`",
                f"- reduction profiled A|B: `{payload['reduction_pct']['profiled_A_given_B']}`",
            ]
        )
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Run bundle: {outdir}")
    if mode == "profiled":
        print(
            "profiled baseline/staging B|A="
            f"{vals_b['profiled_B_given_A']}/{vals_s['profiled_B_given_A']}"
        )
        print(
            "profiled baseline/staging A|B="
            f"{vals_b['profiled_A_given_B']}/{vals_s['profiled_A_given_B']}"
        )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
