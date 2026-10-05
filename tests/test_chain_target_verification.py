"""False-target control for fresh chain likelihood reconstruction."""
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest
pytest.importorskip('cobaya')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_chain_targets import compare_native_row


def test_independently_reconstructed_gaussian_detects_wrong_recorded_target():
    def logposterior(point, cached):
        assert cached is False
        x = point['x']
        # Uniform probability density 1/2 on [-1,1], two Gaussian factors.
        prior = -np.log(2.)
        likes = [-x*x/2, -(x-.5)**2/2]
        return SimpleNamespace(logpost=prior+sum(likes), logpriors=[prior], loglikes=likes)
    model = SimpleNamespace(parameterization=SimpleNamespace(sampled_params=lambda: ['x']),
                            likelihood={'first': None, 'second': None}, logposterior=logposterior)
    header = ['x', 'minuslogpost', 'minuslogprior', 'chi2', 'chi2__first', 'chi2__second']
    row = np.array([.5, np.log(2.)+.125, np.log(2.), .25, .25, 0.])
    assert compare_native_row(header, row, model)['fresh_minus_recorded']['chi2'] == 0
    wrong = row.copy()
    wrong[-1] = .1
    with pytest.raises(ValueError, match='second'):
        compare_native_row(header, wrong, model)
    wrong = row.copy()
    wrong[2] = 0.
    with pytest.raises(ValueError, match='minuslogprior'):
        compare_native_row(header, wrong, model)
