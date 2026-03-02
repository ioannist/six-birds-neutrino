#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract mnu summary metrics from Cobaya chains.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run_dir", type=str, default=None)
    group.add_argument("--chains_prefix", type=str, default=None)
    parser.add_argument("--param", type=str, default="mnu")
    parser.add_argument("--eps", type=float, default=1e-3)
    parser.add_argument("--burnin_frac", type=float, default=0.2)
    parser.add_argument("--output", type=str, default=None)
    return parser.parse_args()


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    if values.size == 0:
        raise ValueError("cannot compute quantile on empty array")
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cdf = np.cumsum(w)
    total = cdf[-1]
    if total <= 0:
        raise ValueError("non-positive total sample weight")
    cdf = cdf / total
    return float(np.interp(q, cdf, v))


def _weighted_mean_var(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    wsum = float(np.sum(weights))
    if values.size == 0 or wsum <= 0:
        raise ValueError("cannot compute weighted moments for empty/non-positive weights")
    mean = float(np.sum(weights * values) / wsum)
    var = float(np.sum(weights * (values - mean) ** 2) / wsum)
    return mean, var


def _weighted_hist_mode(values: np.ndarray, weights: np.ndarray, bins: int = 60) -> float:
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    if not math.isfinite(vmin) or not math.isfinite(vmax):
        raise ValueError("non-finite sample values")
    if vmax <= vmin:
        return vmin
    hist, edges = np.histogram(values, bins=bins, range=(vmin, vmax), weights=weights)
    idx = int(np.argmax(hist))
    return float(0.5 * (edges[idx] + edges[idx + 1]))


def _resolve_prefix_from_run_dir(run_dir: Path) -> Path:
    resolved = run_dir / "resolved.yaml"
    if resolved.exists():
        data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            output = data.get("output")
            if isinstance(output, str) and output.strip():
                return Path(output)

    chains_dir = run_dir / "chains"
    candidates = sorted(chains_dir.glob("*.1.txt"))
    if not candidates:
        candidates = sorted(run_dir.glob("**/*.1.txt"))
    if not candidates:
        raise FileNotFoundError(f"No chain files found under {run_dir}")
    first = candidates[0]
    return first.with_suffix("").with_suffix("")


def _load_with_getdist(prefix: Path, param: str, burnin_frac: float) -> tuple[np.ndarray, np.ndarray]:
    from getdist.mcsamples import loadMCSamples

    samples = loadMCSamples(str(prefix), settings={"ignore_rows": burnin_frac})
    params_obj = samples.getParams()
    if not hasattr(params_obj, param):
        raise KeyError(f"parameter `{param}` not found in GetDist samples")
    values = np.asarray(getattr(params_obj, param), dtype=float)
    weights = np.asarray(samples.weights, dtype=float)
    if values.shape != weights.shape:
        raise ValueError("values/weights shape mismatch in GetDist load")
    return values, weights


def _read_paramnames(prefix: Path) -> list[str]:
    paramnames_path = prefix.with_suffix(".paramnames")
    if not paramnames_path.exists():
        chain_candidates = sorted(prefix.parent.glob(f"{prefix.name}.*.txt"))
        if not chain_candidates:
            single = prefix.with_suffix(".txt")
            if single.exists():
                chain_candidates = [single]
        if not chain_candidates:
            raise FileNotFoundError(
                f"Missing paramnames file and no chain text file for header fallback: {paramnames_path}"
            )
        header = chain_candidates[0].read_text(encoding="utf-8").splitlines()[0].strip()
        if not header.startswith("#"):
            raise ValueError(f"Chain file header missing comment-prefixed names: {chain_candidates[0]}")
        tokens = header.lstrip("#").split()
        if len(tokens) < 3:
            raise ValueError(f"Insufficient columns in chain header: {chain_candidates[0]}")
        # First two columns are always weight and minuslogpost.
        return tokens[2:]
    names: list[str] = []
    for line in paramnames_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        names.append(stripped.split()[0])
    return names


def _load_sequence_raw(prefix: Path, param: str, burnin_frac: float) -> tuple[np.ndarray, np.ndarray]:
    names = _read_paramnames(prefix)
    if param not in names:
        raise KeyError(f"parameter `{param}` not found in {prefix}.paramnames")
    pidx = names.index(param)

    chain_files = sorted(prefix.parent.glob(f"{prefix.name}.*.txt"))
    if not chain_files:
        single = prefix.with_suffix(".txt")
        if single.exists():
            chain_files = [single]
    if not chain_files:
        raise FileNotFoundError(f"No chain text files found for prefix: {prefix}")

    vals_all: list[np.ndarray] = []
    w_all: list[np.ndarray] = []
    for chain in chain_files:
        arr = np.loadtxt(chain)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.shape[1] < 2 + len(names):
            raise ValueError(f"Unexpected chain column count in {chain}: {arr.shape}")

        n = arr.shape[0]
        start = int(max(0, min(n, math.floor(n * burnin_frac))))
        arr = arr[start:]
        if arr.size == 0:
            continue

        w_all.append(np.asarray(arr[:, 0], dtype=float))
        vals_all.append(np.asarray(arr[:, 2 + pidx], dtype=float))

    if not vals_all:
        raise ValueError("No post-burnin samples found in raw chain files")

    values = np.concatenate(vals_all)
    weights = np.concatenate(w_all)
    return values, weights


def _find_lower_bound(prefix: Path, param: str) -> float:
    resolved = prefix.parent.parent / "resolved.yaml"
    if resolved.exists():
        data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            params = data.get("params")
            if isinstance(params, dict):
                block = params.get(param)
                if isinstance(block, dict):
                    prior = block.get("prior")
                    if isinstance(prior, dict):
                        low = prior.get("min")
                        if isinstance(low, (int, float)):
                            return float(low)
    return 0.0


def _split_rhat(
    values_first: np.ndarray,
    weights_first: np.ndarray,
    values_second: np.ndarray,
    weights_second: np.ndarray,
) -> float:
    if values_first.size < 4 or values_second.size < 4:
        raise ValueError("not enough samples for split-Rhat")

    m1, s1 = _weighted_mean_var(values_first, weights_first)
    m2, s2 = _weighted_mean_var(values_second, weights_second)

    n_half = float(min(values_first.size, values_second.size))
    W = 0.5 * (s1 + s2)
    grand = 0.5 * (m1 + m2)
    B = n_half * (((m1 - grand) ** 2 + (m2 - grand) ** 2) / (2.0 - 1.0))

    if W <= 0:
        if abs(m1 - m2) < 1e-12:
            return 1.0
        return float("inf")

    var_hat = ((n_half - 1.0) / n_half) * W + (B / n_half)
    if var_hat < 0:
        var_hat = 0.0
    return float(np.sqrt(var_hat / W))


def _ess_autocorr(values: np.ndarray) -> float:
    n = values.size
    if n < 20:
        raise ValueError("not enough samples for ESS")

    x = np.asarray(values, dtype=float)
    x = x - np.mean(x)
    var = float(np.var(x))
    if var <= 0:
        raise ValueError("zero variance; ESS undefined")

    corr_full = np.correlate(x, x, mode="full")
    acf = corr_full[n - 1 :] / corr_full[n - 1]

    max_lag = min(n - 1, 1000)
    tau = 1.0
    for k in range(1, max_lag + 1):
        if acf[k] <= 0:
            break
        tau += 2.0 * float(acf[k])

    if tau <= 0 or not math.isfinite(tau):
        raise ValueError("invalid integrated autocorrelation time")

    ess = float(n / tau)
    return max(1.0, min(float(n), ess))


def main() -> int:
    args = parse_args()

    if args.run_dir:
        run_dir = Path(args.run_dir).expanduser().resolve()
        prefix = _resolve_prefix_from_run_dir(run_dir)
    else:
        prefix = Path(args.chains_prefix).expanduser().resolve()
        run_dir = prefix.parent.parent if prefix.parent.name == "chains" else prefix.parent

    warnings: list[str] = []

    load_mode = "getdist"
    try:
        values, weights = _load_with_getdist(prefix, args.param, args.burnin_frac)
    except Exception as exc_getdist:  # noqa: BLE001
        load_mode = "raw_fallback"
        warnings.append(f"getdist loader failed: {exc_getdist}")
        values, weights = _load_sequence_raw(prefix, args.param, args.burnin_frac)

    seq_values, seq_weights = _load_sequence_raw(prefix, args.param, args.burnin_frac)

    finite_mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[finite_mask]
    weights = weights[finite_mask]

    seq_mask = np.isfinite(seq_values) & np.isfinite(seq_weights) & (seq_weights > 0)
    seq_values = seq_values[seq_mask]
    seq_weights = seq_weights[seq_mask]

    if values.size == 0:
        raise RuntimeError("No finite positive-weight samples available")
    if seq_values.size == 0:
        raise RuntimeError("No finite positive-weight sequential samples available")

    mnu_median = _weighted_quantile(values, weights, 0.5)
    mnu_p95_upper = _weighted_quantile(values, weights, 0.95)
    mnu_mode = _weighted_hist_mode(values, weights)

    lower_bound = _find_lower_bound(prefix, args.param)
    boundary_fraction = float(np.sum(weights[values <= (lower_bound + args.eps)]) / np.sum(weights))

    # Interleaved split stability check (odd/even) on sequential samples.
    first_values, first_weights = seq_values[::2], seq_weights[::2]
    second_values, second_weights = seq_values[1::2], seq_weights[1::2]

    if first_values.size == 0 or second_values.size == 0:
        raise RuntimeError("Not enough sequential samples to split chain")

    p95_first = _weighted_quantile(first_values, first_weights, 0.95)
    p95_second = _weighted_quantile(second_values, second_weights, 0.95)
    p95_half_diff = abs(p95_first - p95_second)

    try:
        split_rhat = _split_rhat(first_values, first_weights, second_values, second_weights)
    except Exception as exc:  # noqa: BLE001
        split_rhat = float("nan")
        warnings.append(f"split-Rhat unavailable: {exc}")

    try:
        ess = _ess_autocorr(seq_values)
    except Exception as exc:  # noqa: BLE001
        ess = None
        warnings.append(f"ESS unavailable: {exc}")

    metrics: dict[str, Any] = {
        "chains_prefix": str(prefix),
        "param": args.param,
        "loader": load_mode,
        "burnin_frac": float(args.burnin_frac),
        "eps": float(args.eps),
        "prior_lower_bound": float(lower_bound),
        "mnu_median": float(mnu_median),
        "mnu_p95_upper": float(mnu_p95_upper),
        "mnu_mode": float(mnu_mode),
        "boundary_fraction": float(boundary_fraction),
        "n_samples_used": int(seq_values.size),
        "mnu_split_rhat": float(split_rhat) if math.isfinite(split_rhat) else "unknown",
        "mnu_ess": float(ess) if ess is not None and math.isfinite(ess) else "unknown",
        "mnu_p95_upper_first_half": float(p95_first),
        "mnu_p95_upper_second_half": float(p95_second),
        "mnu_p95_half_diff": float(p95_half_diff),
        "warnings": warnings,
    }

    out_path = Path(args.output).expanduser().resolve() if args.output else run_dir / "metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
