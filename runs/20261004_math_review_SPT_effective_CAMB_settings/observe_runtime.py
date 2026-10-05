"""Observe all owned samplers during the SPT CAMB settings audit."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
previous_path = ROOT / 'runs/20261004_math_review_class_backend_transition/runtime_verification.json'
previous = {r['seed']: r for r in json.loads(previous_path.read_text())['records']}
entries = [e for e in state['restoration_chains'] if e['kind'] == 'spt_desi']
for key in ['guarded_solver_posterior_trials', 'guarded_quadrature_posterior_chains',
            'guarded_medium_posterior_chains', 'guarded_grid12_posterior_trials']:
    entries += state[key]
assert len(entries) == len({e['pid'] for e in entries}) == 32
assert {e['seed'] for e in state['guarded_grid12_posterior_trials']} == {1501, 1502, 1503, 1504}
original = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy/_classy.cpython-312-x86_64-linux-gnu.so')
assert hashlib.sha256(original.read_bytes()).hexdigest() == '38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a'
records, launches = [], []
for entry in entries:
    seed, pid = entry['seed'], entry['pid']
    proc = Path('/proc', str(pid))
    if seed in [401, 402, 403, 404]:
        assert not proc.exists()
        records.append({'seed': seed, 'pid': pid, 'status': 'completed_scientific_process_absent'})
        continue
    if seed >= 1501:
        path = ROOT / entry['launch_receipt']
        launch = json.loads(path.read_text())
        assert launch['seed'] == seed and launch['pid'] == pid
        expected = {'process_start_ticks': launch['process_start_ticks'], 'module': launch['module']}
        launches.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    else:
        expected = {'process_start_ticks': previous[seed]['process_start_ticks'],
                    'module': previous[seed]['mapped_guarded_module']}
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert stat[0] != 'Z' and int(stat[19]) == expected['process_start_ticks']
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    if seed >= 1501:
        assert f'seed{seed}/launch_trial.py' in command
    else:
        assert command == previous[seed]['command']
    run = ROOT / entry['run_dir']
    assert not (run / 'stderr.txt').read_bytes()
    if seed >= 1201:
        maps = (proc / 'maps').read_text()
        assert expected['module'] in maps and str(original) not in maps
        assert hashlib.sha256(Path(expected['module']).read_bytes()).hexdigest() == entry['native_module_sha256']
    log = (run / 'stdout.txt').read_text()
    progress = re.findall(r'Progress @ ([^\n]+) : (\d+) steps taken, and (\d+) accepted', log)
    record = {'seed': seed, 'pid': pid, 'status': 'live_same_owned_identity',
              'command': command, 'process_start_ticks': expected['process_start_ticks'],
              'mapped_guarded_module': expected['module'], 'stderr_empty': True}
    if progress:
        utc, steps, accepted = progress[-1]
        record['latest_progress'] = {'utc': utc, 'steps': int(steps), 'accepted': int(accepted)}
    records.append(record)
assert sum(r['status'] == 'live_same_owned_identity' for r in records) == 28
out = {'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
       'earlier_identity_receipt': str(previous_path.relative_to(ROOT)),
       'earlier_identity_receipt_sha256': hashlib.sha256(previous_path.read_bytes()).hexdigest(),
       'grid12_launch_receipts': launches, 'owned_live_samplers': 28, 'SPT_live': 8,
       'guarded_CLASS_live': 20, 'grid12_B_live': 4, 'SPT_diagnostic_families': 12,
       'completed_SPT_families': [401, 402, 403, 404], 'original_CLASS_inference_active': False,
       'precision_cohorts_pooled': False, 'posterior_convergence_certified': False}
with (HERE / 'runtime_observation.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('28 owned samplers verified: 8 SPT and 20 guarded CLASS; four B grid12 replicas.')
