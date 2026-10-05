"""Freeze four candidate targets, preserving source likelihoods and all other priors."""
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
write = lambda p, d: p.open('x').write(json.dumps(d, indent=2, allow_nan=False) + '\n')
source_receipt_path = ROOT / 'runs/20261004_math_review_upper_prior_posterior_preparation/preparation_receipt.json'
sources = json.loads(source_receipt_path.read_text())['entries']
candidate = ROOT / 'runs/20261005_math_review_sigma_time_v3_packaged'
build = json.loads((candidate / 'build_receipt.json').read_text())
assert build['exit_code'] == 0 and sha(build['module']) == build['module_sha256']
policy_path = ROOT / 'native_policies/camb204_sigma_time_v3.json'
assert sha(policy_path) == build['policy_sha256']
implementation_paths = [ROOT / 'scripts/run_cobaya.py', HERE / 'launch_chain.py',
                        *(ROOT / 'src/sbt_spt_audit').rglob('*.py')]
implementation = {str(p.relative_to(ROOT)): sha(p) for p in implementation_paths}
entries = []
for lens_index, lens in enumerate(['A', 'B']):
    original = [e for e in sources if e['lens'] == lens]
    assert len(original) == 4
    proposal = deepcopy(original[0]['proposal'])
    proposal_source = ROOT / proposal['path']
    assert sha(proposal_source) == proposal['sha256']
    matrix = np.loadtxt(proposal_source)
    assert matrix.shape == (7, 7) and np.isfinite(matrix).all()
    assert np.max(np.abs(matrix - matrix.T)) < 1e-18
    np.linalg.cholesky(matrix)
    destination = HERE / f'proposal_{lens}.covmat'
    with destination.open('xb') as f:
        f.write(proposal_source.read_bytes())
    proposal.update(path=str(destination.relative_to(ROOT)), copied_from=str(proposal_source.relative_to(ROOT)),
                    role='same proposal heuristic for both mass caps; no historical samples pooled')
    for cap_index, upper in enumerate([5, 20]):
        group = f'sigma_time_v3_{lens}4095_cap{upper}'
        for start_index, source in enumerate(original):
            assert sha(ROOT / source['config']) == source['config_sha256']
            cfg = yaml.safe_load((ROOT / source['config']).read_text())
            seed = 2101 + lens_index * 8 + cap_index * 4 + start_index
            point = deepcopy(source['initial_point'])
            if start_index >= 2:
                point['mnu'] = upper * [.3, .6][start_index - 2]
            assert all(cfg['params'][k]['prior']['min'] < v < (upper if k == 'mnu' else cfg['params'][k]['prior']['max'])
                       for k, v in point.items())
            cfg['params']['mnu']['prior']['max'] = float(upper)
            for name, value in point.items():
                cfg['params'][name]['ref'] = value
            cfg['notes']['camb_backend'] = {'module_sha256': build['module_sha256'], 'solver_version': '2.0.4'}
            cfg['notes'].update(numerical_target=group, native_policy='camb204_sigma_time_v3',
                native_policy_sha256=sha(policy_path), native_build_receipt=str((candidate / 'build_receipt.json').relative_to(ROOT)),
                mass_prior=f'uniform[0,{upper}] eV', initial_point_label=['original_reference', 'selected_frozen_row', 'mass_30_percent_cap', 'mass_60_percent_cap'][start_index],
                math_review='Experimental native candidate; fresh output and RNG. Qualification and prior sensitivity pending; no historical samples pooled.')
            cfg['sampler']['mcmc']['seed'] = seed
            cfg['sampler']['mcmc']['covmat'] = str(destination.resolve())
            cfg['run_name'] = f'fresh_CAMB_{group}_seed{seed}'
            folder = HERE / f'seed{seed}'
            folder.mkdir(exist_ok=False)
            path = folder / 'input.yaml'
            with path.open('x') as f:
                f.write(yaml.safe_dump(cfg, sort_keys=False))
            run_dir = ROOT / f'runs/20261005_math_review_fresh_CAMB_{group}_seed{seed}'
            assert not run_dir.exists()
            entry = {'seed': seed, 'lens': lens, 'group': group, 'prior_upper_eV': upper,
                'kind': 'spt_desi_fresh_CAMB_sigma_time_v3_candidate', 'config': str(path.relative_to(ROOT)), 'config_sha256': sha(path),
                'run_dir': str(run_dir.relative_to(ROOT)), 'initial_point': point,
                'initial_point_label': cfg['notes']['initial_point_label'],
                'source_config': source['config'], 'source_config_sha256': source['config_sha256'],
                'source_entry_seed': source['seed'], 'proposal': proposal, 'implementation_sha256': implementation,
                'module': build['module'], 'module_sha256': build['module_sha256'],
                'wrapper': source['wrapper'], 'wrapper_sha256': source['wrapper_sha256'],
                'solver_version': '2.0.4', 'Cobaya_version': '3.6.2',
                'policy': str(policy_path.relative_to(ROOT)), 'policy_sha256': sha(policy_path),
                'build_receipt': str((candidate / 'build_receipt.json').relative_to(ROOT)),
                'build_receipt_sha256': sha(candidate / 'build_receipt.json'),
                'required_LD_LIBRARY_PATH': build['LD_LIBRARY_PATH'],
                'launch_receipt': str((folder / 'launch_receipt.json').relative_to(ROOT)),
                'scheduling_nice': 5, 'posterior_qualified': False, 'production_adopted': False}
            write(folder / 'preparation_receipt.json', entry)
            entries.append(entry)
write(HERE / 'preparation_receipt.json', {'utc': datetime.now(timezone.utc).isoformat(), 'entries': entries,
    'source_preparation_receipt_sha256': sha(source_receipt_path), 'targets': sorted({e['group'] for e in entries}),
    'new_samplers_per_target': 4, 'samplers_launched': 0,
    'scope': 'Separately qualified empirical candidate comparison across mass caps 5 and 20 eV. Other priors and likelihoods unchanged.',
    'production_adopted': False, 'posterior_certified': False, 'old_prefix_append_permitted': False})
print('Sixteen fresh configurations frozen; no sampler launched.')
