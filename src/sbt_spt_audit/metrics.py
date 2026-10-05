from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from math import sqrt

import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_triangular

from ._numerics import finite_signed_sum


def _covariance_cholesky(cov: np.ndarray, residual: np.ndarray):
    """Validate the covariance model and return its lower Cholesky factor."""
    c = np.asarray(cov, dtype=float)
    r = np.asarray(residual, dtype=float)
    if r.ndim != 1 or not r.size or c.shape != (r.size, r.size):
        raise ValueError("residual must be non-empty and 1D; cov must have matching square shape.")
    if not np.all(np.isfinite(c)) or not np.all(np.isfinite(r)):
        raise ValueError("covariance and residual must be finite.")
    # Released covariance matrices can differ at floating roundoff near zero.
    # Reject substantive asymmetry; project only roundoff onto the symmetric part.
    symmetry_atol = 64 * float(np.finfo(float).eps) * float(np.max(np.abs(c)))
    if not np.allclose(c, c.T, rtol=0.0, atol=symmetry_atol):
        raise ValueError("covariance must be symmetric.")
    # Exact symmetric entries already satisfy the projection. Halving the
    # smallest subnormal diagonal would erase a positive variance before
    # Cholesky, incorrectly turning a valid covariance into a singular matrix.
    asymmetric = c != c.T
    c = c.copy()
    c[asymmetric] = c[asymmetric] * .5 + c.T[asymmetric] * .5
    try:
        factor = cho_factor(c, lower=True)
    except np.linalg.LinAlgError as exc:
        raise ValueError("covariance must be positive definite.") from exc
    return factor, r


def covariance_solve(cov: np.ndarray, residual: np.ndarray) -> np.ndarray:
    """Solve with a finite, symmetric positive definite covariance.

    A pseudoinverse would silently change the statistical model and is not used.
    """
    factor, r = _covariance_cholesky(cov, residual)
    solution = cho_solve(factor, r)
    if not np.all(np.isfinite(solution)):
        raise ValueError("covariance solve produced nonfinite values; cannot report a finite result.")
    return solution


def quadratic_contributions(residual: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Signed coordinate accounting q_i = r_i (C^-1 r)_i.

    Sum over any partition gives the full quadratic form. Cross terms are
    split equally between their two coordinates. Individual terms can be
    negative; they are not marginal or independent block likelihoods.
    """
    r = np.asarray(residual, dtype=float)
    solution = covariance_solve(cov, r)
    with np.errstate(over="ignore", invalid="ignore"):
        contributions = r * solution
    if not np.all(np.isfinite(contributions)):
        raise ValueError("quadratic contributions overflowed; cannot report finite accounting.")
    return contributions


def delta_chi2_from_loglike(
    loglike_test_at_train: float,
    loglike_test_at_test: float,
) -> float:
    """Compute held-out Delta chi^2 from two test-likelihood evaluations.

    Sign convention:
    Delta chi^2 = -2 * (logL_test(theta_hat_train) - logL_test(theta_hat_test)).
    Delta chi^2 > 0 means the train-fit performs worse on held-out test data
    than the test set's own best-fit.
    """

    if not np.isfinite(loglike_test_at_train) or not np.isfinite(loglike_test_at_test):
        raise ValueError("log-likelihood evaluations must be finite.")
    delta = -2.0 * (float(loglike_test_at_train) - float(loglike_test_at_test))
    if not np.isfinite(delta):
        raise ValueError("likelihood difference overflowed; cannot report a finite Delta chi2.")
    return delta


def rmse(residual: np.ndarray) -> float:
    """Return unweighted root-mean-square error: sqrt(mean(residual^2))."""

    r = np.asarray(residual, dtype=float)
    if r.size == 0:
        raise ValueError("residual must be non-empty.")
    if not np.all(np.isfinite(r)):
        raise ValueError("residual must be finite.")
    scale = float(np.max(np.abs(r)))
    if scale == 0:
        return 0.0
    return float(scale * sqrt(float(np.mean((r / scale) ** 2))))


def weighted_rmse(residual: np.ndarray, cov: np.ndarray) -> float:
    """Return covariance-weighted RMSE: sqrt((r^T C^-1 r) / n).

    Uses Cholesky whitening and a scaled RMS, without forming the inverse or
    squaring the unscaled residual. Requires representable finite whitening.
    """

    r = np.asarray(residual, dtype=float)
    c = np.asarray(cov, dtype=float)

    if r.ndim != 1:
        raise ValueError(f"residual must be 1D with shape (n,), got shape {r.shape}.")
    if c.ndim != 2:
        raise ValueError(f"cov must be 2D with shape (n, n), got shape {c.shape}.")
    if c.shape[0] != c.shape[1]:
        raise ValueError(f"cov must be square, got shape {c.shape}.")
    if c.shape[0] != r.shape[0]:
        raise ValueError(
            "residual and cov shapes are inconsistent: "
            f"residual has length {r.shape[0]}, cov is {c.shape}."
        )
    if r.shape[0] == 0:
        raise ValueError("residual must be non-empty.")

    factor, r = _covariance_cholesky(c, r)
    whitened = solve_triangular(factor[0], r, lower=factor[1])
    if not np.all(np.isfinite(whitened)):
        raise ValueError("covariance whitening produced nonfinite values; cannot report a finite RMSE.")
    # Squared normalized coordinates can underflow, but never overflow; ignore
    # their negligible contributions rather than rejecting a finite RMS.
    with np.errstate(under="ignore"):
        return rmse(whitened)


def blockwise_delta_chi2_from_loglike_blocks(
    block_loglikes_at_train: Mapping[str, float],
    block_loglikes_at_test: Mapping[str, float],
) -> dict[str, object]:
    """Sum actual additive loglike terms with a finite rounding-consistency check.

    The aggregate is computed from the exact rational values of the supplied
    binary64 block loglikes, before endpoint sums can lose their difference.
    The total uses this aggregate; accounting_error records the sum of rounded
    block statistics minus the total, within the declared tolerance.
    This does not make correlated covariance subblocks additive likelihoods.
    """

    train_keys = set(block_loglikes_at_train.keys())
    test_keys = set(block_loglikes_at_test.keys())
    if train_keys != test_keys:
        missing_in_train = sorted(test_keys - train_keys)
        missing_in_test = sorted(train_keys - test_keys)
        raise ValueError(
            "Block keys mismatch between train and test loglikes. "
            f"Missing in train: {missing_in_train}; missing in test: {missing_in_test}."
        )
    if not train_keys:
        raise ValueError("At least one block is required.")

    by_block: dict[str, float] = {}
    aggregate = Fraction(0)
    for block in sorted(train_keys):
        train = float(block_loglikes_at_train[block])
        test = float(block_loglikes_at_test[block])
        by_block[block] = delta_chi2_from_loglike(
            train, test,
        )
        aggregate += -2 * (Fraction(train) - Fraction(test))

    total_from_blocks = finite_signed_sum(by_block.values(), context="block accounting")
    try:
        total_from_aggregate = float(aggregate)
    except OverflowError as exc:
        raise ValueError("Aggregate block likelihood difference is not representable as a finite binary64 output.") from exc
    if not np.isfinite(total_from_aggregate):
        raise ValueError("Aggregate block likelihood difference is not representable as a finite binary64 output.")
    if not np.isclose(total_from_blocks, total_from_aggregate, rtol=1e-12, atol=1e-12):
        raise ValueError(
            "Rounded block statistics do not reconstruct the aggregate at the declared tolerance. "
            f"total_from_blocks={total_from_blocks}, "
            f"total_from_aggregate={total_from_aggregate}."
        )

    return {
        "total": total_from_aggregate,
        "by_block": by_block,
        "accounting_error": finite_signed_sum(
            [total_from_blocks, -total_from_aggregate], context="block accounting"),
    }
