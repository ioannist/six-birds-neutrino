from __future__ import annotations

from dataclasses import dataclass
from math import frexp, ldexp
from pathlib import Path
from typing import Any, Callable

import numpy as np
from sbt_spt_audit.metrics import covariance_solve
try:
    from cobaya.likelihood import Likelihood
except Exception:  # noqa: BLE001
    class Likelihood:  # type: ignore[no-redef]
        pass

C_KM_S = 299792.458
SUPPORTED_OBS = ("DM_over_rd", "DH_over_rd", "DV_over_rd")
OBS_ORDER = {"DM_over_rd": 0, "DH_over_rd": 1, "DV_over_rd": 2}
OBS_MAP = {
    "DM_over_rs": "DM_over_rd",
    "DH_over_rs": "DH_over_rd",
    "DV_over_rs": "DV_over_rd",
    "DM_over_rd": "DM_over_rd",
    "DH_over_rd": "DH_over_rd",
    "DV_over_rd": "DV_over_rd",
}

SUBSET_PATTERNS = {
    "all": "_ALL_GCcomb_",
    "bgs": "_BGS_BRIGHT-21.35_GCcomb_",
    "elg": "_ELG_LOPnotqso_GCcomb_z1.1-1.6_",
    "lrg_z0": "_LRG_GCcomb_z0.4-0.6_",
    "lrg_z1": "_LRG_GCcomb_z0.6-0.8_",
    "lrg_elg": "_LRG+ELG_LOPnotqso_GCcomb_",
    "qso": "_QSO_GCcomb_",
    "lya": "_Lya_GCcomb_",
}


@dataclass(frozen=True)
class BAOPoint:
    z: float
    obs: str
    value: float
    label: str


@dataclass(frozen=True)
class BAODataset:
    points: list[BAOPoint]
    mean: np.ndarray
    cov: np.ndarray
    invcov: np.ndarray


@dataclass(frozen=True)
class BAOLoadMetadata:
    subset: str
    selected_mean_file: str
    selected_cov_file: str
    candidates_considered: list[str]


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "desi_dr2_bao" / "desi_bao_dr2"


def _candidate_mean_files(data_dir: Path) -> list[Path]:
    return sorted(data_dir.glob("desi_gaussian_bao_*_mean.txt"))


def _match_subset(mean_files: list[Path], subset: str) -> list[Path]:
    token = SUBSET_PATTERNS.get(subset.lower())
    if subset.lower() == "elg":
        return sorted(p for p in mean_files if "_elg_" in p.name.lower()
                      and "z1.1-1.6" in p.name.lower())
    if token is not None:
        out = [p for p in mean_files if token.lower() in p.name.lower()]
        if out:
            return sorted(out)

    # Fallback: simple contains match for unknown subset keys.
    fallback = [p for p in mean_files if subset.lower() in p.name.lower()]
    return sorted(fallback)


def discover_subset_files(data_dir: str | Path, subset: str = "all") -> tuple[Path, Path, BAOLoadMetadata]:
    data_path = Path(data_dir).expanduser().resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"BAO data directory does not exist: {data_path}")

    mean_files = _candidate_mean_files(data_path)
    if not mean_files:
        raise FileNotFoundError(f"No DR2 BAO mean files found in: {data_path}")

    candidates = _match_subset(mean_files, subset=subset)
    if not candidates:
        raise FileNotFoundError(f"No DR2 BAO mean file matched subset `{subset}` in {data_path}")

    if len(candidates) != 1:
        raise ValueError(f"Ambiguous BAO subset `{subset}`: {[p.name for p in candidates]}")
    mean_file = candidates[0]
    cov_file = Path(str(mean_file).replace("_mean.txt", "_cov.txt"))
    if not cov_file.exists():
        raise FileNotFoundError(f"Covariance file missing for {mean_file.name}: {cov_file}")

    meta = BAOLoadMetadata(
        subset=subset,
        selected_mean_file=mean_file.name,
        selected_cov_file=cov_file.name,
        candidates_considered=[p.name for p in candidates],
    )
    return mean_file, cov_file, meta


def _normalize_obs(raw_obs: str) -> str:
    if raw_obs not in OBS_MAP:
        raise ValueError(f"Unsupported BAO observable `{raw_obs}`. Supported inputs: {sorted(OBS_MAP)}")
    return OBS_MAP[raw_obs]


def load_desi_dr2_dataset_from_files(
    mean_file: str | Path,
    cov_file: str | Path,
    label: str,
) -> BAODataset:
    mean_path = Path(mean_file).expanduser().resolve()
    cov_path = Path(cov_file).expanduser().resolve()

    points_raw: list[BAOPoint] = []
    with mean_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) != 3:
                raise ValueError(f"Malformed mean-file line in {mean_path}: {line.rstrip()}")
            z = float(parts[0])
            value = float(parts[1])
            obs = _normalize_obs(parts[2])
            points_raw.append(BAOPoint(z=z, obs=obs, value=value, label=label))

    if not points_raw:
        raise ValueError(f"No BAO rows parsed from mean file: {mean_path}")

    mean_raw = np.array([p.value for p in points_raw], dtype=float)
    cov_raw = np.loadtxt(cov_path, dtype=float)
    if cov_raw.ndim == 0:
        cov_raw = np.array([[float(cov_raw)]], dtype=float)
    if cov_raw.ndim == 1:
        cov_raw = np.diag(cov_raw)

    n = len(points_raw)
    if cov_raw.shape != (n, n):
        raise ValueError(
            f"Covariance shape mismatch for {mean_path.name}: expected {(n, n)}, got {cov_raw.shape}"
        )

    order = sorted(range(n), key=lambda i: (points_raw[i].z, OBS_ORDER[points_raw[i].obs], i))
    points = [points_raw[i] for i in order]
    mean = mean_raw[np.array(order, dtype=int)]
    cov = cov_raw[np.ix_(order, order)]
    if not np.all(np.isfinite(mean)):
        raise ValueError("BAO means must be finite.")
    covariance_solve(cov, np.zeros_like(mean))  # Validate covariance, without solving for the mean.

    try:
        invcov = np.linalg.inv(cov)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"Covariance matrix is singular for {mean_path.name}") from exc
    if not np.all(np.isfinite(invcov)):
        raise ValueError(f"Inverse covariance is nonfinite for {mean_path.name}")

    return BAODataset(points=points, mean=mean, cov=cov, invcov=invcov)


def load_desi_dr2_dataset(
    subset: str = "all",
    data_dir: str | Path | None = None,
) -> tuple[BAODataset, BAOLoadMetadata]:
    use_dir = _default_data_dir() if data_dir is None else Path(data_dir)
    mean_file, cov_file, meta = discover_subset_files(use_dir, subset=subset)
    label = mean_file.name.replace("desi_gaussian_bao_", "").replace("_mean.txt", "")
    dataset = load_desi_dr2_dataset_from_files(mean_file, cov_file, label=label)
    return dataset, meta


def compute_observable_value(obs: str, z: float, rd: float, dm_mpc: float, dh_mpc: float) -> float:
    if not np.all(np.isfinite([z, rd, dm_mpc, dh_mpc])) or z < 0 or rd <= 0 or dm_mpc < 0 or dh_mpc <= 0:
        raise ValueError("BAO predictions require finite nonnegative z and distance, positive r_d and D_H.")
    if obs == "DM_over_rd":
        with np.errstate(over="ignore", under="ignore"):
            result = dm_mpc / rd
    elif obs == "DH_over_rd":
        with np.errstate(over="ignore", under="ignore"):
            result = dh_mpc / rd
    elif obs == "DV_over_rd":
        if z == 0 or dm_mpc == 0:
            return 0.0
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            product = z * dh_mpc * dm_mpc * dm_mpc
        if np.isfinite(product) and product > 0:
            # Preserve the ordinary calculation used by existing native runs.
            with np.errstate(over="ignore", under="ignore"):
                result = product ** (1.0 / 3.0) / rd
        else:
            # Compute the ratio directly. The four mantissas have a safe
            # product; separate binary exponents can cancel before scaling.
            mz, ez = frexp(z)
            mh, eh = frexp(dh_mpc)
            mm, em = frexp(dm_mpc)
            mr, er = frexp(rd)
            exponent, remainder = divmod(ez + eh + 2 * em - 3 * er, 3)
            scaled = float(np.cbrt(ldexp(mz * mh * mm * mm, remainder))) / mr
            try:
                result = ldexp(scaled, exponent)
            except OverflowError as exc:
                raise ValueError("BAO observable must have a representable finite output.") from exc
    else:
        raise ValueError(f"Unsupported observable `{obs}`")
    result = float(result)
    if not np.isfinite(result):
        raise ValueError("BAO observable must have a representable finite output.")
    return result


def compute_theory_vector(
    points: list[BAOPoint],
    rd: float,
    angular_diameter_distance_fn: Callable[[float], float],
    hubble_fn: Callable[[float], float],
) -> np.ndarray:
    vals: list[float] = []
    for p in points:
        da = _single_value(angular_diameter_distance_fn(p.z))
        hz = _single_value(hubble_fn(p.z))
        dm = (1.0 + p.z) * da
        dh = C_KM_S / hz
        vals.append(compute_observable_value(obs=p.obs, z=p.z, rd=rd, dm_mpc=dm, dh_mpc=dh))
    return np.asarray(vals, dtype=float)


def _single_value(value: Any) -> float:
    """Cobaya distance providers return length-one arrays for scalar z."""
    arr = np.asarray(value, dtype=float)
    if arr.size != 1 or not np.all(np.isfinite(arr)):
        raise ValueError("A single finite distance or Hubble value is required per redshift.")
    return float(arr.reshape(()))


def compute_gaussian_chi2(mean: np.ndarray, invcov: np.ndarray, pred: np.ndarray) -> float:
    mean, pred, invcov = (np.asarray(x, dtype=float) for x in (mean, pred, invcov))
    if mean.ndim != 1 or not mean.size or pred.shape != mean.shape:
        raise ValueError("mean and prediction must have matching nonempty 1D shapes.")
    if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(pred)):
        raise ValueError("mean and prediction must be finite.")
    covariance_solve(invcov, np.zeros_like(mean))  # Validate precision without inverting a residual.
    with np.errstate(over="ignore", invalid="ignore"):
        residual = pred - mean
        chi2 = float(residual @ invcov @ residual)
    if not np.all(np.isfinite(residual)) or not np.isfinite(chi2) or chi2 < 0:
        raise ValueError("Gaussian quadratic form must be finite and nonnegative.")
    return chi2


def _provider_rdrag(provider: Any) -> float:
    for key in ("rdrag", "rs_drag"):
        try:
            val = provider.get_param(key)
        except Exception:  # noqa: BLE001
            continue
        if val is None:
            continue
        return float(val)
    raise ValueError("Could not retrieve rdrag/rs_drag from Cobaya provider")


class DESIDR2BAOGaussian(Likelihood):
    subset: str = "all"
    data_dir: str = "data/desi_dr2_bao/desi_bao_dr2"
    verbose: bool = False

    def initialize(self) -> None:
        self._dataset, self._meta = load_desi_dr2_dataset(subset=self.subset, data_dir=self.data_dir)
        self._zs = np.array(sorted({p.z for p in self._dataset.points}), dtype=float)
        if self.verbose:
            self.log.info(
                "DESI DR2 BAO subset=%s mean=%s cov=%s",
                self._meta.subset,
                self._meta.selected_mean_file,
                self._meta.selected_cov_file,
            )

    def get_requirements(self) -> dict[str, Any]:
        return {
            "angular_diameter_distance": {"z": self._zs},
            "Hubble": {"z": self._zs},
            "rdrag": None,
        }

    def logp(self, **params_values: float) -> float:
        rd = _provider_rdrag(self.provider)
        pred = compute_theory_vector(
            points=self._dataset.points,
            rd=rd,
            angular_diameter_distance_fn=self.provider.get_angular_diameter_distance,
            hubble_fn=lambda z: self.provider.get_Hubble(z, units="km/s/Mpc"),
        )
        chi2 = compute_gaussian_chi2(self._dataset.mean, self._dataset.invcov, pred)
        return -0.5 * chi2


__all__ = [
    "BAOPoint",
    "BAODataset",
    "BAOLoadMetadata",
    "DESIDR2BAOGaussian",
    "discover_subset_files",
    "load_desi_dr2_dataset",
    "load_desi_dr2_dataset_from_files",
    "compute_theory_vector",
    "compute_gaussian_chi2",
]
