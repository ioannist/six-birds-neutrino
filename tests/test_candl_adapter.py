"""Check the physical spectrum bridge without downloading survey data."""
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip('cobaya')
from sbt_spt_audit.likelihoods.candl_cobaya import CandlCobayaLikelihood, select_internal_priors
from cobaya.theory import Theory
from cobaya.model import get_model


def adapter():
    obj = object.__new__(CandlCobayaLikelihood)
    obj._like_obj = SimpleNamespace(spec_types=['TT', 'TE', 'EE'])
    obj._ells = np.array([2, 3])
    obj._lmax_required = 3
    return obj


def test_physical_cl_to_dl_bridge():
    obj = adapter()
    cls = {'tt': np.array([0., 0., 1., 2.]),
           'te': np.array([0., 0., -1., -2.]),
           'ee': np.array([0., 0., 2., 4.])}
    result = obj._build_dl(cls)
    assert result['TT'] == pytest.approx([3 / np.pi, 12 / np.pi])
    assert result['TE'] == pytest.approx(-result['TT'])
    assert result['EE'] == pytest.approx(2 * result['TT'])


def test_provider_cannot_replace_required_spectra_with_zeros():
    obj = adapter()
    with pytest.raises(ValueError, match='required'):
        obj._build_dl({})
    with pytest.raises(ValueError, match='lmax'):
        obj._get_cl_array({'tt': np.array([0., 0., 1.])}, 'tt')


def test_prior_policy_removes_whole_factors_and_rejects_ambiguous_changes():
    tau = SimpleNamespace(par_names=['tau'])
    joint = SimpleNamespace(par_names=['cal1', 'cal2'])
    priors = [tau, joint]
    assert select_internal_priors(priors, ['tau']) == [joint]
    assert select_internal_priors(priors, ['cal1', 'cal2']) == [tau]
    assert select_internal_priors(priors, None) == priors
    with pytest.raises(ValueError, match='partially'):
        select_internal_priors(priors, ['cal1'])
    with pytest.raises(ValueError, match='No internal prior'):
        select_internal_priors(priors, ['typo'])
    with pytest.raises(ValueError, match='distinct'):
        select_internal_priors(priors, ['tau', 'tau'])
    assert priors == [tau, joint]


class ToySpectra(Theory):
    def get_can_support_params(self):
        return ['x']

    def get_can_provide(self):
        return ['Cl']

    def calculate(self, state, want_derived=True, **params):
        state['Cl'] = {'tt': np.full(4, params['x'])}

    def get_Cl(self, **kwargs):
        return self.current_state['Cl']


class ToyCandl(CandlCobayaLikelihood):
    def initialize(self):
        self._like_obj = SimpleNamespace(spec_types=['TT'],
            log_like=lambda p: -p['y'] ** 2 - sum(p['Dl']['TT']))
        self._base_params = {'y': 0.0}
        self._scalar_parameters = ['y']
        self._ells = np.array([2, 3])
        self._lmax_required = 3
        self._lensing = False


def test_scalar_shared_with_other_component_is_in_cobaya_cache_key():
    # y is also consumed by another likelihood. It must reach candl even
    # though Cobaya would otherwise regard it as already assigned.
    with get_model({'params': {'x': {'prior': {'min': 0, 'max': 3}},
                              'y': {'prior': {'min': 0, 'max': 3}}},
                    'theory': {'spectra': {'external': ToySpectra}},
                    'likelihood': {'spt': {'external': ToyCandl},
                                   'other': {'external': lambda y: -y}}}) as model:
        first = model.loglikes({'x': 1., 'y': 1.}, as_dict=True, return_derived=False)
        second = model.loglikes({'x': 1., 'y': 2.}, as_dict=True, return_derived=False)
        fresh = model.loglikes({'x': 1., 'y': 2.}, as_dict=True, return_derived=False, cached=False)
        assert second['spt'] - first['spt'] == pytest.approx(-3.)
        assert second == pytest.approx(fresh)
        third = model.loglikes({'x': 2., 'y': 2.}, as_dict=True, return_derived=False)
        assert third['spt'] < second['spt']
