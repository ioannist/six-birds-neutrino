"""Prepare six fresh companions; old runs supply fixed initialization points only."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'runs/20261005_math_review_CLASS_fresh_recovery_preparation'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def target(cfg):
    params = deepcopy(cfg['params'])
    for p in params.values():
        if isinstance(p, dict):
            for key in ['ref', 'proposal', 'latex']:
                p.pop(key, None)
    theory = deepcopy(cfg['theory'])
    theory['classy']['path'] = 'global'
    return {'theory': theory, 'likelihood': cfg['likelihood'], 'params': params,
            'prior': cfg.get('prior'), 'packages_path': cfg['packages_path']}


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
existing = {e['seed']: e for key in ['guarded_medium_posterior_chains', 'guarded_quadrature_posterior_chains']
            for e in state[key]}
assignments = [(2301, 1401, 2201), (2302, 1402, 2201), (2303, 1406, 2201),
               (2304, 1302, 2202), (2305, 1303, 2202), (2306, 1304, 2202)]
entries = []
for seed, source_seed, anchor_seed in assignments:
    anchor = json.loads((BASE / f'seed{anchor_seed}/preparation_receipt.json').read_text())
    anchor_cfg = yaml.safe_load((ROOT / anchor['config']).read_text())
    source_config = ROOT / existing[source_seed]['run_dir'] / 'input.yaml'
    source_cfg = yaml.safe_load(source_config.read_text())
    assert target(source_cfg) == target(anchor_cfg)
    names = list(anchor['initial_point'])
    point = {n: float(source_cfg['params'][n]['ref']) for n in names}
    assert np.isfinite(list(point.values())).all()
    assert all(anchor_cfg['params'][n]['prior']['min'] < v < anchor_cfg['params'][n]['prior']['max']
               for n, v in point.items())
    folder = HERE / f'seed{seed}'
    folder.mkdir(exist_ok=False)
    frozen_source = folder / 'initialization_source.yaml'
    with frozen_source.open('xb') as f:
        f.write(source_config.read_bytes())
    proposal = folder / 'initial.covmat'
    with proposal.open('xb') as f:
        f.write((ROOT / anchor['proposal']).read_bytes())
    assert sha(proposal) == anchor['proposal_sha256']
    np.linalg.cholesky(np.loadtxt(proposal))
    cfg = deepcopy(anchor_cfg)
    for n, v in point.items():
        cfg['params'][n]['ref'] = v
    options = next(iter(cfg['sampler'].values()))
    options.update(seed=seed, covmat=str(proposal.resolve()))
    cfg['run_name'] = f'CLASS_recovery_companion_{anchor["group"]}_seed{seed}'
    cfg['notes'].update(recovery_scope='Fresh independent RNG/output; initialization from a fixed source configuration only.',
                        warm_start_fit=f'Fixed initial reference of seed{source_seed}; no historical trajectory appended.')
    config = folder / 'input.yaml'
    with config.open('x') as f:
        f.write(yaml.safe_dump(cfg, sort_keys=False))
    assert target(cfg) == target(anchor_cfg)
    run = ROOT / f'runs/20261005_math_review_CLASS_recovery_companion_{anchor["group"]}_seed{seed}'
    assert not run.exists()
    old_launch = ROOT / f'runs/20261004_math_review_class_backend_transition/launches/seed{source_seed}.json'
    old = json.loads(old_launch.read_text())
    changes = [p for p, digest in old['implementation_sha256'].items() if sha(ROOT / p) != digest]
    assert changes
    entry = {'seed': seed, 'source_seed': source_seed, 'anchor_seed': anchor_seed,
        'group': 'fresh_recovery_' + anchor['group'], 'lens': 'A',
        'config': str(config.relative_to(ROOT)), 'config_sha256': sha(config),
        'source_config': str(frozen_source.relative_to(ROOT)), 'source_config_sha256': sha(frozen_source),
        'original_source_config': str(source_config.relative_to(ROOT)),
        'anchor_config': anchor['config'], 'anchor_config_sha256': anchor['config_sha256'],
        'proposal': str(proposal.relative_to(ROOT)), 'proposal_sha256': sha(proposal),
        'anchor_proposal': anchor['proposal'], 'initial_point': point,
        'run_dir': str(run.relative_to(ROOT)), 'module': anchor['module'],
        'module_sha256': anchor['module_sha256'], 'build_receipt': anchor['build_receipt'],
        'build_receipt_sha256': anchor['build_receipt_sha256'],
        'OMP_NUM_THREADS': anchor['OMP_NUM_THREADS'], 'scheduling_nice': 5,
        'historical_launch_receipt': str(old_launch.relative_to(ROOT)),
        'historical_launch_receipt_sha256': sha(old_launch), 'historical_bound_source_changes': changes,
        'old_prefix_appended': False, 'posterior_qualified': False,
        'implementation_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
            [ROOT / 'scripts/run_cobaya.py', *(ROOT / 'src/sbt_spt_audit').rglob('*.py')]}}
    write(folder / 'preparation_receipt.json', entry)
    entries.append(entry)
cohorts = {}
for anchor_seed in [2201, 2202]:
    children = [e for e in entries if e['anchor_seed'] == anchor_seed]
    anchor = next(e for e in state['guarded_CLASS_fresh_recovery_trials'] if e['seed'] == anchor_seed)
    seeds = [anchor_seed] + [e['seed'] for e in children]
    points = [anchor['initial_point']] + [e['initial_point'] for e in children]
    assert len(seeds) == len(set(seeds)) == len({tuple(p.items()) for p in points}) == 4
    cohorts['fresh_recovery_' + anchor['group']] = {'seeds': seeds,
        'fixed_initial_points': points, 'target': target(yaml.safe_load((ROOT / anchor['config']).read_text())),
        'source_code_identity': children[0]['implementation_sha256'],
        'module_sha256': anchor['module_sha256'], 'OMP_NUM_THREADS': anchor['OMP_NUM_THREADS'],
        'first_history_trigger': 1000, 'later_growth_factor': [6, 5],
        'original_terminal_and_surviving_families_retained_separately': True,
        'distinct_declared_rng_seeds_and_starts': True,
        'independent_PRNG_streams_proved': False,
        'unconditional_independence_or_stationarity_proved': False, 'posterior_qualified': False}
write(HERE / 'preparation_receipt.json', {'utc': datetime.now(timezone.utc).isoformat(),
    'entries': entries, 'cohorts': cohorts, 'samplers_launched': 0,
    'native_preflight_and_launcher_required': True,
    'scope': 'Fixed four-family fresh recovery design. Declared target equality, not historical floating-target equivalence.'})
print('Six fresh configurations prepared for two explicitly separate four-family recovery cohorts.')
