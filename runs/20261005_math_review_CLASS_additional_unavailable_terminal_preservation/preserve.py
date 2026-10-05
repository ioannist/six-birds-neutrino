"""Freeze nine absent original identities without inventing unavailable exit reasons."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


state_path = ROOT / 'runs/20261003_math_review_validation/review_state.json'
state = read(state_path)
baseline_path = ROOT / 'runs/20261005_math_review_registered66_recovery_checkpoint/combined_runtime_verification.json'
baseline = read(baseline_path)
old = {r['seed']: r for r in baseline['records']}
helper = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
assert sha(helper) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
spec = importlib.util.spec_from_file_location('identity', helper)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
seeds = [1302, 1303, 1307, 1308, 1401, 1402, 1403, 1404, 1405]
entries = {e['seed']: e for key in ['guarded_quadrature_posterior_chains', 'guarded_medium_posterior_chains']
           for e in state[key]}
records = []
for seed in seeds:
    e = entries[seed]
    observed = identity.observe_retired_identity(e['pid'], old[seed]['process_start_ticks'])
    assert observed['original_identity_absent']
    assert old[seed]['status'] == 'live_same_owned_native_identity'
    run = ROOT / e['run_dir']
    assert not (run / 'stderr.txt').read_bytes()
    assert not (run / 'summary.json').exists()
    folder = HERE / f'seed{seed}'
    folder.mkdir(exist_ok=False)
    outputs = folder / 'outputs'
    outputs.mkdir()
    files = []
    for source in sorted(run.rglob('*')):
        if not source.is_file():
            continue
        assert not source.is_symlink()
        frozen = outputs / source.relative_to(run)
        frozen.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        with frozen.open('xb') as f:
            f.write(raw)
        digest = hashlib.sha256(raw).hexdigest()
        assert sha(source) == sha(frozen) == digest
        files.append({'source': str(source.relative_to(ROOT)), 'frozen': str(frozen.relative_to(ROOT)),
                      'bytes': len(raw), 'sha256': digest})
    launch = ROOT / e['launch_receipt']
    with (folder / 'original_launch_receipt.json').open('xb') as f:
        f.write(launch.read_bytes())
    chain = next(outputs.joinpath('chains').glob('*.1.txt'))
    raw = chain.read_bytes()
    prefix = raw[:raw.rfind(b'\n') + 1]
    lines = prefix.decode().splitlines()
    header = lines[0].lstrip('#').split()
    rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
    assert len(header) == len(set(header)) and rows
    assert all(len(row) == len(header) and np.isfinite(list(map(float, row))).all() for row in rows)
    weights = [Fraction(row[0]) for row in rows]
    assert all(w > 0 and w.denominator == 1 for w in weights)
    terminal = {'utc': datetime.now(timezone.utc).isoformat(), 'registered_entry': deepcopy(e),
        'last_verified_live_identity': old[seed], 'last_runtime_snapshot': str(baseline_path.relative_to(ROOT)),
        'last_runtime_snapshot_sha256': sha(baseline_path), 'identity_observation': observed,
        'managed_handle_observation': f'write_stdin failed: Unknown process id {e["exec_session"]}',
        'exit_code': None, 'exit_reason': None, 'native_failure_established': False,
        'terminal_output_files': files, 'original_launch_receipt_sha256': sha(launch),
        'complete_chain_prefix_sha256': hashlib.sha256(prefix).hexdigest(),
        'stored_complete_rows': len(rows),
        'retained_represented_steps': sum(int(w) for w in weights[len(weights) // 5:]),
        'last_complete_row': dict(zip(header, rows[-1])), 'exact_resume_state_available': False,
        'scope': 'Original identity absent and managed handle unavailable. Output preserved; no exit cause or successful completion inferred.'}
    receipt = folder / 'terminal_receipt.json'
    write(receipt, terminal)
    e.update(status='terminal_exit_reason_unavailable_preserved',
             terminal_receipt=str(receipt.relative_to(ROOT)), terminal_receipt_sha256=sha(receipt))
    records.append({'seed': seed, 'terminal_receipt': str(receipt.relative_to(ROOT)),
                    'terminal_receipt_sha256': sha(receipt),
                    'retained_represented_steps': terminal['retained_represented_steps']})

for group, value in baseline['growth_by_cohort'].items():
    if group not in ['medium_A', 'medium_B', 'quad_A', 'quad_B']:
        continue
    terminals = [seed for seed in value['seeds'] if seed in entries and entries[seed]['status'].startswith('terminal_')]
    if group == 'medium_A':
        terminals = [1201] + terminals
    state['guarded_CLASS_terminal_family_status'].setdefault(group, {}).update(
        terminal_family_seeds=terminals, assessment_eligible_pending_terminal_review=False,
        recovery_pending=True)
with state_path.open('w') as f:
    json.dump(state, f, indent=2, allow_nan=False)
    f.write('\n')
write(HERE / 'preservation_receipt.json', {'utc': datetime.now(timezone.utc).isoformat(),
    'records': records, 'new_unknown_exit_registrations': 9, 'exit_causes_not_inferred': True,
    'old_prefixes_appended_or_restarted': False, 'original_cohort_membership_preserved': True})
print('Nine additional unknown exits preserved byte-for-byte; no restart or numerical failure inferred.')
