#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_UNSUPPORTED_LENS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 1-mode template rewrite diagnostics between two runs.")
    parser.add_argument("--runA", required=True, type=str, help="Path to run bundle A")
    parser.add_argument("--runB", required=True, type=str, help="Path to run bundle B")
    parser.add_argument(
        "--direction",
        choices=["both", "B_given_A", "A_given_B"],
        default="both",
        help="Direction(s) to evaluate",
    )
    parser.add_argument(
        "--template",
        default="dominant_whitened",
        help="Template mode: dominant_whitened | mode0 | mode1 | ... | full_residual",
    )
    parser.add_argument("--outdir", type=str, default=None, help="Optional output run bundle path")
    return parser.parse_args()


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _fail(msg: str, code: int) -> int:
    print(msg, file=sys.stderr)
    return code


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level mapping")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level object")
    return data


def _validate_bundle(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config_path = run_dir / "config.yaml"
    bestfit_path = run_dir / "bestfit.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing {config_path}")
    if not bestfit_path.exists():
        raise FileNotFoundError(f"Missing {bestfit_path}")
    return _load_yaml(config_path), _load_json(bestfit_path)


def _parse_gaussian_lens(config: dict[str, Any]) -> tuple[str, list[str], np.ndarray, np.ndarray]:
    run_name = config.get("run_name")
    if not isinstance(run_name, str) or not run_name.strip():
        raise ValueError("Missing non-empty run_name")
    lens = config.get("lens")
    if not isinstance(lens, dict):
        raise ValueError("Missing lens mapping")
    if lens.get("type") != "gaussian":
        raise TypeError(f"Unsupported lens.type `{lens.get('type')}`")
    params = lens.get("params")
    mean = lens.get("mean")
    cov = lens.get("cov")
    if not isinstance(params, list) or not params or not all(isinstance(p, str) for p in params):
        raise ValueError("lens.params must be a non-empty list[str]")
    if not isinstance(mean, list) or len(mean) != len(params):
        raise ValueError("lens.mean must match lens.params length")
    if not isinstance(cov, list) or len(cov) != len(params):
        raise ValueError("lens.cov must be square with dim len(params)")
    for row in cov:
        if not isinstance(row, list) or len(row) != len(params):
            raise ValueError("lens.cov rows must all have len(params)")
    mu = np.asarray(mean, dtype=float)
    c = np.asarray(cov, dtype=float)
    return run_name.strip(), params, mu, c


def _theta_hat(bestfit: dict[str, Any], params: list[str]) -> np.ndarray:
    th = bestfit.get("theta_hat")
    if not isinstance(th, dict):
        raise ValueError("bestfit missing theta_hat mapping")
    vals: list[float] = []
    for p in params:
        if p not in th:
            raise ValueError(f"theta_hat missing parameter `{p}`")
        vals.append(float(th[p]))
    return np.asarray(vals, dtype=float)


def _template_vector(
    residual: np.ndarray,
    cov: np.ndarray,
    mode: str,
) -> tuple[np.ndarray, int | None]:
    if mode == "full_residual":
        return residual.copy(), None

    chol = np.linalg.cholesky(cov)
    z = np.linalg.solve(chol, residual)

    if mode == "dominant_whitened":
        k = int(np.argmax(np.abs(z)))
    else:
        m = re.fullmatch(r"mode(\d+)", mode)
        if not m:
            raise ValueError(
                f"Unsupported template mode `{mode}`. Use dominant_whitened, full_residual, or modeN."
            )
        k = int(m.group(1))
        if k < 0 or k >= z.shape[0]:
            raise ValueError(f"Template mode index out of range: mode{k} for dimension {z.shape[0]}")

    sign = 1.0 if z[k] >= 0 else -1.0
    z_t = np.zeros_like(z)
    z_t[k] = sign
    t = chol @ z_t
    return t, k


def _chi2(vec: np.ndarray, cov: np.ndarray) -> float:
    solved = np.linalg.solve(cov, vec)
    return float(vec @ solved)


def _direction_metrics(
    theta_train: np.ndarray,
    theta_test_best: np.ndarray,
    mu_test: np.ndarray,
    cov_test: np.ndarray,
    template_mode: str,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    residual = theta_train - mu_test
    chi2_before = _chi2(residual, cov_test)

    t, dominant_mode_index = _template_vector(residual, cov_test, template_mode)
    cinv_r = np.linalg.solve(cov_test, residual)
    cinv_t = np.linalg.solve(cov_test, t)

    numerator = float(t @ cinv_r)
    denominator = float(t @ cinv_t)
    if abs(denominator) < 1e-18:
        a_star = 0.0
        warnings.append("Template denominator near zero; using a_star=0.")
    else:
        a_star = numerator / denominator

    residual_after = residual - a_star * t
    chi2_after = _chi2(residual_after, cov_test)
    improvement = chi2_before - chi2_after
    if improvement < 0 and improvement > -1e-10:
        improvement = 0.0
    if improvement < -1e-10:
        warnings.append(
            f"Negative improvement beyond tolerance (improvement={improvement}); check numerical stability."
        )

    cond_cov = float(np.linalg.cond(cov_test))
    if cond_cov > 1e10:
        warnings.append(f"Ill-conditioned covariance (cond_cov={cond_cov:.3e}).")

    denom_align = np.sqrt(max(float(t @ cinv_t) * max(float(residual @ cinv_r), 0.0), 0.0))
    if denom_align <= 0.0:
        alignment_cos = 0.0
    else:
        alignment_cos = float((t @ cinv_r) / denom_align)
    alignment_cos = float(np.clip(alignment_cos, -1.0, 1.0))

    residual_driven = template_mode in {"dominant_whitened", "full_residual"}
    if residual_driven and alignment_cos > 0.95:
        warnings.append("high overfit risk: residual-driven template has alignment_cos > 0.95")

    if chi2_before > 0:
        fraction_removed = float(improvement / chi2_before)
    else:
        fraction_removed = 0.0

    metrics = {
        "chi2_before": float(chi2_before),
        "chi2_after": float(chi2_after),
        "improvement": float(improvement),
        "fraction_removed": float(fraction_removed),
        "a_star": float(a_star),
        "dominant_mode_index": dominant_mode_index,
        "alignment_cos": float(alignment_cos),
        "cond_cov": cond_cov,
        "chi2_test_best_reference": float(_chi2(theta_test_best - mu_test, cov_test)),
    }
    return metrics, warnings


def _write_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        check=True,
        capture_output=True,
        text=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _plot_before_after(outpath: Path, results: dict[str, dict[str, Any]], template_mode: str) -> None:
    directions = []
    before = []
    after = []
    if "B_given_A" in results:
        directions.append("B|A")
        before.append(results["B_given_A"]["chi2_before"])
        after.append(results["B_given_A"]["chi2_after"])
    if "A_given_B" in results:
        directions.append("A|B")
        before.append(results["A_given_B"]["chi2_before"])
        after.append(results["A_given_B"]["chi2_after"])

    x = np.arange(len(directions))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, before, width=width, label="chi2_before")
    ax.bar(x + width / 2, after, width=width, label="chi2_after")
    ax.set_xticks(x)
    ax.set_xticklabels(directions)
    ax.set_ylabel("Held-out chi2")
    ax.set_title(f"Template rewrite before/after ({template_mode})")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(outpath, dpi=160)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    run_a = Path(args.runA).resolve()
    run_b = Path(args.runB).resolve()
    if not run_a.exists() or not run_a.is_dir():
        return _fail(f"Invalid --runA path: {run_a}", EXIT_INPUT_ERROR)
    if not run_b.exists() or not run_b.is_dir():
        return _fail(f"Invalid --runB path: {run_b}", EXIT_INPUT_ERROR)

    try:
        cfg_a, best_a = _validate_bundle(run_a)
        cfg_b, best_b = _validate_bundle(run_b)
        run_name_a, params_a, mu_a, cov_a = _parse_gaussian_lens(cfg_a)
        run_name_b, params_b, mu_b, cov_b = _parse_gaussian_lens(cfg_b)
    except TypeError as exc:
        return _fail(f"Unsupported lens type: {exc}", EXIT_UNSUPPORTED_LENS)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Input/validation error: {exc}", EXIT_INPUT_ERROR)

    if params_a != params_b:
        return _fail(f"Parameter mismatch between runs: {params_a} vs {params_b}", EXIT_INPUT_ERROR)
    params = params_a

    try:
        theta_a = _theta_hat(best_a, params)
        theta_b = _theta_hat(best_b, params)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"theta_hat parsing error: {exc}", EXIT_INPUT_ERROR)

    outdir = (
        Path(args.outdir).resolve()
        if args.outdir
        else REPO_ROOT / "runs" / f"{_stamp()}_template_rewrite_{run_name_a}_vs_{run_name_b}"
    )
    outdir.mkdir(parents=True, exist_ok=False)
    figures_dir = outdir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    _write_env(outdir)

    metrics: dict[str, Any] = {
        "template_mode": args.template,
        "direction": args.direction,
    }
    warnings_all: list[str] = []

    if args.direction in {"both", "B_given_A"}:
        m, w = _direction_metrics(
            theta_train=theta_a,
            theta_test_best=theta_b,
            mu_test=mu_b,
            cov_test=cov_b,
            template_mode=args.template,
        )
        metrics["B_given_A"] = m
        warnings_all.extend([f"B_given_A: {msg}" for msg in w])

    if args.direction in {"both", "A_given_B"}:
        m, w = _direction_metrics(
            theta_train=theta_b,
            theta_test_best=theta_a,
            mu_test=mu_a,
            cov_test=cov_a,
            template_mode=args.template,
        )
        metrics["A_given_B"] = m
        warnings_all.extend([f"A_given_B: {msg}" for msg in w])

    metrics["warnings"] = warnings_all

    inputs_payload = {
        "runA": {"path": str(run_a), "run_name": run_name_a},
        "runB": {"path": str(run_b), "run_name": run_name_b},
        "direction": args.direction,
        "template": args.template,
    }
    (outdir / "inputs.yaml").write_text(yaml.safe_dump(inputs_payload, sort_keys=False), encoding="utf-8")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    fig_path = figures_dir / "template_rewrite_before_after.png"
    plot_data = {}
    if "B_given_A" in metrics:
        plot_data["B_given_A"] = metrics["B_given_A"]
    if "A_given_B" in metrics:
        plot_data["A_given_B"] = metrics["A_given_B"]
    _plot_before_after(fig_path, plot_data, args.template)

    summary_lines = [
        "# Template Rewrite Summary",
        "",
        f"- runA: `{run_name_a}` ({run_a})",
        f"- runB: `{run_name_b}` ({run_b})",
        f"- direction: `{args.direction}`",
        f"- template_mode: `{args.template}`",
    ]
    for key in ("B_given_A", "A_given_B"):
        if key in metrics:
            m = metrics[key]
            summary_lines.extend(
                [
                    f"- {key}.chi2_before: `{m['chi2_before']:.12g}`",
                    f"- {key}.chi2_after: `{m['chi2_after']:.12g}`",
                    f"- {key}.improvement: `{m['improvement']:.12g}`",
                    f"- {key}.fraction_removed: `{m['fraction_removed']:.12g}`",
                    f"- {key}.a_star: `{m['a_star']:.12g}`",
                    f"- {key}.dominant_mode_index: `{m['dominant_mode_index']}`",
                    f"- {key}.alignment_cos: `{m['alignment_cos']:.12g}`",
                    f"- {key}.cond_cov: `{m['cond_cov']:.12g}`",
                ]
            )
    summary_lines.append(f"- figure: `{fig_path}`")
    if warnings_all:
        summary_lines.append("- warnings:")
        for w in warnings_all:
            summary_lines.append(f"- `{w}`")
    else:
        summary_lines.append("- warnings: none")
    (outdir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Run bundle: {outdir}")
    if "B_given_A" in metrics:
        m = metrics["B_given_A"]
        print(
            "B_given_A "
            f"chi2_before={m['chi2_before']} chi2_after={m['chi2_after']} "
            f"fraction_removed={m['fraction_removed']}"
        )
    if "A_given_B" in metrics:
        m = metrics["A_given_B"]
        print(
            "A_given_B "
            f"chi2_before={m['chi2_before']} chi2_after={m['chi2_after']} "
            f"fraction_removed={m['fraction_removed']}"
        )
    if warnings_all:
        print("warnings:")
        for w in warnings_all:
            print(f"- {w}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
