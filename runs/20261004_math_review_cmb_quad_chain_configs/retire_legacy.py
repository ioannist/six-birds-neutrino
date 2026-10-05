"""Preserve and retire verified owned legacy default-CMB processes for repaired inference."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
proof = json.loads((HERE / 'target_verification.json').read_text())
manifest = json.loads((HERE / 'manifest.json').read_text())
assert proof['manifest_sha256'] == hashlib.sha256((HERE / 'manifest.json').read_bytes()).hexdigest()
assert len(proof['records']) == 2 and manifest['replicas_per_lens'] == 4
assert manifest['total_omp_threads'] == 32
repair = json.loads((ROOT / 'runs/20261004_math_review_class_tca_failure_seed505/background_quadrature_omp4.json').read_text())
assert repair['succeeded'] and repair['omp_threads'] == '4'
assert repair['declared_precision_overrides'] == {'tol_ncdm_bg': 1e-8}
state_path = ROOT / 'runs/20261003_math_review_validation/review_state.json'
state = json.loads(state_path.read_text())
chains = [entry for entry in state['restoration_chains'] if entry['kind'] == 'cmb_desi']
assert len(chains) == 8
archive_root = ROOT / 'runs/20261004_math_review_cmb_legacy_retirement'
assert not archive_root.exists()
descriptors = {}
for entry in chains:
    proc = Path('/proc') / str(entry['pid'])
    if not proc.exists():
        assert entry['seed'] == 505 and entry['terminal_exit_code'] == 1
        continue
    cmd = (proc / 'cmdline').read_bytes()
    identity = Path(entry['run_dir']).name.encode() in cmd or (
        entry.get('recovery_dir') and entry['recovery_dir'].encode() in cmd and str(entry['seed']).encode() in cmd)
    assert identity
    descriptors[entry['seed']] = os.pidfd_open(entry['pid'])
assert len(descriptors) == 7
archive_root.mkdir()
request = {'utc': datetime.now(timezone.utc).isoformat(),
           'reason': 'replace default numerical target that reproducibly fails inside prior support with explicit quadrature-repaired target',
           'process_identity_and_pidfd_verified': True,
           'agent_requested_sigterm': True,
           'seeds': sorted(descriptors),
           'new_target_verification_sha256': hashlib.sha256((HERE / 'target_verification.json').read_bytes()).hexdigest(),
           'old_trajectories_will_not_be_appended_to_new_target': True}
(archive_root / 'stop_request_receipt.json').write_text(json.dumps(request, indent=2) + '\n')
for descriptor in descriptors.values():
    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
for seed, descriptor in descriptors.items():
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    deadline = time.monotonic() + 5
    while not poller.poll(100):
        assert time.monotonic() < deadline, ('Await exact owned process termination', seed)
    os.close(descriptor)
records = []
for entry in chains:
    source = ROOT / entry['run_dir']
    destination = archive_root / f"seed{entry['seed']}"
    shutil.copytree(source, destination)
    if entry.get('resume_seed'):
        log = ROOT / entry['recovery_dir'] / f"seed{entry['seed']}" / 'resume_stdout.txt'
        shutil.copyfile(log, destination / 'active_resume_stdout.txt')
    hashes = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in destination.rglob('*') if path.is_file()}
    chain_file = next((destination / 'chains').glob('*.txt'))
    raw = chain_file.read_bytes()
    complete = raw[:raw.rfind(b'\n') + 1]
    rows = sum(bool(line.strip()) and not line.lstrip().startswith(b'#') for line in complete.splitlines())
    records.append({'seed': entry['seed'], 'last_active_segment_seed': entry.get('resume_seed', entry['seed']),
                    'old_pid': entry['pid'], 'old_exec_session': entry['exec_session'],
                    'source_run_dir': entry['run_dir'], 'archive_run_dir': str(destination.relative_to(ROOT)),
                    'agent_requested_sigterm': entry['seed'] in descriptors,
                    'known_prior_native_failure_exit_code': 1 if entry['seed'] == 505 else None,
                    'chain_raw_bytes': len(raw), 'chain_complete_prefix_bytes': len(complete),
                    'complete_saved_rows': rows, 'chain_sha256': hashlib.sha256(raw).hexdigest(),
                    'archive_file_sha256': hashes})
    if entry['seed'] != 505:
        entry.update(status='retired_agent_requested_sigterm_default_target_archived',
                     retirement_archive=str(archive_root.relative_to(ROOT)),
                     retirement_utc=datetime.now(timezone.utc).isoformat())
        runtime_path = source / 'runtime_state.json'
        runtime = json.loads(runtime_path.read_text()) if runtime_path.exists() else dict(entry)
        runtime.update(status=entry['status'], agent_requested_sigterm=True,
                       retirement_archive=entry['retirement_archive'], retirement_utc=entry['retirement_utc'])
        runtime_path.write_text(json.dumps(runtime, indent=2) + '\n')
state['retired_default_cmb_cohort'] = str(archive_root.relative_to(ROOT))
state['default_cmb_cohort_retirement_reason'] = request['reason']
state['default_chain_seed505_recovery_pending_defined_numerical_target'] = False
state['default_cmb_unchanged_target_continuation_planned'] = False
state_path.write_text(json.dumps(state, indent=2, allow_nan=False) + '\n')
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
           'all_eight_legacy_families_preserved': True, 'seven_owned_processes_signaled_and_observed_terminal': True,
           'managed_exit_collection_pending': True, 'new_numerical_target_will_use_fresh_files': True,
           'unwritten_holding_history_reconstructed': False, 'posterior_convergence_verified': False}
(archive_root / 'preservation_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('Eight legacy families preserved; seven exact owned processes retired after verified repaired-target preparation.')
