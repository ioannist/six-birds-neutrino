"""Full covariance accounting for Gaussian residuals."""
from __future__ import annotations

import numpy as np

from .metrics import quadratic_contributions


def localize_quadratic_difference(cov, r_train, r_best, spec_by_bin, effective_ells, edges, best_cov=None):
    """Return heatmap, ranked groups, spectra, and exhaustive accounting.

    Bins outside the requested heatmap (including unknown spectra) are retained
    in ``unlocalized_deltaQ``. Native likelihood adjustments must be accounted
    separately by callers; residual Q need not equal -2 log L. If covariance
    depends on parameters, supply the covariance at each point.
    """
    if best_cov is None:
        best_cov = cov
    delta = quadratic_contributions(r_train, cov) - quadratic_contributions(r_best, best_cov)
    specs = np.asarray(spec_by_bin)
    ells = np.asarray(effective_ells, dtype=float)
    edges = np.asarray(edges, dtype=float)
    if specs.shape != delta.shape or ells.shape != delta.shape:
        raise ValueError("bin metadata must match residual vector shape.")
    if not np.all(np.isfinite(ells)) or edges.size < 2 or not np.all(np.diff(edges) > 0):
        raise ValueError("effective multipoles must be finite and edges strictly increasing.")
    spectra = [s for s in ["TT", "TE", "EE"] if np.any(specs == s)]
    covered = np.zeros(delta.size, dtype=bool)
    grid, groups = {}, []
    for spec in spectra:
        vals = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            mask = (specs == spec) & (ells >= lo) & (ells < hi)
            covered |= mask
            dq = float(np.sum(delta[mask]))
            vals.append(dq)
            if np.any(mask):
                groups.append({"spec": spec, "ell": [float(lo), float(hi)],
                               "deltaQ": dq, "n_bins": int(np.count_nonzero(mask))})
        grid[spec] = vals
    groups.sort(key=lambda g: g["deltaQ"], reverse=True)
    accounted = float(sum(sum(v) for v in grid.values()))
    remainder = float(np.sum(delta[~covered]))
    total = float(np.sum(delta))
    if not np.isclose(accounted + remainder, total, atol=1e-8, rtol=1e-10):
        raise ValueError("quadratic accounting failed to sum to full covariance statistic.")
    accounting = {
        "method": "r_i_times_full_precision_r_i_signed_cross_term_allocation",
        "deltaQ_full": total, "deltaQ_heatmap": accounted,
        "unlocalized_deltaQ": remainder,
        "n_bins_unlocalized": int(np.count_nonzero(~covered)),
        "accounting_error": accounted + remainder - total,
    }
    return grid, groups[:10], spectra, accounting
