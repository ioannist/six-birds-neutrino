"""Known-target and drift controls for the posterior diagnostic bridge."""
import numpy as np
import pytest

pytest.importorskip('arviz')
from sbt_spt_audit.mcmc_diagnostics import rank_tail_diagnostics


def test_independent_normal_chains_have_resolved_quantile():
    rng = np.random.default_rng(241)
    chains = [(rng.normal(size=5000), np.ones(5000)) for _ in range(4)]
    result = rank_tail_diagnostics(chains, quantile_mcse_limit=.03)
    assert result['diagnostic_thresholds_pass']
    assert result['rank_folded_split_rhat'] < 1.01
    assert result['tail_ess_05_95'] > 2000
    assert abs(result['quantile_full_draws'] - 1.64485) < .06


def test_chronological_drift_and_single_start_do_not_pass():
    rng = np.random.default_rng(242)
    chains = [(np.r_[rng.normal(size=2000), rng.normal(2., size=2000)],
               np.ones(4000)) for _ in range(4)]
    result = rank_tail_diagnostics(chains, quantile_mcse_limit=.03)
    assert not result['diagnostic_thresholds_pass']
    assert result['rank_folded_split_rhat'] > 1.1
    assert any('drift' in w for w in result['warnings'])
    single = rank_tail_diagnostics([chains[0]], quantile_mcse_limit=.03)
    assert any('separately initialized' in w for w in single['warnings'])


def test_fractional_importance_weights_are_not_markov_holding_times():
    with pytest.raises(ValueError, match='integer'):
        rank_tail_diagnostics([(np.arange(20.), np.full(20, .5))])
