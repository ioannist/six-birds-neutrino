"""A cached transfer must not depend on another native model's mutable state."""
from copy import deepcopy
from types import SimpleNamespace
import pytest

pytest.importorskip('cobaya')
from cobaya.theories.camb.camb import CambTransfers, camb
from sbt_spt_audit.boltzmann import (
    FreshCAMB, FreshCAMBTransfers, FRESH_CAMB_CLASS, configure_fresh_camb_transfers,
)


def native_state_fixture(helper_class, shared, cache_size):
    # Deliberately stateful synthetic native calculator. Actual CAMB spectrum
    # controls are separate; this is a regression for the cache precondition.
    parent=SimpleNamespace(camb=SimpleNamespace(),speed=1.)
    helper=helper_class(parent,'camb.transfers',{})
    helper.set_cache_size(cache_size)
    def calculate(state, want_derived=True, **params):
        shared['background']=params['x']
        state['results']=params['x']
    helper.calculate=calculate
    return helper


@pytest.mark.parametrize('cache_size',[1,3,100])
def test_fresh_transfers_restore_fixed_point_after_another_model(cache_size):
    def evaluate(helper, x, shared, cached=True):
        assert helper.check_cache_and_compute({'x':x},cached=cached)
        return helper.current_state['results']+shared['background']
    for helper_class, expected in [(CambTransfers,3.),(FreshCAMBTransfers,2.)]:
        shared={}
        main=native_state_fixture(helper_class,shared,cache_size)
        other=native_state_fixture(CambTransfers,shared,cache_size)
        assert evaluate(main,1.,shared)==2.
        assert evaluate(other,2.,shared)==4.
        assert evaluate(main,1.,shared)==expected
        assert evaluate(main,1.,shared,cached=False)==2.
        # A later sampler cache resize must not undo the repaired behavior.
        main.set_cache_size(50)
        assert evaluate(main,1.,shared)==2.
        evaluate(other,2.,shared,cached=False)
        assert evaluate(main,1.,shared)==expected


def test_fresh_adapter_preserves_upstream_numerical_defaults():
    assert FreshCAMB.get_defaults()==camb.get_defaults()


def test_configuration_retains_declared_physics_and_native_build():
    config={'theory':{'camb':{'version':'1.6.5','path':'global',
                            'extra_args':{'lmax':3200,'nnu':3.046,'num_massive_neutrinos':3}}},
            'params':{'mnu':{'prior':{'min':0.,'max':5.}}},
            'notes':{'camb_backend':{'module_sha256':'a'*64,'solver_version':'1.6.5'}},
            'likelihood':{'native':{}},'sampler':{'mcmc':{'seed':17}}}
    original=deepcopy(config)
    configure_fresh_camb_transfers(config)
    assert config['theory']['camb'].pop('class')==FRESH_CAMB_CLASS
    assert config==original


@pytest.mark.parametrize('custom',[{'class':'other.CustomCAMB'}, {'external':camb}])
def test_custom_camb_target_requires_review_instead_of_silent_replacement(custom):
    config={'theory':{'camb':custom}}
    original=deepcopy(config)
    with pytest.raises(ValueError,match='Custom CAMB'):
        configure_fresh_camb_transfers(config)
    assert config==original


def test_class_configuration_is_preserved():
    config={'theory':{'classy':{'extra_args':{'l_max_scalars':4095}}}}
    original=deepcopy(config)
    configure_fresh_camb_transfers(config)
    assert config==original
