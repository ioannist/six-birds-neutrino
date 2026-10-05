from __future__ import annotations

from copy import deepcopy
import math
from typing import Any

from cobaya.likelihood import Likelihood
import numpy as np

from sbt_spt_audit.candl_support import instantiate_like_with_metadata, load_test_vector


def select_internal_priors(priors, excluded_parameters):
    """Remove whole declared prior factors before any native JIT evaluation.

    Removing a coordinate from a correlated factor is ambiguous (conditioning
    and marginalizing differ), so partial removal is rejected.
    """
    if excluded_parameters is None:
        return list(priors)
    if not isinstance(excluded_parameters, list) or any(
        not isinstance(n, str) or not n for n in excluded_parameters
    ) or len(set(excluded_parameters)) != len(excluded_parameters):
        raise ValueError("exclude_prior_parameters must be a list of distinct parameter names.")
    excluded = set(excluded_parameters)
    present = {n for p in priors for n in p.par_names}
    if excluded - present:
        raise ValueError(f"No internal prior for: {sorted(excluded - present)}")
    kept = []
    for p in priors:
        names = set(p.par_names)
        if names & excluded:
            if not names <= excluded:
                raise ValueError("Cannot partially remove a joint internal prior factor.")
        else:
            kept.append(p)
    return kept


class CandlCobayaLikelihood(Likelihood):
    """Cobaya likelihood adapter for candl dataset shortcut expressions."""

    dataset_expr: str
    test_yaml: str | None = None
    lensing: bool | None = None
    ell_cuts: dict[str, list[float]] | None = None
    exclude_prior_parameters: list[str] | None = None

    def initialize(self) -> None:
        if not isinstance(self.dataset_expr, str) or not self.dataset_expr.strip():
            raise ValueError("dataset_expr must be a non-empty module.attr string")

        self._test_vector = load_test_vector(
            dataset_expr=self.dataset_expr.strip(),
            test_yaml_override=self.test_yaml,
        )

        lensing = self._test_vector.lensing if self.lensing is None else bool(self.lensing)
        self._like_obj, self._like_meta = instantiate_like_with_metadata(
            dataset_path=self._test_vector.dataset_path,
            lensing=lensing,
            ell_cuts=self.ell_cuts,
        )

        self._like_obj.priors = select_internal_priors(
            self._like_obj.priors, self.exclude_prior_parameters
        )
        self._like_obj.required_prior_parameters = sorted({
            n for p in self._like_obj.priors for n in p.par_names
        })
        self._internal_prior_policy = {
            "excluded_parameters": list(self.exclude_prior_parameters or []),
            "retained_factors": [{"parameters": list(p.par_names),
                                  "multiplicative_log_coordinates": bool(p.multiplicative_par),
                                  "central_value": np.asarray(p.central_value).tolist(),
                                  "covariance": np.asarray(p.prior_covariance).tolist()}
                                 for p in self._like_obj.priors],
        }

        self._base_params = deepcopy(self._test_vector.base_params)
        self._lensing = lensing
        self._ells = np.asarray(getattr(self._like_obj, "ells"), dtype=int)
        if self._ells.ndim != 1 or self._ells.size == 0:
            raise ValueError("candl likelihood did not expose 1D `ells` array")
        if lensing:
            raise ValueError("This adapter supports CMB TT/TE/EE likelihoods. Use candl's native Cobaya adapter for lensing spectra and pp/kk conversion.")

        self._lmax_required = int(np.max(self._ells))
        self._scalar_parameters = sorted(set(
            self._like_obj.required_nuisance_parameters
            + self._like_obj.required_prior_parameters
        ))
        missing = set(self._scalar_parameters) - self._base_params.keys()
        if missing:
            raise ValueError(f"Packaged defaults lack candl scalar parameters: {sorted(missing)}")

    def get_can_support_params(self) -> list[str]:
        # Cobaya assigns these inputs to us and includes them in cache keys,
        # even when another component also consumes the parameter.
        return self._scalar_parameters

    def get_requirements(self) -> dict[str, dict[str, int]]:
        cl_req = {
            "tt": self._lmax_required,
            "te": self._lmax_required,
            "ee": self._lmax_required,
            "bb": self._lmax_required,
        }
        if self._lensing:
            cl_req["pp"] = self._lmax_required
        return {"Cl": cl_req}

    def _get_cl_array(self, cls: dict[str, Any], key: str) -> np.ndarray:
        arr = cls.get(key)
        if arr is None:
            if key.upper() in self._like_obj.spec_types:
                raise ValueError(f"provider did not supply required {key} spectrum.")
            return np.zeros(self._lmax_required + 1, dtype=float)

        out = np.asarray(arr, dtype=float)
        if out.ndim != 1 or not np.all(np.isfinite(out)):
            raise ValueError(f"provider spectrum {key} must be finite and 1D.")

        if out.size < self._lmax_required + 1:
            raise ValueError(f"provider spectrum {key} does not cover required lmax.")
        return out

    def _build_dl(self, cls: dict[str, Any]) -> dict[str, np.ndarray]:
        ell = self._ells.astype(float)
        factor = ell * (ell + 1.0) / (2.0 * np.pi)

        tt = self._get_cl_array(cls, "tt")[self._ells]
        te = self._get_cl_array(cls, "te")[self._ells]
        ee = self._get_cl_array(cls, "ee")[self._ells]
        bb = self._get_cl_array(cls, "bb")[self._ells]
        pp = self._get_cl_array(cls, "pp")[self._ells]

        dl = {
            "ell": self._ells.astype(float),
            "TT": factor * tt,
            "TE": factor * te,
            "EE": factor * ee,
            "BB": factor * bb,
            "pp": factor * pp,
            "kk": np.zeros_like(factor),
        }
        return dl

    def current_candl_params(self, params_values: dict[str, float]) -> dict[str, Any]:
        """Recomputed spectra plus declared scalar inputs and fixed defaults."""
        cls = self.provider.get_Cl(ell_factor=False, units="muK2")
        dl = self._build_dl(cls)

        pars = deepcopy(self._base_params)
        pars["Dl"] = dl

        for key, val in params_values.items():
            if key not in self._scalar_parameters:
                raise ValueError(f"Undeclared candl scalar input: {key}")
            value = float(val)
            if not math.isfinite(value):
                raise ValueError(f"Nonfinite candl scalar input: {key}")
            pars[key] = value
        return pars

    def logp(self, _derived=None, **params_values) -> float:
        pars = self.current_candl_params(params_values)
        out = float(self._like_obj.log_like(pars))

        if not math.isfinite(out):
            return -np.inf
        return out

    def self_test_at_defaults(self) -> float:
        """Evaluate candl log-like at its packaged test/default vector."""
        return float(self._like_obj.log_like(self._test_vector.base_params))
