from fractions import Fraction
from pathlib import Path
import json
import sys

import numpy as np
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import extract_mnu_limits as extractor


def test_histogram_mode_preserves_overflowing_bin_mass_order():
    scale = np.ldexp(1., 1023)
    weights = np.array([scale, scale, 1.5 * scale, 1.5 * scale])
    with np.errstate(over="ignore", invalid="ignore"):
        assert extractor._weighted_hist_mode(np.array([0., 0., 1., 1.]), weights, 2) == .75


def test_tiny_positive_weight_breaks_histogram_bin_tie():
    assert extractor._weighted_hist_mode(
        np.array([0., 1., 1.]), np.array([1e308, 1e308, 1e-300]), 2
    ) == .75


def test_zero_weight_outlier_does_not_change_histogram_range():
    assert extractor._weighted_hist_mode(
        np.array([0., 1., 100.]), np.array([1., 2., 0.]), 2
    ) == .75


def test_histogram_mode_midpoint_remains_finite_at_large_coordinates():
    values = np.array([1e308, 1.5e308])
    edges = np.linspace(values[0], values[1], 3)
    expected = float((Fraction(float(edges[1])) + Fraction(float(edges[2]))) / 2)
    with np.errstate(over="ignore", invalid="ignore"):
        assert extractor._weighted_hist_mode(values, np.array([1., 2.]), 2) == expected


def test_histogram_mode_supports_finite_opposite_extreme_coordinates():
    with np.errstate(over="ignore", invalid="ignore"):
        assert extractor._weighted_hist_mode(
            np.array([-1e308, 1e308]), np.array([1., 2.]), 2
        ) == 5e307


@pytest.mark.parametrize("exponent", [-1000, 0, 1000])
def test_histogram_mode_is_invariant_to_representable_weight_scaling(exponent):
    weights = np.ldexp(np.array([1., 1., 2., 2.]), exponent)
    assert extractor._weighted_hist_mode(np.array([0., 0., 1., 1.]), weights, 2) == .75


def _extract(tmp_path, monkeypatch, values, weights):
    run = tmp_path / "run"
    (run / "chains").mkdir(parents=True)
    prefix = run / "chains" / "posterior"
    (run / "resolved.yaml").write_text(yaml.safe_dump({
        "output": str(prefix), "params": {"mnu": {"prior": {"min": 0, "max": 5}}}
    }))
    np.savetxt(str(prefix) + ".1.txt", np.column_stack([weights, np.zeros(len(values)), values]),
               header="weight minuslogpost mnu", fmt="%.17g")
    output = tmp_path / "metrics.json"
    monkeypatch.setattr(sys, "argv", ["extract", "--chains_prefix", str(prefix),
                                    "--burnin_frac", "0", "--output", str(output)])
    with np.errstate(over="ignore", invalid="ignore"):
        assert extractor.main() == 0
    def nonfinite(value):
        raise AssertionError(f"Nonfinite value serialized: {value}")
    return json.loads(output.read_text(), parse_constant=nonfinite)


@pytest.mark.parametrize("case, expected", [("none", 0.), ("some", .4), ("all", 1.)])
def test_boundary_fraction_handles_finite_weights_with_overflowing_total(tmp_path, monkeypatch,
                                                                       case, expected):
    scale = np.ldexp(1., 1023)
    weights = np.array([scale, scale, 1.5 * scale, 1.5 * scale])
    values = np.array({"none": [.1, .1, 1., 1.], "some": [0., 0., 1., 1.],
                       "all": [0., 0., 0., 0.]}[case])
    result = _extract(tmp_path, monkeypatch, values, weights)
    assert result["boundary_fraction"] == expected
    assert result["n_represented_steps"] is None


def test_positive_boundary_fraction_underflow_is_reported_unknown(tmp_path, monkeypatch):
    result = _extract(tmp_path, monkeypatch, np.array([0., 1.]), np.array([1e-300, 1e308]))
    assert result["boundary_fraction"] == "unknown"
    assert any("underflow" in warning.lower() for warning in result["warnings"])
