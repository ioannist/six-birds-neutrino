#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sbt_spt_audit.candl_support import (  # noqa: E402
    compute_residual_from_base,
    evaluate_loglike_from_base,
    get_bin_spec_types,
    get_required_params_and_defaults,
    instantiate_like_with_metadata,
    load_test_vector,
)


EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_PROFILE_FAILURE = 3

COSMO_SHARED_CANDIDATES = [
    "theta",
    "100theta_s",
    "omegabh2",
    "omegach2",
    "H0",
    "logA",
    "ns",
    "tau",
    "mnu",
    "sum_mnu",
    "As",
    "A_s",
    "n_s",
]
ELL_BIN_EDGES = [400.0, 750.0, 1000.0, 1500.0, 2000.0, 2500.0, 3000.0, 3500.0, 4000.0]
MAX_PROFILE_PARAMS = 12


@dataclass
class LensContext:
    run_name: str
    likelihood_id: str
    like_obj: Any
    defaults: dict[str, float]
    required_params: list[str]
    theta_hat: dict[str, float]
    base_params: dict[str, Any]


@dataclass
class ProfileResult:
    success: bool
    message: str
    nit: int
    nfev: int
    chi2: float
    loglike: float
    params: dict[str, float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profiled candl cross-audit.")
    parser.add_argument("--runA", required=True, type=str)
    parser.add_argument("--runB", required=True, type=str)
    parser.add_argument(
        "--profile_set",
        choices=["TT_cal_beta", "TT_cal", "TT_only", "all_nuisance"],
        default="TT_cal_beta",
    )
    parser.add_argument(
        "--shared_params",
        type=str,
        default=None,
        help="Optional comma-separated explicit shared params, e.g. TT_tSZ_Amp,TT_kSZ_Amp",
    )
    parser.add_argument("--maxiter", type=int, default=200)
    parser.add_argument("--outdir", type=str, default=None)
    return parser.parse_args()


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def _fail(msg: str, code: int) -> int:
    print(msg, file=sys.stderr)
    return code


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping.")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected object.")
    return data


def _load_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    cfg = _load_yaml(run_dir / "config.yaml")
    best = _load_json(run_dir / "bestfit.json")
    return cfg, best


def _extract_theta_hat(bestfit: dict[str, Any]) -> dict[str, float]:
    raw = bestfit.get("theta_hat")
    if not isinstance(raw, dict):
        raise ValueError("bestfit missing theta_hat mapping.")
    out: dict[str, float] = {}
    for k, v in raw.items():
        out[str(k)] = float(v)
    return out


def _make_lens_context(config: dict[str, Any], bestfit: dict[str, Any]) -> LensContext:
    run_name = config.get("run_name")
    if not isinstance(run_name, str) or not run_name.strip():
        raise ValueError("config missing run_name.")
    lens = config.get("lens")
    if not isinstance(lens, dict):
        raise ValueError("config missing lens mapping.")
    lens_type = lens.get("type")
    if lens_type not in {"candl", "candl_spt"}:
        raise TypeError(f"unsupported lens.type `{lens_type}`; expected candl.")

    likelihood_id = (
        lens.get("likelihood_id")
        or lens.get("shortcut")
        or lens.get("dataset_id")
        or lens.get("dataset_expr")
    )
    if not isinstance(likelihood_id, str) or not likelihood_id.strip():
        raise ValueError("lens requires likelihood_id.")
    likelihood_id = likelihood_id.strip()

    test_yaml = lens.get("test_yaml")
    if test_yaml is not None and not isinstance(test_yaml, str):
        raise ValueError("lens.test_yaml must be string if provided.")
    test_vector = load_test_vector(likelihood_id, test_yaml_override=test_yaml)

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

    like_obj, _ = instantiate_like_with_metadata(
        dataset_path=test_vector.dataset_path,
        lensing=lensing,
        ell_cuts=ell_cuts,
    )
    required, defaults = get_required_params_and_defaults(like_obj)
    theta_hat = _extract_theta_hat(bestfit)
    return LensContext(
        run_name=run_name,
        likelihood_id=likelihood_id,
        like_obj=like_obj,
        defaults=defaults,
        required_params=required,
        theta_hat=theta_hat,
        base_params=test_vector.base_params,
    )


def _shared_keys(ctx_a: LensContext, ctx_b: LensContext) -> list[str]:
    return sorted(
        set(ctx_a.required_params)
        .intersection(ctx_b.required_params)
        .intersection(COSMO_SHARED_CANDIDATES)
    )


def _parse_explicit_shared(shared_params_raw: str | None) -> list[str] | None:
    if shared_params_raw is None:
        return None
    items = [s.strip() for s in shared_params_raw.split(",")]
    items = [s for s in items if s]
    if not items:
        return None
    dedup: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            dedup.append(item)
            seen.add(item)
    return dedup


def _shared_values_for_direction(
    shared_keys: list[str],
    source_theta: dict[str, float],
    test_defaults: dict[str, float],
) -> dict[str, float]:
    out: dict[str, float] = {}
    for key in shared_keys:
        if key in source_theta:
            out[key] = float(source_theta[key])
        else:
            out[key] = float(test_defaults[key])
    return out


def _bound_for_param(name: str) -> tuple[float | None, float | None]:
    low_name = name.lower()
    if "corr" in low_name:
        return (-1.0, 1.0)
    if "tcal" in low_name or "ecal" in low_name:
        return (0.5, 1.5)
    if re.fullmatch(r"beta_[0-9]+", name):
        return (-5.0, 5.0)
    if any(tok in name for tok in ["Amp", "Poisson", "CIB", "tSZ", "kSZ"]):
        return (0.0, 50.0)
    return (None, None)


def _select_profile_params(
    required_params: list[str],
    shared_keys: list[str],
    profile_set: str,
    warnings: list[str],
) -> tuple[list[str], str]:
    nuisance = [p for p in required_params if p not in shared_keys]

    def select(mode: str) -> list[str]:
        if mode == "all_nuisance":
            return list(nuisance)
        if mode == "TT_only":
            return [p for p in nuisance if p.startswith("TT_")]
        if mode == "TT_cal":
            return [p for p in nuisance if p.startswith("TT_") or ("Tcal" in p) or ("Ecal" in p)]
        if mode == "TT_cal_beta":
            return [
                p
                for p in nuisance
                if p.startswith("TT_")
                or ("Tcal" in p)
                or ("Ecal" in p)
                or re.fullmatch(r"beta_[0-9]+", p)
            ]
        raise ValueError(f"unknown profile_set `{mode}`")

    selected = select(profile_set)
    used = profile_set
    if len(selected) > 30:
        warnings.append(
            f"profile set `{profile_set}` produced {len(selected)} params; downshifting to TT_cal_beta."
        )
        selected = select("TT_cal_beta")
        used = "TT_cal_beta"
    if len(selected) > 30:
        warnings.append(
            f"TT_cal_beta still produced {len(selected)} params; truncating to first 30 for stability."
        )
        selected = sorted(selected)[:30]

    # Additional pragmatic cap to keep finite-difference profiling tractable.
    # Prioritize well-known dominant TT/cali nuisance knobs before truncation.
    priority_exact = [
        "TT_tSZ_Amp",
        "TT_kSZ_Amp",
        "TT_tSZ_CIB_Corr_Amp",
        "TT_tSZ_CIB_corr",
        "Tcal_ext150",
        "Tcal_rel90",
        "Tcal_rel220",
        "Ecal_ext150",
        "Ecal_rel90",
        "Ecal_rel220",
    ]
    ordered: list[str] = []
    seen: set[str] = set()
    for name in priority_exact:
        if name in selected and name not in seen:
            ordered.append(name)
            seen.add(name)
    for name in selected:
        if name not in seen:
            ordered.append(name)
            seen.add(name)

    if len(ordered) > MAX_PROFILE_PARAMS:
        warnings.append(
            f"profile set `{used}` reduced from {len(ordered)} to {MAX_PROFILE_PARAMS} params "
            "for finite-difference runtime tractability."
        )
        ordered = ordered[:MAX_PROFILE_PARAMS]

    return ordered, used


def _clamp_zero(x: float | None, eps: float = 1e-12) -> float | None:
    if x is None:
        return None
    xv = float(x)
    if abs(xv) < eps:
        return 0.0
    return xv


def _evaluate_unprofiled_loglike(
    test_ctx: LensContext,
    source_theta: dict[str, float],
) -> tuple[float, dict[str, float]]:
    params = dict(test_ctx.defaults)
    for key, value in source_theta.items():
        if key in params:
            params[key] = float(value)
    logl = evaluate_loglike_from_base(
        like_obj=test_ctx.like_obj,
        base_params=test_ctx.base_params,
        overrides=params,
    )
    return float(logl), params


def _profile_test_lens(
    test_ctx: LensContext,
    shared_values: dict[str, float],
    profile_params: list[str],
    maxiter: int,
) -> ProfileResult:
    params = dict(test_ctx.defaults)
    for k, v in test_ctx.theta_hat.items():
        if k in params:
            params[k] = float(v)
    for k, v in shared_values.items():
        if k in params:
            params[k] = float(v)

    if not profile_params:
        logl = evaluate_loglike_from_base(
            like_obj=test_ctx.like_obj,
            base_params=test_ctx.base_params,
            overrides=params,
        )
        chi2 = float(-2.0 * logl)
        return ProfileResult(
            success=True,
            message="no profiled nuisance parameters",
            nit=0,
            nfev=1,
            chi2=chi2,
            loglike=float(logl),
            params=params,
        )

    x0 = np.array([params[p] for p in profile_params], dtype=float)
    bounds = [_bound_for_param(p) for p in profile_params]

    def objective(x: np.ndarray) -> float:
        overrides = dict(params)
        for p, val in zip(profile_params, x):
            overrides[p] = float(val)
        logl = evaluate_loglike_from_base(
            like_obj=test_ctx.like_obj,
            base_params=test_ctx.base_params,
            overrides=overrides,
        )
        return float(-2.0 * logl)

    res = minimize(
        objective,
        x0,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": int(maxiter), "ftol": 1e-6, "gtol": 1e-6},
    )

    best_params = dict(params)
    for p, val in zip(profile_params, np.asarray(res.x, dtype=float)):
        best_params[p] = float(val)
    chi2 = float(res.fun)
    logl = float(-0.5 * chi2)
    return ProfileResult(
        success=bool(res.success),
        message=str(res.message),
        nit=int(getattr(res, "nit", 0)) if hasattr(res, "nit") else 0,
        nfev=int(getattr(res, "nfev", 0)) if hasattr(res, "nfev") else 0,
        chi2=chi2,
        loglike=logl,
        params=best_params,
    )


def _safe_q(cov: np.ndarray, residual: np.ndarray) -> float:
    try:
        sol = np.linalg.solve(cov, residual)
    except np.linalg.LinAlgError:
        sol = np.linalg.pinv(cov) @ residual
    return float(residual @ sol)


def _localize_profiled_direction(
    test_ctx: LensContext,
    params_train_profiled: dict[str, float],
    params_best_profiled: dict[str, float],
) -> tuple[dict[str, list[float]], list[dict[str, Any]], list[str]]:
    like = test_ctx.like_obj
    spec_by_bin = get_bin_spec_types(like)
    eff_ells = np.asarray(getattr(like, "effective_ells"), dtype=float)
    cov = np.asarray(getattr(like, "covariance"), dtype=float)

    r_train = compute_residual_from_base(
        like_obj=like,
        base_params=test_ctx.base_params,
        overrides=params_train_profiled,
    )
    r_best = compute_residual_from_base(
        like_obj=like,
        base_params=test_ctx.base_params,
        overrides=params_best_profiled,
    )

    spectra_present = [s for s in ["TT", "TE", "EE"] if np.any(spec_by_bin == s)]
    delta_by_spec_ell: dict[str, list[float]] = {}
    groups: list[dict[str, Any]] = []
    for spec in spectra_present:
        spec_mask = spec_by_bin == spec
        vals: list[float] = []
        for i in range(len(ELL_BIN_EDGES) - 1):
            lo = ELL_BIN_EDGES[i]
            hi = ELL_BIN_EDGES[i + 1]
            idx = np.where(spec_mask & (eff_ells >= lo) & (eff_ells < hi))[0]
            if idx.size == 0:
                vals.append(0.0)
                continue
            cov_g = cov[np.ix_(idx, idx)]
            q_train = _safe_q(cov_g, r_train[idx])
            q_best = _safe_q(cov_g, r_best[idx])
            dq = float(q_train - q_best)
            vals.append(dq)
            groups.append(
                {
                    "spec": spec,
                    "ell": [int(lo), int(hi)],
                    "deltaQ": dq,
                    "n_bins": int(idx.size),
                }
            )
        delta_by_spec_ell[spec] = vals
    groups.sort(key=lambda x: x["deltaQ"], reverse=True)
    return delta_by_spec_ell, groups[:10], spectra_present


def _plot_profiled_delta_bars(
    outpath: Path,
    un_ba: float,
    pr_ba: float,
    un_ab: float,
    pr_ab: float,
) -> None:
    labels = ["B|A", "A|B"]
    x = np.arange(2)
    width = 0.34
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, [un_ba, un_ab], width, label="unprofiled")
    ax.bar(x + width / 2, [pr_ba, pr_ab], width, label="profiled")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Δχ²")
    ax.set_title("Profiled vs Unprofiled Cross-Audit Δχ²")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def _plot_heatmap(
    outpath: Path,
    delta_by_spec_ell: dict[str, list[float]],
    spectra: list[str],
    title: str,
) -> None:
    if not spectra:
        return
    mat = np.asarray([delta_by_spec_ell.get(s, []) for s in spectra], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 3 + 0.7 * len(spectra)))
    im = ax.imshow(mat, aspect="auto", interpolation="nearest")
    ax.set_yticks(np.arange(len(spectra)))
    ax.set_yticklabels(spectra)
    xlabels = [f"[{int(ELL_BIN_EDGES[i])},{int(ELL_BIN_EDGES[i+1])})" for i in range(len(ELL_BIN_EDGES) - 1)]
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


def _write_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _diag_payload(result: ProfileResult) -> dict[str, Any]:
    return {
        "success": bool(result.success),
        "message": result.message,
        "nit": int(result.nit),
        "nfev": int(result.nfev),
        "chi2": float(result.chi2),
        "loglike": float(result.loglike),
    }


def main() -> int:
    args = parse_args()
    run_a = Path(args.runA).resolve()
    run_b = Path(args.runB).resolve()
    if not run_a.exists() or not run_a.is_dir():
        return _fail(f"invalid --runA: {run_a}", EXIT_INPUT_ERROR)
    if not run_b.exists() or not run_b.is_dir():
        return _fail(f"invalid --runB: {run_b}", EXIT_INPUT_ERROR)

    outdir = (
        Path(args.outdir).resolve()
        if args.outdir
        else REPO_ROOT / "runs" / f"{_stamp()}_cross_audit_profiled_spt2018_vs_sptd1"
    )
    outdir.mkdir(parents=True, exist_ok=False)
    figures_dir = outdir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    _write_env(outdir)

    warnings: list[str] = []
    direction_errors: dict[str, str] = {}

    try:
        cfg_a, best_a = _load_run(run_a)
        cfg_b, best_b = _load_run(run_b)
        ctx_a = _make_lens_context(cfg_a, best_a)
        ctx_b = _make_lens_context(cfg_b, best_b)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"input parsing/setup failed: {exc}", EXIT_INPUT_ERROR)

    shared_keys = _shared_keys(ctx_a, ctx_b)
    explicit_shared = _parse_explicit_shared(args.shared_params)
    if explicit_shared is not None:
        shared_keys = explicit_shared

    # B|A: train=A, test=B
    try:
        shared_keys_b = [k for k in shared_keys if k in ctx_b.required_params]
        shared_from_a_for_b = _shared_values_for_direction(shared_keys_b, ctx_a.theta_hat, ctx_b.defaults)
        shared_from_b_for_b = _shared_values_for_direction(shared_keys_b, ctx_b.theta_hat, ctx_b.defaults)
        profile_params_b, used_set_b = _select_profile_params(
            ctx_b.required_params,
            shared_keys_b,
            args.profile_set,
            warnings,
        )
        logl_b_at_a, params_unprofiled_b_at_a = _evaluate_unprofiled_loglike(ctx_b, ctx_a.theta_hat)
        prof_b_at_a = _profile_test_lens(ctx_b, shared_from_a_for_b, profile_params_b, args.maxiter)
        prof_b_best = _profile_test_lens(ctx_b, shared_from_b_for_b, profile_params_b, args.maxiter)
        delta_un_ba = _clamp_zero(float(-2.0 * (logl_b_at_a - prof_b_best.loglike)))
        delta_pr_ba = _clamp_zero(float(-2.0 * (prof_b_at_a.loglike - prof_b_best.loglike)))
        assert delta_un_ba is not None and delta_pr_ba is not None
        if delta_pr_ba > delta_un_ba + 1e-8:
            warnings.append(
                f"B|A profiled delta exceeded unprofiled ({delta_pr_ba} > {delta_un_ba})."
            )
        red_ba = None if delta_un_ba <= 0 else _clamp_zero(100.0 * (delta_un_ba - delta_pr_ba) / delta_un_ba)
        b_delta_grid, b_top_groups, b_specs = _localize_profiled_direction(
            ctx_b,
            params_train_profiled=prof_b_at_a.params,
            params_best_profiled=prof_b_best.params,
        )
    except Exception as exc:  # noqa: BLE001
        direction_errors["B_given_A"] = f"{type(exc).__name__}: {exc}"
        logl_b_at_a = None
        prof_b_at_a = None
        prof_b_best = None
        delta_un_ba = None
        delta_pr_ba = None
        red_ba = None
        profile_params_b = []
        used_set_b = args.profile_set
        b_delta_grid = {}
        b_top_groups = []
        b_specs = []
        shared_keys_b = []

    # A|B: train=B, test=A
    try:
        shared_keys_a = [k for k in shared_keys if k in ctx_a.required_params]
        shared_from_b_for_a = _shared_values_for_direction(shared_keys_a, ctx_b.theta_hat, ctx_a.defaults)
        shared_from_a_for_a = _shared_values_for_direction(shared_keys_a, ctx_a.theta_hat, ctx_a.defaults)
        profile_params_a, used_set_a = _select_profile_params(
            ctx_a.required_params,
            shared_keys_a,
            args.profile_set,
            warnings,
        )
        logl_a_at_b, params_unprofiled_a_at_b = _evaluate_unprofiled_loglike(ctx_a, ctx_b.theta_hat)
        prof_a_at_b = _profile_test_lens(ctx_a, shared_from_b_for_a, profile_params_a, args.maxiter)
        prof_a_best = _profile_test_lens(ctx_a, shared_from_a_for_a, profile_params_a, args.maxiter)
        delta_un_ab = _clamp_zero(float(-2.0 * (logl_a_at_b - prof_a_best.loglike)))
        delta_pr_ab = _clamp_zero(float(-2.0 * (prof_a_at_b.loglike - prof_a_best.loglike)))
        assert delta_un_ab is not None and delta_pr_ab is not None
        if delta_pr_ab > delta_un_ab + 1e-8:
            warnings.append(
                f"A|B profiled delta exceeded unprofiled ({delta_pr_ab} > {delta_un_ab})."
            )
        red_ab = None if delta_un_ab <= 0 else _clamp_zero(100.0 * (delta_un_ab - delta_pr_ab) / delta_un_ab)
        a_delta_grid, a_top_groups, a_specs = _localize_profiled_direction(
            ctx_a,
            params_train_profiled=prof_a_at_b.params,
            params_best_profiled=prof_a_best.params,
        )
    except Exception as exc:  # noqa: BLE001
        direction_errors["A_given_B"] = f"{type(exc).__name__}: {exc}"
        logl_a_at_b = None
        prof_a_at_b = None
        prof_a_best = None
        delta_un_ab = None
        delta_pr_ab = None
        red_ab = None
        profile_params_a = []
        used_set_a = args.profile_set
        a_delta_grid = {}
        a_top_groups = []
        a_specs = []
        shared_keys_a = []

    spectra_present = [s for s in ["TT", "TE", "EE"] if s in set(b_specs) | set(a_specs)]

    # Figures
    if all(v is not None for v in [delta_un_ba, delta_pr_ba, delta_un_ab, delta_pr_ab]):
        _plot_profiled_delta_bars(
            figures_dir / "profiled_delta_chi2_bars.png",
            float(delta_un_ba),
            float(delta_pr_ba),
            float(delta_un_ab),
            float(delta_pr_ab),
        )
    if b_delta_grid:
        _plot_heatmap(
            figures_dir / "profiled_localization_heatmap_B_given_A.png",
            b_delta_grid,
            spectra_present,
            "Profiled localization ΔQ (B|A)",
        )
    if a_delta_grid:
        _plot_heatmap(
            figures_dir / "profiled_localization_heatmap_A_given_B.png",
            a_delta_grid,
            spectra_present,
            "Profiled localization ΔQ (A|B)",
        )

    metrics: dict[str, Any] = {
        "shared_param_keys": shared_keys,
        "shared_param_keys_explicit": explicit_shared,
        "profile_set_requested": args.profile_set,
        "profile_set_used": {"B_given_A": used_set_b, "A_given_B": used_set_a},
        "B_given_A": {
            "shared_keys_test_lens": shared_keys_b,
            "shared_values_from_A": shared_from_a_for_b if "B_given_A" not in direction_errors else None,
            "shared_values_from_B": shared_from_b_for_b if "B_given_A" not in direction_errors else None,
            "profile_params": profile_params_b,
            "n_profile_params": len(profile_params_b),
            "logL_at_train_unprofiled": logl_b_at_a,
            "logL_profiled_at_train_shared": None if prof_b_at_a is None else prof_b_at_a.loglike,
            "logL_profiled_best": None if prof_b_best is None else prof_b_best.loglike,
            "delta_chi2_unprofiled": delta_un_ba,
            "delta_chi2_profiled": delta_pr_ba,
            "reduction_pct": red_ba,
            "profiling_train_diag": None if prof_b_at_a is None else _diag_payload(prof_b_at_a),
            "profiling_best_diag": None if prof_b_best is None else _diag_payload(prof_b_best),
        },
        "A_given_B": {
            "shared_keys_test_lens": shared_keys_a,
            "shared_values_from_B": shared_from_b_for_a if "A_given_B" not in direction_errors else None,
            "shared_values_from_A": shared_from_a_for_a if "A_given_B" not in direction_errors else None,
            "profile_params": profile_params_a,
            "n_profile_params": len(profile_params_a),
            "logL_at_train_unprofiled": logl_a_at_b,
            "logL_profiled_at_train_shared": None if prof_a_at_b is None else prof_a_at_b.loglike,
            "logL_profiled_best": None if prof_a_best is None else prof_a_best.loglike,
            "delta_chi2_unprofiled": delta_un_ab,
            "delta_chi2_profiled": delta_pr_ab,
            "reduction_pct": red_ab,
            "profiling_train_diag": None if prof_a_at_b is None else _diag_payload(prof_a_at_b),
            "profiling_best_diag": None if prof_a_best is None else _diag_payload(prof_a_best),
        },
        "localization": {
            "ell_bin_edges": ELL_BIN_EDGES,
            "spectra_present": spectra_present,
            "B_given_A": {
                "deltaQ_by_spec_ell": b_delta_grid,
                "top_groups": b_top_groups,
            },
            "A_given_B": {
                "deltaQ_by_spec_ell": a_delta_grid,
                "top_groups": a_top_groups,
            },
        },
        "warnings": warnings,
        "errors": direction_errors,
    }
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    inputs = {
        "runA": str(run_a),
        "runB": str(run_b),
        "profile_set": args.profile_set,
        "shared_params": explicit_shared,
        "maxiter": args.maxiter,
    }
    (outdir / "inputs.yaml").write_text(yaml.safe_dump(inputs, sort_keys=False), encoding="utf-8")

    summary_lines = [
        "# Profiled Cross-Audit Summary",
        "",
        f"- runA: `{run_a}`",
        f"- runB: `{run_b}`",
        f"- profile_set_requested: `{args.profile_set}`",
        f"- shared_param_keys_explicit: `{explicit_shared}`",
        f"- profile_set_used_B|A: `{used_set_b}`",
        f"- profile_set_used_A|B: `{used_set_a}`",
        f"- Δχ²_unprofiled_B|A: `{delta_un_ba}`",
        f"- Δχ²_profiled_B|A: `{delta_pr_ba}`",
        f"- Δχ²_unprofiled_A|B: `{delta_un_ab}`",
        f"- Δχ²_profiled_A|B: `{delta_pr_ab}`",
        f"- reduction_pct_B|A: `{red_ba}`",
        f"- reduction_pct_A|B: `{red_ab}`",
        f"- warnings: `{warnings}`",
        f"- errors: `{direction_errors}`",
    ]
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    catastrophic = len(direction_errors) == 2
    print(f"Run bundle: {outdir}")
    print(f"B|A: unprofiled={delta_un_ba}, profiled={delta_pr_ba}, reduction_pct={red_ba}")
    print(f"A|B: unprofiled={delta_un_ab}, profiled={delta_pr_ab}, reduction_pct={red_ab}")
    if catastrophic:
        return EXIT_PROFILE_FAILURE
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
