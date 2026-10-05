"""Locate logged proposal updates in existing frozen diagnostic histories."""
from datetime import datetime, timezone
from fractions import Fraction as Q
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
runtime_path = HERE / 'runtime_observation.json'
runtime = json.loads(runtime_path.read_text())
owned = {r['seed']: r for r in runtime['records']}
entries = [e for e in state['restoration_chains'] if e['kind'] == 'spt_desi']
for key in ['guarded_solver_posterior_trials', 'guarded_quadrature_posterior_chains',
            'guarded_medium_posterior_chains']:
    entries += state[key]
entries = {e['seed']: e for e in entries}
groups = {
    'SPT_A': (state['latest_SPT_A_diagnostic_bundle'], None),
    'SPT_B': (state['latest_SPT_B_diagnostic_bundle'], None),
    **{k: (v, k) for k, v in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items()},
}
records, files = [], []
for group, (bundle, wanted) in groups.items():
    receipt_path = ROOT / bundle / 'snapshot_receipt.json'
    receipt = json.loads(receipt_path.read_text())
    files.append({'path': str(receipt_path.relative_to(ROOT)), 'sha256': digest(receipt_path)})
    for item in receipt['files']:
        if wanted is not None and item['group'] != wanted:
            continue
        seed = item.get('seed', item.get('original_seed'))
        entry = entries[seed]
        chain_path = ROOT / item['snapshot']
        raw = chain_path.read_bytes()
        assert digest(chain_path) == item['sha256']
        live_path = ROOT / item['source']
        assert live_path.read_bytes().startswith(raw)
        rows = np.atleast_2d(np.loadtxt(BytesIO(raw)))
        assert np.all(rows[:, 0] > 0) and np.all(rows[:, 0] == np.floor(rows[:, 0]))
        count = len(rows)
        burn = int(.2 * count)
        config_path = chain_path.parents[1] / 'resolved.yaml'
        cfg = yaml.safe_load(config_path.read_text())
        options, = cfg['sampler'].values()
        assert options['learn_proposal'] is True and options['oversample_thin'] is False
        assert options['oversample_power'] == 0 and options.get('temperature', 1) == 1
        source = ROOT / entry['run_dir'] / 'stdout.txt'
        log_raw = source.read_bytes()
        log_raw = log_raw[:log_raw.rfind(b'\n') + 1]
        saved = HERE / f'seed{seed}' / 'stdout_prefix.txt'
        saved.parent.mkdir()
        saved.write_bytes(log_raw)
        check, updates = None, []
        for line in log_raw.decode().splitlines():
            match = re.search(r'Learn \+ convergence test @ (\d+) samples accepted\.', line)
            if match:
                check = int(match[1])
            if 'Updated covariance matrix of proposal pdf.' in line:
                assert check is not None
                updates.append(check)
        assert updates == sorted(set(updates))
        assert owned[seed]['pid'] == entry['pid']
        records.append({
            'cohort': group, 'seed': seed, 'pid': entry['pid'],
            'runtime_status': owned[seed]['status'],
            'frozen_chain': item['snapshot'], 'frozen_chain_sha256': item['sha256'],
            'frozen_config_sha256': digest(config_path),
            'stored_rows': count, 'discarded_stored_rows': burn,
            'retained_represented_steps': sum(int(x) for x in rows[burn:, 0]),
            'log_snapshot': str(saved.relative_to(ROOT)), 'log_snapshot_sha256': digest(saved),
            'logged_update_collection_sizes': updates,
            'updates_strictly_inside_retained_history': [n for n in updates if burn < n < count],
            'update_at_retained_left_boundary': burn in updates,
            'update_after_last_frozen_row': count in updates,
            'updates_later_than_frozen_history': [n for n in updates if n > count],
            'absence_of_logged_updates_is_not_a_convergence_certificate': True,
        })
        files.append({'path': str(saved.relative_to(ROOT)), 'sha256': digest(saved)})
assert len(records) == len({r['seed'] for r in records}) == 28

# Two exact reversible kernels for the same uniform target. Choosing the kernel
# from the current state need not leave that target invariant.
target = [Q(1, 2), Q(1, 2)]
identity = [[Q(1), Q(0)], [Q(0), Q(1)]]
flip = [[Q(0), Q(1)], [Q(1), Q(0)]]
def push(p, kernel):
    return [sum(p[i] * kernel[i][j] for i in range(2)) for j in range(2)]
for kernel in [identity, flip]:
    assert push(target, kernel) == target
    assert all(target[i] * kernel[i][j] == target[j] * kernel[j][i]
               for i in range(2) for j in range(2))
adaptive = [flip[0], identity[1]]
assert push(target, adaptive) == [Q(0), Q(1)] != target

upstream = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/cobaya/samplers/mcmc/mcmc.py')
upstream_saved = HERE / 'pinned_cobaya_mcmc.py'
upstream_saved.write_bytes(upstream.read_bytes())
files.append({'path': str(upstream_saved.relative_to(ROOT)), 'sha256': digest(upstream_saved)})
files.append({'path': str(Path(__file__).relative_to(ROOT)), 'sha256': digest(Path(__file__))})
out = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'existing_frozen_histories_and_later_individually_frozen_logs_not_atomic_checkpoints',
    'row_coordinate_basis': 'check_ready uses len(collection); updates apply after N stored rows; output thinning disabled',
    'upstream_source': str(upstream), 'upstream_sha256': digest(upstream),
    'upstream_version': '3.6.2', 'runtime_receipt': str(runtime_path.relative_to(ROOT)),
    'runtime_receipt_sha256': digest(runtime_path), 'records': records, 'files': files,
    'families_with_updates_inside_retained_history': sum(bool(r['updates_strictly_inside_retained_history']) for r in records),
    'guarded_quadrature_families_with_any_logged_update': sum(bool(r['logged_update_collection_sizes']) for r in records if r['cohort'].startswith('quad_')),
    'exact_counterexample': {
        'target': ['1/2', '1/2'], 'identity_kernel': [[1, 0], [0, 1]],
        'flip_kernel': [[0, 1], [1, 0]], 'both_kernels_target_reversible': True,
        'selection': 'flip if current state is 0; identity if current state is 1',
        'selected_transition': [[0, 1], [0, 1]], 'one_step_from_target': [0, 1],
        'scope': 'arbitrary adaptation counterexample; not a Cobaya failure or model of its adaptation',
    },
    'SPT_diagnostic_gate_results_changed': False,
    'adaptive_MCMC_convergence_theorem_established': False,
    'sampler_or_burn_or_gates_changed': False,
    'paper_modified': False,
}
with (HERE / 'adaptation_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps({k: out[k] for k in ['families_with_updates_inside_retained_history',
      'guarded_quadrature_families_with_any_logged_update']}, indent=2))
