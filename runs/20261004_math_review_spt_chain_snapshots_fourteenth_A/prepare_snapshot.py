"""Freeze all six SPT A families after growth of the diagnostic-length history."""
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
previous_path = HERE.parent / '20261004_math_review_spt_chain_snapshots_twelfth_A/snapshot_receipt.json'
previous = json.loads(previous_path.read_text())
old = {f['original_seed']: f for f in previous['files']}
entries = [e for e in state['restoration_chains'] if e['kind'] == 'spt_desi' and e['lens'] == 'A']
assert sorted(e['seed'] for e in entries) == [301, 302, 303, 304, 401, 402]
assert not (HERE / 'snapshot_receipt.json').exists()
# Cache complete prefixes and check growth before writing any snapshot files.
old_diag = json.loads((HERE.parent / '20261004_math_review_spt_chain_snapshots_twelfth_A/chain_A_diagnostics.json').read_text())
old_length = old_diag['diagnostics']['mnu']['draws_per_chain']
cached, current_lengths = {}, []
for entry in entries:
    source = ROOT / entry['run_dir']
    original = next((source / 'chains').glob('*.1.txt'))
    raw = original.read_bytes()
    complete = raw[:raw.rfind(b'\n') + 1]
    rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
    assert np.all(np.isfinite(rows)) and np.all(rows[:, 0] > 0)
    assert np.all(rows[:, 0] == np.floor(rows[:, 0]))
    cached[entry['seed']] = (original, complete)
    current_lengths.append(int(rows[len(rows)//5:, 0].sum()))
if min(current_lengths) < 1.2 * old_length:
    print(json.dumps({'status': 'growth_threshold_not_reached_no_snapshot_written',
                      'minimum': min(current_lengths), 'required': int(np.ceil(1.2 * old_length))}))
    sys.exit(3)
files, configurations, retained = [], [], []
for entry in sorted(entries, key=lambda e: e['seed']):
    assert not entry.get('resume_seed')
    source = ROOT / entry['run_dir']
    destination = HERE / f"chain_A_seed{entry['seed']}"
    assert not destination.exists()
    (destination / 'chains').mkdir(parents=True)
    original, complete = cached[entry['seed']]
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
    if entry['seed'] in (401, 402):
        frozen = HERE.parent / '20261004_math_review_spt_sample_cap_completion' / f"seed{entry['seed']}" / 'chains' / original.name
        assert complete == frozen.read_bytes()
        assert not Path('/proc', str(entry['pid'])).exists()
    files.append({'source': str(original.relative_to(ROOT)), 'snapshot': str(target.relative_to(ROOT)),
                  'sha256': hashlib.sha256(complete).hexdigest(), 'snapshot_bytes': len(complete),
                  'stored_rows': len(rows), 'retained_represented_steps': retained_steps,
                  'original_seed': entry['seed'], 'active_segment_seed': entry['seed'],
                  'trajectory_scope': 'uninterrupted_saved_prefix',
                  'completed_family': entry['seed'] in (401, 402)})
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
old_diag = json.loads((HERE.parent / '20261004_math_review_spt_chain_snapshots_twelfth_A/chain_A_diagnostics.json').read_text())
old_length = old_diag['diagnostics']['mnu']['draws_per_chain']
assert min(retained) >= 1.2 * old_length
command = [sys.executable, str(ROOT / 'scripts/diagnose_cobaya_chains.py')]
for entry in sorted(entries, key=lambda e: e['seed']):
    command += ['--run-dir', str(HERE / f"chain_A_seed{entry['seed']}")]
command += ['--burnin-frac', '0.2', '--quantile-mcse-limit', '0.005',
            '--relative-quantile-mcse-limit', '0.05', '--output', str(HERE / 'chain_A_diagnostics.json')]
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'fourteenth_SPT_A_six_family_growth_qualified_diagnostics',
           'previous_snapshot_receipt': str(previous_path.relative_to(ROOT)),
           'previous_snapshot_receipt_sha256': hashlib.sha256(previous_path.read_bytes()).hexdigest(),
           'files': files, 'configurations': configurations, 'complete_lines_only': True,
           'previous_draws_per_chain': old_length, 'current_draws_per_chain': min(retained),
           'growth_fraction': min(retained) / old_length - 1,
           'completed_families_401_402_retained': True, 'SPT_B_reassessed': False,
           'CLASS_cohorts_included': False, 'diagnostic_gates_changed': False,
           'diagnostic_commands': {'chain_A': command},
           'diagnostic_dependency_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT / 'scripts/extract_mnu_limits.py', ROOT / 'src/sbt_spt_audit/mcmc.py', ROOT / 'src/sbt_spt_audit/mcmc_diagnostics.py']},
           'diagnostic_script_sha256': hashlib.sha256((ROOT / 'scripts/diagnose_cobaya_chains.py').read_bytes()).hexdigest()}
with (HERE / 'snapshot_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(f"Six A families frozen; equalized diagnostic history growth {receipt['growth_fraction']:.1%}.")
