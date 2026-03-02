#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sbt_spt_audit.candl_support import (  # noqa: E402
    CandlLikeMetadata,
    CandlTestVector,
    compute_residual_from_base,
    evaluate_loglike_from_base,
    get_bin_spec_types,
    instantiate_like_with_metadata,
    load_test_vector,
)
from sbt_spt_audit.metrics import delta_chi2_from_loglike  # noqa: E402


EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_UNSUPPORTED_LENS = 3


@dataclass
class CandlLensRuntime:
    run_name: str
    likelihood_id: str
    test_vector: CandlTestVector
    like_obj: Any
    like_meta: CandlLikeMetadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run cross-lens held-out audit.")
    parser.add_argument("--runA", required=True, type=str, help="Path to run bundle A")
    parser.add_argument("--runB", required=True, type=str, help="Path to run bundle B")
    parser.add_argument("--outdir", type=str, default=None, help="Optional output run bundle path")
    parser.add_argument("--localize", dest="localize", action="store_true", default=None)
    parser.add_argument("--no-localize", dest="localize", action="store_false")
    return parser.parse_args()


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _fail(msg: str, code: int) -> int:
    print(msg, file=sys.stderr)
    return code


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level mapping.")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level object.")
    return data


def _validate_run_bundle(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config_path = run_dir / "config.yaml"
    bestfit_path = run_dir / "bestfit.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing {config_path}")
    if not bestfit_path.exists():
        raise FileNotFoundError(f"Missing {bestfit_path}")
    config = _load_yaml(config_path)
    bestfit = _load_json(bestfit_path)
    return config, bestfit


def _lens_type(config: dict[str, Any]) -> str:
    lens = config.get("lens")
    if not isinstance(lens, dict):
        raise ValueError("config missing `lens` mapping.")
    lens_type = lens.get("type")
    if lens_type == "gaussian":
        return "gaussian"
    if lens_type in {"candl", "candl_spt"}:
        return "candl"
    raise TypeError(f"unsupported lens.type `{lens_type}`.")


def _validate_gaussian_lens(config: dict[str, Any]) -> tuple[str, list[str], np.ndarray, np.ndarray]:
    run_name = config.get("run_name")
    if not isinstance(run_name, str) or not run_name.strip():
        raise ValueError("config missing non-empty `run_name`.")
    lens = config.get("lens")
    if not isinstance(lens, dict):
        raise ValueError("config missing `lens` mapping.")
    params = lens.get("params")
    mean = lens.get("mean")
    cov = lens.get("cov")
    if not isinstance(params, list) or not params or not all(isinstance(p, str) for p in params):
        raise ValueError("lens.params must be a non-empty list of strings.")
    if not isinstance(mean, list) or len(mean) != len(params):
        raise ValueError("lens.mean must match lens.params length.")
    if not isinstance(cov, list) or len(cov) != len(params):
        raise ValueError("lens.cov must be square with dimension len(params).")
    for row in cov:
        if not isinstance(row, list) or len(row) != len(params):
            raise ValueError("lens.cov rows must all have length len(params).")
    mu = np.asarray(mean, dtype=float)
    c = np.asarray(cov, dtype=float)
    return run_name, params, mu, c


def _validate_candl_lens(config: dict[str, Any]) -> CandlLensRuntime:
    run_name = config.get("run_name")
    if not isinstance(run_name, str) or not run_name.strip():
        raise ValueError("config missing non-empty `run_name`.")
    lens = config.get("lens")
    if not isinstance(lens, dict):
        raise ValueError("config missing `lens` mapping.")

    likelihood_id = (
        lens.get("likelihood_id")
        or lens.get("shortcut")
        or lens.get("dataset_id")
        or lens.get("dataset_expr")
    )
    if not isinstance(likelihood_id, str) or not likelihood_id.strip():
        raise ValueError("candl config requires `lens.likelihood_id` as module.attr string.")
    likelihood_id = likelihood_id.strip()

    test_yaml = lens.get("test_yaml")
    if test_yaml is not None and not isinstance(test_yaml, str):
        raise ValueError("lens.test_yaml must be a string path if provided.")

    test_vector = load_test_vector(
        dataset_expr=likelihood_id,
        test_yaml_override=test_yaml,
    )

    lensing_cfg = lens.get("lensing")
    if lensing_cfg is None:
        lensing = test_vector.lensing
    elif isinstance(lensing_cfg, bool):
        lensing = lensing_cfg
    else:
        raise ValueError("lens.lensing must be bool if provided.")

    ell_cuts = lens.get("ell_cuts")
    if ell_cuts is not None and not isinstance(ell_cuts, dict):
        raise ValueError("lens.ell_cuts must be mapping if provided.")

    like_obj, like_meta = instantiate_like_with_metadata(
        dataset_path=test_vector.dataset_path,
        lensing=lensing,
        ell_cuts=ell_cuts,
    )
    return CandlLensRuntime(
        run_name=run_name,
        likelihood_id=likelihood_id,
        test_vector=test_vector,
        like_obj=like_obj,
        like_meta=like_meta,
    )


def _theta_vector(bestfit: dict[str, Any], params: list[str]) -> np.ndarray:
    theta_hat = bestfit.get("theta_hat")
    if not isinstance(theta_hat, dict):
        raise ValueError("bestfit missing `theta_hat` mapping.")
    vals: list[float] = []
    for p in params:
        if p not in theta_hat:
            raise ValueError(f"theta_hat missing parameter `{p}`.")
        vals.append(float(theta_hat[p]))
    return np.asarray(vals, dtype=float)


def _theta_mapping(bestfit: dict[str, Any]) -> dict[str, float]:
    theta_hat = bestfit.get("theta_hat")
    if not isinstance(theta_hat, dict):
        raise ValueError("bestfit missing `theta_hat` mapping.")
    out: dict[str, float] = {}
    for k, v in theta_hat.items():
        out[str(k)] = float(v)
    return out


def _chi2(theta: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> float:
    delta = theta - mu
    solved = np.linalg.solve(cov, delta)
    return float(delta @ solved)


def _loglike_gaussian(theta: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> float:
    return -0.5 * _chi2(theta, mu, cov)


def _whitened_components(theta: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    chol = np.linalg.cholesky(cov)
    delta = theta - mu
    return np.linalg.solve(chol, delta)


def _blockwise_delta_gaussian(
    theta_train: np.ndarray,
    theta_test: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
) -> dict[str, float]:
    z_train = _whitened_components(theta_train, mu, cov)
    z_test = _whitened_components(theta_test, mu, cov)
    return {f"mode{i}": float(z_train[i] ** 2 - z_test[i] ** 2) for i in range(len(z_train))}


def _write_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _plot_blockwise(
    outpath: Path,
    blocks_b_given_a: dict[str, float],
    blocks_a_given_b: dict[str, float],
    total_b_given_a: float,
    total_a_given_b: float,
) -> None:
    labels = ["Δχ²_{B|A}", "Δχ²_{A|B}"]
    mode_names = sorted(set(blocks_b_given_a.keys()) | set(blocks_a_given_b.keys()))

    x = np.arange(2)
    pos_bottom = np.zeros(2)
    neg_bottom = np.zeros(2)

    fig, ax = plt.subplots(figsize=(8, 5))
    for mode in mode_names:
        vals = np.array(
            [
                blocks_b_given_a.get(mode, 0.0),
                blocks_a_given_b.get(mode, 0.0),
            ],
            dtype=float,
        )
        bottoms = np.where(vals >= 0.0, pos_bottom, neg_bottom)
        ax.bar(x, vals, bottom=bottoms, label=mode)
        pos_bottom = np.where(vals >= 0.0, pos_bottom + vals, pos_bottom)
        neg_bottom = np.where(vals < 0.0, neg_bottom + vals, neg_bottom)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Block contribution to Δχ²")
    ax.set_title(
        "Cross-audit block decomposition\n"
        f"Totals: B|A={total_b_given_a:.3f}, A|B={total_a_given_b:.3f}"
    )
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def _safe_quadratic_form(cov: np.ndarray, residual: np.ndarray) -> float:
    try:
        solved = np.linalg.solve(cov, residual)
    except np.linalg.LinAlgError:
        solved = np.linalg.pinv(cov) @ residual
    return float(residual @ solved)


def _format_ell_label(lo: float, hi: float) -> str:
    return f"[{int(lo)},{int(hi)})"


def _compute_candl_localization_direction(
    like_obj: Any,
    base_params: dict[str, Any],
    theta_train: dict[str, float],
    theta_test: dict[str, float],
    ell_bin_edges: list[float],
) -> tuple[dict[str, list[float]], list[dict[str, Any]], list[str]]:
    spec_by_bin = get_bin_spec_types(like_obj)
    eff_ells = np.asarray(getattr(like_obj, "effective_ells"), dtype=float)
    cov = np.asarray(getattr(like_obj, "covariance"), dtype=float)

    residual_train = compute_residual_from_base(
        like_obj=like_obj,
        base_params=base_params,
        overrides=theta_train,
    )
    residual_test = compute_residual_from_base(
        like_obj=like_obj,
        base_params=base_params,
        overrides=theta_test,
    )

    spectra_present = [s for s in ["TT", "TE", "EE"] if np.any(spec_by_bin == s)]
    delta_by_spec_ell: dict[str, list[float]] = {}
    ranked_groups: list[dict[str, Any]] = []
    for spec in spectra_present:
        values: list[float] = []
        spec_mask = spec_by_bin == spec
        for i in range(len(ell_bin_edges) - 1):
            lo = float(ell_bin_edges[i])
            hi = float(ell_bin_edges[i + 1])
            idx = np.where(spec_mask & (eff_ells >= lo) & (eff_ells < hi))[0]
            if idx.size == 0:
                values.append(0.0)
                continue
            cov_g = cov[np.ix_(idx, idx)]
            q_train = _safe_quadratic_form(cov_g, residual_train[idx])
            q_test = _safe_quadratic_form(cov_g, residual_test[idx])
            delta_q = float(q_train - q_test)
            values.append(delta_q)
            ranked_groups.append(
                {
                    "spec": spec,
                    "ell": [int(lo), int(hi)],
                    "deltaQ": delta_q,
                    "n_bins": int(idx.size),
                }
            )
        delta_by_spec_ell[spec] = values

    ranked_groups.sort(key=lambda item: item["deltaQ"], reverse=True)
    return delta_by_spec_ell, ranked_groups[:10], spectra_present


def _plot_localization_heatmap(
    outpath: Path,
    ell_bin_edges: list[float],
    spectra: list[str],
    delta_by_spec_ell: dict[str, list[float]],
    title: str,
) -> None:
    if not spectra:
        return
    matrix = np.asarray([delta_by_spec_ell.get(spec, []) for spec in spectra], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 3 + 0.6 * len(spectra)))
    im = ax.imshow(matrix, aspect="auto", interpolation="nearest")
    ax.set_yticks(np.arange(len(spectra)))
    ax.set_yticklabels(spectra)
    xlabels = [_format_ell_label(ell_bin_edges[i], ell_bin_edges[i + 1]) for i in range(len(ell_bin_edges) - 1)]
    ax.set_xticks(np.arange(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=45, ha="right")
    ax.set_xlabel("ell bin")
    ax.set_ylabel("spectrum")
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("ΔQ")
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def main() -> int:
    args = parse_args()

    run_a = Path(args.runA).resolve()
    run_b = Path(args.runB).resolve()
    if not run_a.exists() or not run_a.is_dir():
        return _fail(f"Invalid --runA path: {run_a}", EXIT_INPUT_ERROR)
    if not run_b.exists() or not run_b.is_dir():
        return _fail(f"Invalid --runB path: {run_b}", EXIT_INPUT_ERROR)

    try:
        cfg_a, bestfit_a = _validate_run_bundle(run_a)
        cfg_b, bestfit_b = _validate_run_bundle(run_b)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Input validation error: {exc}", EXIT_INPUT_ERROR)

    try:
        lens_type_a = _lens_type(cfg_a)
        lens_type_b = _lens_type(cfg_b)
    except TypeError as exc:
        return _fail(f"Unsupported lens type: {exc}", EXIT_UNSUPPORTED_LENS)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Lens validation error: {exc}", EXIT_INPUT_ERROR)

    if lens_type_a != lens_type_b:
        return _fail(
            f"Unsupported mixed lens types: runA={lens_type_a}, runB={lens_type_b}",
            EXIT_UNSUPPORTED_LENS,
        )

    do_localize = args.localize
    if do_localize is None:
        do_localize = lens_type_a == "candl"

    localization_payload: dict[str, Any] | None = None
    ell_bin_edges = [400.0, 750.0, 1000.0, 1500.0, 2000.0, 2500.0, 3000.0, 3500.0, 4000.0]
    spectra_present: list[str] = []

    try:
        if lens_type_a == "gaussian":
            run_name_a, params_a, mu_a, cov_a = _validate_gaussian_lens(cfg_a)
            run_name_b, params_b, mu_b, cov_b = _validate_gaussian_lens(cfg_b)
            if params_a != params_b:
                return _fail(
                    f"Parameter mismatch: runA params={params_a}, runB params={params_b}",
                    EXIT_INPUT_ERROR,
                )
            theta_a = _theta_vector(bestfit_a, params_a)
            theta_b = _theta_vector(bestfit_b, params_a)

            logl_b_at_a = _loglike_gaussian(theta_a, mu_b, cov_b)
            logl_b_at_b = _loglike_gaussian(theta_b, mu_b, cov_b)
            delta_b_given_a = float(delta_chi2_from_loglike(logl_b_at_a, logl_b_at_b))

            logl_a_at_b = _loglike_gaussian(theta_b, mu_a, cov_a)
            logl_a_at_a = _loglike_gaussian(theta_a, mu_a, cov_a)
            delta_a_given_b = float(delta_chi2_from_loglike(logl_a_at_b, logl_a_at_a))

            blocks_b_given_a = _blockwise_delta_gaussian(theta_a, theta_b, mu_b, cov_b)
            blocks_a_given_b = _blockwise_delta_gaussian(theta_b, theta_a, mu_a, cov_a)
        else:
            candl_a = _validate_candl_lens(cfg_a)
            candl_b = _validate_candl_lens(cfg_b)
            run_name_a = candl_a.run_name
            run_name_b = candl_b.run_name
            theta_a_map = _theta_mapping(bestfit_a)
            theta_b_map = _theta_mapping(bestfit_b)

            logl_b_at_a = evaluate_loglike_from_base(candl_b.like_obj, candl_b.test_vector.base_params, theta_a_map)
            logl_b_at_b = evaluate_loglike_from_base(candl_b.like_obj, candl_b.test_vector.base_params, theta_b_map)
            delta_b_given_a = float(delta_chi2_from_loglike(logl_b_at_a, logl_b_at_b))

            logl_a_at_b = evaluate_loglike_from_base(candl_a.like_obj, candl_a.test_vector.base_params, theta_b_map)
            logl_a_at_a = evaluate_loglike_from_base(candl_a.like_obj, candl_a.test_vector.base_params, theta_a_map)
            delta_a_given_b = float(delta_chi2_from_loglike(logl_a_at_b, logl_a_at_a))

            blocks_b_given_a = {"loglike_scalar": delta_b_given_a}
            blocks_a_given_b = {"loglike_scalar": delta_a_given_b}

            if do_localize:
                b_delta, b_top, b_specs = _compute_candl_localization_direction(
                    like_obj=candl_b.like_obj,
                    base_params=candl_b.test_vector.base_params,
                    theta_train=theta_a_map,
                    theta_test=theta_b_map,
                    ell_bin_edges=ell_bin_edges,
                )
                a_delta, a_top, a_specs = _compute_candl_localization_direction(
                    like_obj=candl_a.like_obj,
                    base_params=candl_a.test_vector.base_params,
                    theta_train=theta_b_map,
                    theta_test=theta_a_map,
                    ell_bin_edges=ell_bin_edges,
                )
                spectra_present = [s for s in ["TT", "TE", "EE"] if s in set(b_specs) | set(a_specs)]
                localization_payload = {
                    "ell_bin_edges": ell_bin_edges,
                    "spectra_present": spectra_present,
                    "B_given_A": {
                        "deltaQ_by_spec_ell": b_delta,
                        "top_groups": b_top,
                    },
                    "A_given_B": {
                        "deltaQ_by_spec_ell": a_delta,
                        "top_groups": a_top,
                    },
                }
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Metric computation error: {exc}", EXIT_INPUT_ERROR)

    sum_b_given_a = float(sum(blocks_b_given_a.values()))
    sum_a_given_b = float(sum(blocks_a_given_b.values()))
    if abs(sum_b_given_a - delta_b_given_a) > 1e-8:
        return _fail(
            "Blockwise decomposition mismatch for B|A: "
            f"sum={sum_b_given_a}, total={delta_b_given_a}",
            EXIT_INPUT_ERROR,
        )
    if abs(sum_a_given_b - delta_a_given_b) > 1e-8:
        return _fail(
            "Blockwise decomposition mismatch for A|B: "
            f"sum={sum_a_given_b}, total={delta_a_given_b}",
            EXIT_INPUT_ERROR,
        )

    outdir = (
        Path(args.outdir).resolve()
        if args.outdir
        else (
            REPO_ROOT
            / "runs"
            / f"{_stamp()}_cross_audit_{run_name_a}_vs_{run_name_b}"
        )
    )
    outdir.mkdir(parents=True, exist_ok=False)
    figures_dir = outdir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    _write_env(outdir)

    inputs_payload = {
        "runA": {"path": str(run_a), "run_name": run_name_a, "lens_type": lens_type_a},
        "runB": {"path": str(run_b), "run_name": run_name_b, "lens_type": lens_type_b},
        "localize": bool(do_localize),
    }
    (outdir / "inputs.yaml").write_text(
        yaml.safe_dump(inputs_payload, sort_keys=False),
        encoding="utf-8",
    )

    metrics_payload: dict[str, Any] = {
        "runA": {"path": str(run_a), "run_name": run_name_a},
        "runB": {"path": str(run_b), "run_name": run_name_b},
        "lens_type": lens_type_a,
        "delta_chi2": {
            "B_given_A": delta_b_given_a,
            "A_given_B": delta_a_given_b,
        },
        "blockwise": {
            "B_given_A": blocks_b_given_a,
            "A_given_B": blocks_a_given_b,
        },
    }
    if localization_payload is not None:
        metrics_payload["localization"] = localization_payload
    (outdir / "metrics.json").write_text(
        json.dumps(metrics_payload, indent=2),
        encoding="utf-8",
    )

    figure_path = figures_dir / "delta_chi2_blockwise_bars.png"
    _plot_blockwise(
        figure_path,
        blocks_b_given_a,
        blocks_a_given_b,
        delta_b_given_a,
        delta_a_given_b,
    )

    if localization_payload is not None:
        _plot_localization_heatmap(
            figures_dir / "localization_heatmap_B_given_A.png",
            ell_bin_edges=ell_bin_edges,
            spectra=spectra_present,
            delta_by_spec_ell=localization_payload["B_given_A"]["deltaQ_by_spec_ell"],
            title=f"Localization ΔQ (B|A): {run_name_b} test",
        )
        _plot_localization_heatmap(
            figures_dir / "localization_heatmap_A_given_B.png",
            ell_bin_edges=ell_bin_edges,
            spectra=spectra_present,
            delta_by_spec_ell=localization_payload["A_given_B"]["deltaQ_by_spec_ell"],
            title=f"Localization ΔQ (A|B): {run_name_a} test",
        )

    summary_lines = [
        "# Cross Audit Summary",
        "",
        f"- runA: `{run_name_a}` ({run_a})",
        f"- runB: `{run_name_b}` ({run_b})",
        f"- lens_type: `{lens_type_a}`",
        f"- localize: `{bool(do_localize)}`",
        f"- Δχ²_B|A: `{delta_b_given_a:.12g}`",
        f"- Δχ²_A|B: `{delta_a_given_b:.12g}`",
        f"- sum(blocks_B|A): `{sum_b_given_a:.12g}`",
        f"- sum(blocks_A|B): `{sum_a_given_b:.12g}`",
        f"- figure: `{figure_path}`",
    ]
    if localization_payload is not None:
        summary_lines.append(f"- localization_spectra: `{spectra_present}`")
        summary_lines.append(
            f"- localization_heatmap_B|A: `{figures_dir / 'localization_heatmap_B_given_A.png'}`"
        )
        summary_lines.append(
            f"- localization_heatmap_A|B: `{figures_dir / 'localization_heatmap_A_given_B.png'}`"
        )
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Run bundle: {outdir}")
    print(f"Δχ²_B|A={delta_b_given_a}")
    print(f"Δχ²_A|B={delta_a_given_b}")
    print(f"sum(blocks_B|A)={sum_b_given_a}")
    print(f"sum(blocks_A|B)={sum_a_given_b}")
    if localization_payload is not None:
        print("localization=enabled")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
