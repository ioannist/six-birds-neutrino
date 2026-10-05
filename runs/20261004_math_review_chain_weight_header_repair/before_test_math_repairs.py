from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from sbt_spt_audit.localization import localize_quadratic_difference
from sbt_spt_audit.metrics import covariance_solve, quadratic_contributions, weighted_rmse, rmse, delta_chi2_from_loglike
from sbt_spt_audit.mcmc import expand_chain, split_rhat, weighted_quantile, ess_autocorr
from sbt_spt_audit.likelihoods.desi_dr2_bao import load_desi_dr2_dataset
from sbt_spt_audit.candl_support import compute_gaussian_residual_and_covariance, gaussian_native_adjustment

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from toy_truncated_gaussian import (
    truncated_gaussian_pdf, combine_gaussians, boundary_mode_probability,
)
import extract_mnu_limits
import diagnose_cobaya_chains
import compare_mnu_posteriors
import run_cross_audit_profiled as profiled
import run_template_rewrite as rewrite


def _write_temperature_chain(root, sampler_name, seed, temperature):
    import json
    import yaml
    (root / 'chains').mkdir(parents=True)
    prefix = root / 'chains' / 'sample'
    options = {'seed': seed}
    if temperature is not None:
        options['temperature'] = temperature
    cfg = {'output': str(prefix), 'likelihood': {}, 'theory': {},
           'params': {'mnu': {'prior': {'min': 0, 'max': 5}}},
           'sampler': {sampler_name: options}}
    (root / 'resolved.yaml').write_text(yaml.safe_dump(cfg))
    # Deterministic half-normal coordinates: heating widens the distribution.
    value = norm.ppf(.5 + .5 * (np.arange(40) + .5) / 40) * np.sqrt(temperature or 1)
    np.savetxt(str(prefix) + '.1.txt', np.column_stack([np.ones(40),
               value ** 2 / (2 * (temperature or 1)), value]),
               header='weight minuslogpost mnu')
    (root / 'metrics.json').write_text(json.dumps({'burnin_frac': .2}))
    return prefix


@pytest.mark.parametrize('mode', ['different_builds', 'recorded_and_unknown', 'conflicting_records', 'declared_without_record', 'malformed_record'])
@pytest.mark.parametrize('solver', ['classy', 'camb'])
def test_chain_diagnostics_reject_incompatible_native_backend_evidence(tmp_path, monkeypatch, mode, solver):
    import json
    import yaml
    runs = [tmp_path / 'first', tmp_path / 'second']
    for seed, run in enumerate(runs, 11):
        _write_temperature_chain(run, 'mcmc', seed, 1)
        path = run / 'resolved.yaml'
        cfg = yaml.safe_load(path.read_text())
        cfg['theory'] = {solver: {'path': 'global'}}
        path.write_text(yaml.safe_dump(cfg))
    (runs[0] / 'solver_backend.json').write_text(json.dumps({'module_sha256': 'a' * 64}))
    if mode == 'different_builds':
        (runs[1] / 'runtime_state.json').write_text(json.dumps({'module_sha256': 'b' * 64}))
    if mode == 'conflicting_records':
        (runs[0] / 'runtime_state.json').write_text(json.dumps({'module_sha256': 'b' * 64}))
    if mode == 'declared_without_record':
        path = runs[1] / 'resolved.yaml'
        cfg = yaml.safe_load(path.read_text())
        cfg['notes'] = {solver + '_backend': {'module_sha256': 'a' * 64}}
        path.write_text(yaml.safe_dump(cfg))
    if mode == 'malformed_record':
        (runs[1] / 'runtime_state.json').write_text(json.dumps({'module_sha256': 'invalid'}))
    monkeypatch.setattr(sys, 'argv', ['diagnose', '--run-dir', str(runs[0]), '--run-dir', str(runs[1]),
                                   '--output', str(tmp_path / 'diagnostics.json')])
    with pytest.raises(ValueError, match='backend'):
        diagnose_cobaya_chains.main()
    assert not (tmp_path / 'diagnostics.json').exists()


@pytest.mark.parametrize('solver', ['classy', 'camb'])
@pytest.mark.parametrize('version', [None, '1.6.5'])
def test_chain_diagnostics_preserve_matching_recorded_backend(tmp_path, monkeypatch, solver, version):
    import json
    import yaml
    runs = [tmp_path / 'first', tmp_path / 'second']
    for seed, run in enumerate(runs, 11):
        _write_temperature_chain(run, 'mcmc', seed, 1)
        path = run / 'resolved.yaml'
        cfg = yaml.safe_load(path.read_text())
        cfg['theory'] = {solver: {'path': 'global'}}
        cfg['notes'] = {solver + '_backend': {'module_sha256': 'a' * 64, 'solver_version': version}}
        path.write_text(yaml.safe_dump(cfg))
        (run / 'runtime_state.json').write_text(json.dumps({'module': f'/different/path/{seed}',
                                                         'module_sha256': 'a' * 64, 'solver_version': version}))
    output = tmp_path / 'diagnostics.json'
    monkeypatch.setattr(sys, 'argv', ['diagnose', '--run-dir', str(runs[0]), '--run-dir', str(runs[1]),
                                   '--output', str(output)])
    assert diagnose_cobaya_chains.main() == 0
    result = json.loads(output.read_text())
    assert len(result['native_backend_provenance']) == 2
    assert {r['module_sha256'] for r in result['native_backend_provenance']} == {'a' * 64}
    assert {r['solver_version'] for r in result['native_backend_provenance']} == {version}
    assert result['native_backend_identity_scope'] == 'recorded_native_module_hash_agreement_not_uniform_solver_accuracy'


@pytest.mark.parametrize('solver', ['classy', 'camb'])
def test_legacy_chain_diagnostics_report_unrecorded_backend_assumption(tmp_path, monkeypatch, solver):
    import json
    import yaml
    runs = [tmp_path / 'first', tmp_path / 'second']
    for seed, run in enumerate(runs, 11):
        _write_temperature_chain(run, 'mcmc', seed, 1)
        path = run / 'resolved.yaml'
        cfg = yaml.safe_load(path.read_text())
        cfg.update(theory={solver: {'path': 'global'}}, notes=None)
        path.write_text(yaml.safe_dump(cfg))
    output = tmp_path / 'diagnostics.json'
    monkeypatch.setattr(sys, 'argv', ['diagnose', '--run-dir', str(runs[0]), '--run-dir', str(runs[1]),
                                   '--output', str(output)])
    assert diagnose_cobaya_chains.main() == 0
    result = json.loads(output.read_text())
    assert result['native_backend_identity_scope'] == 'unrecorded_native_builds_target_identity_assumed'
    assert all(r['module_sha256'] is None for r in result['native_backend_provenance'])


@pytest.mark.parametrize('mode', ['different_versions', 'recorded_and_unknown_version',
                                  'conflicting_version_records', 'declared_version_without_record'])
def test_camb_diagnostics_reject_incompatible_recorded_versions(tmp_path, monkeypatch, mode):
    import json
    import yaml
    runs = [tmp_path / 'first', tmp_path / 'second']
    for seed, run in enumerate(runs, 11):
        prefix = _write_temperature_chain(run, 'mcmc', seed, 1)
        cfg_path = run / 'resolved.yaml'
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg['theory'] = {'camb': {}}
        if mode == 'declared_version_without_record':
            cfg['notes'] = {'camb_backend': {'module_sha256': 'a' * 64, 'solver_version': '1.6.5'}}
        cfg_path.write_text(yaml.safe_dump(cfg))
        (run / 'solver_backend.json').write_text(json.dumps({'module_sha256': 'a' * 64}))
        version = '1.6.5' if seed == 11 else '2.0.4'
        if mode == 'conflicting_version_records':
            version = '1.6.5'
            (run / 'runtime_state.json').write_text(json.dumps({'solver_version': '2.0.4'}))
        if mode not in ['recorded_and_unknown_version', 'declared_version_without_record'] or seed == 11:
            Path(str(prefix)+'.updated.yaml').write_text(yaml.safe_dump({'theory': {'camb': {'version':version}}}))
    output = tmp_path / 'diagnostics.json'
    monkeypatch.setattr(sys, 'argv', ['diagnose', '--run-dir', str(runs[0]), '--run-dir', str(runs[1]), '--output', str(output)])
    with pytest.raises(ValueError, match='backend'):
        diagnose_cobaya_chains.main()
    assert not output.exists()


@pytest.mark.parametrize('sampler_name', ['mcmc', 'sbt_spt_audit.samplers.FullPrecisionMCMC'])
@pytest.mark.parametrize('workflow', ['diagnose', 'extract', 'compare'])
def test_original_posterior_workflows_reject_tempered_target(tmp_path, monkeypatch,
                                                          sampler_name, workflow):
    cold, heated = tmp_path / 'cold', tmp_path / 'heated'
    _write_temperature_chain(cold, sampler_name, 11, 1)
    _write_temperature_chain(heated, sampler_name, 12, 2)
    if workflow == 'diagnose':
        argv = ['diagnose', '--run-dir', str(cold), '--run-dir', str(heated),
                '--output', str(tmp_path / 'diagnostics.json')]
        main = diagnose_cobaya_chains.main
    elif workflow == 'extract':
        argv = ['extract', '--run_dir', str(heated), '--output', str(tmp_path / 'summary.json')]
        main = extract_mnu_limits.main
    else:
        argv = ['compare', '--run2018', str(cold), '--runD1', str(heated),
                '--outdir', str(tmp_path / 'comparison')]
        # Rendering is irrelevant to the target contract; without the guard,
        # the workflow would emit a comparison of the two different targets.
        from types import SimpleNamespace
        monkeypatch.setattr(compare_mnu_posteriors, '_load_density',
                            lambda *args: SimpleNamespace(x=np.array([0., 1.]), P=np.ones(2)))
        main = compare_mnu_posteriors.main
    monkeypatch.setattr(sys, 'argv', argv)
    with pytest.raises(ValueError, match='temperature=1'):
        main()


@pytest.mark.parametrize('sampler_name', ['mcmc', 'sbt_spt_audit.samplers.FullPrecisionMCMC'])
def test_default_and_explicit_unit_temperature_keep_same_empirical_quantiles(tmp_path,
                                                                          monkeypatch,
                                                                          sampler_name):
    import json
    results = []
    for index, temperature in enumerate([None, 1]):
        root = tmp_path / str(index)
        _write_temperature_chain(root, sampler_name, index + 1, temperature)
        output = root / 'summary.json'
        monkeypatch.setattr(sys, 'argv', ['extract', '--run_dir', str(root), '--output', str(output)])
        assert extract_mnu_limits.main() == 0
        results.append(json.loads(output.read_text()))
    for key in ['mnu_median', 'mnu_p95_upper', 'mnu_mode', 'boundary_fraction']:
        assert results[0][key] == results[1][key]


@pytest.mark.parametrize('case', ['duplicate_header', 'duplicate_paramnames', 'duplicate_extra_header'])
def test_chain_loader_rejects_conflicting_parameter_identity(tmp_path, case):
    prefix = tmp_path / 'sample'
    if case == 'duplicate_paramnames':
        # Removing GetDist's derived marker exposes the same coordinate label.
        Path(str(prefix) + '.paramnames').write_text('mnu mass1\nmnu* mass2\n')
        header = ''
    else:
        header = '# weight minuslogpost mnu mnu\n'
    if case == 'duplicate_extra_header':
        # Even a unique metadata prefix cannot disambiguate the complete header.
        Path(str(prefix) + '.paramnames').write_text('mnu mass\n')
    Path(str(prefix) + '.1.txt').write_text(header + '1 0 .02 4.9\n2 0 .03 4.8\n')
    with pytest.raises(ValueError, match='unique'):
        extract_mnu_limits._load_chains_raw(prefix, 'mnu', 0)


def test_chain_diagnostics_reject_ambiguous_mass_before_reporting(tmp_path, monkeypatch):
    run = tmp_path / 'run'
    prefix = _write_temperature_chain(run, 'mcmc', 11, 1)
    Path(str(prefix) + '.1.txt').write_text('# weight minuslogpost mnu mnu\n1 0 .02 4.9\n')
    output = tmp_path / 'diagnostics.json'
    monkeypatch.setattr(sys, 'argv', ['diagnose', '--run-dir', str(run), '--output', str(output)])
    with pytest.raises(ValueError, match='unique'):
        diagnose_cobaya_chains.main()
    assert not output.exists()


@pytest.mark.parametrize('case', ['duplicate_paramnames', 'conflicting_header'])
def test_density_loader_rejects_conflicting_mass_identity_before_getdist(tmp_path, monkeypatch, case):
    import getdist.mcsamples as backend
    prefix = tmp_path / 'sample'
    metadata = 'mnu mass\nmnu* duplicated_mass\n' if case == 'duplicate_paramnames' else 'other other\nmnu mass\n'
    Path(str(prefix) + '.paramnames').write_text(metadata)
    Path(str(prefix) + '.1.txt').write_text(
        '# weight minuslogpost mnu other\n1 0 .02 4.9\n2 0 .03 4.8\n')
    def forbidden(*args, **kwargs):
        pytest.fail('GetDist must not interpret a chain with conflicting coordinate identity.')
    monkeypatch.setattr(backend, 'loadMCSamples', forbidden)
    with pytest.raises(ValueError, match='unique|disagree'):
        compare_mnu_posteriors._load_density(prefix, 0)


def test_correlated_localization_is_exhaustive_and_signed():
    cov = np.array([[1., .9], [.9, 1.]])
    r = np.array([1., 2.])
    terms = quadratic_contributions(r, cov)
    assert terms[0] < 0
    expected = float(r @ np.linalg.solve(cov, r))
    assert terms.sum() == pytest.approx(expected)
    assert expected != pytest.approx(5.)  # Separate marginal block inverses fail.
    grid, groups, specs, ledger = localize_quadratic_difference(
        cov, r, np.zeros(2), ['TT', 'EE'], [2500., 300.], [400., 3000.])
    assert ledger['n_bins_unlocalized'] == 1
    assert ledger['deltaQ_heatmap'] + ledger['unlocalized_deltaQ'] == pytest.approx(expected)


def test_localization_preserves_finite_group_when_coordinate_difference_overflows():
    covariance = np.array([[5., 2.], [2., 1.]])  # Positive definite, determinant one.
    train = np.full(2, np.sqrt(5e307))
    best = np.array([np.sqrt(1.5e308), 0.])
    with np.errstate(over='raise', invalid='raise'):
        grid, groups, _, ledger = localize_quadratic_difference(
            covariance, train, best, ['TT', 'TT'], [1000., 1000.], [400., 3000.])
    # Both endpoint Q values are finite; subtracting the first coordinate
    # contributions would overflow to -inf before the second cancels part of it.
    assert grid['TT'][0] == pytest.approx(-5e307, rel=2e-14)
    assert groups[0]['deltaQ'] == grid['TT'][0]
    assert ledger['deltaQ_full'] == ledger['deltaQ_heatmap'] == grid['TT'][0]
    assert ledger['accounting_error'] == 0


def test_localization_recovers_signed_sum_after_partial_sum_overflow():
    train = np.array([1e154, 1e154, 0., 0.])
    best = np.array([0., 0., 1e154, 1e154])
    grid, _, _, ledger = localize_quadratic_difference(
        np.eye(4), train, best, ['TT'] * 4, [1000.] * 4, [400., 3000.])
    assert grid['TT'][0] == ledger['deltaQ_full'] == ledger['deltaQ_heatmap'] == 0
    assert ledger['accounting_error'] == 0


def test_localization_rejects_unrepresentable_reported_group():
    covariance = np.array([[5., 2.], [2., 1.]])
    train = np.full(2, np.sqrt(5e307))
    best = np.array([np.sqrt(1.5e308), 0.])
    with pytest.raises(ValueError, match='not representable'):
        localize_quadratic_difference(covariance, train, best, ['TT', 'EE'],
                                     [1000., 1000.], [400., 3000.])


@pytest.mark.parametrize('edges', [[400., np.inf], [[400., 800.], [1200., 3000.]]])
def test_localization_requires_finite_vector_edges(edges):
    with pytest.raises(ValueError, match='finite, 1D'):
        localize_quadratic_difference(np.eye(2), np.ones(2), np.zeros(2),
                                     ['TT', 'TT'], [1000., 1000.], edges)


def test_localization_cannot_broadcast_different_endpoint_dimensions():
    with pytest.raises(ValueError, match='matching shape'):
        localize_quadratic_difference(np.eye(1), np.ones(1), np.ones(2),
                                     ['TT', 'TT'], [1000., 1000.], [400., 3000.], best_cov=np.eye(2))


@pytest.mark.parametrize('cov', [np.array([[1., 2.], [2., 1.]]),
                                np.array([[1., 2.], [0., 1.]]),
                                np.array([[1., 0.], [0., 0.]]),
                                np.array([[np.nan, 0.], [0., 1.]])])
def test_invalid_covariance_cannot_define_a_gaussian(cov):
    with pytest.raises(ValueError):
        weighted_rmse(np.ones(2), cov)


@pytest.mark.parametrize('subnormal_units', [1, 3, 17])
def test_exact_symmetric_subnormal_variance_is_not_erased_by_projection(subnormal_units):
    variance = subnormal_units * np.nextafter(0., 1.)
    covariance = np.array([[variance]])
    residual = np.array([variance])
    # The native Cholesky factor and solve are representable; no inverse is
    # needed. Rejecting this positive covariance is a projection failure.
    with np.errstate(under='raise', over='raise', invalid='raise'):
        solution = covariance_solve(covariance, residual)
    with np.errstate(under='ignore', over='raise', invalid='raise'):
        contributions = quadratic_contributions(residual, covariance)
    assert solution[0] == pytest.approx(1., rel=2e-14)
    assert contributions[0] == variance
    assert covariance[0, 0] == variance


def test_quantile_invariant_under_compressed_row_representation():
    assert weighted_quantile([0., 10.], [9., 1.], .95) == 10.
    assert weighted_quantile([0., 0., 10.], [4., 5., 1.], .95) == 10.
    assert weighted_quantile(np.repeat([0., 10.], [9, 1]), np.ones(10), .95) == 10.


def test_quantile_endpoints_preserve_tiny_positive_support_and_ignore_zero_weights():
    assert weighted_quantile([0., 10., 20.], [1., 1e-20, 0.], 1.) == 10.
    assert weighted_quantile([-20., -10., 0.], [0., 1e-20, 1.], 0.) == -10.


def test_quantile_row_splitting_at_cdf_threshold_is_exact_for_integer_and_fractional_mass():
    for scale in [1., 2. ** -10, 2. ** 60]:
        original = weighted_quantile([0., 10.], np.array([418., 22.]) * scale, .95)
        split = weighted_quantile([0., 0., 10.], np.array([201., 217., 22.]) * scale, .95)
        assert original == split == 0.
        assert weighted_quantile([0., 10.], np.array([418., 22.]) * scale,
                                 np.nextafter(.95, 1.)) == 10.
    # Each holding time fits int64, but their sum does not.
    assert weighted_quantile([0., 10.], np.array([7., 7.]) * 2. ** 60, .5) == 0.


def test_tiny_positive_middle_weight_can_determine_the_empirical_median():
    assert weighted_quantile([-1., 0., 1.], [1., 1e-20, 1.], .5) == 0.


def test_chronological_rhat_detects_drift_hidden_by_odd_even_split():
    x = np.r_[np.tile([0., 1.], 100), np.tile([10., 11.], 100)]
    assert split_rhat([x]) > 10.
    assert np.mean(x[::2]) == pytest.approx(np.mean(x[1::2]), abs=1.)
    compressed = expand_chain([0., 1., 10., 11.], [100, 100, 100, 100])
    assert split_rhat([compressed]) > 10.
    with pytest.raises(ValueError, match='noninteger'):
        expand_chain([0., 1.], [1.1, 2.])


@pytest.mark.parametrize('exponent', [700, -700])
def test_ess_is_invariant_to_extreme_power_of_two_units(exponent):
    sequence = np.sin(np.arange(512) / 17.)
    expected = ess_autocorr(sequence)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        actual = ess_autocorr(np.ldexp(sequence, exponent))
    assert actual == pytest.approx(expected, rel=1e-13)


def test_ess_handles_large_offset_and_subnormal_variation():
    ordinary = np.tile([.5, .75], 32)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        assert ess_autocorr(np.ldexp(ordinary, 1023)) == pytest.approx(ess_autocorr(ordinary))
    ordinary = np.tile([0., 1., 2., 3.], 32)
    subnormal = ordinary * np.nextafter(0., 1.)
    assert ess_autocorr(subnormal) == pytest.approx(ess_autocorr(ordinary), rel=1e-13)


@pytest.mark.parametrize('constant', [np.finfo(float).max, np.nextafter(0., 1.)])
def test_ess_rejects_constant_sequences_at_extreme_scales(constant):
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        with pytest.raises(ValueError, match='zero variance'):
            ess_autocorr(np.full(64, constant))


@pytest.mark.parametrize('exponent', [700, -700])
def test_classical_rhat_is_invariant_to_extreme_power_of_two_units(exponent):
    sequence = np.r_[np.tile([0., 1.], 100), np.tile([10., 11.], 100)]
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        actual = split_rhat([np.ldexp(sequence, exponent)])
    assert actual == pytest.approx(split_rhat([sequence]), rel=1e-13)
    assert actual > 10.


def test_classical_rhat_handles_subnormal_variation_and_rejects_nonfinite_draws():
    ordinary = np.tile([0., 1., 2., 3.], 32)
    subnormal = ordinary * np.nextafter(0., 1.)
    assert split_rhat([subnormal]) == pytest.approx(split_rhat([ordinary]), rel=1e-13)
    with pytest.raises(ValueError, match='finite represented steps'):
        split_rhat([np.r_[np.full(32, 1.), np.inf]])


def test_holding_times_affect_autocorrelation():
    rng = np.random.default_rng(23)
    iid = rng.normal(size=1000)
    assert ess_autocorr(np.repeat(iid, 20)) < 2 * ess_autocorr(iid)


def test_identical_decimal_draws_do_not_manufacture_autocorrelation_variance():
    with pytest.raises(ValueError, match='zero variance'):
        ess_autocorr(np.full(60, .1))


def test_classical_rhat_identical_decimal_draws_remain_undefined():
    assert np.isnan(split_rhat([np.full(60, .1), np.full(60, .1)]))


def test_classical_rhat_distinct_constant_chains_remain_infinite():
    assert np.isinf(split_rhat([np.full(60, .1), np.full(60, .2)]))


def test_classical_diagnostics_preserve_adjacent_float_variation_under_offset():
    sequence = np.tile([0., 1.], 30)
    translated = np.tile([.1, np.nextafter(.1, 1.)], 30)
    assert ess_autocorr(translated) == pytest.approx(ess_autocorr(sequence), rel=1e-13)
    assert split_rhat([translated] * 3) == pytest.approx(split_rhat([sequence] * 3), rel=1e-13)
    assert split_rhat([translated] * 3) == pytest.approx(np.sqrt(29/30), rel=1e-13)


def test_relocated_prefix_and_derived_paramnames(tmp_path):
    chains = tmp_path / 'chains'
    chains.mkdir()
    prefix = chains / 'sample.v1'
    (tmp_path / 'resolved.yaml').write_text('output: /missing/old/run/chains/sample.v1\n')
    Path(str(prefix) + '.1.txt').write_text('# weight minuslogpost mnu\n1 0 .1\n2 0 .2\n')
    Path(str(prefix) + '.paramnames').write_text('mnu* mass\n')
    assert extract_mnu_limits._resolve_prefix_from_run_dir(tmp_path) == prefix
    assert extract_mnu_limits._load_sequence_raw(prefix, 'mnu', 0)[0].tolist() == [.1, .2]


@pytest.mark.parametrize('mu,sigma', [(-12., 1.), (-40., 1.), (.5, .3), (0., 2.)])
def test_truncated_density_remains_normalized_in_negative_tail(mu, sigma):
    integral = quad(lambda x: float(truncated_gaussian_pdf(np.array(x), mu, sigma)), 0, np.inf)[0]
    assert integral == pytest.approx(1., abs=1e-8)
    assert truncated_gaussian_pdf(np.array([-1.]), mu, sigma)[0] == 0.


def test_combination_does_not_make_nonnegative_means_negative():
    mean, sigma = combine_gaussians(.1, 1e-200, .2, 1e-200)
    assert mean == pytest.approx(.15)
    assert np.isfinite(sigma) and sigma > 0
    assert boundary_mode_probability(.1, .02, .07, .03, .002) > boundary_mode_probability(.1, .02, .07, .03, .05)
    assert boundary_mode_probability(-.1, .02, .07, .03, .002) < boundary_mode_probability(-.1, .02, .07, .03, .05)


@pytest.mark.parametrize('sign', [1., -1.])
def test_finite_convex_gaussian_mean_with_binary64_intermediates(monkeypatch, sign):
    from fractions import Fraction
    first = sign * np.finfo(float).max
    second = np.array([first, .5 * first, -first])
    expected = [float((Fraction(float(first)) + Fraction(float(x))) / 2) for x in second]
    # Exercise platforms with no extended intermediate exponent range.
    monkeypatch.setattr(np, 'longdouble', np.float64)
    with np.errstate(over='raise', invalid='raise'):
        mean, sigma = combine_gaussians(first, 1., second, 1.)
    np.testing.assert_array_equal(mean, expected)
    np.testing.assert_allclose(sigma, 1 / np.sqrt(2), rtol=2e-16, atol=0)


@pytest.mark.parametrize('sign', [1., -1.])
def test_subnormal_precision_weight_preserves_mean_with_binary64_intermediates(monkeypatch, sign):
    from fractions import Fraction
    # The tiny weight is positive (about 1e-320), but has poor relative accuracy
    # in binary64. Multiplication by a large mean makes its contribution visible.
    small, large, mean = 1e-60, 1e100, sign * 1e300
    expected = float(Fraction(mean) * Fraction(small) ** 2 /
                     (Fraction(small) ** 2 + Fraction(large) ** 2))
    monkeypatch.setattr(np, 'longdouble', np.float64)
    with np.errstate(over='raise', invalid='raise'):
        actual, sigma = combine_gaussians(0., small, mean, large)
        swapped, swapped_sigma = combine_gaussians(mean, large, 0., small)
    assert actual == swapped == expected
    assert sigma == swapped_sigma == small


@pytest.mark.skipif(np.finfo(np.longdouble).maxexp <= np.finfo(float).maxexp,
                    reason='Needs finite inputs wider than binary64 output range.')
def test_combination_refuses_unrepresentable_mean_from_wider_scalar_input():
    with pytest.raises(ValueError, match='mean is not representable'):
        combine_gaussians(np.longdouble('1e400'), 1., 0., 1.)


@pytest.mark.skipif(np.finfo(np.longdouble).maxexp <= np.finfo(float).maxexp,
                    reason='Needs finite inputs wider than binary64 output range.')
def test_combination_refuses_zero_width_after_output_underflow():
    with pytest.raises(ValueError, match='standard deviation is not representable'):
        combine_gaussians(0., np.longdouble('1e-400'), 0., 1.)


def test_far_negative_density_preserves_finite_exponential_tail():
    # alpha=1e200: h(alpha)/alpha differs from one by less than 1e-400.
    # At x=k*1e-300, the limiting density is 1e300*exp(-k).
    density = truncated_gaussian_pdf(np.array([-1., 0., 1e-300, 2e-300]), -1e100, 1e-100)
    np.testing.assert_allclose(density / 1e300, [0., 1., np.exp(-1.), np.exp(-2.)],
                               rtol=1e-12, atol=0)


def test_truncated_density_refuses_nonfinite_readouts():
    with pytest.raises(ValueError, match='not representable'):
        truncated_gaussian_pdf(np.array([0.]), 0., np.nextafter(0., 1.))
    with pytest.raises(ValueError, match='NaN'):
        truncated_gaussian_pdf(np.array([np.nan]), 0., 1.)


def test_boundary_probability_does_not_overflow_valid_intermediate_ratios():
    assert boundary_mode_probability(0., 1e-200, .07, .03, 1e200) == pytest.approx(norm.cdf(.07/.03))
    assert boundary_mode_probability(1e-300, 1e-200, 1e100, 1e100, 1.) == pytest.approx(.5, abs=1e-14)


def test_tiny_precision_weight_can_still_shift_mode_by_one_combined_sigma():
    # The squared precision ratio underflows in binary64, but multiplying it
    # by the second mean gives a representable shift of one combined sigma.
    mean, sigma = combine_gaussians(0., 1e-100, np.array([1e300, -1e300]), 1e100)
    np.testing.assert_allclose(mean, [1e-100, -1e-100], rtol=1e-14, atol=0)
    np.testing.assert_allclose(sigma, 1e-100, rtol=1e-14, atol=0)
    assert mean[0] > 0  # A false zero would incorrectly select the boundary.
    swapped_mean, swapped_sigma = combine_gaussians(1e300, 1e100, 0., 1e-100)
    np.testing.assert_allclose(swapped_mean, mean[0], rtol=1e-14, atol=0)
    np.testing.assert_allclose(swapped_sigma, sigma, rtol=1e-14, atol=0)


@pytest.mark.parametrize('sign', [1., -1.])
def test_near_cancellation_preserves_gaussian_mean_and_boundary_classification(sign):
    epsilon = 2. ** -52
    second_width = 1. + epsilon
    # Numerator: sign * ((1 + epsilon)^2 - (1 + 2*epsilon))
    # = sign * epsilon^2, strictly nonzero even though wide arithmetic loses it.
    expected = sign * epsilon ** 2 / (2. + 2. * epsilon + epsilon ** 2)
    mean, width = combine_gaussians(sign, 1., -sign * (1. + 2. * epsilon), second_width)
    assert mean == pytest.approx(expected, rel=4e-16, abs=0)
    assert (mean > 0) == (sign > 0)
    swapped, swapped_width = combine_gaussians(-sign * (1. + 2. * epsilon), second_width, sign, 1.)
    assert swapped == pytest.approx(expected, rel=4e-16, abs=0)
    assert swapped_width == width
    zero, _ = combine_gaussians(sign, 1., -sign, 1.)
    assert zero == 0


@pytest.mark.parametrize('sign', [1., -1.])
def test_unrepresentable_nonzero_gaussian_mean_is_rejected(sign):
    smallest = np.nextafter(0., 1.)
    with pytest.raises(ValueError, match='mode sign would be lost'):
        combine_gaussians(0., smallest, sign * smallest, 2. * smallest)


@pytest.mark.parametrize('sign', [1., -1.])
def test_boundary_probability_retains_cancellation_before_standardization(sign):
    epsilon = 2. ** -52
    # The threshold is -sign * epsilon^2, exactly one offset SD from zero.
    result = boundary_mode_probability(sign, 1., sign * (2. + 2. * epsilon),
                                       epsilon ** 2, np.array([1. + epsilon]))
    assert result[0] == pytest.approx(norm.cdf(-sign), rel=1e-14, abs=0)


def test_all_vendored_bao_subsets_are_positive_definite():
    for subset in ['all', 'bgs', 'elg', 'lrg_z0', 'lrg_z1', 'lrg_elg', 'qso', 'lya']:
        dataset, metadata = load_desi_dr2_dataset(subset)
        assert dataset.points
        assert np.linalg.eigvalsh(dataset.cov).min() > 0


def test_profile_cannot_smuggle_missing_shared_parameter():
    with pytest.raises(ValueError, match='source fit'):
        profiled._shared_values_for_direction(['mnu'], {}, {'mnu': .06})
    assert profiled._bound_for_param('TT_CIBClustering_Alpha') == (None, None)


def test_signed_directional_difference_and_rmse_scaling():
    assert delta_chi2_from_loglike(-1., -2.) == -2.
    assert rmse(np.array([1e200, -1e200])) == pytest.approx(1e200)
    with pytest.raises(ValueError, match='overflow'):
        delta_chi2_from_loglike(-1e308, 1e308)


def test_rewrite_is_invariant_under_small_nonzero_template_scale(monkeypatch):
    # There is no mathematical near-zero exception for a nonzero template.
    monkeypatch.setattr(rewrite, '_template_vector', lambda r, c, m: (np.array([1e-12]), None))
    metrics, warnings = rewrite._direction_metrics(np.array([2.]), np.array([0.]),
                                                  np.array([0.]), np.eye(1), 'mode0')
    assert metrics['chi2_after'] == pytest.approx(0.)
    assert metrics['improvement'] == pytest.approx(4.)


def test_profile_reference_releases_shared_parameters_and_keeps_frozen_values(monkeypatch):
    # Native log L maximum: shared=2, nuisance=shared, frozen=7.
    def evaluate(like_obj, base_params, overrides):
        p = overrides
        assert p['frozen'] == 7.
        return -((p['shared'] - 2.) ** 2 + (p['nuisance'] - p['shared']) ** 2)
    monkeypatch.setattr(profiled, 'evaluate_loglike_from_base', evaluate)
    ctx = profiled.LensContext('test', 'fake', None,
                              {'shared': 0., 'nuisance': 0., 'frozen': 1.},
                              ['shared', 'nuisance', 'frozen'],
                              {'shared': 0., 'nuisance': 0., 'frozen': 7.}, {})
    cross = profiled._profile_test_lens(ctx, {'shared': 0.}, ['nuisance'], 100)
    best = profiled._profile_test_lens(ctx, {}, ['nuisance', 'shared'], 100,
                                     initial_params=cross.params)
    assert cross.loglike == pytest.approx(-4.)
    assert best.loglike == pytest.approx(0., abs=1e-8)
    assert best.params['frozen'] == 7.


def test_beam_covariance_and_hartlap_are_included_in_accounting():
    class FakeLike:
        _data_bandpowers = np.array([4., 5.])
        covariance = np.eye(2)
        beam_correlation = np.eye(2) * .1
        data_set_dict = {'likelihood_form': 'gaussian_beam_detcov',
                         'hartlap_correction': {'N_sims': 11}}
        N_bins_total = 2
        def get_model_specs(self, pars):
            return np.array([2., 3.])
        def bin_model_specs(self, model):
            return model
        def prior_logl(self, pars):
            return 3.
        def log_like(self, pars):
            cov = np.diag(np.array([1.4, 1.9]) / .7)
            return -.5 * (np.array([2., 2.]) @ np.linalg.solve(cov, np.array([2., 2.]))
                          + np.linalg.slogdet(cov)[1]) - 3.
    r, c = compute_gaussian_residual_and_covariance(FakeLike(), {})
    assert r.tolist() == [2., 2.]
    assert np.diag(c) == pytest.approx(np.array([1.4, 1.9]) / .7)
    bridge = gaussian_native_adjustment(FakeLike(), {}, {}, r, c)
    assert bridge['prior_penalty'] == 6.
    assert bridge['native_reconstruction_error'] == pytest.approx(0., abs=1e-12)
    best_cov = np.eye(2)
    grid, groups, specs, ledger = localize_quadratic_difference(
        c, r, np.ones(2), ['TT', 'TE'], [500., 500.], [400., 600.], best_cov=best_cov)
    assert ledger['deltaQ_full'] == pytest.approx(float(r @ np.linalg.solve(c, r)) - 2.)
