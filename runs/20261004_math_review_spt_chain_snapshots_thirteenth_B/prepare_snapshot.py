"""Freeze all six SPT B families after growth of the diagnostic-length history."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
previous_path = HERE.parent / '20261004_math_review_spt_chain_snapshots_eleventh_B/snapshot_receipt.json'
previous = json.loads(previous_path.read_text())
old = {f['original_seed']: f for f in previous['files']}
entries = [e for e in state['restoration_chains'] if e['kind'] == 'spt_desi' and e['lens'] == 'B']
assert sorted(e['seed'] for e in entries) == [305, 306, 307, 308, 403, 404]
assert not (HERE / 'snapshot_receipt.json').exists()
# Check growth before writing any scientific snapshot files.
previous_diagnostic=json.loads((previous_path.parent/'chain_B_diagnostics.json').read_text())
previous_length=previous_diagnostic['diagnostics']['mnu']['draws_per_chain']
preflight_lengths={}
for entry in entries:
    path=next((ROOT/entry['run_dir']/'chains').glob('*.1.txt'))
    raw=path.read_bytes();raw=raw[:raw.rfind(b'\n')+1]
    rows=np.atleast_2d(np.loadtxt(BytesIO(raw)))
    preflight_lengths[entry['seed']]=int(rows[int(.2*len(rows)):,0].sum())
if min(preflight_lengths.values()) < 1.2*previous_length:
    print(f'Growth threshold not met; no snapshots written. Minimum {min(preflight_lengths.values())}, required {1.2*previous_length:.0f}.')
    sys.exit(0)
files, configurations, retained = [], [], []
for entry in sorted(entries, key=lambda e: e['seed']):
    assert not entry.get('resume_seed')
    source = ROOT / entry['run_dir']
    destination = HERE / f"chain_B_seed{entry['seed']}"
    assert not destination.exists()
    (destination / 'chains').mkdir(parents=True)
    original = next((source / 'chains').glob('*.1.txt'))
    raw = original.read_bytes()
    complete = raw[:raw.rfind(b'\n') + 1]
    earlier = (ROOT / old[entry['seed']]['snapshot']).read_bytes()
    assert complete.startswith(earlier)
    assert hashlib.sha256(earlier).hexdigest() == old[entry['seed']]['sha256']
    target = destination / 'chains' / original.name
    target.write_bytes(complete)
    rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
    assert np.all(np.isfinite(rows)) and np.all(rows[:, 0] > 0)
    assert np.all(rows[:, 0] == np.floor(rows[:, 0]))
    retained_steps = int(rows[int(.2 * len(rows)):, 0].sum())
    retained.append(retained_steps)
    if entry['seed'] in [403, 404]:
        folder = '20261004_math_review_spt_internal_completion_B404/seed404' if entry['seed']==404 else '20261004_math_review_spt_sample_cap_completion_B403/seed403'
        frozen = HERE.parent / folder / 'chains' / original.name
        assert complete == frozen.read_bytes()
        assert not Path('/proc', str(entry['pid'])).exists()
    files.append({'source': str(original.relative_to(ROOT)), 'snapshot': str(target.relative_to(ROOT)),
                  'sha256': hashlib.sha256(complete).hexdigest(), 'snapshot_bytes': len(complete),
                  'stored_rows': len(rows), 'retained_represented_steps': retained_steps,
                  'original_seed': entry['seed'], 'active_segment_seed': entry['seed'],
                  'trajectory_scope': 'uninterrupted_saved_prefix',
                  'completed_family': entry['seed'] in [403,404]})
    for name in ['input.yaml', 'resolved.yaml']:
        data = (source / name).read_bytes()
        cfg = yaml.safe_load(data)
        saved = data
        if name == 'resolved.yaml':
            prefix = Path(cfg['output']).name
            assert original.name == prefix + '.1.txt'
            cfg['output'] = str(destination / 'chains' / prefix)
            saved = yaml.safe_dump(cfg, sort_keys=False).encode()
        p = destination / name
        p.write_bytes(saved)
        configurations.append({'source': str((source / name).relative_to(ROOT)),
                               'snapshot': str(p.relative_to(ROOT)),
                               'source_sha256': hashlib.sha256(data).hexdigest(),
                               'snapshot_sha256': hashlib.sha256(saved).hexdigest()})
old_diag = json.loads((HERE.parent / '20261004_math_review_spt_chain_snapshots_eleventh_B/chain_B_diagnostics.json').read_text())
old_length = old_diag['diagnostics']['mnu']['draws_per_chain']
assert min(retained) >= 1.2 * old_length
command = [sys.executable, str(ROOT / 'scripts/diagnose_cobaya_chains.py')]
for entry in sorted(entries, key=lambda e: e['seed']):
    command += ['--run-dir', str(HERE / f"chain_B_seed{entry['seed']}")]
command += ['--burnin-frac', '0.2', '--quantile-mcse-limit', '0.005',
            '--relative-quantile-mcse-limit', '0.05', '--output', str(HERE / 'chain_B_diagnostics.json')]
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'SPT_B_six_family_progress_diagnostics',
           'previous_snapshot_receipt': str(previous_path.relative_to(ROOT)),
           'previous_snapshot_receipt_sha256': hashlib.sha256(previous_path.read_bytes()).hexdigest(),
           'files': files, 'configurations': configurations, 'complete_lines_only': True,
           'previous_draws_per_chain': old_length, 'current_draws_per_chain': min(retained),
           'growth_fraction': min(retained) / old_length - 1,
           'completed_families_403_404_retained': True, 'SPT_A_reassessed': False,
           'CLASS_cohorts_included': False, 'diagnostic_gates_changed': False,
           'diagnostic_commands': {'chain_B': command},
           'diagnostic_script_sha256': hashlib.sha256((ROOT / 'scripts/diagnose_cobaya_chains.py').read_bytes()).hexdigest()}
with (HERE / 'snapshot_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(f"Six B families frozen; equalized diagnostic history growth {receipt['growth_fraction']:.1%}.")
