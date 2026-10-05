"""Freeze declared guarded-chain coordinates for a two-target sensitivity check."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from sbt_spt_audit.mcmc import weighted_quantile

OVERLAY = Path('/mnt/8tb/six-birds-ml/tmp/neutrino_class_finite_jacobian_20261004/python_backend')
NATIVE = OVERLAY / 'classy/_classy.cpython-312-x86_64-linux-gnu.so'
NATIVE_HASH = '7a5d736220b3d236f3dc7c89944d025fe3e4c7cb4c8e4473ef807c898fc71539'
assert hashlib.sha256(NATIVE.read_bytes()).hexdigest() == NATIVE_HASH
settings_path = ROOT / 'runs/20261003_math_review_class_accuracy_control_medium/precision_settings.json'
settings = json.loads(settings_path.read_text())
assert len(settings['settings']) == 7
all_selections, frozen = [], []
for lens, quad_seed, medium_seed in [('A', 1301, 1401), ('B', 1305, 1403)]:
    out = HERE / lens
    out.mkdir()
    quad_run = ROOT / f'runs/20261004_math_review_guarded_quad_chain_{lens}_seed{quad_seed}'
    cfg = yaml.safe_load((quad_run / 'input.yaml').read_text())
    names = [k for k, v in cfg['params'].items() if isinstance(v, dict) and 'prior' in v]
    points = {}
    for cohort, seed, probabilities in [('quad', quad_seed, [.5, .95]), ('medium', medium_seed, [.95])]:
        source = ROOT / f'runs/20261004_math_review_guarded_{cohort}_chain_{lens}_seed{seed}'
        other = yaml.safe_load((source / 'input.yaml').read_text())
        # Only initialization, execution and declared numerical controls differ.
        for key in ['likelihood', 'packages_path']:
            assert cfg[key] == other[key]
        for name, value in cfg['params'].items():
            other_value = other['params'][name]
            if isinstance(value, dict):
                assert {k:v for k,v in value.items() if k not in ['ref','proposal']} == {
                    k:v for k,v in other_value.items() if k not in ['ref','proposal']}
            else:
                assert value == other_value
        assert cfg['theory']['classy']['input_params'] == other['theory']['classy']['input_params']
        allowed_numerical = set(settings['settings'])
        assert {k:v for k,v in cfg['theory']['classy']['extra_args'].items() if k not in allowed_numerical} == {
            k:v for k,v in other['theory']['classy']['extra_args'].items() if k not in allowed_numerical}
        original = next((source / 'chains').glob('*.1.txt'))
        raw = original.read_bytes()
        complete = raw[:raw.rfind(b'\n') + 1]
        archive = out / f'seed{seed}.txt'
        archive.write_bytes(complete)
        header = complete.decode().splitlines()[0].lstrip('#').split()
        assert len(set(header)) == len(header)
        rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
        assert np.all(np.isfinite(rows)) and np.all(rows[:,0] > 0)
        assert np.all(rows[:,0] == np.floor(rows[:,0]))
        discarded = int(.2 * len(rows))
        used = rows[discarded:]
        values, weights = used[:,header.index('mnu_sample')], used[:,header.index('weight')]
        for probability in probabilities:
            mass = weighted_quantile(values, weights, probability)
            index = int(np.flatnonzero(values == mass)[0]) + discarded
            label = f'{cohort}_q{int(probability * 100)}'
            point = {n:float(rows[index,header.index(n)]) for n in names}
            assert all(cfg['params'][n]['prior']['min'] <= v <= cfg['params'][n]['prior']['max'] for n,v in point.items())
            points[label] = point
            all_selections.append({'lens':lens,'label':label,'seed':seed,'frozen_chain':str(archive.relative_to(ROOT)),
                                   'stored_row_zero_based':index,'discarded_stored_rows':discarded,
                                   'empirical_selection_probability':probability,'selected_mass':mass,
                                   'native_chi2_recorded':{n[6:]:float(rows[index,j]) for j,n in enumerate(header) if n.startswith('chi2__')},
                                   'point_is_from_target':cohort,'selection_scope':'unconverged_guarded_chain_coordinate_only'})
        frozen.append({'source':str(original.relative_to(ROOT)),'snapshot':str(archive.relative_to(ROOT)),
                       'sha256':hashlib.sha256(complete).hexdigest(),'stored_rows':len(rows)})
    base = points['quad_q50']
    assert base['mnu_sample'] + .01 < cfg['params']['mnu_sample']['prior']['max']
    points['quad_q50_mass_plus'] = dict(base, mnu_sample=base['mnu_sample'] + .01)
    cfg['theory']['classy']['path'] = 'global'
    cfg['notes']['classy_backend'] = {
        'build_receipt':'runs/20261004_math_review_class_python_repair/build_verification_receipt.json',
        'module_sha256':NATIVE_HASH}
    for name, content in [('input.yaml',yaml.safe_dump(cfg,sort_keys=False)),
                          ('precision_settings.json',settings_path.read_text()),
                          ('points.json',json.dumps(points,indent=2,allow_nan=False)+'\n')]:
        (out/name).write_text(content)
receipt = {'utc':datetime.now(timezone.utc).isoformat(),'scope':'selected_guarded_CLASS_points_quad_vs_medium',
           'selection_rule':'first stored row attaining exact weighted mass quantile after 20 percent stored-row burn-in',
           'mass_offset_eV':.01,'native_module_path':str(NATIVE),'native_module_sha256':NATIVE_HASH,
           'settings_source':str(settings_path.relative_to(ROOT)),'settings_source_sha256':hashlib.sha256(settings_path.read_bytes()).hexdigest(),
           'files':frozen,'selections':all_selections,'physical_models_and_likelihoods_unchanged_within_each_lens':True,
           'posterior_convergence_verified':False,'posterior_accuracy_certified':False}
(HERE/'selection_receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
print('Six guarded-chain coordinates and two local mass offsets frozen; targets kept separate.')
