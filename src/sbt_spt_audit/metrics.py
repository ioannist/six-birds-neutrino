from __future__ import annotations

from collections.abc import Mapping
from math import sqrt

import numpy as np


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

    return -2.0 * (loglike_test_at_train - loglike_test_at_test)


def rmse(residual: np.ndarray) -> float:
    """Return unweighted root-mean-square error: sqrt(mean(residual^2))."""

    r = np.asarray(residual, dtype=float)
    if r.size == 0:
        raise ValueError("residual must be non-empty.")
    return float(sqrt(float(np.mean(r**2))))


def weighted_rmse(residual: np.ndarray, cov: np.ndarray) -> float:
    """Return covariance-weighted RMSE: sqrt((r^T C^-1 r) / n).

    Uses a linear solve and never forms the explicit matrix inverse.
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

    try:
        c_inv_r = np.linalg.solve(c, r)
    except np.linalg.LinAlgError as exc:
        raise ValueError("cov must be invertible for weighted_rmse.") from exc

    quad = float(r @ c_inv_r)
    if quad < 0.0 and abs(quad) < 1e-12:
        quad = 0.0
    if quad < 0.0:
        raise ValueError(
            "Quadratic form r^T C^-1 r must be non-negative; "
            "check covariance input."
        )

    return float(sqrt(quad / r.shape[0]))


def blockwise_delta_chi2_from_loglike_blocks(
    block_loglikes_at_train: Mapping[str, float],
    block_loglikes_at_test: Mapping[str, float],
) -> dict[str, object]:
    """Compute blockwise held-out Delta chi^2 with aggregate consistency check."""

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
    for block in sorted(train_keys):
        by_block[block] = delta_chi2_from_loglike(
            float(block_loglikes_at_train[block]),
            float(block_loglikes_at_test[block]),
        )

    total_from_blocks = float(sum(by_block.values()))
    total_from_aggregate = delta_chi2_from_loglike(
        float(sum(block_loglikes_at_train.values())),
        float(sum(block_loglikes_at_test.values())),
    )
    if not np.isclose(total_from_blocks, total_from_aggregate, rtol=1e-12, atol=1e-12):
        raise ValueError(
            "Blockwise decomposition mismatch: total does not equal sum(by_block). "
            f"total_from_blocks={total_from_blocks}, "
            f"total_from_aggregate={total_from_aggregate}."
        )

    return {
        "total": total_from_blocks,
        "by_block": by_block,
    }
