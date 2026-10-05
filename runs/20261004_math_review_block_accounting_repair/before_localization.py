"""Full covariance accounting for Gaussian residuals."""
from __future__ import annotations

from fractions import Fraction
from itertools import chain
from math import fsum, isfinite

import numpy as np

from .metrics import quadratic_contributions


def _finite_signed_sum(values):
    """Accumulate a finite signed sum; recover intermediate overflow."""
    numbers = [float(value) for value in values]
    if any(not isfinite(value) for value in numbers):
        raise ValueError("quadratic accounting requires finite signed inputs.")
    try:
        result = fsum(numbers)
    except OverflowError:
        exact = sum((Fraction(value) for value in numbers), Fraction(0))
        try:
            result = float(exact)
        except OverflowError as exc:
            raise ValueError("quadratic accounting is not representable as a finite binary64 output.") from exc
    if not isfinite(result):
        raise ValueError("quadratic accounting is not representable as a finite binary64 output.")
    return result


def localize_quadratic_difference(cov, r_train, r_best, spec_by_bin, effective_ells, edges, best_cov=None):
    """Return heatmap, ranked groups, spectra, and exhaustive accounting.

    Bins outside the requested heatmap (including unknown spectra) are retained
    in ``unlocalized_deltaQ``. Native likelihood adjustments must be accounted
    separately by callers; residual Q need not equal -2 log L. If covariance
    depends on parameters, supply the covariance at each point.
    """
    if best_cov is None:
        best_cov = cov
    train = quadratic_contributions(r_train, cov)
    best = quadratic_contributions(r_best, best_cov)
    if train.shape != best.shape:
        raise ValueError("train and reference residual vectors must have matching shape.")
    specs = np.asarray(spec_by_bin)
    ells = np.asarray(effective_ells, dtype=float)
    edges = np.asarray(edges, dtype=float)
    if specs.shape != train.shape or ells.shape != train.shape:
        raise ValueError("bin metadata must match residual vector shape.")
    if (not np.all(np.isfinite(ells)) or edges.ndim != 1 or edges.size < 2
            or not np.all(np.isfinite(edges)) or not np.all(edges[1:] > edges[:-1])):
        raise ValueError("effective multipoles must be finite; edges must be finite, 1D, and strictly increasing.")

    def difference(mask):
        # Sum the actual endpoint allocations before forming a rounded group
        # difference. Individual coordinate differences can overflow even when
        # the requested group difference and both endpoint Q values are finite.
        return _finite_signed_sum(chain(train[mask], (-float(value) for value in best[mask])))
    spectra = [s for s in ["TT", "TE", "EE"] if np.any(specs == s)]
    covered = np.zeros(train.size, dtype=bool)
    grid, groups = {}, []
    for spec in spectra:
        vals = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            mask = (specs == spec) & (ells >= lo) & (ells < hi)
            covered |= mask
            dq = difference(mask)
            vals.append(dq)
            if np.any(mask):
                groups.append({"spec": spec, "ell": [float(lo), float(hi)],
                               "deltaQ": dq, "n_bins": int(np.count_nonzero(mask))})
        grid[spec] = vals
    groups.sort(key=lambda g: g["deltaQ"], reverse=True)
    accounted = _finite_signed_sum(chain.from_iterable(grid.values()))
    remainder = difference(~covered)
    total = difference(np.ones(train.size, dtype=bool))
    error = _finite_signed_sum([accounted, remainder, -total])
    if abs(error) > 1e-8 + 1e-10 * abs(total):
        raise ValueError("quadratic accounting failed to sum to full covariance statistic.")
    accounting = {
        "method": "r_i_times_full_precision_r_i_signed_cross_term_allocation",
        "deltaQ_full": total, "deltaQ_heatmap": accounted,
        "unlocalized_deltaQ": remainder,
        "n_bins_unlocalized": int(np.count_nonzero(~covered)),
        "accounting_error": error,
    }
    return grid, groups[:10], spectra, accounting
