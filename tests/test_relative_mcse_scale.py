"""Known moments and unit changes for the empirical precision-scale bridge."""
import json
from pathlib import Path
import sys

import numpy as np
import pytest
import yaml

from sbt_spt_audit.mcmc import holding_time_population_sd


@pytest.mark.parametrize('magnitude', [1e200, 1e-200, np.finfo(float).max])
def test_finite_population_sd_survives_unrepresentable_variance(magnitude):
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        sd = holding_time_population_sd([(np.array([-magnitude, magnitude]), np.ones(2))])
    assert sd == pytest.approx(magnitude, rel=2e-15, abs=0)


def test_population_sd_uses_holding_times_across_unequal_chains():
    # Four represented draws: [-2,-2,-2,2], mean -1, variance 3.
    chains = [(np.array([-2.]), np.array([3.])), (np.array([2.]), np.array([1.]))]
    assert holding_time_population_sd(chains) == pytest.approx(np.sqrt(3.), rel=2e-15)
    with pytest.raises(ValueError, match='integer'):
        holding_time_population_sd([(np.array([-2., 2.]), np.array([.5, 1.5]))])


def test_population_sd_preserves_constant_and_adjacent_float_histories():
    assert holding_time_population_sd([(np.full(60, .1), np.ones(60))]) == 0
    low = 1e300
    high = np.nextafter(low, np.inf)
    assert holding_time_population_sd([(np.array([low, high]), np.ones(2))]) == (high - low) / 2
    unit = np.nextafter(0., 1.)
    assert holding_time_population_sd([(np.array([0., 4*unit]), np.ones(2))]) == 2*unit


@pytest.mark.parametrize('exponent', [700, -700])
def test_diagnostic_cli_preserves_relative_precision_under_unit_changes(tmp_path, monkeypatch, exponent):
    pytest.importorskip('arviz')
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
    import diagnose_cobaya_chains

    rng = np.random.default_rng(20261004)
    samples = [rng.normal(size=2000) for _ in range(4)]
    reports = []
    for label, power in [('ordinary', 0), ('scaled', exponent)]:
        command = ['diagnose']
        for seed, x in enumerate(samples, 101):
            run = tmp_path / label / str(seed)
            (run / 'chains').mkdir(parents=True)
            prefix = run / 'chains' / 'sample'
            cfg = {'output': str(prefix), 'likelihood': {}, 'theory': {},
                   'params': {'x': {'prior': {'dist': 'norm', 'loc': 0, 'scale': float(np.ldexp(1., power))}}},
                   'sampler': {'mcmc': {'seed': seed}}}
            (run / 'resolved.yaml').write_text(yaml.safe_dump(cfg))
            np.savetxt(str(prefix) + '.1.txt', np.column_stack([np.ones(x.size), np.zeros(x.size), np.ldexp(x, power)]),
                       header='weight minuslogpost x')
            command += ['--run-dir', str(run)]
        output = tmp_path / (label + '.json')
        command += ['--burnin-frac', '0', '--output', str(output)]
        monkeypatch.setattr(sys, 'argv', command)
        assert diagnose_cobaya_chains.main() == 0
        reports.append(json.loads(output.read_text())['diagnostics']['x'])
    ordinary, scaled = reports
    assert ordinary['diagnostic_thresholds_pass'] and scaled['diagnostic_thresholds_pass']
    assert scaled['quantile_mcse_limit'] == pytest.approx(np.ldexp(ordinary['quantile_mcse_limit'], exponent), rel=2e-15, abs=0)
    assert scaled['rank_folded_split_rhat'] == ordinary['rank_folded_split_rhat']
    assert scaled['quantile_ess'] == ordinary['quantile_ess']
