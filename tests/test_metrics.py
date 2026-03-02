import numpy as np
import pytest

from sbt_spt_audit.metrics import (
    blockwise_delta_chi2_from_loglike_blocks,
    delta_chi2_from_loglike,
    weighted_rmse,
)


def test_delta_chi2_sign_convention() -> None:
    delta = delta_chi2_from_loglike(loglike_test_at_train=-10.0, loglike_test_at_test=-5.0)
    assert delta == 10.0


def test_weighted_rmse_identity_covariance() -> None:
    residual = np.array([1.0, -2.0, 3.0])
    cov = np.eye(3)
    expected = np.sqrt(np.sum(residual**2) / residual.size)
    assert weighted_rmse(residual, cov) == pytest.approx(expected)


def test_blockwise_decomposition_sums_to_total() -> None:
    at_train = {"A": -10.0, "B": -1.25}
    at_test = {"A": -8.0, "B": -1.0}
    result = blockwise_delta_chi2_from_loglike_blocks(at_train, at_test)

    assert result["by_block"]["A"] == pytest.approx(4.0)
    assert result["by_block"]["B"] == pytest.approx(0.5)
    assert result["total"] == pytest.approx(result["by_block"]["A"] + result["by_block"]["B"])


def test_asymmetry_demonstration() -> None:
    def gaussian_loglike(theta: float, mu: float, sigma: float) -> float:
        return -0.5 * ((theta - mu) / sigma) ** 2

    mean_a, sigma_a = 0.0, 1.0
    mean_b, sigma_b = 3.0, 2.0
    theta_hat_a = mean_a
    theta_hat_b = mean_b

    delta_b_given_a = delta_chi2_from_loglike(
        loglike_test_at_train=gaussian_loglike(theta_hat_a, mean_b, sigma_b),
        loglike_test_at_test=gaussian_loglike(theta_hat_b, mean_b, sigma_b),
    )
    delta_a_given_b = delta_chi2_from_loglike(
        loglike_test_at_train=gaussian_loglike(theta_hat_b, mean_a, sigma_a),
        loglike_test_at_test=gaussian_loglike(theta_hat_a, mean_a, sigma_a),
    )

    assert delta_b_given_a >= 0.0
    assert delta_a_given_b >= 0.0
    assert delta_b_given_a != pytest.approx(delta_a_given_b)
