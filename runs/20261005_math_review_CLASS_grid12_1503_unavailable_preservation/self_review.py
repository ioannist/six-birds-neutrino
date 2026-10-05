"""Recount complete frozen histories and verify every unavailable-exit boundary."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
state = read(ROOT / 'runs/20261003_math_review_validation/review_state.json')
entries = {e['seed']: e for key in ['guarded_quadrature_posterior_chains', 'guarded_medium_posterior_chains', 'guarded_grid12_posterior_trials']
           for e in state[key]}
helper = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
assert sha(helper) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
spec = importlib.util.spec_from_file_location('identity', helper)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
records = []
for item in read(HERE / 'preservation_receipt.json')['records']:
    seed = item['seed']
    receipt_path = ROOT / item['terminal_receipt']
    receipt = read(receipt_path)
    entry = entries[seed]
    assert sha(receipt_path) == item['terminal_receipt_sha256'] == entry['terminal_receipt_sha256']
    assert entry['status'] == 'terminal_exit_reason_unavailable_preserved'
    assert receipt['exit_code'] is None and receipt['exit_reason'] is None
    assert not receipt['native_failure_established']
    assert 'Unknown process id' in receipt['managed_handle_observation']
    old = receipt['last_verified_live_identity']
    assert identity.observe_retired_identity(entry['pid'], old['process_start_ticks'])['original_identity_absent']
    baseline = read(ROOT / receipt['last_runtime_snapshot'])
    assert sha(ROOT / receipt['last_runtime_snapshot']) == receipt['last_runtime_snapshot_sha256']
    assert next(r for r in baseline['records'] if r['seed'] == seed) == old
    assert old['status'] == 'live_same_owned_native_identity'
    for f in receipt['terminal_output_files']:
        assert sha(ROOT / f['source']) == sha(ROOT / f['frozen']) == f['sha256']
        assert (ROOT / f['frozen']).stat().st_size == f['bytes']
    assert sha(ROOT / entry['launch_receipt']) == receipt['original_launch_receipt_sha256']
    assert sha(HERE / f'seed{seed}/original_launch_receipt.json') == receipt['original_launch_receipt_sha256']
    chain = next((HERE / f'seed{seed}/outputs/chains').glob('*.1.txt'))
    raw = chain.read_bytes()
    prefix = raw[:raw.rfind(b'\n') + 1]
    assert hashlib.sha256(prefix).hexdigest() == receipt['complete_chain_prefix_sha256']
    lines = prefix.decode().splitlines()
    header = lines[0].lstrip('#').split()
    rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
    assert len(header) == len(set(header)) and all(len(row) == len(header) for row in rows)
    assert np.isfinite(np.array(rows, dtype=float)).all()
    weights = [Fraction(row[0]) for row in rows]
    assert all(w > 0 and w.denominator == 1 for w in weights)
    assert len(rows) == receipt['stored_complete_rows']
    assert sum(int(w) for w in weights[len(weights) // 5:]) == receipt['retained_represented_steps']
    assert dict(zip(header, rows[-1])) == receipt['last_complete_row']
    checkpoint = next((HERE / f'seed{seed}/outputs/chains').glob('*.checkpoint'))
    fields = next(iter(yaml.safe_load(checkpoint.read_text())['sampler'].values()))
    assert set(fields) == {'converged', 'Rminus1_last', 'burn_in', 'mpi_size'}
    assert not fields['converged'] and not receipt['exact_resume_state_available']
    records.append({'seed': seed, 'terminal_receipt_sha256': sha(receipt_path),
                    'retained_represented_steps': receipt['retained_represented_steps'],
                    'preserved_checkpoint_fields': sorted(fields)})
assert {r['seed'] for r in records} == {1503}
for group in ['grid12_B']:
    assert not state['guarded_CLASS_terminal_family_status'][group]['assessment_eligible_pending_terminal_review']
with (HERE / 'self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'records': records,
        'output_tree_and_complete_history_reconstructed': True,
        'exit_codes_and_causes_unavailable': True, 'exact_resume_state_not_supplied': True,
        'original_cohort_membership_preserved': True, 'posterior_qualification_asserted': False},
        f, indent=2, allow_nan=False)
    f.write('\n')
print('One unknown exit reconstructed; original families retained and causes unasserted.')
