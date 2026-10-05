#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


CANONICAL_PATHS = {
    "toy_trunc_gauss": "runs/20260211_103448_toy_trunc_gauss/metrics.json",
    "cross_unprofiled_compare": "runs/20260211_154016_522463_spt_common_staging_compare/metrics.json",
    "cross_profiled_compare": "runs/20260211_181258_958327_spt_profiled_common_staging_compare/metrics.json",
    "mnu_shift_spt_only_desi": "runs/20260212_080120_648405_mnu_shift_spt_only_desi/metrics.json",
    "mnu_shift_cmb_plancksubset_desi": "runs/20260212_111357_576743_mnu_shift_cmb_plancksubset_desi/metrics.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize canonical run metrics into one JSON artifact.")
    parser.add_argument(
        "--output",
        default="docs/findings/canonical_results.json",
        help="Path to write the consolidated JSON summary.",
    )
    return parser.parse_args()


def _load_json(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        warnings.append(f"missing metrics file: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return None
    if not isinstance(data, dict):
        warnings.append(f"unexpected JSON root (not object): {path}")
        return None
    return data


def _subset_toy(data: dict[str, Any]) -> dict[str, Any]:
    ex = data.get("example_case", {}) if isinstance(data.get("example_case"), dict) else {}
    sweep = data.get("sweep", {}) if isinstance(data.get("sweep"), dict) else {}
    return {
        "example_case": {
            "mu_star": ex.get("mu_star"),
            "sigma_star": ex.get("sigma_star"),
            "mode": ex.get("mode"),
        },
        "sweep": {
            "boundary_mode_fraction_min": sweep.get("boundary_mode_fraction_min"),
            "boundary_mode_fraction_max": sweep.get("boundary_mode_fraction_max"),
            "boundary_mode_fraction_min_sigma2": sweep.get("boundary_mode_fraction_min_sigma2"),
            "boundary_mode_fraction_max_sigma2": sweep.get("boundary_mode_fraction_max_sigma2"),
            "n_mc": sweep.get("n_mc"),
        },
    }


def _subset_cross_compare(data: dict[str, Any], profiled: bool) -> dict[str, Any]:
    baseline = data.get("baseline", {}) if isinstance(data.get("baseline"), dict) else {}
    staging = data.get("staging", {}) if isinstance(data.get("staging"), dict) else {}
    reduction = data.get("reduction_pct", {}) if isinstance(data.get("reduction_pct"), dict) else {}

    if profiled:
        return {
            "mode": data.get("mode", "profiled"),
            "baseline": {
                "profiled_B_given_A": baseline.get("profiled_B_given_A"),
                "profiled_A_given_B": baseline.get("profiled_A_given_B"),
                "unprofiled_B_given_A": baseline.get("unprofiled_B_given_A"),
                "unprofiled_A_given_B": baseline.get("unprofiled_A_given_B"),
            },
            "staging": {
                "profiled_B_given_A": staging.get("profiled_B_given_A"),
                "profiled_A_given_B": staging.get("profiled_A_given_B"),
                "unprofiled_B_given_A": staging.get("unprofiled_B_given_A"),
                "unprofiled_A_given_B": staging.get("unprofiled_A_given_B"),
            },
            "reduction_pct": {
                "profiled_B_given_A": reduction.get("profiled_B_given_A"),
                "profiled_A_given_B": reduction.get("profiled_A_given_B"),
                "unprofiled_B_given_A": reduction.get("unprofiled_B_given_A"),
                "unprofiled_A_given_B": reduction.get("unprofiled_A_given_B"),
            },
        }

    base_d = baseline.get("delta_chi2", {}) if isinstance(baseline.get("delta_chi2"), dict) else {}
    stage_d = staging.get("delta_chi2", {}) if isinstance(staging.get("delta_chi2"), dict) else {}
    return {
        "baseline": {
            "B_given_A": base_d.get("B_given_A"),
            "A_given_B": base_d.get("A_given_B"),
        },
        "staging": {
            "B_given_A": stage_d.get("B_given_A"),
            "A_given_B": stage_d.get("A_given_B"),
        },
        "reduction_pct": {
            "B_given_A": reduction.get("B_given_A"),
            "A_given_B": reduction.get("A_given_B"),
        },
    }


def _subset_mnu(data: dict[str, Any]) -> dict[str, Any]:
    run2018 = data.get("run2018", {}) if isinstance(data.get("run2018"), dict) else {}
    run_d1 = data.get("runD1", {}) if isinstance(data.get("runD1"), dict) else {}
    shift = data.get("shift", {}) if isinstance(data.get("shift"), dict) else {}

    return {
        "run2018": {
            "mnu_median": run2018.get("mnu_median"),
            "mnu_p95_upper": run2018.get("mnu_p95_upper"),
            "mnu_mode": run2018.get("mnu_mode"),
            "boundary_fraction": run2018.get("boundary_fraction"),
            "n_samples_used": run2018.get("n_samples_used"),
            "mnu_split_rhat": run2018.get("mnu_split_rhat"),
            "mnu_p95_half_diff": run2018.get("mnu_p95_half_diff"),
            "mnu_ess": run2018.get("mnu_ess"),
            "diagnostic_method": run2018.get("diagnostic_method", "legacy_unverified"),
            "diagnostic_scope": run2018.get("diagnostic_scope", "legacy_unverified"),
            "warnings": run2018.get("warnings", ["Legacy posterior diagnostics have not been recomputed."]),
        },
        "runD1": {
            "mnu_median": run_d1.get("mnu_median"),
            "mnu_p95_upper": run_d1.get("mnu_p95_upper"),
            "mnu_mode": run_d1.get("mnu_mode"),
            "boundary_fraction": run_d1.get("boundary_fraction"),
            "n_samples_used": run_d1.get("n_samples_used"),
            "mnu_split_rhat": run_d1.get("mnu_split_rhat"),
            "mnu_p95_half_diff": run_d1.get("mnu_p95_half_diff"),
            "mnu_ess": run_d1.get("mnu_ess"),
            "diagnostic_method": run_d1.get("diagnostic_method", "legacy_unverified"),
            "diagnostic_scope": run_d1.get("diagnostic_scope", "legacy_unverified"),
            "warnings": run_d1.get("warnings", ["Legacy posterior diagnostics have not been recomputed."]),
        },
        "shift": {
            "delta_p95_upper": shift.get("delta_p95_upper"),
            "delta_median": shift.get("delta_median"),
        },
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    warnings: list[str] = []

    loaded: dict[str, dict[str, Any] | None] = {}
    for key, rel in CANONICAL_PATHS.items():
        loaded[key] = _load_json(repo_root / rel, warnings)

    summary: dict[str, Any] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {k: str(v) for k, v in CANONICAL_PATHS.items()},
        "toy_truncation": _subset_toy(loaded["toy_trunc_gauss"] or {}),
        "cross_audit": {
            "unprofiled_baseline_vs_staging": _subset_cross_compare(
                loaded["cross_unprofiled_compare"] or {}, profiled=False
            ),
            "profiled_baseline_vs_staging": _subset_cross_compare(
                loaded["cross_profiled_compare"] or {}, profiled=True
            ),
        },
        "mnu_shift": {
            "spt_only_plus_desi": _subset_mnu(loaded["mnu_shift_spt_only_desi"] or {}),
            "cmb_plancksubset_plus_desi": _subset_mnu(loaded["mnu_shift_cmb_plancksubset_desi"] or {}),
        },
        "warnings": warnings,
    }

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote: {out_path}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
