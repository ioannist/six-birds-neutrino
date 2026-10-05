"""Freeze two wider-prior targets with four separately verified starts each."""
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
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
control_root = ROOT / state['upper_prior_control_preparation']['root']
preparation = json.loads((control_root / 'preparation_receipt.json').read_text())
assert json.loads((control_root / 'preflight_completion.json').read_text())['exit_code'] == 0
assert json.loads((control_root / 'self_review_receipt.json').read_text())['six_models_rederived_from_original_targets']
implementation_paths = [ROOT / 'scripts/run_cobaya.py', HERE / 'launch_chain.py', *(ROOT / 'src/sbt_spt_audit').rglob('*.py')]
implementation = {str(p.relative_to(ROOT)): sha(p) for p in implementation_paths}
entries = []
proposals = {}
for lens, baseline_group, first_seed in [('A', 'current_A4095', 2001), ('B', 'current_B4095', 2005)]:
    control = preparation['groups'][baseline_group]
    baseline_entry = next(e for e in state['fresh_CAMB_posterior_chains'] if e['seed'] == control['baseline_seed'])
    source_path = ROOT / control['source_config']
    assert sha(source_path) == control['source_config_sha256'] == baseline_entry['config_sha256']
    baseline = yaml.safe_load(source_path.read_text())
    proposal = deepcopy(baseline_entry['proposal'])
    proposal_source = ROOT / proposal['path']
    assert sha(proposal_source) == proposal['sha256']
    names = proposal_source.read_text().splitlines()[0].lstrip('#').split()
    assert names == ['omegabh2', 'omegach2', 'H0', 'logA', 'ns', 'tau', 'mnu']
    matrix = np.loadtxt(proposal_source)
    assert matrix.shape == (7, 7) and np.isfinite(matrix).all()
    assert np.max(np.abs(matrix - matrix.T)) < 1e-18
    np.linalg.cholesky(matrix)
    destination = HERE / f'proposal_{lens}.covmat'
    with destination.open('xb') as f: f.write(proposal_source.read_bytes())
    proposal.update({'copied_from': str(proposal_source.relative_to(ROOT)), 'path': str(destination.relative_to(ROOT)),
                     'role': 'same fixed proposal heuristic; no posterior samples pooled'})
    proposals[lens] = proposal
    model_path = ROOT / control['controls']['20']['path']
    assert sha(model_path) == control['controls']['20']['sha256']
    isolated = yaml.safe_load(model_path.read_text())
    native_points = model_path.parent / 'native_points.json'
    point_records = json.loads(native_points.read_text())['points']
    group = f'upper20_{lens}4095'
    for seed, label in zip(range(first_seed, first_seed + 4), ['original_reference', 'selected_latest_frozen_row', 'mass_6_eV', 'mass_12_eV']):
        point = deepcopy(control['points'][label])
        assert point_records[label]['point'] == point and point_records[label]['status'] == 'finite_native_target'
        cfg = deepcopy(baseline)
        cfg['params']['mnu']['prior']['max'] = 20.0
        for name, value in point.items():
            cfg['params'][name]['ref'] = value
            assert cfg['params'][name]['prior']['min'] <= value <= cfg['params'][name]['prior']['max']
        model = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
        for name in point: model['params'][name]['ref'] = isolated['params'][name]['ref']
        assert model == isolated
        cfg['run_name'] = f'fresh_CAMB_{group}_seed{seed}'
        cfg['sampler']['mcmc']['seed'] = seed
        cfg['sampler']['mcmc']['covmat'] = str(destination)
        cfg['notes'].update({'mass_prior': 'uniform[0,20] eV', 'initial_point_label': label,
                             'numerical_target': group, 'math_review': 'Wider-prior control; independent output and RNG; posterior qualification pending.'})
        folder = HERE / f'seed{seed}'; folder.mkdir(exist_ok=False)
        config_path = folder / 'input.yaml'
        with config_path.open('x') as f: f.write(yaml.safe_dump(cfg, sort_keys=False))
        run_dir = f'runs/20261004_math_review_fresh_CAMB_{group}_seed{seed}'
        assert not (ROOT / run_dir).exists()
        entry = {'seed': seed, 'lens': lens, 'group': group, 'kind': 'spt_desi_fresh_CAMB_upper_prior_control',
                 **control['expected_environment'], 'config': str(config_path.relative_to(ROOT)),
                 'config_sha256': sha(config_path), 'run_dir': run_dir, 'initial_point': point,
                 'initial_point_label': label, 'baseline_group': baseline_group, 'baseline_config': str(source_path.relative_to(ROOT)),
                 'baseline_config_sha256': sha(source_path), 'control': str(native_points.relative_to(ROOT)),
                 'control_sha256': sha(native_points), 'proposal': proposal, 'implementation_sha256': implementation,
                 'launch_receipt': str((folder / 'launch_receipt.json').relative_to(ROOT)), 'scheduling_nice': 5,
                 'only_target_change': 'mass prior upper endpoint 5 to 20 eV', 'posterior_qualified': False}
        write(folder / 'preparation_receipt.json', entry); entries.append(entry)
write(HERE / 'preparation_receipt.json', {'utc': datetime.now(timezone.utc).isoformat(), 'entries': entries,
      'proposal_heuristics': proposals, 'targets': ['upper20_A4095', 'upper20_B4095'],
      'primary_40_samplers_changed': False, 'primary_samplers_and_wider_prior_controls_separate': True,
      'source_preflight_receipt_sha256': sha(control_root / 'preflight_receipt.json'),
      'prior_upper_eV': 20, 'new_samplers_per_target': 4, 'scheduling_nice': 5,
      'scope': 'empirical comparison of caps 5 and 20 eV after separate convergence qualification',
      'omitted_tail_or_quantile_stability_established': False, 'uniform_accuracy_certified': False,
      'paper_modified': False})
print('Eight configurations prepared for two separate 20 eV targets; no sampler launched yet.', flush=True)
