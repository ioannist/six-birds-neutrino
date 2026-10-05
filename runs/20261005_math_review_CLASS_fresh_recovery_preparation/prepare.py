"""Prepare fresh recovery replicas from preserved terminal points and covariance heuristics."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
write = lambda p, d: p.open('x').write(json.dumps(d, indent=2, allow_nan=False) + '\n')
build_path = ROOT / 'runs/20261004_math_review_class_python_repair/build_verification_receipt.json'
build = json.loads(build_path.read_text())
assert sha(build['module']) == build['module_sha256']
implementation = {str(p.relative_to(ROOT)): sha(p) for p in [HERE / 'launch.py', ROOT / 'scripts/run_cobaya.py',
                                                            *(ROOT / 'src/sbt_spt_audit').rglob('*.py')]}
entries = []
for parent_seed, seed, group in [(1201, 2201, 'medium_A'), (1301, 2202, 'quad_A')]:
    terminal_path = ROOT / f'runs/20261005_math_review_CLASS_unavailable_terminal_preservation/seed{parent_seed}/terminal_receipt.json'
    terminal = json.loads(terminal_path.read_text())
    assert terminal['exit_code'] is None and terminal['identity_observation']['original_identity_absent']
    config_record = next(f for f in terminal['terminal_output_files'] if f['source'].endswith('/input.yaml'))
    assert sha(ROOT / config_record['frozen']) == config_record['sha256']
    cfg = yaml.safe_load((ROOT / config_record['frozen']).read_text())
    chain_record = next(f for f in terminal['terminal_output_files'] if f['source'].endswith('.1.txt'))
    chain = ROOT / chain_record['frozen']
    assert sha(chain) == chain_record['sha256']
    raw = chain.read_bytes()
    raw = raw[:raw.rfind(b'\n') + 1]
    header = raw.decode().splitlines()[0].lstrip('#').split()
    rows = [l.split() for l in raw.decode().splitlines() if l.strip() and not l.startswith('#')]
    assert len(header) == len(set(header)) == len(rows[-1])
    last = dict(zip(header, rows[-1]))
    assert Fraction(last['weight']) > 0 and Fraction(last['weight']).denominator == 1
    names = [name for name, block in cfg['params'].items() if isinstance(block, dict) and 'prior' in block]
    point = {name: float(last[name]) for name in names}
    assert all(cfg['params'][n]['prior']['min'] < v < cfg['params'][n]['prior']['max'] for n, v in point.items())
    for name, value in point.items():
        cfg['params'][name]['ref'] = value
    covariance_record = next(f for f in terminal['terminal_output_files'] if f['source'].endswith('.covmat'))
    covariance = ROOT / covariance_record['frozen']
    assert sha(covariance) == covariance_record['sha256']
    covariance_names = covariance.read_text().splitlines()[0].lstrip('#').split()
    assert set(covariance_names) == set(names)
    matrix = np.loadtxt(covariance)
    assert matrix.shape == (len(names), len(names)) and np.isfinite(matrix).all()
    assert np.max(np.abs(matrix - matrix.T)) < 1e-15
    np.linalg.cholesky(matrix)
    folder = HERE / f'seed{seed}'
    folder.mkdir(exist_ok=False)
    proposal = folder / 'initial.covmat'
    with proposal.open('xb') as f:
        f.write(covariance.read_bytes())
    assert len(cfg['sampler']) == 1
    options = next(iter(cfg['sampler'].values()))
    options['seed'] = seed
    options['covmat'] = str(proposal.resolve())
    cfg['theory']['classy']['path'] = 'global'
    cfg['notes']['classy_backend'] = {'build_receipt': str(build_path.relative_to(ROOT)), 'module_sha256': build['module_sha256']}
    cfg['notes'].update(recovery_scope='Fresh replica of preserved target; new RNG and output. No exact resume or old-prefix append.',
                        warm_start_fit='Last complete preserved terminal row, initialization only.',
                        proposal_scope='Preserved learned covariance used as a positive-definite proposal heuristic only.')
    cfg['run_name'] = f'CLASS_fresh_recovery_{group}_seed{seed}'
    path = folder / 'input.yaml'
    with path.open('x') as f:
        f.write(yaml.safe_dump(cfg, sort_keys=False))
    run_dir = ROOT / f'runs/20261005_math_review_CLASS_fresh_recovery_{group}_seed{seed}'
    assert not run_dir.exists()
    entry = {'seed': seed, 'parent_seed': parent_seed, 'lens': 'A', 'group': group,
        'config': str(path.relative_to(ROOT)), 'config_sha256': sha(path),
        'run_dir': str(run_dir.relative_to(ROOT)), 'initial_point': point,
        'terminal_receipt': str(terminal_path.relative_to(ROOT)), 'terminal_receipt_sha256': sha(terminal_path),
        'source_config': config_record['frozen'], 'source_config_sha256': config_record['sha256'],
        'source_chain': chain_record['frozen'], 'source_chain_sha256': chain_record['sha256'],
        'source_row': last, 'source_covariance': covariance_record['frozen'],
        'source_covariance_sha256': covariance_record['sha256'], 'proposal': str(proposal.relative_to(ROOT)),
        'proposal_sha256': sha(proposal), 'module': build['module'], 'module_sha256': build['module_sha256'],
        'build_receipt': str(build_path.relative_to(ROOT)), 'build_receipt_sha256': sha(build_path),
        'implementation_sha256': implementation, 'launch_receipt': str((folder / 'launch_receipt.json').relative_to(ROOT)),
        'OMP_NUM_THREADS': '8' if parent_seed == 1201 else '4', 'scheduling_nice': 5,
        'old_prefix_appended': False, 'exact_resume_asserted': False, 'posterior_qualified': False}
    write(folder / 'preparation_receipt.json', entry)
    entries.append(entry)
write(HERE / 'preparation_receipt.json', {'utc': datetime.now(timezone.utc).isoformat(), 'entries': entries,
    'samplers_launched': 0, 'terminal_outputs_unchanged': True, 'physical_target_change_asserted': False,
    'scope': 'Two fresh recovery replicas. Native target matching must pass before launch; no trajectory continuation or convergence assertion.'})
print('Two recovery configurations prepared; original checkpoints do not supply exact-resume state.')
