from __future__ import annotations

from copy import deepcopy
import math
from typing import Any

from cobaya.likelihood import Likelihood
import numpy as np

from sbt_spt_audit.candl_support import instantiate_like_with_metadata, load_test_vector


class CandlCobayaLikelihood(Likelihood):
    """Cobaya likelihood adapter for candl dataset shortcut expressions."""

    dataset_expr: str
    test_yaml: str | None = None
    lensing: bool | None = None
    ell_cuts: dict[str, list[float]] | None = None

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

        self._base_params = deepcopy(self._test_vector.base_params)
        self._lensing = lensing
        self._ells = np.asarray(getattr(self._like_obj, "ells"), dtype=int)
        if self._ells.ndim != 1 or self._ells.size == 0:
            raise ValueError("candl likelihood did not expose 1D `ells` array")

        self._lmax_required = int(np.max(self._ells))
        self._float_base_keys = [
            k
            for k, v in self._base_params.items()
            if k != "Dl" and isinstance(v, (int, float))
        ]

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
            return np.zeros(self._lmax_required + 1, dtype=float)

        out = np.asarray(arr, dtype=float)
        if out.ndim != 1:
            out = out.reshape(-1)

        if out.size < self._lmax_required + 1:
            padded = np.zeros(self._lmax_required + 1, dtype=float)
            padded[: out.size] = out
            return padded
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

    def _inject_current_scalars(self, pars: dict[str, Any]) -> None:
        for key in self._float_base_keys:
            try:
                val = self.provider.get_param(key)
            except Exception:  # noqa: BLE001
                continue
            if isinstance(val, (int, float)) and math.isfinite(float(val)):
                pars[key] = float(val)

    def logp(self, **params_values) -> float:
        cls = self.provider.get_Cl(ell_factor=False)
        dl = self._build_dl(cls)

        pars = deepcopy(self._base_params)
        pars["Dl"] = dl

        self._inject_current_scalars(pars)

        for key, val in params_values.items():
            if isinstance(val, (int, float)) and math.isfinite(float(val)):
                pars[key] = float(val)

        try:
            out = float(self._like_obj.log_like(pars))
        except Exception:  # noqa: BLE001
            return -np.inf

        if not math.isfinite(out):
            return -np.inf
        return out

    def self_test_at_defaults(self) -> float:
        """Evaluate candl log-like at its packaged test/default vector."""
        return float(self._like_obj.log_like(self._test_vector.base_params))
