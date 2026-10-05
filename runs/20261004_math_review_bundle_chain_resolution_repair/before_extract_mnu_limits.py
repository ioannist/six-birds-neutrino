#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from sbt_spt_audit.mcmc import (
    weighted_quantile, validate_samples, expand_chain, chronological_halves,
    split_rhat, ess_autocorr, require_unit_temperature,
)


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
    return weighted_quantile(values, weights, q)


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
                candidate = Path(output)
                if candidate.is_absolute() and candidate.parent.exists():
                    return candidate
                if not candidate.is_absolute():
                    candidate = run_dir / candidate
                    if candidate.parent.exists():
                        return candidate

    chains_dir = run_dir / "chains"
    candidates = sorted(chains_dir.glob("*.1.txt"))
    if not candidates:
        candidates = sorted(run_dir.glob("**/*.1.txt"))
    if not candidates:
        raise FileNotFoundError(f"No chain files found under {run_dir}")
    first = candidates[0]
    return first.with_suffix("").with_suffix("")


def _read_paramnames(prefix: Path) -> list[str]:
    paramnames_path = Path(str(prefix) + ".paramnames")
    if not paramnames_path.exists():
        chain_candidates = sorted(prefix.parent.glob(f"{prefix.name}.*.txt"))
        if not chain_candidates:
            single = Path(str(prefix) + ".txt")
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
        _require_unique_names(tokens, chain_candidates[0])
        # First two columns are always weight and minuslogpost.
        return tokens[2:]
    names: list[str] = []
    for line in paramnames_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        names.append(stripped.split()[0].rstrip("*"))
    _require_unique_names(names, paramnames_path)
    return names


def _require_unique_names(names: list[str], source: Path) -> None:
    """An ambiguous coordinate label cannot identify a reported parameter."""
    if not names or any(not name for name in names) or len(set(names)) != len(names):
        raise ValueError(f"Parameter and chain column names must be nonempty and unique: {source}")


def _require_untempered_metadata(prefix: Path, run_dir: Path | None = None) -> None:
    """Reject declared heated targets before interpreting raw weights as posterior mass."""
    paths = [prefix.parent.parent / 'resolved.yaml', prefix.parent / 'resolved.yaml',
             Path(str(prefix) + '.updated.yaml'), Path(str(prefix) + '.input.yaml')]
    if run_dir is not None:
        paths.insert(0, run_dir / 'resolved.yaml')
    for path in dict.fromkeys(paths):
        if not path.exists():
            continue
        cfg = yaml.safe_load(path.read_text())
        if not isinstance(cfg, dict) or not isinstance(cfg.get('sampler'), dict):
            continue
        for options in cfg['sampler'].values():
            if isinstance(options, dict):
                require_unit_temperature(options)


def _load_chains_raw(prefix: Path, param: str, burnin_frac: float) -> list[tuple[np.ndarray, np.ndarray]]:
    _require_untempered_metadata(prefix)
    if not np.isfinite(burnin_frac) or not 0 <= burnin_frac < 1:
        raise ValueError("burnin_frac must lie in [0, 1).")
    names = _read_paramnames(prefix)
    if param not in names:
        raise KeyError(f"parameter `{param}` not found in {prefix}.paramnames")
    pidx = names.index(param)

    chain_files = sorted(p for p in prefix.parent.glob(f"{prefix.name}.*.txt")
                         if p.name[len(prefix.name)+1:-4].isdigit())
    if not chain_files:
        single = Path(str(prefix) + ".txt")
        if single.exists():
            chain_files = [single]
    if not chain_files:
        raise FileNotFoundError(f"No chain text files found for prefix: {prefix}")

    vals_all: list[np.ndarray] = []
    w_all: list[np.ndarray] = []
    for chain in chain_files:
        with chain.open(encoding="utf-8") as handle:
            header = handle.readline().strip()
        if header.startswith("#"):
            _require_unique_names(header.lstrip("#").split(), chain)
        if header.startswith("#") and header.lstrip("#").split()[2:2 + len(names)] != names:
            raise ValueError(f"Chain column names disagree with parameter names: {chain}")
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

        v, w = validate_samples(arr[:, 2 + pidx], arr[:, 0])
        w_all.append(w)
        vals_all.append(v)

    if not vals_all:
        raise ValueError("No post-burnin samples found in raw chain files")

    return list(zip(vals_all, w_all))


def _load_sequence_raw(prefix: Path, param: str, burnin_frac: float) -> tuple[np.ndarray, np.ndarray]:
    chains = _load_chains_raw(prefix, param, burnin_frac)
    return np.concatenate([v for v, w in chains]), np.concatenate([w for v, w in chains])


def _find_lower_bound(prefix: Path, param: str) -> float:
    resolved = prefix.parent.parent / "resolved.yaml"
    if resolved.exists():
        data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            params = data.get("params")
            if isinstance(params, dict):
                block = params.get(param)
                if isinstance(block, dict) and param == "mnu" and block.get("derived") == "lambda mnu_sample: mnu_sample":
                    block = params.get("mnu_sample")
                if isinstance(block, dict):
                    prior = block.get("prior")
                    if isinstance(prior, dict):
                        low = prior.get("min")
                        if isinstance(low, (int, float)):
                            return float(low)
    raise ValueError(f"No explicit lower prior bound found for parameter {param}.")


def main() -> int:
    args = parse_args()

    if args.run_dir:
        run_dir = Path(args.run_dir).expanduser().resolve()
        prefix = _resolve_prefix_from_run_dir(run_dir)
    else:
        prefix = Path(args.chains_prefix).expanduser().resolve()
        run_dir = prefix.parent.parent if prefix.parent.name == "chains" else prefix.parent

    _require_untempered_metadata(prefix, run_dir)
    warnings: list[str] = []

    if not np.isfinite(args.eps) or args.eps < 0:
        raise ValueError("eps must be finite and non-negative.")
    # Use one deterministic loader for summaries and sequential diagnostics.
    # Burn-in is discarded per file as a fraction of stored rows (GetDist convention).
    chains = _load_chains_raw(prefix, args.param, args.burnin_frac)
    values = np.concatenate([v for v, w in chains])
    weights = np.concatenate([w for v, w in chains])
    load_mode = "raw_per_chain"

    mnu_median = _weighted_quantile(values, weights, 0.5)
    mnu_p95_upper = _weighted_quantile(values, weights, 0.95)
    mnu_mode = _weighted_hist_mode(values, weights)

    lower_bound = None
    boundary_fraction = "unknown"
    try:
        lower_bound = _find_lower_bound(prefix, args.param)
        boundary_fraction = float(np.sum(weights[values <= (lower_bound + args.eps)]) / np.sum(weights))
    except ValueError as exc:
        warnings.append(str(exc))

    p95_first = p95_second = p95_half_diff = split_rhat_value = float("nan")
    ess = None
    represented_steps = None
    try:
        expanded = [expand_chain(v, w) for v, w in chains]
        represented_steps = sum(len(x) for x in expanded)
        halves = chronological_halves(expanded, equalize=False)
        first_values = np.concatenate(halves[::2])
        second_values = np.concatenate(halves[1::2])
        p95_first = weighted_quantile(first_values, np.ones(first_values.size), .95)
        p95_second = weighted_quantile(second_values, np.ones(second_values.size), .95)
        p95_half_diff = abs(p95_first - p95_second)
        split_rhat_value = split_rhat(expanded)
        # Do not concatenate independent chains before computing autocorrelation.
        ess = sum(ess_autocorr(x) for x in expanded)
        if ess < 400:
            warnings.append("Scalar ESS proxy below 400; tail quantile precision is not established.")
        if not math.isfinite(split_rhat_value) or split_rhat_value > 1.05:
            warnings.append("Scalar chronological split-Rhat does not pass 1.05; posterior bounds are not verified stable.")
    except ValueError as exc:
        warnings.append(f"Sequential diagnostics unavailable: {exc}")

    metrics: dict[str, Any] = {
        "chains_prefix": str(prefix),
        "param": args.param,
        "loader": load_mode,
        "burnin_frac": float(args.burnin_frac),
        "eps": float(args.eps),
        "prior_lower_bound": lower_bound if lower_bound is not None else "unknown",
        "mnu_median": float(mnu_median),
        "mnu_p95_upper": float(mnu_p95_upper),
        "mnu_mode": float(mnu_mode),
        "boundary_fraction": boundary_fraction,
        "n_samples_used": int(values.size),
        "n_chains": len(chains),
        "n_represented_steps": represented_steps,
        "quantile_definition": "inverse_weighted_empirical_cdf",
        "diagnostic_method": "classical_chronological_split_rhat_integer_holding_times",
        "ess_method": "sum_per_chain_scalar_initial_positive_monotone_fft_proxy",
        "diagnostic_scope": "scalar_proxies_not_rank_normalized_or_multivariate_certificates",
        "mnu_split_rhat": float(split_rhat_value) if math.isfinite(split_rhat_value) else "unknown",
        "mnu_ess": float(ess) if ess is not None and math.isfinite(ess) else "unknown",
        "mnu_p95_upper_first_half": float(p95_first) if math.isfinite(p95_first) else "unknown",
        "mnu_p95_upper_second_half": float(p95_second) if math.isfinite(p95_second) else "unknown",
        "mnu_p95_half_diff": float(p95_half_diff) if math.isfinite(p95_half_diff) else "unknown",
        "warnings": warnings,
    }

    out_path = Path(args.output).expanduser().resolve() if args.output else run_dir / "metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
