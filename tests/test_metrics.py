import numpy as np
import pytest

from sbt_spt_audit.metrics import (
    blockwise_delta_chi2_from_loglike_blocks,
    covariance_solve,
    delta_chi2_from_loglike,
    quadratic_contributions,
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


@pytest.mark.parametrize("value", [1e200, 1e-200, np.nextafter(0., 1.)])
def test_weighted_rmse_preserves_representable_magnitude(value) -> None:
    with np.errstate(all="raise"):
        result = weighted_rmse(np.array([value]), np.eye(1))
    assert result == value


def test_weighted_rmse_does_not_require_representable_inverse_solve() -> None:
    variance = 1e-320
    with np.errstate(all="raise"):
        result = weighted_rmse(np.array([1., 0.]), np.diag([variance, 1.]))
    expected = (1. / np.sqrt(variance)) / np.sqrt(2.)
    assert result == pytest.approx(expected, rel=1e-14)


def test_weighted_rmse_matches_correlated_whitened_norm() -> None:
    # C^-1 = [[1,-2],[-2,5]], so r=(1,1) has quadratic form 2.
    # Its signed coordinate allocations are -1 and 3.
    assert weighted_rmse(np.ones(2), np.array([[5., 2.], [2., 1.]])) == pytest.approx(1.)


def test_weighted_rmse_rejects_nonfinite_whitening() -> None:
    with pytest.raises(ValueError, match="whitening produced nonfinite"):
        weighted_rmse(np.array([1e308]), np.array([[1e-308]]))


def test_blockwise_decomposition_sums_to_total() -> None:
    at_train = {"A": -10.0, "B": -1.25}
    at_test = {"A": -8.0, "B": -1.0}
    result = blockwise_delta_chi2_from_loglike_blocks(at_train, at_test)

    assert result["by_block"]["A"] == pytest.approx(4.0)
    assert result["by_block"]["B"] == pytest.approx(0.5)
    assert result["total"] == pytest.approx(result["by_block"]["A"] + result["by_block"]["B"])


def test_blockwise_common_offset_does_not_erase_small_difference() -> None:
    result = blockwise_delta_chi2_from_loglike_blocks(
        {"large": -1e16, "small": -1.}, {"large": -1e16, "small": -2.})
    assert result["total"] == result["by_block"]["small"] == -2.


def test_blockwise_aggregate_does_not_depend_on_dictionary_insertion_order() -> None:
    result = blockwise_delta_chi2_from_loglike_blocks(
        {"a": -1e16, "b": -1., "c": -1.}, {"b": -1., "c": -1., "a": -1e16})
    assert result["total"] == 0.


def test_blockwise_recovers_cancellation_after_partial_sum_overflow() -> None:
    result = blockwise_delta_chi2_from_loglike_blocks(
        {"a": -5e307, "b": -5e307, "c": 0., "d": 0.},
        {"a": 0., "b": 0., "c": -5e307, "d": -5e307})
    assert result["total"] == 0.
    assert result["by_block"] == {"a": 1e308, "b": 1e308, "c": -1e308, "d": -1e308}


def test_blockwise_rejects_unrepresentable_total() -> None:
    with pytest.raises(ValueError, match="not representable"):
        blockwise_delta_chi2_from_loglike_blocks({"a": -5e307, "b": -5e307}, {"a": 0., "b": 0.})


def test_blockwise_rejects_small_aggregate_hidden_by_rounded_blocks() -> None:
    # The exact aggregate of the supplied block loglikes is -2, while the
    # separately rounded block statistics are +2e16 and -2e16. Reporting zero
    # would silently lose the likelihood difference.
    with pytest.raises(ValueError, match="Rounded block statistics"):
        blockwise_delta_chi2_from_loglike_blocks({"a": -1e16, "b": 0.}, {"a": -1., "b": -1e16})


def test_blockwise_total_preserves_small_signal_within_rounding_tolerance() -> None:
    result = blockwise_delta_chi2_from_loglike_blocks(
        {"a": -1e16, "b": 0.}, {"a": -1e-14, "b": -1e16})
    assert result["total"] == -2e-14
    assert sum(result["by_block"].values()) == 0.
    assert result["accounting_error"] == 2e-14


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


@pytest.mark.parametrize("variance,residual", [(1e-308, 1e308), (1e-320, 1.0)])
def test_finite_spd_covariance_with_nonfinite_solve_is_rejected(variance, residual) -> None:
    # These diagonal matrices are SPD; their first solution coordinate exceeds
    # binary64's range. BLAS can return NaN or infinity without raising an error.
    cov = np.diag([variance, 1.0])
    vector = np.array([residual, 0.0])
    with pytest.raises(ValueError, match="covariance solve produced nonfinite"):
        covariance_solve(cov, vector)
    with pytest.raises(ValueError, match="covariance solve produced nonfinite"):
        quadratic_contributions(vector, cov)


def test_finite_solve_with_overflowing_quadratic_allocation_is_rejected() -> None:
    vector = np.array([1e200])
    cov = np.eye(1)
    np.testing.assert_array_equal(covariance_solve(cov, vector), vector)
    with pytest.raises(ValueError, match="quadratic contributions overflowed"):
        quadratic_contributions(vector, cov)
