"""Analytic linear-response and false-target controls for proposal construction."""
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip('cobaya')
pytest.importorskip('pybobyqa')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_cmb_bao_proposal import fisher_gram, regularized_proposal
from build_cmb_bao_proposal import gaussian_completion_residuals, PLIK
from types import SimpleNamespace


def test_linear_gaussian_precision_and_parameter_units():
    jac = np.array([[1., 2.], [0., 1.]])
    precision = fisher_gram(jac, np.eye(2))
    covariance, meta = regularized_proposal(precision, [2., 3.])
    assert covariance == pytest.approx(np.array([[20., -12.], [-12., 9.]]))
    assert meta['n_regularized_directions'] == 0


def test_rank_deficiency_produces_only_a_regularized_proposal():
    covariance, meta = regularized_proposal(np.diag([2., 0.]), [1., 1.])
    assert np.linalg.eigvalsh(covariance).min() > 0
    assert meta['n_regularized_directions'] == 1
    with pytest.raises(ValueError, match='semidefinite'):
        regularized_proposal(np.diag([2., -.1]), [1., 1.])
    with pytest.raises(ValueError, match='symmetric'):
        regularized_proposal([[1., 1.], [0., 1.]], [1., 1.])


def test_planck_calibration_response_matches_known_correlated_gaussian():
    like = SimpleNamespace(used_bins=[np.array([0, 1]), [], []],
                           blmin=np.array([1, 2]), blmax=np.array([1, 2]),
                           weights=np.array([0., 1., 1.]), X_data=np.array([1., 2.]),
                           calibration_param='A_planck', cov=np.array([[4., 1.], [1., 2.]]))
    model = SimpleNamespace(likelihood={PLIK: like},
        provider=SimpleNamespace(get_Cl=lambda **kwargs: {'tt': np.array([0., 8., 20.])}))
    result = gaussian_completion_residuals(model, {'A_planck': 2.}, {PLIK: -16./7.})
    assert result[PLIK][0] == pytest.approx([-1., -3.])
    with pytest.raises(ValueError, match='bridge failed'):
        gaussian_completion_residuals(model, {'A_planck': 2.}, {PLIK: -100.})
