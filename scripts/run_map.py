#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
from scipy.optimize import minimize
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sbt_spt_audit.candl_support import (  # noqa: E402
    CandlLikeMetadata,
    CandlTestVector,
    evaluate_loglike_from_base,
    get_required_params_and_defaults,
    instantiate_like_with_metadata,
    load_test_vector,
)


EXIT_OK = 0
EXIT_CONFIG_ERROR = 2
EXIT_OPTIM_ERROR = 3


COSMO_LIKE_KEYS_NORMALIZED = {
    "omegab",
    "omegabh2",
    "omegacdm",
    "omegach2",
    "h0",
    "loga",
    "ln1010as",
    "as",
    "ns",
    "tau",
    "mnu",
    "summnu",
    "theta",
    "thetas",
    "100thetas",
}


@dataclass
class GaussianLens:
    params: list[str]
    mean: np.ndarray
    cov: np.ndarray


@dataclass
class CandlLens:
    likelihood_id: str
    test_vector: CandlTestVector
    like_obj: Any
    lensing: bool
    ell_cuts: dict[str, list[float]] | None
    like_meta: CandlLikeMetadata
    required_params: list[str]
    defaults: dict[str, float]


@dataclass
class CandlParamPlan:
    strategy: str
    theta_default: dict[str, float]
    theta_init: dict[str, float]
    free_params: list[str]
    bounds_map: dict[str, tuple[float | None, float | None]]
    n_params_total: int
    n_params_free: int
    n_params_fixed: int
    nuisance_free_list: list[str]
    cosmo_fixed_list: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic MAP run for configured lens.")
    parser.add_argument("--config", required=True, type=str)
    parser.add_argument("--outdir", default=None, type=str)
    parser.add_argument("--dry_run", action="store_true")
    return parser.parse_args()


def _error(msg: str) -> int:
    print(f"CONFIG ERROR: {msg}", file=sys.stderr)
    return EXIT_CONFIG_ERROR


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _normalize_key(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _is_cosmo_like(name: str) -> bool:
    return _normalize_key(name) in COSMO_LIKE_KEYS_NORMALIZED


def load_yaml_config(path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return None, f"Cannot read config: {exc}"

    try:
        cfg = yaml.safe_load(raw)
    except Exception as exc:  # noqa: BLE001
        return None, f"Invalid YAML: {exc}"
    if not isinstance(cfg, dict):
        return None, "Top-level config must be a mapping."
    return cfg, raw


def validate_gaussian_lens(lens: dict[str, Any]) -> tuple[GaussianLens | None, str | None]:
    params = lens.get("params")
    mean = lens.get("mean")
    cov = lens.get("cov")
    if not isinstance(params, list) or not params or not all(isinstance(p, str) for p in params):
        return None, "`lens.params` must be a non-empty list of strings."
    if not isinstance(mean, list) or len(mean) != len(params):
        return None, "`lens.mean` must be a list with same length as `lens.params`."
    if not isinstance(cov, list):
        return None, "`lens.cov` must be a square matrix list."
    if len(cov) != len(params):
        return None, "`lens.cov` row count must match `lens.params` length."
    for row in cov:
        if not isinstance(row, list) or len(row) != len(params):
            return None, "`lens.cov` must be square with dimension len(params)."

    try:
        mean_arr = np.asarray(mean, dtype=float)
        cov_arr = np.asarray(cov, dtype=float)
    except Exception as exc:  # noqa: BLE001
        return None, f"`lens.mean`/`lens.cov` must be numeric: {exc}"

    if np.linalg.det(cov_arr) == 0:
        return None, "`lens.cov` is singular; inversion/solve is not possible."

    return GaussianLens(params=params, mean=mean_arr, cov=cov_arr), None


def validate_candl_lens(lens: dict[str, Any]) -> tuple[CandlLens | None, str | None]:
    likelihood_id = (
        lens.get("likelihood_id")
        or lens.get("shortcut")
        or lens.get("dataset_id")
        or lens.get("dataset_expr")
    )
    if not isinstance(likelihood_id, str) or not likelihood_id.strip():
        return None, "candl lens requires `likelihood_id` (module.attr shortcut string)."
    likelihood_id = likelihood_id.strip()

    test_yaml_override = lens.get("test_yaml")
    if test_yaml_override is not None and not isinstance(test_yaml_override, str):
        return None, "`lens.test_yaml` must be a string path when provided."

    try:
        test_vector = load_test_vector(
            dataset_expr=likelihood_id,
            test_yaml_override=test_yaml_override,
        )
    except Exception as exc:  # noqa: BLE001
        return None, f"failed loading candl test vector for `{likelihood_id}`: {exc}"

    lensing_cfg = lens.get("lensing")
    if lensing_cfg is None:
        lensing = test_vector.lensing
    elif isinstance(lensing_cfg, bool):
        lensing = lensing_cfg
    else:
        return None, "`lens.lensing` must be bool when provided."

    ell_cuts_cfg = lens.get("ell_cuts")
    if ell_cuts_cfg is not None and not isinstance(ell_cuts_cfg, dict):
        return None, "`lens.ell_cuts` must be a mapping when provided."

    try:
        like_obj, like_meta = instantiate_like_with_metadata(
            dataset_path=test_vector.dataset_path,
            lensing=lensing,
            ell_cuts=ell_cuts_cfg,
        )
        required_params, defaults = get_required_params_and_defaults(like_obj)
    except Exception as exc:  # noqa: BLE001
        return None, f"failed candl setup for `{likelihood_id}`: {exc}"

    if not required_params:
        return None, f"no required parameters discovered for `{likelihood_id}`."
    missing = [p for p in required_params if p not in defaults]
    if missing:
        return None, f"defaults missing required params for `{likelihood_id}`: {missing}"

    return (
        CandlLens(
            likelihood_id=likelihood_id,
            test_vector=test_vector,
            like_obj=like_obj,
            lensing=lensing,
            ell_cuts=like_meta.ell_cuts,
            like_meta=like_meta,
            required_params=required_params,
            defaults=defaults,
        ),
        None,
    )


def validate_lens(cfg: dict[str, Any]) -> tuple[str | None, GaussianLens | CandlLens | None, str | None]:
    lens = cfg.get("lens")
    if not isinstance(lens, dict):
        return None, None, "Missing or invalid `lens` mapping."
    lens_type = lens.get("type")
    if lens_type == "gaussian":
        obj, err = validate_gaussian_lens(lens)
        return "gaussian", obj, err
    if lens_type in {"candl", "candl_spt"}:
        obj, err = validate_candl_lens(lens)
        return "candl", obj, err
    return None, None, f"Unsupported lens.type `{lens_type}`."


def validate_gaussian_parameters(cfg: dict[str, Any], param_order: list[str]) -> tuple[dict[str, Any] | None, str | None]:
    params = cfg.get("parameters")
    if not isinstance(params, dict):
        return None, "Missing or invalid `parameters` mapping."
    for p in param_order:
        if p not in params:
            return None, f"Missing parameter block for `{p}`."
        block = params[p]
        if not isinstance(block, dict):
            return None, f"`parameters.{p}` must be a mapping."
        if "initial" not in block:
            return None, f"`parameters.{p}.initial` is required."
        try:
            float(block["initial"])
        except Exception as exc:  # noqa: BLE001
            return None, f"`parameters.{p}.initial` must be numeric: {exc}"
        if "bounds" in block and block["bounds"] is not None:
            b = block["bounds"]
            if (
                not isinstance(b, list)
                or len(b) != 2
                or (b[0] is not None and not isinstance(b[0], (int, float)))
                or (b[1] is not None and not isinstance(b[1], (int, float)))
            ):
                return None, f"`parameters.{p}.bounds` must be [low, high] with numeric/null entries."
    return params, None


def _validate_bounds_mapping(raw_bounds: Any) -> tuple[dict[str, tuple[float | None, float | None]] | None, str | None]:
    if raw_bounds is None:
        return {}, None
    if not isinstance(raw_bounds, dict):
        return None, "`parameters.bounds` must be a mapping."
    out: dict[str, tuple[float | None, float | None]] = {}
    for key, bound in raw_bounds.items():
        if not isinstance(key, str):
            return None, "bounds keys must be strings."
        if (
            not isinstance(bound, list)
            or len(bound) != 2
            or (bound[0] is not None and not isinstance(bound[0], (int, float)))
            or (bound[1] is not None and not isinstance(bound[1], (int, float)))
        ):
            return None, f"bounds for `{key}` must be [low, high] with numeric/null entries."
        out[key] = (
            None if bound[0] is None else float(bound[0]),
            None if bound[1] is None else float(bound[1]),
        )
    return out, None


def build_candl_param_plan(cfg: dict[str, Any], lens: CandlLens) -> tuple[CandlParamPlan | None, str | None]:
    params_cfg = cfg.get("parameters")
    if params_cfg is None:
        params_cfg = {}
    if not isinstance(params_cfg, dict):
        return None, "`parameters` must be a mapping."

    theta_default = {k: float(v) for k, v in lens.defaults.items()}
    required = list(lens.required_params)

    if params_cfg.get("strategy") == "candl_defaults":
        strategy = "candl_defaults"
        free_cfg = params_cfg.get("free", {})
        if free_cfg is None:
            free_cfg = {}
        if not isinstance(free_cfg, dict):
            return None, "`parameters.free` must be a mapping."
        mode = free_cfg.get("mode", "all_nuisance")
        include = free_cfg.get("include", [])
        exclude = free_cfg.get("exclude", [])
        if not isinstance(include, list) or not all(isinstance(x, str) for x in include):
            return None, "`parameters.free.include` must be a list of strings."
        if not isinstance(exclude, list) or not all(isinstance(x, str) for x in exclude):
            return None, "`parameters.free.exclude` must be a list of strings."

        cosmo_like = [p for p in required if _is_cosmo_like(p)]
        nuisance_like = [p for p in required if not _is_cosmo_like(p)]

        if mode == "all_nuisance":
            free_set = set(nuisance_like)
            free_set.update([p for p in include if p in required])
        elif mode == "explicit_list":
            if not include:
                return None, "`free.mode=explicit_list` requires non-empty `free.include`."
            free_set = set([p for p in include if p in required])
        else:
            return None, f"Unsupported `parameters.free.mode` `{mode}`."

        for p in exclude:
            free_set.discard(p)
        free_params = [p for p in required if p in free_set]

        bounds_map, bounds_err = _validate_bounds_mapping(params_cfg.get("bounds"))
        if bounds_err:
            return None, bounds_err
        assert bounds_map is not None
        theta_init = dict(theta_default)
    else:
        # Legacy mode: parameters.<name>.initial / .bounds
        strategy = "legacy_explicit"
        if not params_cfg:
            return None, "candl config needs either `strategy: candl_defaults` or explicit parameter blocks."
        explicit_blocks = {k: v for k, v in params_cfg.items() if isinstance(v, dict) and "initial" in v}
        if not explicit_blocks:
            return None, "No explicit parameter blocks found for legacy candl mode."
        free_params = []
        bounds_map = {}
        theta_init = dict(theta_default)
        for p in required:
            block = explicit_blocks.get(p)
            if block is None:
                continue
            free_params.append(p)
            try:
                theta_init[p] = float(block["initial"])
            except Exception as exc:  # noqa: BLE001
                return None, f"`parameters.{p}.initial` must be numeric: {exc}"
            if "bounds" in block and block["bounds"] is not None:
                b = block["bounds"]
                if (
                    not isinstance(b, list)
                    or len(b) != 2
                    or (b[0] is not None and not isinstance(b[0], (int, float)))
                    or (b[1] is not None and not isinstance(b[1], (int, float)))
                ):
                    return None, f"`parameters.{p}.bounds` must be [low, high] with numeric/null entries."
                bounds_map[p] = (
                    None if b[0] is None else float(b[0]),
                    None if b[1] is None else float(b[1]),
                )

        cosmo_like = [p for p in required if _is_cosmo_like(p)]
        nuisance_like = [p for p in required if not _is_cosmo_like(p)]

    n_total = len(required)
    n_free = len(free_params)
    n_fixed = n_total - n_free
    nuisance_free_list = [p for p in free_params if not _is_cosmo_like(p)]
    cosmo_fixed_list = [p for p in required if _is_cosmo_like(p) and p not in free_params]

    return (
        CandlParamPlan(
            strategy=strategy,
            theta_default=theta_default,
            theta_init=theta_init,
            free_params=free_params,
            bounds_map=bounds_map,
            n_params_total=n_total,
            n_params_free=n_free,
            n_params_fixed=n_fixed,
            nuisance_free_list=nuisance_free_list,
            cosmo_fixed_list=cosmo_fixed_list,
        ),
        None,
    )


def parse_optimizer(cfg: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    opt = cfg.get("optimizer", {})
    if not isinstance(opt, dict):
        return {}, "`optimizer` must be a mapping."
    method = opt.get("method", "L-BFGS-B")
    tol = opt.get("tol", None)
    options = opt.get("options", {})
    if not isinstance(method, str):
        return {}, "`optimizer.method` must be a string."
    if tol is not None and not isinstance(tol, (int, float)):
        return {}, "`optimizer.tol` must be numeric if provided."
    if not isinstance(options, dict):
        return {}, "`optimizer.options` must be a mapping."
    return {"method": method, "tol": tol, "options": options}, None


def make_gaussian_objective(mean: np.ndarray, cov: np.ndarray):
    def obj(theta_vec: np.ndarray) -> float:
        delta = theta_vec - mean
        solved = np.linalg.solve(cov, delta)
        return float(delta @ solved)

    return obj


def make_candl_objective(
    like_obj: Any,
    base_params: dict[str, Any],
    theta_template: dict[str, float],
    free_params: list[str],
    penalty_value: float = 1e30,
):
    def obj(theta_free: np.ndarray) -> float:
        overrides = dict(theta_template)
        for p, v in zip(free_params, theta_free):
            overrides[p] = float(v)
        try:
            loglike = evaluate_loglike_from_base(
                like_obj=like_obj,
                base_params=base_params,
                overrides=overrides,
            )
        except Exception:
            return penalty_value
        val = -2.0 * loglike
        if not math.isfinite(val):
            return penalty_value
        return float(val)

    return obj


def run_env_dump(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _bound_hits(
    free_params: list[str],
    theta_vec: np.ndarray,
    bounds: list[tuple[float | None, float | None]],
    atol: float = 1e-8,
) -> list[str]:
    hits: list[str] = []
    for p, v, (lo, hi) in zip(free_params, theta_vec, bounds):
        if lo is not None and abs(float(v) - float(lo)) <= atol:
            hits.append(f"{p}@lower")
        if hi is not None and abs(float(v) - float(hi)) <= atol:
            hits.append(f"{p}@upper")
    return hits


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()

    cfg, cfg_raw_or_err = load_yaml_config(config_path)
    if cfg is None:
        return _error(cfg_raw_or_err)
    cfg_raw = cfg_raw_or_err

    run_name = cfg.get("run_name")
    if not isinstance(run_name, str) or not run_name.strip():
        return _error("`run_name` is required and must be a non-empty string.")
    run_name = run_name.strip()

    lens_kind, lens_obj, lens_err = validate_lens(cfg)
    if lens_obj is None or lens_kind is None:
        return _error(lens_err or "Invalid lens.")

    optimizer, opt_err = parse_optimizer(cfg)
    if opt_err:
        return _error(opt_err)

    outdir = (
        Path(args.outdir).resolve()
        if args.outdir
        else (REPO_ROOT / "runs" / f"{_timestamp()}_{run_name}")
    )
    try:
        outdir.mkdir(parents=True, exist_ok=False)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Cannot create outdir `{outdir}`: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    objective_label = "chi2"
    max_abs_grad: float | None = None
    n_params_total = None
    n_params_free = None
    n_params_fixed = None
    nuisance_free_list: list[str] = []
    cosmo_fixed_list: list[str] = []
    bound_hits: list[str] = []
    theta_default_out: dict[str, float] | None = None
    free_params_out: list[str] | None = None

    if lens_kind == "gaussian":
        lens: GaussianLens = lens_obj
        params_cfg, params_err = validate_gaussian_parameters(cfg, lens.params)
        if params_cfg is None:
            return _error(params_err or "Invalid parameters block.")

        free_params = list(lens.params)
        theta_init_vec = np.array([float(params_cfg[p]["initial"]) for p in free_params], dtype=float)
        bounds = []
        for p in free_params:
            b = params_cfg[p].get("bounds")
            bounds.append((None, None) if b is None else (b[0], b[1]))
        objective = make_gaussian_objective(lens.mean, lens.cov)

        chi2_init = float(objective(theta_init_vec))
        if args.dry_run:
            theta_hat_vec = theta_init_vec.copy()
            chi2_best = chi2_init
            success = True
            message = "dry_run: optimization skipped"
            nfev = 1
            nit = 0
        else:
            res = minimize(
                objective,
                theta_init_vec,
                method=optimizer["method"],
                bounds=bounds,
                tol=optimizer["tol"],
                options=optimizer["options"],
            )
            theta_hat_vec = np.asarray(res.x, dtype=float)
            chi2_best = float(res.fun)
            success = bool(res.success)
            message = str(res.message)
            nfev = int(getattr(res, "nfev", 0)) if hasattr(res, "nfev") else None
            nit = int(getattr(res, "nit", 0)) if hasattr(res, "nit") else None
            if hasattr(res, "jac") and getattr(res, "jac") is not None:
                jac = np.asarray(getattr(res, "jac"), dtype=float)
                if jac.size > 0:
                    max_abs_grad = float(np.max(np.abs(jac)))
        theta_hat = {p: float(v) for p, v in zip(free_params, theta_hat_vec)}
        theta_init = {p: float(v) for p, v in zip(free_params, theta_init_vec)}
        n_params_total = len(free_params)
        n_params_free = len(free_params)
        n_params_fixed = 0
        free_params_out = list(free_params)
    else:
        lens = lens_obj
        candl_plan, plan_err = build_candl_param_plan(cfg, lens)
        if candl_plan is None:
            return _error(plan_err or "Invalid candl parameter strategy.")

        free_params = list(candl_plan.free_params)
        free_params_out = list(free_params)
        theta_default_out = dict(candl_plan.theta_default)
        n_params_total = candl_plan.n_params_total
        n_params_free = candl_plan.n_params_free
        n_params_fixed = candl_plan.n_params_fixed
        nuisance_free_list = list(candl_plan.nuisance_free_list)
        cosmo_fixed_list = list(candl_plan.cosmo_fixed_list)

        theta_init_vec = np.array([candl_plan.theta_init[p] for p in free_params], dtype=float)
        bounds = [candl_plan.bounds_map.get(p, (None, None)) for p in free_params]
        objective = make_candl_objective(
            like_obj=lens.like_obj,
            base_params=lens.test_vector.base_params,
            theta_template=candl_plan.theta_init,
            free_params=free_params,
        )
        objective_label = "-2loglike"

        chi2_init = float(objective(theta_init_vec))
        if len(free_params) == 0:
            theta_hat_vec = theta_init_vec.copy()
            chi2_best = chi2_init
            success = True
            message = "no free parameters; objective evaluated at baseline point"
            nfev = 1
            nit = 0
        elif args.dry_run:
            theta_hat_vec = theta_init_vec.copy()
            chi2_best = chi2_init
            success = True
            message = "dry_run: optimization skipped"
            nfev = 1
            nit = 0
        else:
            res = minimize(
                objective,
                theta_init_vec,
                method=optimizer["method"],
                bounds=bounds,
                tol=optimizer["tol"],
                options=optimizer["options"],
            )
            theta_hat_vec = np.asarray(res.x, dtype=float)
            chi2_best = float(res.fun)
            success = bool(res.success)
            message = str(res.message)
            nfev = int(getattr(res, "nfev", 0)) if hasattr(res, "nfev") else None
            nit = int(getattr(res, "nit", 0)) if hasattr(res, "nit") else None
            if hasattr(res, "jac") and getattr(res, "jac") is not None:
                jac = np.asarray(getattr(res, "jac"), dtype=float)
                if jac.size > 0:
                    max_abs_grad = float(np.max(np.abs(jac)))

        theta_hat = dict(candl_plan.theta_default)
        theta_init = dict(candl_plan.theta_init)
        for p, v in zip(free_params, theta_hat_vec):
            theta_hat[p] = float(v)

        bound_hits = _bound_hits(free_params, theta_hat_vec, bounds)

    (outdir / "config.yaml").write_text(cfg_raw, encoding="utf-8")
    run_env_dump(outdir)

    bestfit: dict[str, Any] = {
        "theta_hat": theta_hat,
        "theta_init": theta_init,
    }
    fit_quality: dict[str, Any] = {
        "chi2_best": float(chi2_best),
        "chi2_init": float(chi2_init),
        "success": bool(success),
        "message": message,
        "nfev": nfev,
        "nit": nit,
        "objective": objective_label,
        "n_params_total": n_params_total,
        "n_params_free": n_params_free,
        "n_params_fixed": n_params_fixed,
        "nuisance_free_list": nuisance_free_list,
        "cosmo_fixed_list": cosmo_fixed_list,
        "bound_hits": bound_hits,
    }
    if max_abs_grad is not None:
        fit_quality["max_abs_grad"] = max_abs_grad

    if lens_kind == "candl":
        fit_quality["loglike_best"] = float(-0.5 * chi2_best)
        fit_quality["loglike_init"] = float(-0.5 * chi2_init)
        bestfit["likelihood_id"] = lens.likelihood_id
        bestfit["test_yaml"] = str(lens.test_vector.test_yaml)
        bestfit["ell_cuts"] = lens.ell_cuts
        bestfit["dataset_yaml_used"] = lens.like_meta.dataset_yaml_used
        bestfit["n_bins_total"] = lens.like_meta.n_bins_total
        bestfit["n_bins_used"] = lens.like_meta.n_bins_used
        bestfit["spectra_present"] = lens.like_meta.spectra_present
        bestfit["theta_default"] = theta_default_out
        bestfit["free_params"] = free_params_out

    (outdir / "bestfit.json").write_text(json.dumps(bestfit, indent=2), encoding="utf-8")
    (outdir / "fit_quality.json").write_text(json.dumps(fit_quality, indent=2), encoding="utf-8")

    summary_lines = [
        "# MAP Run Summary",
        "",
        f"- run_name: `{run_name}`",
        f"- config: `{config_path}`",
        f"- lens_type: `{lens_kind}`",
        f"- dry_run: `{args.dry_run}`",
        f"- success: `{success}`",
        f"- message: `{message}`",
        f"- objective: `{objective_label}`",
        f"- chi2_init: `{chi2_init:.12g}`",
        f"- chi2_best: `{chi2_best:.12g}`",
    ]
    if lens_kind == "candl":
        summary_lines.extend(
            [
                f"- n_params_total: `{n_params_total}`",
                f"- n_params_free: `{n_params_free}`",
                f"- n_params_fixed: `{n_params_fixed}`",
                f"- bound_hits: `{bound_hits}`",
            ]
        )
    summary_lines.append("- theta_init:")
    for k in sorted(theta_init):
        summary_lines.append(f"- `{k}`: `{float(theta_init[k]):.12g}`")
    summary_lines.append("- theta_hat:")
    for k in sorted(theta_hat):
        summary_lines.append(f"- `{k}`: `{float(theta_hat[k]):.12g}`")
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Run bundle: {outdir}")
    print(f"success={success} chi2_best={chi2_best}")
    print(f"n_params_free={n_params_free}")

    if not success:
        return EXIT_OPTIM_ERROR
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
