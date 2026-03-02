from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import importlib
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml


@dataclass
class CandlTestVector:
    dataset_expr: str
    dataset_path: str
    module_name: str
    attr_name: str
    test_yaml: Path
    payload: dict[str, Any]
    base_params: dict[str, Any]
    lensing: bool


@dataclass
class CandlLikeMetadata:
    dataset_yaml_used: str
    ell_cuts: dict[str, list[float]] | None
    spectra_present: list[str]
    n_bins_total: int
    n_bins_used: int


@dataclass
class CandlParamInspection:
    required_params: list[str]
    defaults: dict[str, float]
    checked_sources: list[str]


def resolve_dataset_expr(dataset_expr: str) -> tuple[str, str, str]:
    parts = dataset_expr.split(".")
    if len(parts) != 2:
        raise ValueError(f"Dataset expression must be module.attr, got: {dataset_expr}")
    module_name, attr_name = parts
    mod = importlib.import_module(module_name)
    dataset_path = getattr(mod, attr_name, None)
    if not isinstance(dataset_path, str) or not dataset_path:
        raise ValueError(f"{dataset_expr} did not resolve to a valid dataset path string.")
    return module_name, attr_name, dataset_path


def find_test_yaml_for_dataset(
    dataset_expr: str,
    module_name: str,
    test_yaml_override: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    if test_yaml_override:
        path = Path(test_yaml_override).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Explicit test_yaml does not exist: {path}")
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid test yaml contents: {path}")
        return path, payload

    mod = importlib.import_module(module_name)
    data_path = getattr(mod, "data_path", None)
    if not isinstance(data_path, str) or not data_path:
        raise FileNotFoundError(f"{module_name} has no data_path to auto-discover test vectors.")
    tests_dir = Path(data_path) / "tests"
    if not tests_dir.exists():
        raise FileNotFoundError(f"Tests directory missing: {tests_dir}")

    for test_yaml in sorted(tests_dir.glob("*.yaml")):
        payload = yaml.safe_load(test_yaml.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        if payload.get("data_set_file") == dataset_expr:
            return test_yaml, payload
    raise FileNotFoundError(f"No matching test yaml found for {dataset_expr} in {tests_dir}")


def build_base_params_from_test_vector(
    test_yaml: Path,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    param_values = payload.get("param_values")
    test_spectrum = payload.get("test_spectrum")
    if not isinstance(param_values, dict):
        raise ValueError(f"{test_yaml}: missing mapping `param_values`.")
    if not isinstance(test_spectrum, str):
        raise ValueError(f"{test_yaml}: missing string `test_spectrum`.")

    spec_path = test_yaml.parent / test_spectrum
    if not spec_path.exists():
        raise FileNotFoundError(f"Test spectrum file not found: {spec_path}")
    spec_arr = np.loadtxt(spec_path)
    if spec_arr.ndim != 2 or spec_arr.shape[1] < 7:
        raise ValueError(f"Unexpected spectrum shape in {spec_path}: {spec_arr.shape}")

    base_params = deepcopy(param_values)
    base_params["Dl"] = {}
    for i, spec in enumerate(["ell", "TT", "TE", "EE", "BB", "pp", "kk"]):
        base_params["Dl"][spec] = spec_arr[:, i]
    lensing = bool(payload.get("lensing", False))
    return base_params, lensing


def load_test_vector(
    dataset_expr: str,
    test_yaml_override: str | None = None,
) -> CandlTestVector:
    module_name, attr_name, dataset_path = resolve_dataset_expr(dataset_expr)
    test_yaml, payload = find_test_yaml_for_dataset(
        dataset_expr=dataset_expr,
        module_name=module_name,
        test_yaml_override=test_yaml_override,
    )
    base_params, lensing = build_base_params_from_test_vector(test_yaml, payload)
    return CandlTestVector(
        dataset_expr=dataset_expr,
        dataset_path=dataset_path,
        module_name=module_name,
        attr_name=attr_name,
        test_yaml=test_yaml,
        payload=payload,
        base_params=base_params,
        lensing=lensing,
    )


def _normalize_ell_cuts(
    ell_cuts: Mapping[str, Any] | None,
) -> dict[str, list[float]] | None:
    if ell_cuts is None:
        return None
    if not isinstance(ell_cuts, Mapping):
        raise ValueError("ell_cuts must be a mapping from spectrum type to [lmin, lmax].")
    out: dict[str, list[float]] = {}
    for raw_spec, raw_range in ell_cuts.items():
        spec = str(raw_spec).strip().upper()
        if spec == "":
            raise ValueError("ell_cuts contains empty spectrum key.")
        if (
            not isinstance(raw_range, (list, tuple))
            or len(raw_range) != 2
            or not isinstance(raw_range[0], (int, float))
            or not isinstance(raw_range[1], (int, float))
        ):
            raise ValueError(f"ell_cuts[{spec}] must be [lmin, lmax] numeric.")
        lmin = float(raw_range[0])
        lmax = float(raw_range[1])
        if lmax < lmin:
            raise ValueError(f"ell_cuts[{spec}] has lmax < lmin.")
        out[spec] = [lmin, lmax]
    return out


def _instantiate_raw_like(dataset_path: str, lensing: bool, **kwargs):
    candl_mod = importlib.import_module("candl")
    like_cls = candl_mod.LensLike if lensing else candl_mod.Like
    return like_cls(dataset_path, feedback=False, **kwargs)


def get_bin_spec_types(like_obj: Any) -> np.ndarray:
    spec_order = list(getattr(like_obj, "spec_order"))
    spec_types = list(getattr(like_obj, "spec_types"))
    start_ix = np.asarray(getattr(like_obj, "bins_start_ix"), dtype=int)
    stop_ix = np.asarray(getattr(like_obj, "bins_stop_ix"), dtype=int)
    n_bins = int(getattr(like_obj, "N_bins_total"))
    out = np.empty(n_bins, dtype=object)
    for i in range(len(spec_order)):
        out[start_ix[i] : stop_ix[i]] = spec_types[i]
    return out


def _build_data_selection_mask_for_ell_cuts(
    like_obj: Any,
    ell_cuts: dict[str, list[float]],
) -> np.ndarray:
    current_mask = np.asarray(getattr(like_obj, "crop_mask"), dtype=bool)
    spec_by_bin = get_bin_spec_types(like_obj)
    eff_ells = np.asarray(getattr(like_obj, "effective_ells"), dtype=float)
    new_mask = np.array(current_mask, dtype=bool)

    for spec, (lmin, lmax) in ell_cuts.items():
        spec_selector = spec_by_bin == spec
        if not np.any(spec_selector):
            continue
        ell_selector = (eff_ells >= lmin) & (eff_ells <= lmax)
        keep = spec_selector & ell_selector
        new_mask[spec_selector] = new_mask[spec_selector] & keep[spec_selector]

    return new_mask


def instantiate_like_with_metadata(
    dataset_path: str,
    lensing: bool,
    ell_cuts: Mapping[str, Any] | None = None,
) -> tuple[Any, CandlLikeMetadata]:
    normalized_cuts = _normalize_ell_cuts(ell_cuts)

    if normalized_cuts is None:
        like_obj = _instantiate_raw_like(dataset_path, lensing=lensing)
        crop_mask = np.asarray(getattr(like_obj, "crop_mask"), dtype=bool)
        spec_types = get_bin_spec_types(like_obj)
        meta = CandlLikeMetadata(
            dataset_yaml_used=str(getattr(like_obj, "data_set_file", dataset_path)),
            ell_cuts=None,
            spectra_present=sorted(set(str(s) for s in spec_types)),
            n_bins_total=int(getattr(like_obj, "N_bins_total")),
            n_bins_used=int(np.count_nonzero(crop_mask)),
        )
        return like_obj, meta

    base_like = _instantiate_raw_like(dataset_path, lensing=lensing)
    selection_mask = _build_data_selection_mask_for_ell_cuts(base_like, normalized_cuts)
    if not np.any(selection_mask):
        raise ValueError("ell_cuts removed all bins; no data left for likelihood.")

    like_obj = _instantiate_raw_like(
        dataset_path,
        lensing=lensing,
        data_selection=[bool(x) for x in selection_mask.tolist()],
    )
    spec_types = get_bin_spec_types(like_obj)
    meta = CandlLikeMetadata(
        dataset_yaml_used=str(getattr(like_obj, "data_set_file", dataset_path)),
        ell_cuts={k: [float(v[0]), float(v[1])] for k, v in normalized_cuts.items()},
        spectra_present=sorted(set(str(s) for s in spec_types)),
        n_bins_total=int(selection_mask.size),
        n_bins_used=int(np.count_nonzero(selection_mask)),
    )
    return like_obj, meta


def instantiate_like(
    dataset_path: str,
    lensing: bool,
    ell_cuts: Mapping[str, Any] | None = None,
):
    like_obj, _ = instantiate_like_with_metadata(
        dataset_path=dataset_path,
        lensing=lensing,
        ell_cuts=ell_cuts,
    )
    return like_obj


def build_params_with_overrides(
    base_params: dict[str, Any],
    overrides: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    pars = deepcopy(base_params)
    if overrides:
        for k, v in overrides.items():
            if k in pars:
                pars[k] = float(v)
    return pars


def evaluate_loglike_from_base(
    like_obj: Any,
    base_params: dict[str, Any],
    overrides: Mapping[str, float] | None = None,
) -> float:
    pars = build_params_with_overrides(base_params=base_params, overrides=overrides)
    raw = like_obj.log_like(pars)
    val = float(raw)
    if not math.isfinite(val):
        raise ValueError(f"Non-finite loglike returned: {val}")
    return val


def compute_residual_from_base(
    like_obj: Any,
    base_params: dict[str, Any],
    overrides: Mapping[str, float] | None = None,
) -> np.ndarray:
    pars = build_params_with_overrides(base_params=base_params, overrides=overrides)
    modified_theory = np.asarray(like_obj.get_model_specs(pars), dtype=float)
    binned_theory = np.asarray(like_obj.bin_model_specs(modified_theory), dtype=float)
    data_vec = np.asarray(getattr(like_obj, "_data_bandpowers"), dtype=float)
    if data_vec.shape != binned_theory.shape:
        raise ValueError("Binned theory shape mismatch with data vector shape.")
    return data_vec - binned_theory


def _try_cast_defaults(mapping: Mapping[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for k, v in mapping.items():
        if isinstance(k, str) and isinstance(v, (int, float)):
            out[k] = float(v)
    return out


def _collect_names_from_data_model(obj: Any, param_context: bool = False) -> set[str]:
    names: set[str] = set()
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            key = str(k).lower()
            ctx = param_context or ("param" in key) or key in {
                "par_names",
                "modes_params",
                "pol_params",
                "spec_param_dict",
                "param_dict",
            }
            names.update(_collect_names_from_data_model(v, param_context=ctx))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            names.update(_collect_names_from_data_model(item, param_context=param_context))
    elif isinstance(obj, str) and param_context:
        token = obj.strip()
        if token and " " not in token and "/" not in token:
            names.add(token)
    return names


def _defaults_from_test_yaml_for_like(like_obj: Any) -> tuple[dict[str, float], str | None]:
    dataset_file_raw = getattr(like_obj, "data_set_file", None)
    if not isinstance(dataset_file_raw, str):
        return {}, None
    dataset_file = Path(dataset_file_raw).resolve()
    candidate_test_dirs = [
        dataset_file.parent / "tests",
        dataset_file.parent.parent / "tests",
        dataset_file.parent.parent.parent / "tests",
    ]
    for test_dir in candidate_test_dirs:
        if not test_dir.exists() or not test_dir.is_dir():
            continue
        for test_yaml in sorted(test_dir.glob("*.yaml")):
            try:
                payload = yaml.safe_load(test_yaml.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, Mapping):
                continue
            data_set_expr = payload.get("data_set_file")
            if not isinstance(data_set_expr, str):
                continue
            try:
                _, _, resolved_path = resolve_dataset_expr(data_set_expr)
            except Exception:
                continue
            if Path(resolved_path).resolve() != dataset_file:
                continue
            param_values = payload.get("param_values")
            if not isinstance(param_values, Mapping):
                continue
            defaults = _try_cast_defaults(param_values)
            if defaults:
                return defaults, str(test_yaml)
    return {}, None


def get_required_params_and_defaults(like_obj: Any) -> tuple[list[str], dict[str, float]]:
    checked_sources: list[str] = []
    defaults: dict[str, float] = {}

    for attr in ["pars", "default_pars", "defaults", "params_default", "param_defaults"]:
        checked_sources.append(attr)
        value = getattr(like_obj, attr, None)
        if isinstance(value, Mapping):
            defaults = _try_cast_defaults(value)
            if defaults:
                break

    if not defaults:
        defaults, test_yaml_used = _defaults_from_test_yaml_for_like(like_obj)
        checked_sources.append(f"test_yaml_scan:{test_yaml_used or 'none'}")

    if not defaults:
        like_name = str(getattr(like_obj, "name", "unknown_like"))
        dataset_file = str(getattr(like_obj, "data_set_file", "unknown_dataset"))
        raise ValueError(
            "Could not infer candl defaults. "
            f"like={like_name}, dataset={dataset_file}, checked={checked_sources}"
        )

    required_names = set(defaults.keys())
    data_set_dict = getattr(like_obj, "data_set_dict", None)
    if isinstance(data_set_dict, Mapping):
        checked_sources.append("data_set_dict.priors")
        priors = data_set_dict.get("priors")
        if isinstance(priors, list):
            for prior in priors:
                if not isinstance(prior, Mapping):
                    continue
                par_names = prior.get("par_names")
                if isinstance(par_names, str) and par_names in defaults:
                    required_names.add(par_names)
                elif isinstance(par_names, (list, tuple)):
                    for p in par_names:
                        if isinstance(p, str) and p in defaults:
                            required_names.add(p)

        checked_sources.append("data_set_dict.data_model")
        model_names = _collect_names_from_data_model(data_set_dict.get("data_model"))
        for name in model_names:
            if name in defaults:
                required_names.add(name)

    required_sorted = sorted(required_names)
    if not required_sorted:
        raise ValueError("No required parameters discovered for candl likelihood.")
    return required_sorted, {k: defaults[k] for k in required_sorted}
