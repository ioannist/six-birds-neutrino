from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from sbt_spt_audit.likelihoods.desi_dr2_bao import (
    BAOPoint,
    compute_gaussian_chi2,
    compute_theory_vector,
    load_desi_dr2_dataset_from_files,
)


def test_gaussian_chi2_matches_manual() -> None:
    mean = np.array([10.0, 20.0], dtype=float)
    cov = np.array([[4.0, 1.0], [1.0, 9.0]], dtype=float)
    invcov = np.linalg.inv(cov)
    pred = np.array([11.5, 18.0], dtype=float)

    expected = float((pred - mean) @ invcov @ (pred - mean))
    got = compute_gaussian_chi2(mean=mean, invcov=invcov, pred=pred)

    assert got == pytest.approx(expected)


def test_loader_applies_deterministic_ordering(tmp_path: Path) -> None:
    mean_file = tmp_path / "mean.txt"
    cov_file = tmp_path / "cov.txt"

    mean_file.write_text(
        "\n".join(
            [
                "# z value observable",
                "0.7000 20.0 DH_over_rs",
                "0.5000 10.0 DM_over_rs",
                "0.5000 8.0 DV_over_rs",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cov = np.diag([1.0, 2.0, 3.0])
    np.savetxt(cov_file, cov)

    dataset = load_desi_dr2_dataset_from_files(mean_file=mean_file, cov_file=cov_file, label="test")

    assert [(p.z, p.obs) for p in dataset.points] == [
        (0.5, "DM_over_rd"),
        (0.5, "DV_over_rd"),
        (0.7, "DH_over_rd"),
    ]
    assert dataset.mean.tolist() == pytest.approx([10.0, 8.0, 20.0])
    assert np.diag(dataset.cov).tolist() == pytest.approx([2.0, 3.0, 1.0])


def test_loader_rejects_cov_dimension_mismatch(tmp_path: Path) -> None:
    mean_file = tmp_path / "mean.txt"
    cov_file = tmp_path / "cov.txt"

    mean_file.write_text(
        "\n".join(
            [
                "0.295 7.94 DV_over_rs",
                "0.510 13.58 DM_over_rs",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    np.savetxt(cov_file, np.eye(3))

    with pytest.raises(ValueError, match="Covariance shape mismatch"):
        load_desi_dr2_dataset_from_files(mean_file=mean_file, cov_file=cov_file, label="bad")


# Keep BAOPoint imported and referenced to ensure dataclass stays importable.
def test_baopoint_dataclass_fields() -> None:
    p = BAOPoint(z=0.5, obs="DM_over_rd", value=10.0, label="x")
    assert p.obs == "DM_over_rd"


def test_distance_provider_arrays_are_single_observations() -> None:
    points = [BAOPoint(z=0.5, obs="DM_over_rd", value=0.0, label="x")]
    pred = compute_theory_vector(points, 150.0,
                                 lambda z: np.array([1000.0]),
                                 lambda z: np.array([100.0]))
    assert pred == pytest.approx([10.0])
    with pytest.raises(ValueError, match="single finite"):
        compute_theory_vector(points, 150.0, lambda z: [1000.0, 1100.0], lambda z: 100.0)


def test_small_precision_does_not_require_representable_inverse_residual() -> None:
    # The precision solve overflows, but the requested quadratic form is finite.
    got = compute_gaussian_chi2(np.array([0.]), np.array([[1e-320]]), np.array([1.]))
    assert got == 1e-320


@pytest.mark.parametrize("mean,pred", [(0., 1e200), (-1e308, 1e308)])
def test_gaussian_quadratic_overflow_is_rejected(mean, pred) -> None:
    with pytest.raises(ValueError, match="quadratic form must be finite"):
        compute_gaussian_chi2(np.array([mean]), np.eye(1), np.array([pred]))


def test_loader_does_not_require_representable_covariance_solve_for_mean(tmp_path) -> None:
    mean_file, cov_file = tmp_path / 'mean.txt', tmp_path / 'cov.txt'
    mean_file.write_text('0.5 1e308 DM_over_rs\n')
    np.savetxt(cov_file, np.array([[1e-308]]))
    dataset = load_desi_dr2_dataset_from_files(mean_file, cov_file, label='extreme')
    assert np.isfinite(dataset.invcov).all()
    assert compute_gaussian_chi2(dataset.mean, dataset.invcov, dataset.mean) == 0.
