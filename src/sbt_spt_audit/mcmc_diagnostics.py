"""Rank and quantile diagnostics for actual sequential MCMC draws.

ArviZ is optional; arbitrary importance weights are not Markov holding times.
No threshold provides a mathematical convergence certificate.
"""
from __future__ import annotations

import numpy as np
from .mcmc import expand_chain, weighted_quantile


def rank_tail_diagnostics(chains, quantile=.95, quantile_mcse_limit=.001):
    import arviz as az

    if not 0 < quantile < 1 or not np.isfinite(quantile_mcse_limit) or quantile_mcse_limit <= 0:
        raise ValueError('A quantile in (0,1) and positive finite MCSE limit are required.')
    expanded = [expand_chain(v, w) for v, w in chains]
    if not expanded or min(len(c) for c in expanded) < 8:
        raise ValueError('Each chain needs at least eight represented steps.')
    n = min(len(c) for c in expanded)
    # Keep the last n draws of each chain. Report every dropped prefix.
    # Full-data quantile and chronological-half checks retain the whole record.
    draws = np.stack([c[-n:] for c in expanded])
    full = np.concatenate(expanded)
    full_q = weighted_quantile(full, np.ones(full.size), quantile)
    retained_q = weighted_quantile(draws.ravel(), np.ones(draws.size), quantile)
    first = np.concatenate([c[:len(c)//2] for c in expanded])
    second = np.concatenate([c[len(c)//2:] for c in expanded])
    half_difference = abs(weighted_quantile(first, np.ones(first.size), quantile)
                          - weighted_quantile(second, np.ones(second.size), quantile))
    estimates = {
        'rank_folded_split_rhat': float(az.rhat(draws, method='rank')),
        'bulk_ess': float(az.ess(draws, method='bulk')),
        'tail_ess_05_95': float(az.ess(draws, method='tail', prob=(.05, .95))),
        'quantile_ess': float(az.ess(draws, method='quantile', prob=quantile)),
        'quantile_mcse': float(az.mcse(draws, method='quantile', prob=quantile)),
    }
    warnings = []
    if len(expanded) < 2:
        warnings.append('Fewer than two separately initialized chains; split halves do not supply independent starts.')
    for k, v in estimates.items():
        if not np.isfinite(v):
            warnings.append(f'Nonfinite diagnostic: {k}')
    if estimates['rank_folded_split_rhat'] > 1.01:
        warnings.append('Rank/folded split Rhat exceeds 1.01.')
    if min(estimates['bulk_ess'], estimates['tail_ess_05_95'], estimates['quantile_ess']) < 400:
        warnings.append('Bulk, tail, or quantile ESS is below 400.')
    if estimates['quantile_mcse'] > quantile_mcse_limit:
        warnings.append('Quantile MCSE exceeds the declared precision target.')
    if estimates['quantile_mcse'] <= 0:
        warnings.append('Zero quantile MCSE from tied empirical order statistics does not establish continuous-posterior precision.')
    precision = estimates['quantile_mcse']
    if not np.isfinite(precision):
        precision = quantile_mcse_limit
    # Drift and unequal-length deletion are distinct from stationary MCSE.
    if half_difference > 4 * max(precision, quantile_mcse_limit):
        warnings.append('Chronological quantile drift exceeds four times the precision scale.')
    if abs(full_q - retained_q) > 2 * max(precision, quantile_mcse_limit):
        warnings.append('Equal-length selection materially changes the quantile.')
    return {
        'method': 'ArviZ_rank_folded_split_rhat_bulk_tail_quantile_ESS_and_MCSE',
        'arviz_version': az.__version__, 'n_chains': len(expanded),
        'draws_per_chain': n,
        'dropped_prefix_draws_per_chain': [len(c) - n for c in expanded],
        'quantile_probability': quantile, 'quantile_full_draws': full_q,
        'quantile_retained_draws': retained_q, 'quantile_half_difference': half_difference,
        'quantile_mcse_limit': quantile_mcse_limit,
        'quantile_mcse_scope': 'population_quantile_estimated_from_equal_length_last_draws',
        **{k: v if np.isfinite(v) else None for k, v in estimates.items()},
        'diagnostic_thresholds_pass': not warnings,
        'mathematical_convergence_certificate': False,
        'warnings': warnings,
    }
