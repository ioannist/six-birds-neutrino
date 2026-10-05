#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml
from extract_mnu_limits import _resolve_prefix_from_run_dir, _require_untempered_metadata, _load_chains_raw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare mnu posteriors between two Cobaya run bundles.")
    parser.add_argument("--run2018", required=True, type=str)
    parser.add_argument("--runD1", required=True, type=str)
    parser.add_argument("--outdir", default=None, type=str)
    parser.add_argument("--title", default="CMB baseline + DESI DR2: mnu posterior overlay", type=str)
    parser.add_argument("--outdir_name", default="mnu_shift_spt_only_desi", type=str)
    parser.add_argument("--label2018", default="SPT2018", type=str)
    parser.add_argument("--labelD1", default="SPT D1", type=str)
    return parser.parse_args()


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def _resolve_prefix(run_dir: Path) -> Path:
    prefix = _resolve_prefix_from_run_dir(run_dir)
    _require_untempered_metadata(prefix, run_dir)
    return prefix


def _load_metrics(run_dir: Path) -> dict[str, Any]:
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing metrics.json in {run_dir}")
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{metrics_path}: expected JSON object")
    return data


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _load_density(prefix: Path, burnin_frac: float):
    from getdist.mcsamples import loadMCSamples

    # GetDist can silently select another column when names are duplicated or
    # disagree with the chain header. Use the extractor's coordinate contract
    # before interpreting its smoothed curve as the mass density.
    _load_chains_raw(prefix, "mnu", burnin_frac)
    samples = loadMCSamples(str(prefix), settings={"ignore_rows": burnin_frac})
    density = samples.get1DDensityGridData("mnu")
    if density is None:
        raise RuntimeError(f"Could not compute mnu density for {prefix}")
    return density


def _plot_overlay(
    outpath: Path,
    label_2018: str,
    label_d1: str,
    density_2018: Any,
    density_d1: Any,
    title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(density_2018.x, density_2018.P, label=label_2018)
    ax.plot(density_d1.x, density_d1.P, label=label_d1)
    ax.set_xlabel("mnu [eV]")
    ax.set_ylabel("Empirical density (arb. norm)")
    ax.set_title(title)
    fig.text(0.5, 0.01, "Empirical chain densities; convergence and quantile precision are not verified by this plot.",
             ha="center", fontsize=8)
    ax.legend(loc="best")
    ax.grid(alpha=0.25)
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def _fmt_num(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.6f}"
    return str(value)


def _plot_bounds_table(
    outpath: Path,
    row_2018: dict[str, Any],
    row_d1: dict[str, Any],
    label_2018: str,
    label_d1: str,
) -> None:
    headers = ["run", "median", "p95_upper", "mode", "boundary_fraction"]
    rows = [
        [
            label_2018,
            _fmt_num(row_2018.get("mnu_median")),
            _fmt_num(row_2018.get("mnu_p95_upper")),
            _fmt_num(row_2018.get("mnu_mode")),
            _fmt_num(row_2018.get("boundary_fraction")),
        ],
        [
            label_d1,
            _fmt_num(row_d1.get("mnu_median")),
            _fmt_num(row_d1.get("mnu_p95_upper")),
            _fmt_num(row_d1.get("mnu_mode")),
            _fmt_num(row_d1.get("boundary_fraction")),
        ],
    ]

    fig, ax = plt.subplots(figsize=(11, 2.5))
    ax.axis("off")
    ax.set_title("Empirical chain summaries; posterior bounds require separate convergence and precision checks.",
                 fontsize=10)
    tbl = ax.table(cellText=rows, colLabels=headers, cellLoc="center", loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.4)
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    run2018 = Path(args.run2018).expanduser().resolve()
    run_d1 = Path(args.runD1).expanduser().resolve()

    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else repo_root / "runs" / f"{_stamp()}_{args.outdir_name}"
    )
    outdir.mkdir(parents=True, exist_ok=False)
    figures_dir = outdir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    inputs = {
        "run2018": str(run2018),
        "runD1": str(run_d1),
        "title": args.title,
        "label2018": args.label2018,
        "labelD1": args.labelD1,
    }
    (outdir / "inputs.yaml").write_text(yaml.safe_dump(inputs, sort_keys=False), encoding="utf-8")

    metrics_2018 = _load_metrics(run2018)
    metrics_d1 = _load_metrics(run_d1)

    burnin_2018 = float(metrics_2018.get("burnin_frac", 0.2))
    burnin_d1 = float(metrics_d1.get("burnin_frac", 0.2))

    prefix_2018 = _resolve_prefix(run2018)
    prefix_d1 = _resolve_prefix(run_d1)

    density_2018 = _load_density(prefix_2018, burnin_2018)
    density_d1 = _load_density(prefix_d1, burnin_d1)

    fig_path = figures_dir / "mnu_posterior_overlay.png"
    _plot_overlay(
        outpath=fig_path,
        label_2018=args.label2018,
        label_d1=args.labelD1,
        density_2018=density_2018,
        density_d1=density_d1,
        title=args.title,
    )

    table_fig_path = figures_dir / "mnu_bounds_table.png"

    p95_2018 = _as_float(metrics_2018.get("mnu_p95_upper"))
    p95_d1 = _as_float(metrics_d1.get("mnu_p95_upper"))
    med_2018 = _as_float(metrics_2018.get("mnu_median"))
    med_d1 = _as_float(metrics_d1.get("mnu_median"))

    delta_p95 = None if (p95_2018 is None or p95_d1 is None) else float(p95_2018 - p95_d1)
    delta_median = None if (med_2018 is None or med_d1 is None) else float(med_2018 - med_d1)

    output_metrics: dict[str, Any] = {
        "scope": "empirical_chain_summary_comparison",
        "posterior_convergence_verified": False,
        "run2018": {
            "path": str(run2018),
            "chains_prefix": str(prefix_2018),
            "mnu_median": metrics_2018.get("mnu_median"),
            "mnu_p95_upper": metrics_2018.get("mnu_p95_upper"),
            "mnu_mode": metrics_2018.get("mnu_mode"),
            "boundary_fraction": metrics_2018.get("boundary_fraction"),
            "n_samples_used": metrics_2018.get("n_samples_used"),
            "mnu_split_rhat": metrics_2018.get("mnu_split_rhat"),
            "mnu_ess": metrics_2018.get("mnu_ess"),
            "mnu_p95_half_diff": metrics_2018.get("mnu_p95_half_diff"),
            "warnings": metrics_2018.get("warnings", []),
            "diagnostic_method": metrics_2018.get("diagnostic_method", "legacy_unverified"),
        },
        "runD1": {
            "path": str(run_d1),
            "chains_prefix": str(prefix_d1),
            "mnu_median": metrics_d1.get("mnu_median"),
            "mnu_p95_upper": metrics_d1.get("mnu_p95_upper"),
            "mnu_mode": metrics_d1.get("mnu_mode"),
            "boundary_fraction": metrics_d1.get("boundary_fraction"),
            "n_samples_used": metrics_d1.get("n_samples_used"),
            "mnu_split_rhat": metrics_d1.get("mnu_split_rhat"),
            "mnu_ess": metrics_d1.get("mnu_ess"),
            "mnu_p95_half_diff": metrics_d1.get("mnu_p95_half_diff"),
            "warnings": metrics_d1.get("warnings", []),
            "diagnostic_method": metrics_d1.get("diagnostic_method", "legacy_unverified"),
        },
        "shift": {
            "delta_p95_upper": delta_p95,
            "delta_median": delta_median,
        },
    }

    output_metrics["warnings"] = [
        f"{label}: {warning}"
        for label, m in [("SPT2018", metrics_2018), ("D1", metrics_d1)]
        for warning in m.get("warnings", [])
    ]
    if any("diagnostic_method" not in m for m in [metrics_2018, metrics_d1]):
        output_metrics["warnings"].append("Legacy chain diagnostics require re-extraction before interpreting convergence.")

    _plot_bounds_table(
        outpath=table_fig_path,
        row_2018=output_metrics["run2018"],
        row_d1=output_metrics["runD1"],
        label_2018=args.label2018,
        label_d1=args.labelD1,
    )

    (outdir / "metrics.json").write_text(json.dumps(output_metrics, indent=2), encoding="utf-8")

    summary_lines = [
        "Empirical chain summaries. This comparison does not establish posterior convergence or quantile precision.",
        "",
        f"- run2018: {run2018}",
        f"- runD1: {run_d1}",
        f"- delta_p95_upper: {delta_p95}",
        f"- delta_median: {delta_median}",
        f"- overlay_plot: {fig_path}",
        f"- table_plot: {table_fig_path}",
    ]
    if output_metrics["warnings"]:
        summary_lines.extend(["", "Warnings:", ""])
        summary_lines.extend(f"- {warning}" for warning in output_metrics["warnings"])
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Comparison bundle: {outdir}")
    print(f"Overlay plot: {fig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
