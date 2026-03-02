#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

import camb
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sbt_spt_audit.likelihoods.desi_dr2_bao import (  # noqa: E402
    compute_gaussian_chi2,
    compute_theory_vector,
    load_desi_dr2_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sanity-check DESI DR2 BAO Gaussian likelihood data.")
    parser.add_argument("--subset", default="all", type=str)
    parser.add_argument("--data_dir", default="data/desi_dr2_bao/desi_bao_dr2", type=str)
    parser.add_argument("--outdir", default=None, type=str)
    return parser.parse_args()


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def _write_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _build_background() -> camb.CAMBdata:
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=67.36, ombh2=0.02237, omch2=0.12, mnu=0.06, tau=0.0544)
    pars.InitPower.set_params(As=np.exp(3.044) * 1e-10, ns=0.9649)
    return camb.get_background(pars)


def main() -> int:
    args = parse_args()
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else REPO_ROOT / "runs" / f"{_stamp()}_desi_dr2_bao_sanity"
    outdir.mkdir(parents=True, exist_ok=False)

    logs: list[str] = []

    def log(msg: str) -> None:
        print(msg)
        logs.append(msg)

    _write_env(outdir)

    dataset, meta = load_desi_dr2_dataset(subset=args.subset, data_dir=args.data_dir)

    bg = _build_background()
    derived = bg.get_derived_params()
    rd = float(derived["rdrag"])

    pred = compute_theory_vector(
        points=dataset.points,
        rd=rd,
        angular_diameter_distance_fn=lambda z: float(bg.angular_diameter_distance(z)),
        hubble_fn=lambda z: float(bg.hubble_parameter(z)),
    )
    chi2 = compute_gaussian_chi2(dataset.mean, dataset.invcov, pred)

    labels = [f"({p.z:.3f}, {p.obs})" for p in dataset.points]
    log(f"subset={args.subset}")
    log(f"points={len(dataset.points)}")
    log(f"labels={labels}")
    log(f"chi2={chi2:.6f}")

    metrics = {
        "chi2": float(chi2),
        "n_points": int(len(dataset.points)),
        "subset": args.subset,
        "data_files_used": [meta.selected_mean_file, meta.selected_cov_file],
        "rd_mpc": rd,
        "first5_vector_order": [[float(p.z), p.obs] for p in dataset.points[:5]],
    }

    (outdir / "stdout.txt").write_text("\n".join(logs) + "\n", encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (outdir / "summary.md").write_text(
        "\n".join(
            [
                f"- subset: {args.subset}",
                f"- n_points: {len(dataset.points)}",
                f"- chi2: {chi2:.6f}",
                f"- mean_file: {meta.selected_mean_file}",
                f"- cov_file: {meta.selected_cov_file}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    log(f"run_bundle={outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
