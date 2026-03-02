#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
import yaml


def combine_gaussians(
    mu1: float,
    sigma1: float,
    mu2: float | np.ndarray,
    sigma2: float | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Combine two Gaussian constraints via product of densities."""
    if sigma1 <= 0:
        raise ValueError(f"sigma1 must be > 0, got {sigma1}.")
    sigma2_arr = np.asarray(sigma2, dtype=float)
    if np.any(sigma2_arr <= 0):
        raise ValueError("sigma2 must be > 0.")

    mu2_arr = np.asarray(mu2, dtype=float)
    prec1 = 1.0 / (sigma1**2)
    prec2 = 1.0 / (sigma2_arr**2)
    var_star = 1.0 / (prec1 + prec2)
    mu_star = var_star * (mu1 * prec1 + mu2_arr * prec2)
    sigma_star = np.sqrt(var_star)
    return np.asarray(mu_star), np.asarray(sigma_star)


def truncated_gaussian_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Normalized truncated Gaussian density on m >= 0."""
    if sigma <= 0:
        raise ValueError(f"sigma must be > 0, got {sigma}.")
    x_arr = np.asarray(x, dtype=float)
    z = 1.0 - norm.cdf((0.0 - mu) / sigma)
    if z <= 0:
        raise ValueError("Invalid truncation normalization (Z <= 0).")
    pdf = norm.pdf(x_arr, loc=mu, scale=sigma) / z
    return np.where(x_arr >= 0.0, pdf, 0.0)


def truncated_mode(mu: float) -> float:
    """Mode under m >= 0 truncation."""
    return max(0.0, mu)


def make_default_outdir(repo_root: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return repo_root / "runs" / f"{ts}_toy_trunc_gauss"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Toy truncated-Gaussian boundary-mode demonstration.",
    )
    parser.add_argument("--outdir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mu1", type=float, default=0.05)
    parser.add_argument("--sigma1", type=float, default=0.02)
    parser.add_argument("--d", type=float, default=0.07)
    parser.add_argument("--s", type=float, default=0.03)
    parser.add_argument("--n_mc", type=int, default=20000)
    parser.add_argument("--sigma2_min", type=float, default=0.002)
    parser.add_argument("--sigma2_max", type=float, default=0.05)
    parser.add_argument("--sigma2_n", type=int, default=30)
    parser.add_argument(
        "--example_sigma2",
        type=float,
        default=0.01,
        help="Sigma2 used for Figure A illustrative single case.",
    )
    return parser.parse_args()


def write_env_txt(outdir: Path, script_dir: Path) -> None:
    env_result = subprocess.run(
        [sys.executable, str(script_dir / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(env_result.stdout, encoding="utf-8")


def main() -> int:
    args = parse_args()

    if args.sigma2_min <= 0 or args.sigma2_max <= 0:
        raise ValueError("sigma2_min and sigma2_max must be > 0.")
    if args.sigma2_min >= args.sigma2_max:
        raise ValueError("sigma2_min must be < sigma2_max.")
    if args.sigma2_n < 2:
        raise ValueError("sigma2_n must be >= 2.")
    if args.n_mc < 1:
        raise ValueError("n_mc must be >= 1.")
    if args.sigma1 <= 0:
        raise ValueError("sigma1 must be > 0.")
    if args.s <= 0:
        raise ValueError("s must be > 0.")
    if args.example_sigma2 <= 0:
        raise ValueError("example_sigma2 must be > 0.")

    repo_root = Path(__file__).resolve().parents[1]
    outdir = Path(args.outdir).resolve() if args.outdir else make_default_outdir(repo_root)
    outdir.mkdir(parents=True, exist_ok=False)
    figures_dir = outdir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)

    sigma2_grid = np.logspace(np.log10(args.sigma2_min), np.log10(args.sigma2_max), args.sigma2_n)
    boundary_fraction_grid: list[float] = []

    for sigma2 in sigma2_grid:
        epsilon = rng.normal(loc=-args.d, scale=args.s, size=args.n_mc)
        mu2_draws = args.mu1 + epsilon
        mu_star_draws, _ = combine_gaussians(args.mu1, args.sigma1, mu2_draws, float(sigma2))
        boundary_fraction_grid.append(float(np.mean(mu_star_draws <= 0.0)))

    boundary_fraction_arr = np.asarray(boundary_fraction_grid, dtype=float)
    min_idx = int(np.argmin(boundary_fraction_arr))
    max_idx = int(np.argmax(boundary_fraction_arr))

    example_mu2 = args.mu1 - args.d
    example_mu_star_arr, example_sigma_star_arr = combine_gaussians(
        args.mu1,
        args.sigma1,
        example_mu2,
        args.example_sigma2,
    )
    example_mu_star = float(np.asarray(example_mu_star_arr))
    example_sigma_star = float(np.asarray(example_sigma_star_arr))
    example_mode = float(truncated_mode(example_mu_star))

    x = np.linspace(-0.05, 0.15, 1200)
    unconstrained_pdf = norm.pdf(x, loc=example_mu_star, scale=example_sigma_star)
    truncated_pdf = truncated_gaussian_pdf(x, example_mu_star, example_sigma_star)

    fig_a, ax_a = plt.subplots(figsize=(8, 5))
    ax_a.plot(x, unconstrained_pdf, label="Unconstrained Gaussian", lw=2)
    ax_a.plot(x, truncated_pdf, label="Truncated density (m >= 0)", lw=2)
    ax_a.axvline(example_mode, color="black", ls="--", lw=1.5, label=f"Mode = {example_mode:.4f}")
    ax_a.axvline(0.0, color="gray", ls=":", lw=1.2)
    ax_a.set_xlabel("m")
    ax_a.set_ylabel("density")
    ax_a.set_title(
        "Figure A: Truncation at m >= 0 "
        f"(mu*={example_mu_star:.4f}, sigma*={example_sigma_star:.4f}, mode={example_mode:.4f})"
    )
    ax_a.legend(loc="upper right")
    ax_a.grid(alpha=0.25)
    fig_a.tight_layout()
    fig_a_path = figures_dir / "figure_a_density_comparison.png"
    fig_a.savefig(fig_a_path, dpi=160)
    plt.close(fig_a)

    fig_b, ax_b = plt.subplots(figsize=(8, 5))
    ax_b.plot(sigma2_grid, boundary_fraction_arr, marker="o", ms=3, lw=1.8)
    ax_b.set_xscale("log")
    ax_b.set_xlabel("sigma2")
    ax_b.set_ylabel("boundary mode fraction: P(mu* <= 0)")
    ax_b.set_title("Figure B: Boundary-mode frequency vs sigma2 (smaller sigma2 = tighter dataset 2)")
    ax_b.grid(alpha=0.25, which="both")
    fig_b.tight_layout()
    fig_b_path = figures_dir / "figure_b_boundary_frequency_sweep.png"
    fig_b.savefig(fig_b_path, dpi=160)
    plt.close(fig_b)

    metrics = {
        "example_case": {
            "mu1": float(args.mu1),
            "sigma1": float(args.sigma1),
            "mu2": float(example_mu2),
            "sigma2": float(args.example_sigma2),
            "mu_star": example_mu_star,
            "sigma_star": example_sigma_star,
            "mode": example_mode,
        },
        "sweep": {
            "sigma2_grid": [float(v) for v in sigma2_grid.tolist()],
            "boundary_mode_fraction_grid": [float(v) for v in boundary_fraction_arr.tolist()],
            "boundary_mode_fraction_min": float(boundary_fraction_arr[min_idx]),
            "boundary_mode_fraction_max": float(boundary_fraction_arr[max_idx]),
            "boundary_mode_fraction_min_sigma2": float(sigma2_grid[min_idx]),
            "boundary_mode_fraction_max_sigma2": float(sigma2_grid[max_idx]),
            "n_mc": int(args.n_mc),
            "mismatch_params": {
                "d": float(args.d),
                "s": float(args.s),
            },
        },
    }

    config = {
        "seed": int(args.seed),
        "mu1": float(args.mu1),
        "sigma1": float(args.sigma1),
        "d": float(args.d),
        "s": float(args.s),
        "n_mc": int(args.n_mc),
        "sigma2_min": float(args.sigma2_min),
        "sigma2_max": float(args.sigma2_max),
        "sigma2_n": int(args.sigma2_n),
        "example_sigma2": float(args.example_sigma2),
        "outdir": str(outdir),
    }

    (outdir / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    summary_lines = [
        "# Toy Truncated Gaussian Run Summary",
        "",
        "- Purpose: quantify boundary-mode behavior from Gaussian combination plus m >= 0 truncation.",
        f"- Example case: mu1={args.mu1:.4f}, sigma1={args.sigma1:.4f}, mu2={example_mu2:.4f}, sigma2={args.example_sigma2:.4f}.",
        f"- Example posterior: mu*={example_mu_star:.6f}, sigma*={example_sigma_star:.6f}, truncated mode={example_mode:.6f}.",
        f"- Sweep size: sigma2_n={args.sigma2_n}, n_mc={args.n_mc}, seed={args.seed}.",
        (
            "- Boundary fraction range: "
            f"min={boundary_fraction_arr[min_idx]:.4f} at sigma2={sigma2_grid[min_idx]:.6f}, "
            f"max={boundary_fraction_arr[max_idx]:.4f} at sigma2={sigma2_grid[max_idx]:.6f}."
        ),
        "",
        "Figures:",
        f"- {fig_a_path.name}",
        f"- {fig_b_path.name}",
    ]
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    write_env_txt(outdir, Path(__file__).resolve().parent)

    print(f"Run bundle written to: {outdir}")
    print(f"Boundary fraction min={boundary_fraction_arr[min_idx]:.4f}, max={boundary_fraction_arr[max_idx]:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
