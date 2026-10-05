"""Archive owned unmodified CLASS runs and prepare fresh pinned-backend replicas."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import signal
import time

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE = ROOT / 'runs/20261003_math_review_validation/review_state.json'
SAMPLER = 'sbt_spt_audit.samplers.FullPrecisionMCMC'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def target(config):
    result = {key: deepcopy(config[key]) for key in ['likelihood', 'theory', 'params']}
    for block in result['params'].values():
        if isinstance(block, dict):
            block.pop('ref', None)
            block.pop('proposal', None)
    return result


state = json.loads(STATE.read_text())
entries = []
mapping = {601: 1401, 602: 1402, 603: 1403, 604: 1404, 702: 1405, 811: 1406, 813: 1407}
for key in ['controlled_precision_posterior_chains', 'controlled_precision_dragging_trials',
            'controlled_precision_learned_proposal_trials', 'quadrature_repaired_posterior_chains']:
    for entry in state[key]:
        if entry['seed'] == 701:
            continue
        item = deepcopy(entry)
        item.update(state_key=key,
                    cohort='quad' if key == 'quadrature_repaired_posterior_chains' else 'medium',
                    replacement_seed=entry['seed'] + 200 if key == 'quadrature_repaired_posterior_chains' else mapping[entry['seed']],
                    replacement_omp_threads=4 if key == 'quadrature_repaired_posterior_chains' else 8)
        entries.append(item)
assert len(entries) == 15 and len({x['pid'] for x in entries}) == 15
assert not (HERE / 'retirement_intent.json').exists()
hole = ROOT / 'runs/20261004_math_review_class_quadrature_hole_seed701/verification_receipt.json'
proof = json.loads(hole.read_text())
assert not proof['original_native_compute_succeeded'] and proof['guarded_native_compute_succeeded']
module = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy/_classy.cpython-312-x86_64-linux-gnu.so')
assert sha(module) == '38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a'
handles = []
for entry in entries:
    proc = Path('/proc') / str(entry['pid'])
    handle = os.pidfd_open(entry['pid'])
    handles.append(handle)
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    if entry.get('resume_seed'):
        assert entry['recovery_dir'] in command and command.rstrip().endswith(' ' + str(entry['seed']))
    else:
        assert entry['run_dir'] in command and '--seed ' + str(entry['seed']) in command
    assert str(module) in (proc / 'maps').read_text()
    entry.update(owned_command=command,
                 process_start_ticks=int((proc / 'stat').read_text().split()[21]))
intent = {'utc': datetime.now(timezone.utc).isoformat(), 'records': entries,
          'reason': 'known_quadrature_and_medium_native_solver_hole_replaced_by_verified_private_guarded_build',
          'hole_verification_sha256': sha(hole), 'signal': int(signal.SIGTERM),
          'historical_prefixes_will_not_be_appended': True,
          'stopping_and_diagnostic_thresholds_changed': False}
(HERE / 'retirement_intent.json').write_text(json.dumps(intent, indent=2) + '\n')
for handle in handles:
    signal.pidfd_send_signal(handle, signal.SIGTERM)
for handle in handles:
    os.close(handle)
deadline = time.monotonic() + 20
while True:
    remaining = [entry['pid'] for entry in entries if (Path('/proc') / str(entry['pid'])).exists()
                 and (Path('/proc') / str(entry['pid']) / 'stat').read_text().split()[2] != 'Z']
    if not remaining:
        break
    assert time.monotonic() < deadline, f'Owned processes still live: {remaining}; inspect, do not duplicate'
    time.sleep(.05)

boundary_source = ROOT / 'runs/20261003_math_review_controlled_chain_recovery/segment_boundaries.json'
boundary = json.loads(boundary_source.read_text())['segments']
shutil.copyfile(boundary_source, HERE / 'historical_segment_boundaries.json')
files = {}
prepared = []
groups = {}
for entry in entries:
    source = ROOT / entry['run_dir']
    archive = HERE / 'archives' / f"seed{entry['seed']}"
    shutil.copytree(source, archive / 'run')
    config_source = source / 'resolved.yaml'
    if entry.get('resume_seed'):
        recovery = ROOT / entry['recovery_dir'] / f"seed{entry['seed']}"
        shutil.copytree(recovery, archive / 'active_segment')
        config_source = recovery / 'resume_input.yaml'
    chain = next((archive / 'run/chains').glob('*.txt'))
    raw = chain.read_bytes()
    complete = raw[:raw.rfind(b'\n') + 1]
    assert raw == complete, 'Stopped chain has an incomplete final row; preserve and inspect before preparing'
    rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
    header = complete.splitlines()[0].decode().lstrip('#').split()
    assert len(set(header)) == len(header) and len(rows) >= 2
    assert np.isfinite(rows).all() and (rows[:, 0] > 0).all()
    assert (rows[:, 0] == np.floor(rows[:, 0])).all()
    historical_rows = 0
    if entry.get('resume_seed'):
        historical = next((archive / 'active_segment/chains').glob('*.txt')).read_bytes()
        assert sha(next((archive / 'active_segment/chains').glob('*.txt'))) == boundary[str(entry['seed'])]['historical_chain_sha256']
        assert raw.startswith(historical)
        historical_rows = boundary[str(entry['seed'])]['historical_saved_rows']
        assert len(rows) > historical_rows
    values = dict(zip(header, rows[-1]))
    original_config = yaml.safe_load(config_source.read_text())
    cfg = deepcopy(original_config)
    cfg.pop('resume', None)
    cfg.pop('output')
    sampled = [name for name, block in cfg['params'].items()
               if isinstance(block, dict) and 'prior' in block]
    assert len(sampled) == 10
    point = {name: float(values[name]) for name in sampled}
    for name, value in point.items():
        block = cfg['params'][name]
        assert block['prior']['min'] <= value <= block['prior']['max']
        block['ref'] = value
    new_seed = entry['replacement_seed']
    name = f"math_guarded_{entry['cohort']}_{entry['lens']}_seed{new_seed}"
    cfg['run_name'] = name
    options = cfg['sampler'][SAMPLER]
    options['seed'] = new_seed
    covariance = next((archive / 'run/chains').glob('*.covmat'))
    matrix = np.loadtxt(covariance)
    assert matrix.shape == (10, 10) and np.isfinite(matrix).all()
    assert covariance.read_text().splitlines()[0].lstrip('#').split() == sampled
    np.linalg.cholesky(matrix)
    options['covmat'] = str(covariance)
    old_options = original_config['sampler'][SAMPLER]
    assert {key: value for key, value in options.items() if key not in ['seed', 'covmat']} == {
        key: value for key, value in old_options.items() if key not in ['seed', 'covmat']}
    assert options['temperature'] == 1 and options['oversample_thin'] is False
    assert options['Rminus1_stop'] == .01 and options['Rminus1_cl_stop'] == .05
    assert options['Rminus1_cl_level'] == .95 and options['max_samples'] == 20000
    assert target(cfg) == target(original_config)
    numerical = cfg['theory']['classy']['extra_args']
    assert numerical['tol_ncdm_bg'] == 1e-8 and numerical['l_max_scalars'] == 4095
    if entry['cohort'] == 'quad':
        assert set(numerical) == {'N_ncdm', 'N_ur', 'l_max_scalars', 'tol_ncdm_bg'}
    else:
        assert numerical['tol_perturbations_integration'] == 1e-6
    cfg['notes']['solver_backend'] = 'Requires pinned private CLASS finite-Jacobian build; fresh seed and files. Do not pool unmodified-backend histories. Initial point and covariance are proposal inputs, not posterior certificates.'
    config = HERE / f"{entry['cohort']}_{entry['lens']}_seed{new_seed}.yaml"
    config.write_text(yaml.safe_dump(cfg, sort_keys=False))
    outdir = ROOT / 'runs' / f"20261004_math_review_guarded_{entry['cohort']}_chain_{entry['lens']}_seed{new_seed}"
    assert not outdir.exists()
    record = dict(entry, config=str(config.relative_to(ROOT)), config_sha256=sha(config),
                  outdir=str(outdir.relative_to(ROOT)),
                  archived_chain=str(chain.relative_to(ROOT)), archived_chain_sha256=sha(chain),
                  source_config=str(config_source.relative_to(ROOT)), source_config_sha256=sha(config_source),
                  archived_stored_rows=len(rows), historical_saved_rows=historical_rows,
                  last_complete_row_index=len(rows)-1, fixed_initial_point=point,
                  covariance=str(covariance.relative_to(ROOT)), covariance_sha256=sha(covariance),
                  physical_target_and_precision_unchanged=True,
                  original_backend_numerical_target_identity_asserted=False,
                  historical_prefix_appended=False, managed_terminal_exit_code=None)
    prepared.append(record)
    group = entry['cohort'] + '_' + entry['lens']
    current = target(cfg)
    if group in groups:
        assert groups[group] == current
    else:
        groups[group] = current
    for path in archive.rglob('*'):
        if path.is_file():
            files[str(path.relative_to(HERE))] = sha(path)
guarded = yaml.safe_load((ROOT / 'runs/20261004_math_review_class_python_repair/A_seed1201.yaml').read_text())
assert groups['medium_A'] == target(guarded)
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'records': prepared,
           'archive_file_sha256': files,
           'agent_requested_sigterm_owned_pids_absent_or_zombie': True,
           'original_installed_native_module_unchanged': sha(module) == '38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a',
           'prepared_new_runs': 15, 'quad_replicas_per_lens': 4,
           'medium_replicas_per_lens_including_existing_seed1201': 4,
           'historical_prefixes_appended': False, 'unknown_holding_time_reconstructed': False,
           'posterior_convergence_certified': False, 'uniform_numerical_accuracy_certified': False}
(HERE / 'preparation_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('15 original CLASS runs stopped and archived; fresh guarded configs prepared.')
