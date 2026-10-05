from pathlib import Path
import argparse
import json
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_template_rewrite as rewrite


@pytest.mark.parametrize("mode", ["full_residual", "dominant_whitened"])
def test_rewrite_accepts_finite_quadratic_without_representable_inverse_solve(mode):
    # r/C overflows, but (r/sqrt(C))^2 and the physical correction are finite.
    variance = 1e-320
    with np.errstate(all="raise"):
        metrics, _ = rewrite._direction_metrics(
            np.array([1e-10]), np.zeros(1), np.zeros(1), np.array([[variance]]), mode)
    assert all(np.isfinite(value) for key, value in metrics.items()
               if key != "dominant_mode_index" and value is not None)
    assert metrics["chi2_before"] == pytest.approx((1e-10 / np.sqrt(variance)) ** 2, rel=1e-14)
    assert metrics["chi2_after"] <= 1e-28 * metrics["chi2_before"]
    assert metrics["fraction_removed"] == pytest.approx(1.)
    assert metrics["alignment_cos"] == pytest.approx(1.)


def test_rewrite_covariance_validation_does_not_solve_for_mean():
    config = {"run_name": "valid_mean", "lens": {
        "type": "gaussian", "params": ["x"], "mean": [1.], "cov": [[1e-320]]}}
    _, _, mean, covariance = rewrite._parse_gaussian_lens(config)
    np.testing.assert_array_equal(mean, [1.])
    np.testing.assert_array_equal(covariance, [[1e-320]])


@pytest.mark.parametrize("residual", [1e200, np.nan])
def test_rewrite_rejects_nonfinite_or_unrepresentable_quadratic(residual):
    with pytest.raises(ValueError):
        rewrite._direction_metrics(np.array([residual]), np.zeros(1), np.zeros(1),
                                   np.eye(1), "full_residual")


def test_rewrite_nonzero_subnormal_quadratic_is_not_reported_as_zero():
    with pytest.raises(ValueError, match="underflow"):
        rewrite._chi2(np.array([1e-200]), np.eye(1))


def test_rewrite_projection_matches_independent_correlated_quadratic():
    covariance = np.array([[5., 2.], [2., 1.]])
    residual = np.array([3., 4.])
    metrics, _ = rewrite._direction_metrics(residual, np.zeros(2), np.zeros(2),
                                           covariance, "mode1")
    template = np.linalg.cholesky(covariance)[:, 1]
    correction = metrics["a_star"] * template
    before = residual @ np.linalg.solve(covariance, residual)
    after_vector = residual - correction
    after = after_vector @ np.linalg.solve(covariance, after_vector)
    assert metrics["chi2_before"] == pytest.approx(before)
    assert metrics["chi2_after"] == pytest.approx(after, abs=1e-12)
    assert metrics["improvement"] == pytest.approx(before - after)
    assert 0 <= metrics["alignment_cos"] <= 1


def test_rewrite_zero_template_has_zero_removal_and_finite_diagnostics():
    metrics, warnings = rewrite._direction_metrics(np.zeros(2), np.zeros(2), np.zeros(2),
                                                np.eye(2), "full_residual")
    assert metrics["chi2_before"] == metrics["chi2_after"] == metrics["a_star"] == 0
    assert metrics["fraction_removed"] == metrics["alignment_cos"] == 0
    assert warnings == ["Zero template; using a_star=0."]


@pytest.mark.parametrize("scale", [1e-200, 1e200])
def test_rewrite_coefficient_cancels_extreme_nonzero_template_scale(monkeypatch, scale):
    monkeypatch.setattr(rewrite, "_template_vector",
                        lambda r, c, m: (np.array([scale]), None))
    with np.errstate(all="raise"):
        metrics, _ = rewrite._direction_metrics(np.array([2.]), np.zeros(1), np.zeros(1),
                                               np.eye(1), "mode0")
    assert metrics["a_star"] == pytest.approx(2. / scale)
    assert metrics["chi2_after"] <= 1e-28
    assert metrics["fraction_removed"] == pytest.approx(1.)


def test_rewrite_cli_serializes_unknown_condition_estimate(tmp_path, monkeypatch):
    import yaml

    covariance = [[1e-320, 0.], [0., 1.]]
    runs = []
    for name, mean in [("A", [1e-160, 0.]), ("B", [0., 0.])]:
        run = tmp_path / name
        run.mkdir()
        (run / "config.yaml").write_text(yaml.safe_dump({
            "run_name": name, "lens": {"type": "gaussian", "params": ["x", "y"],
                                      "mean": mean, "cov": covariance}}))
        (run / "bestfit.json").write_text(json.dumps({"theta_hat": dict(zip(["x", "y"], mean))}))
        runs.append(run)
    outdir = tmp_path / "output"
    monkeypatch.setattr(rewrite, "parse_args", lambda: argparse.Namespace(
        runA=str(runs[0]), runB=str(runs[1]), outdir=str(outdir),
        direction="both", template="full_residual"))
    monkeypatch.setattr(rewrite, "_write_env", lambda _: None)
    assert rewrite.main() == rewrite.EXIT_OK
    payload = json.loads((outdir / "metrics.json").read_text())
    assert payload["B_given_A"]["cond_cov"] is None
    assert "cond_cov: `unknown`" in (outdir / "summary.md").read_text()
