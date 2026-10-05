"""Self-review native preflights and actual same-target replica activations."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
runtime = json.loads((HERE / 'activation_runtime_observation.json').read_text())
identities = {r['seed']: r for r in runtime['records']}
base = yaml.safe_load((HERE.parent / '20261004_math_review_guarded_grid12_trial_B_seed1501/input.yaml').read_text())
clean = lambda ps: {n: {k: v for k, v in p.items() if k not in ['ref', 'proposal']}
                   if isinstance(p, dict) else p for n, p in ps.items()}
records, files = [], []
for seed in [1501, 1502, 1503, 1504]:
    folder = HERE.parent / f'20261004_math_review_guarded_grid12_trial_B_seed{seed}'
    prep = json.loads((folder / 'preparation_receipt.json').read_text())
    launch = json.loads((folder / 'launch_receipt.json').read_text())
    native = json.loads((folder / 'initial_point_verification.json').read_text())
    cfg = yaml.safe_load((folder / 'run/resolved.yaml').read_text())
    assert clean(cfg['params']) == clean(base['params'])
    assert cfg['theory'] == base['theory'] and cfg['likelihood'] == base['likelihood']
    assert cfg.get('prior') == base.get('prior')
    sampler = deepcopy(cfg['sampler'])
    sampler['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] = 1501
    assert sampler == base['sampler']
    assert native['initial_point_finite_native_target_verified']
    assert native['initial_point'] == prep['initial_point']
    assert len(native['native_chi2']) == 6 and np.all(np.isfinite(list(native['native_chi2'].values())))
    assert np.isfinite(native['native_logposterior']) and np.all(np.isfinite(native['native_logprior']))
    assert native['config_sha256'] == prep['config_sha256'] == launch['config_sha256']
    assert native['module_sha256'] == prep['native_module_sha256'] == launch['module_sha256']
    assert native['covariance_sha256'] == prep['covariance_sha256'] == launch['covariance_sha256']
    assert hashlib.sha256((folder / 'input.yaml').read_bytes()).hexdigest() == launch['config_sha256']
    assert hashlib.sha256((ROOT / prep['covariance']).read_bytes()).hexdigest() == launch['covariance_sha256']
    assert hashlib.sha256((folder / 'initial_point_verification.json').read_bytes()).hexdigest() == launch['native_initial_point_verification_sha256']
    assert launch['fresh_rng_and_output'] and not launch['historical_prefix_appended']
    assert not launch['existing_sampler_modified_or_stopped']
    for path, expected in launch['implementation_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    witness = json.loads((folder / 'run/solver_backend.json').read_text())
    assert witness['module_sha256'] == launch['module_sha256']
    owned = identities[seed]
    assert owned['status'] == 'live_same_owned_identity' and owned['pid'] == launch['pid']
    assert owned['process_start_ticks'] == launch['process_start_ticks']
    records.append({'seed': seed, 'pid': launch['pid'], 'initial_mass_eV': prep['initial_point']['mnu_sample'],
                    'actual_target_definitions_and_backend_match': True,
                    'saved_row_native_check_pending': seed != 1501})
    for name in ['input.yaml', 'preparation_receipt.json', 'launch_receipt.json', 'activation_receipt.json',
                 'initial_point_verification.json', 'run/resolved.yaml', 'run/solver_backend.json']:
        p = folder / name
        files.append({'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
assert len({r['pid'] for r in records}) == 4
assert runtime['owned_live_samplers'] == 28 and runtime['guarded_CLASS_live'] == 20
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_review',
       'scope': 'four_start_B_grid12_cohort_activation_native_preflight_and_runtime_identity',
       'records': records, 'files': files,
       'runtime_observation_sha256': hashlib.sha256((HERE / 'activation_runtime_observation.json').read_bytes()).hexdigest(),
       'verification_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'same_target_across_four_grid12_chains': True, 'four_distinct_seeds_and_starting_points': True,
       'old_numerical_target_histories_appended': False, 'other_precision_cohorts_pooled': False,
       'posterior_convergence_or_uniform_accuracy_certified': False}
with (HERE / 'activation_verification.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Four same-target starts, native preflights and recorded activations pass self-review.')
