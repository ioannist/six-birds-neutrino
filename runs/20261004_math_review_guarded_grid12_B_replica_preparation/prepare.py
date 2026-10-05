"""Prepare three distinct starts for the exact seed-1501 numerical target."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from sbt_spt_audit.mcmc import weighted_quantile
from sbt_spt_audit.metrics import covariance_solve

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'runs/20261004_math_review_guarded_grid12_trial_B_seed1501'
PREVIOUS = ROOT / 'runs/20261004_math_review_guarded_posterior_precision'
assert not (HERE / 'preparation_receipt.json').exists()
assert json.loads((BASE / 'first_saved_rows/completion_receipt.json').read_text())['exit_code'] == 0
anchor = yaml.safe_load((BASE / 'input.yaml').read_text())
native_prep = json.loads((BASE / 'preparation_receipt.json').read_text())
names = [n for n, p in anchor['params'].items() if isinstance(p, dict) and 'prior' in p]
covariance = ROOT / native_prep['covariance']
assert covariance.read_text().splitlines()[0].lstrip('#').split() == names
assert hashlib.sha256(covariance.read_bytes()).hexdigest() == native_prep['covariance_sha256']
covariance_solve(np.loadtxt(covariance), np.zeros(len(names)))
selections = json.loads((PREVIOUS / 'selection_receipt.json').read_text())
records = []
for seed, label in [(1502, 'quad_q95'), (1503, 'medium_q95'), (1504, 'second_cohort_seed1308_median')]:
    if seed in [1502, 1503]:
        selected = next(r for r in selections['selections'] if r['lens'] == 'B' and r['label'] == label)
        source = ROOT / selected['frozen_chain']
        witness = next(f for f in selections['files'] if f['snapshot'] == selected['frozen_chain'])
        assert hashlib.sha256(source.read_bytes()).hexdigest() == witness['sha256']
        index = selected['stored_row_zero_based']
    else:
        prior = ROOT / 'runs/20261004_math_review_guarded_CLASS_second_diagnostics/snapshot_receipt.json'
        snapshots = json.loads(prior.read_text())
        witness = next(f for f in snapshots['files'] if f['seed'] == 1308)
        source = ROOT / witness['snapshot']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == witness['sha256']
    header = source.read_text().splitlines()[0].lstrip('#').split()
    data = np.atleast_2d(np.loadtxt(source))
    if seed == 1504:
        burn = len(data) // 5
        median = weighted_quantile(data[burn:, header.index('mnu_sample')], data[burn:, 0], .5)
        index = burn + int(np.flatnonzero(data[burn:, header.index('mnu_sample')] == median)[0])
    point = {n: float(data[index, header.index(n)]) for n in names}
    assert np.all(np.isfinite(list(point.values())))
    assert all(anchor['params'][n]['prior']['min'] < x < anchor['params'][n]['prior']['max'] for n, x in point.items())
    cfg = deepcopy(anchor)
    cfg['run_name'] = f'math_guarded_grid12_trial_B_seed{seed}'
    cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] = seed
    for n, x in point.items():
        cfg['params'][n]['ref'] = x
    cfg['notes']['warm_start_fit'] = f'Declared immutable {label} coordinate; initialization only, not a grid12 posterior draw.'
    cfg['notes']['initialization_scope'] = f'Fresh seed {seed} and output; member of distinct-start B grid12 cohort; no older numerical histories appended.'
    folder = HERE.parent / f'20261004_math_review_guarded_grid12_trial_B_seed{seed}'
    folder.mkdir()
    target = folder / 'input.yaml'
    target.write_text(yaml.safe_dump(cfg, sort_keys=False))
    # Actual likelihood, prior, theory and parameter transformations are identical.
    assert cfg['likelihood'] == anchor['likelihood'] and cfg['theory'] == anchor['theory']
    assert cfg.get('prior') == anchor.get('prior')
    for n in names:
        actual = deepcopy(cfg['params'][n]); actual['ref'] = anchor['params'][n]['ref']
        assert actual == anchor['params'][n]
    prep = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'distinct_start_same_B_grid12_numerical_target',
            'seed': seed, 'lens': 'B', 'cohort': 'grid12', 'outdir': str((folder / 'run').relative_to(ROOT)),
            'config': str(target.relative_to(ROOT)), 'config_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'covariance': native_prep['covariance'], 'covariance_sha256': native_prep['covariance_sha256'],
            'initial_point': point, 'initialization_source': str(source.relative_to(ROOT)),
            'initialization_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'stored_row_zero_based': int(index), 'initialization_label': label,
            'native_module_path': native_prep['native_module_path'], 'native_module_sha256': native_prep['native_module_sha256'],
            'same_numerical_target_as_seed1501': True, 'pilot_covariance_certified': False,
            'old_history_appended_or_existing_sampler_modified': False}
    with (folder / 'preparation_receipt.json').open('x') as handle:
        handle.write(json.dumps(prep, indent=2, allow_nan=False) + '\n')
    records.append(prep)
points = [native_prep['initial_point']] + [p['initial_point'] for p in records]
assert len({tuple(p[n] for n in names) for p in points}) == 4
out = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'three_more_grid12_B_replicas_no_target_pooling',
       'reference_config': str((BASE / 'input.yaml').relative_to(ROOT)),
       'reference_config_sha256': hashlib.sha256((BASE / 'input.yaml').read_bytes()).hexdigest(),
       'reference_saved_row_replay': str((BASE / 'first_saved_rows/native_target_verification.json').relative_to(ROOT)),
       'records': records, 'four_distinct_initial_points': True, 'new_seeds': [1502, 1503, 1504],
       'native_initial_point_checks_required_before_launch': True,
       'posterior_convergence_or_uniform_accuracy_certified': False}
with (HERE / 'preparation_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps({p['seed']: p['initial_point']['mnu_sample'] for p in records}, indent=2))
