"""False-target controls for cosmological completion matching."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest
import yaml

pytest.importorskip('cobaya')
pytest.importorskip('pybobyqa')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_cosmological_audit import build_common_config, SPT, validate_transfer_domain


def test_common_model_rejects_parameter_backend_or_completion_changes():
    root = Path(__file__).resolve().parents[1]
    a = yaml.safe_load((root / 'configs/neutrino/spt2018_desi_lcdm_mnu.yaml').read_text())
    b = yaml.safe_load((root / 'configs/neutrino/sptd1_desi_lcdm_mnu.yaml').read_text())
    cfg, completion = build_common_config(a, b)
    assert len(cfg['theory']) == 1
    assert cfg['likelihood']['lensA']['dataset_expr'] == a['likelihood'][SPT]['dataset_expr']
    assert cfg['likelihood']['lensB']['dataset_expr'] == b['likelihood'][SPT]['dataset_expr']
    assert completion == [k for k in a['likelihood'] if k != SPT]
    for key, change in [('params', lambda c: c['params']['mnu']['prior'].update(max=1.)),
                        ('theory', lambda c: c['theory']['camb']['extra_args'].update(nnu=4.)),
                        ('completion', lambda c: c['likelihood'].pop(completion[0]))]:
        changed = deepcopy(b)
        change(changed)
        with pytest.raises(ValueError, match=key):
            build_common_config(a, changed)


def test_transfer_domain_rejects_false_source_or_profile_scope():
    names = ['H0', 'mnu_sample', 'TT_kSZ_Amp']
    source = {'point': dict(zip(names, [68., .06, 2.])), 'loglike': -100.}
    cross = {'point': dict(zip(names, [68., .06, 3.])), 'loglike': -110.,
             'free': ['TT_kSZ_Amp']}
    reference = {'point': dict(zip(names, [69., .04, 4.])), 'loglike': -105.}
    direction = {'shared_parameters': names[:2], 'profiled_parameters': names[2:],
                 'cross_candidate': cross, 'reference_candidate': reference}
    validate_transfer_domain(direction, source, names)
    cases = [
        ('fixed source', lambda d: d['cross_candidate']['point'].update(mnu_sample=.05)),
        ('partition', lambda d: d.update(shared_parameters=['H0'])),
        ('exactly the nuisance', lambda d: d['cross_candidate'].update(free=names)),
        ('worse', lambda d: d['reference_candidate'].update(loglike=-111.)),
        ('complete finite', lambda d: d['cross_candidate']['point'].pop('H0')),
        ('finite candidate', lambda d: d['reference_candidate'].update(loglike=float('nan'))),
    ]
    for error, change in cases:
        changed = deepcopy(direction)
        change(changed)
        with pytest.raises(ValueError, match=error):
            validate_transfer_domain(changed, source, names)
