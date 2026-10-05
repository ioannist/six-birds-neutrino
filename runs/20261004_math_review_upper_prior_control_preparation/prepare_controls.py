"""Prepare model-only upper-prior controls; do not launch any sampler."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
assert not (HERE / 'preparation_receipt.json').exists()
groups = {}
keys = ['theory', 'likelihood', 'params', 'packages_path', 'prior']
for group in ['current_A4095', 'current_B4095']:
    entry = next(e for e in state['fresh_CAMB_posterior_chains'] if e['group'] == group)
    source = ROOT / entry['config']
    assert sha(source) == entry['config_sha256']
    config = yaml.safe_load(source.read_text())
    base = {k: deepcopy(config[k]) for k in keys if k in config}
    assert base['params']['mnu']['prior'] == {'min': 0.0, 'max': 5.0}
    assert base['theory']['camb']['class'] == 'sbt_spt_audit.boltzmann.FreshCAMB'
    assert base['theory']['camb']['extra_args']['lmax'] == 4095
    assessment = state['fresh_CAMB_production_assessments'][group]
    native_path = ROOT / assessment['native_verification']
    native = json.loads(native_path.read_text())
    assert native['solver_version'] == '2.0.4' and native['upstream_original_class_forced_fresh']
    selected = next(f for f in native['records'] if f['seed'] == entry['seed'])
    latest = selected['checks'][-1]['point']
    points = {'original_reference': deepcopy(entry['initial_point']),
              'selected_latest_frozen_row': deepcopy(latest)}
    for mass in [6.0, 12.0]:
        point = deepcopy(entry['initial_point']); point['mnu'] = mass
        points[f'mass_{int(mass)}_eV'] = point
    controls = {}
    for upper in [5, 10, 20]:
        control = deepcopy(base); control['params']['mnu']['prior']['max'] = float(upper)
        restored = deepcopy(control); restored['params']['mnu']['prior']['max'] = 5.0
        assert restored == base
        destination = HERE / group / f'upper_{upper}' / 'model.yaml'
        destination.parent.mkdir(parents=True, exist_ok=False)
        with destination.open('x') as f: f.write(yaml.safe_dump(control, sort_keys=False))
        controls[str(upper)] = {'path': str(destination.relative_to(ROOT)), 'sha256': sha(destination)}
    groups[group] = {'baseline_seed': entry['seed'], 'source_config': str(source.relative_to(ROOT)),
                     'source_config_sha256': sha(source), 'native_baseline_verification': str(native_path.relative_to(ROOT)),
                     'native_baseline_verification_sha256': sha(native_path), 'points': points,
                     'controls': controls, 'expected_environment': {k: entry[k] for k in
                       ['module', 'module_sha256', 'wrapper', 'wrapper_sha256', 'solver_version', 'Cobaya_version']}}
implementation = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'src/sbt_spt_audit').rglob('*.py'))}
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'groups': groups,
           'implementation_sha256': implementation, 'model_only_no_sampler_or_output': True,
           'only_model_change': 'mnu uniform-prior upper endpoint',
           'upper_limits_eV': [5, 10, 20], 'samplers_launched': 0,
           'conditional_mathematical_relation': 'With the same likelihood and other priors and a proper positive-evidence wide posterior, the U=5 posterior is the U>5 posterior conditioned on mnu<=5.',
           'relation_premises_verified_uniformly': False,
           'tail_probability_or_quantile_stability_inferred': False,
           'posterior_qualification': False, 'paper_modified': False}
with (HERE / 'preparation_receipt.json').open('x') as f: f.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('Six model-only configurations prepared; no sampler or output block.', flush=True)
