"""Prepare two fresh B four-start cohorts using old configurations only as fixed inputs."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def target(cfg):
    params = deepcopy(cfg['params'])
    for b in params.values():
        if isinstance(b, dict):
            b.pop('ref', None)
            b.pop('proposal', None)
    theory = deepcopy(cfg['theory'])
    theory['classy']['path'] = 'global'
    return {'theory': theory, 'likelihood': cfg['likelihood'], 'params': params,
            'prior': cfg.get('prior'), 'packages_path': cfg['packages_path']}


state = read(ROOT / 'runs/20261003_math_review_validation/review_state.json')
sources = {e['seed']: e for k in ['guarded_medium_posterior_chains', 'guarded_quadrature_posterior_chains'] for e in state[k]}
build_path = ROOT / 'runs/20261004_math_review_class_python_repair/build_verification_receipt.json'
build = read(build_path)
assert sha(build['module']) == build['module_sha256']
entries, cohorts = [], {}
for group, seeds, source_seeds, proposal_seed, threads in [
    ('fresh_recovery_medium_B', [2401, 2402, 2403, 2404], [1403, 1404, 1405, 1407], 1403, '8'),
    ('fresh_recovery_quad_B', [2405, 2406, 2407, 2408], [1305, 1306, 1307, 1308], 1307, '4')]:
    terminal_path = ROOT / sources[proposal_seed]['terminal_receipt']
    terminal = read(terminal_path)
    assert sha(terminal_path) == sources[proposal_seed]['terminal_receipt_sha256']
    covariance_record = next(f for f in terminal['terminal_output_files'] if f['source'].endswith('.covmat'))
    covariance = ROOT / covariance_record['frozen']
    assert sha(covariance) == covariance_record['sha256']
    matrix = np.loadtxt(covariance)
    assert matrix.shape == (10, 10) and np.isfinite(matrix).all() and np.max(abs(matrix - matrix.T)) < 1e-15
    np.linalg.cholesky(matrix)
    covariance_names = covariance.read_text().splitlines()[0].lstrip('#').split()
    signatures, points = [], []
    for seed, source_seed in zip(seeds, source_seeds):
        source_entry = sources[source_seed]
        source_config = ROOT / source_entry['run_dir'] / 'input.yaml'
        source = yaml.safe_load(source_config.read_text())
        signatures.append(target(source))
        names = [n for n, b in source['params'].items() if isinstance(b, dict) and 'prior' in b]
        point = {n: float(source['params'][n]['ref']) for n in names}
        assert len(point) == 10 and set(names) == set(covariance_names)
        assert all(source['params'][n]['prior']['min'] < v < source['params'][n]['prior']['max'] for n, v in point.items())
        assert np.isfinite(list(point.values())).all()
        folder = HERE / f'seed{seed}'
        folder.mkdir(exist_ok=False)
        frozen_source = folder / 'initialization_source.yaml'
        with frozen_source.open('xb') as f:
            f.write(source_config.read_bytes())
        proposal = folder / 'initial.covmat'
        with proposal.open('xb') as f:
            f.write(covariance.read_bytes())
        cfg = deepcopy(source)
        cfg['theory']['classy']['path'] = 'global'
        cfg['notes']['classy_backend'] = {'build_receipt': str(build_path.relative_to(ROOT)), 'module_sha256': build['module_sha256']}
        cfg['notes'].update(recovery_scope='Fresh RNG and output; original fixed reference used only for initialization.',
            proposal_scope='Shared frozen positive-definite proposal heuristic; no historical samples pooled.',
            numerical_scope='Current guarded native build and current bound Python sources; historical floating-target identity not asserted.')
        options = next(iter(cfg['sampler'].values()))
        options.update(seed=seed, covmat=str(proposal.resolve()))
        cfg['run_name'] = f'CLASS_fresh_B_{group.removeprefix("fresh_recovery_")}_seed{seed}'
        config = folder / 'input.yaml'
        with config.open('x') as f:
            f.write(yaml.safe_dump(cfg, sort_keys=False))
        assert target(cfg) == target(source)
        run = ROOT / f'runs/20261005_math_review_CLASS_fresh_B_{group.removeprefix("fresh_recovery_")}_seed{seed}'
        assert not run.exists()
        old_launch = ROOT / source_entry['launch_receipt']
        old = read(old_launch)
        assert old['environment']['OMP_NUM_THREADS'] == threads
        changes = [p for p, digest in old['implementation_sha256'].items() if sha(ROOT / p) != digest]
        assert changes
        entry = {'seed': seed, 'source_seed': source_seed, 'group': group, 'lens': 'B',
            'config': str(config.relative_to(ROOT)), 'config_sha256': sha(config),
            'source_config': str(frozen_source.relative_to(ROOT)), 'source_config_sha256': sha(frozen_source),
            'original_source_config': str(source_config.relative_to(ROOT)),
            'proposal': str(proposal.relative_to(ROOT)), 'proposal_sha256': sha(proposal),
            'source_covariance': covariance_record['frozen'], 'source_covariance_sha256': covariance_record['sha256'],
            'proposal_terminal_receipt': str(terminal_path.relative_to(ROOT)), 'proposal_terminal_receipt_sha256': sha(terminal_path),
            'initial_point': point, 'run_dir': str(run.relative_to(ROOT)),
            'module': build['module'], 'module_sha256': build['module_sha256'],
            'build_receipt': str(build_path.relative_to(ROOT)), 'build_receipt_sha256': sha(build_path),
            'OMP_NUM_THREADS': threads, 'scheduling_nice': 5,
            'historical_launch_receipt': str(old_launch.relative_to(ROOT)), 'historical_launch_receipt_sha256': sha(old_launch),
            'historical_bound_source_changes': changes,
            'implementation_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
                [ROOT / 'scripts/run_cobaya.py', *(ROOT / 'src/sbt_spt_audit').rglob('*.py')]},
            'old_prefix_appended': False, 'posterior_qualified': False}
        write(folder / 'preparation_receipt.json', entry)
        entries.append(entry)
        points.append(point)
    assert all(s == signatures[0] for s in signatures)
    assert len(seeds) == len(set(seeds)) == len({tuple(p.items()) for p in points}) == 4
    cohorts[group] = {'seeds': seeds, 'fixed_initial_points': points, 'target': signatures[0],
        'source_code_identity': entries[-1]['implementation_sha256'], 'module_sha256': build['module_sha256'],
        'OMP_NUM_THREADS': threads, 'first_history_trigger': 1000, 'later_growth_factor': [6, 5],
        'original_terminal_and_surviving_families_retained_separately': True,
        'distinct_declared_rng_seeds_and_starts': True, 'independent_PRNG_streams_proved': False,
        'unconditional_independence_or_stationarity_proved': False, 'posterior_qualified': False}
write(HERE / 'preparation_receipt.json', {'utc': datetime.now(timezone.utc).isoformat(),
    'entries': entries, 'cohorts': cohorts, 'samplers_launched': 0,
    'native_preflight_and_launcher_required': True,
    'scope': 'Two new B four-start cohorts; fixed inputs and selected native starts do not prove global numerical accuracy or posterior convergence.'})
print('Eight fresh B configurations prepared; all original B registrations retained separately.')
