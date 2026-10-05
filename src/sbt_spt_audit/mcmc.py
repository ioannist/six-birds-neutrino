"""Posterior summaries and classical chronological MCMC diagnostics.

These are scalar diagnostics, not rank-normalized or multivariate convergence
certificates. Integer weights are holding times in a compressed Markov chain.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import fftconvolve


def mcmc_config_options(config):
    """Resolve the one supported sampler without silently losing its seed."""
    sampler = config.get('sampler')
    if not isinstance(sampler, dict) or len(sampler) != 1:
        raise ValueError('Exactly one MCMC sampler must be configured.')
    name, options = next(iter(sampler.items()))
    if name not in ('mcmc', 'sbt_spt_audit.samplers.FullPrecisionMCMC') or not isinstance(options, dict):
        raise ValueError('Unsupported MCMC sampler configuration.')
    return options


def require_unit_temperature(options):
    """Raw holding-time summaries of the original posterior require T=1."""
    try:
        temperature = float(options.get('temperature', 1))
    except (TypeError, ValueError) as error:
        raise ValueError('Original-posterior summaries require sampler temperature=1.') from error
    if not np.isfinite(temperature) or temperature != 1:
        raise ValueError('Original-posterior summaries require sampler temperature=1; '
                         'raw tempered chains require an explicit cooling workflow.')


def validate_samples(values, weights):
    v, w = np.asarray(values, dtype=float), np.asarray(weights, dtype=float)
    if v.ndim != 1 or not v.size or v.shape != w.shape:
        raise ValueError("values and weights must have matching non-empty 1D shapes.")
    if not np.all(np.isfinite(v)) or not np.all(np.isfinite(w)) or np.any(w < 0) or not np.any(w > 0):
        raise ValueError("samples must be finite with non-negative weights and positive total weight.")
    return v[w > 0], w[w > 0]


def weighted_quantile(values, weights, q):
    """Inverse empirical CDF for binary64 weights and probability, without CDF rounding."""
    v, w = validate_samples(values, weights)
    if not np.isfinite(q) or not 0 <= q <= 1:
        raise ValueError("quantile must lie in [0, 1].")
    # A positive tail weight can disappear when added to a larger cumulative
    # weight. Endpoint quantiles still select the extremes of positive support.
    if q == 0:
        return float(v.min())
    if q == 1:
        return float(v.max())
    order = np.argsort(v)
    w = w[order]
    q_num, q_den = float(q).as_integer_ratio()
    if np.all(w == np.floor(w)) and np.max(w) < 2. ** 63:
        # Holding times have an exact, fast integer cumulative sum. If any
        # prefix overflows int64, fall through to arbitrary precision below.
        cdf = np.cumsum(w.astype(np.int64), dtype=np.int64)
        if np.all(cdf >= 0):
            total = int(cdf[-1])
            threshold = (q_num * total + q_den - 1) // q_den
            ix = int(np.searchsorted(cdf, threshold, side="left"))
            return float(v[order[ix]])
    # All finite binary64 weights are dyadic rationals. A common power-of-two
    # denominator gives exact integer mass, including fractional importance
    # weights and extreme dynamic ranges, without normalization or overflow.
    ratios = [float(weight).as_integer_ratio() for weight in w]
    common_den = max(den for _, den in ratios)
    masses = [num * (common_den // den) for num, den in ratios]
    threshold = (q_num * sum(masses) + q_den - 1) // q_den
    cumulative = 0
    for ix, mass in enumerate(masses):
        cumulative += mass
        if cumulative >= threshold:
            return float(v[order[ix]])
    raise RuntimeError("Positive empirical mass did not reach its quantile.")


def expand_chain(values, weights, max_steps=2_000_000):
    v, w = validate_samples(values, weights)
    if not np.all(w == np.floor(w)):
        raise ValueError("noninteger weights do not specify Markov holding times; sequential diagnostics unavailable.")
    if w.sum() > max_steps:
        raise ValueError("chain expansion exceeds diagnostic resource limit; summaries remain available.")
    return np.repeat(v, w.astype(np.int64))


def chronological_halves(chains, equalize=True):
    halves = []
    for x in chains:
        n = len(x) // 2
        if n < 4:
            raise ValueError("each chain needs at least 8 represented steps for split diagnostics.")
        halves.extend([np.asarray(x[:n]), np.asarray(x[-n:])])
    # Standard split Rhat requires the same length for all chains.
    if not equalize:
        return halves
    n = min(map(len, halves))
    return np.asarray([x[:n] for x in halves])


def _power_of_two_rescale(x):
    """Bound moment inputs without inexact multiplication at ordinary scales."""
    magnitude = float(np.max(np.abs(x)))
    if magnitude == 0:
        return x
    exponent = int(np.frexp(magnitude)[1])
    with np.errstate(under="ignore"):
        return np.ldexp(x, -exponent)


def holding_time_population_sd(chains):
    """Population SD of all represented draws, with scaled centered moments.

    Integer holding times and the usual per-chain expansion limit apply.
    Equal-length deletion is not used to set the full-history precision scale.
    """
    expanded = [expand_chain(v, w) for v, w in chains]
    if not expanded:
        raise ValueError("At least one chain is required for its population SD.")
    x = np.concatenate(expanded)
    if np.all(x == x[0]):
        return 0.0
    exponent = int(np.frexp(float(np.max(np.abs(x))))[1])
    with np.errstate(under="ignore"):
        centered = np.ldexp(x, -exponent)
        centered = centered - centered[0]
        offset_exponent = int(np.frexp(float(np.max(np.abs(centered))))[1])
        centered = np.ldexp(centered, -offset_exponent)
        sd = float(np.sqrt(np.mean((centered - centered.mean()) ** 2)))
        result = float(np.ldexp(sd, exponent + offset_exponent))
    if not np.isfinite(result):
        raise ValueError("Population SD is not representable as a finite binary64 output.")
    return result


def split_rhat(chains):
    xs = chronological_halves(chains)
    if not np.all(np.isfinite(xs)):
        raise ValueError("Rhat needs finite represented steps.")
    # One common scale preserves the ratio of between/within variances.
    xs = _power_of_two_rescale(xs)
    # Remove a common offset before computing small fluctuations around it.
    xs = _power_of_two_rescale(xs - xs[0, 0])
    n = xs.shape[1]
    constant = np.all(xs == xs[:, :1], axis=1)
    variances = np.var(xs, axis=1, ddof=1)
    means = np.mean(xs, axis=1)
    # A rounded mean of identical entries can manufacture a tiny variance.
    variances[constant] = 0.
    means[constant] = xs[constant, 0]
    within = float(np.mean(variances))
    between = 0. if np.all(means == means[0]) else float(n * np.var(means, ddof=1))
    if within == 0:
        return float("inf") if np.any(means != means[0]) else float("nan")
    var_hat = (n - 1) / n * within + between / n
    return float(np.sqrt(var_hat / within))


def ess_autocorr(values):
    """FFT autocorrelation with Geyer's initial positive monotone pair sum."""
    x = np.asarray(values, dtype=float)
    n = x.size
    if x.ndim != 1 or n < 20 or not np.all(np.isfinite(x)):
        raise ValueError("ESS needs at least 20 finite represented steps.")
    if np.all(x == x[0]):
        raise ValueError("zero variance; ESS undefined.")
    # Autocorrelation is invariant under a common positive scale. Power-of-two
    # scaling prevents overflow of the mean and FFT products, and avoids
    # underflow of the autocovariance for small but nonconstant sequences.
    x = _power_of_two_rescale(x)
    x = _power_of_two_rescale(x - x[0])
    x = x - x.mean()
    x = _power_of_two_rescale(x)
    acov = fftconvolve(x, x[::-1], mode="full")[n - 1:] / n
    if not np.all(np.isfinite(acov)):
        raise ValueError("nonfinite autocovariance; ESS unavailable.")
    if acov[0] <= 0:
        raise ValueError("zero variance; ESS undefined.")
    rho = acov / acov[0]
    pair_sum, previous = 0.0, float("inf")
    for k in range(0, n - 1, 2):
        pair = float(rho[k] + rho[k + 1])
        if pair <= 0:
            break
        previous = min(previous, pair)
        pair_sum += previous
    tau = max(1.0, -1.0 + 2.0 * pair_sum)
    return float(min(n, n / tau))
