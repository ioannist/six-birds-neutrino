"""Exercise real PID reuse and refusal to hide an original live identity."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('review_retirement_identity', HERE / 'retirement_identity.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
observe = module.observe_retired_identity
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
live = state['fresh_CAMB_posterior_chains'][0]
ticks = int((Path('/proc', str(live['pid'])) / 'stat').read_text().rsplit(')', 1)[1].split()[19])
assert ticks == live['process_start_ticks']
checks = []
same = observe(live['pid'], ticks)
assert not same['original_identity_absent'] and same['status'] == 'original_process_identity_present'
checks.append({'case': 'actual_original_live_identity_is_refused', 'observation': same})
different = observe(live['pid'], ticks - 1)
assert different['original_identity_absent'] and different['status'] == 'PID_reused_by_different_identity'
checks.append({'case': 'same_actual_PID_different_start_is_distinguished', 'observation': different})
fixture = HERE / 'proc_controls'; fixture.mkdir(exist_ok=False)
missing = observe(8001, 42, fixture)
assert missing['original_identity_absent'] and missing['status'] == 'PID_not_present'
checks.append({'case': 'missing_PID_is_absent', 'observation': missing})
directory = fixture / '8001'; directory.mkdir()
fields = ['Z'] + ['1'] * 18 + ['42']
with (directory / 'stat').open('x') as f: f.write('8001 (name (with) spaces) ' + ' '.join(fields) + '\n')
zombie = observe(8001, 42, fixture)
assert not zombie['original_identity_absent'] and zombie['observed_state'] == 'Z'
assert zombie['observed_process_name'] == 'name (with) spaces'
checks.append({'case': 'same_identity_zombie_remains_present_with_parentheses_in_name', 'observation': zombie})
reused = observe(8001, 41, fixture)
assert reused['original_identity_absent']
checks.append({'case': 'reused_fixture_PID_with_distinct_start_is_absent', 'observation': reused})
for pid, start in [(0, 1), (8001, 0), (8001, True)]:
    try: observe(pid, start, fixture)
    except ValueError: checks.append({'case': 'invalid_identity_refused', 'pid': pid, 'start': start})
    else: raise AssertionError('Invalid identity silently accepted')
with patch.object(Path, 'read_text', side_effect=PermissionError('controlled unreadable stat')):
    try: observe(8001, 42, fixture)
    except PermissionError: checks.append({'case': 'unreadable_stat_is_not_treated_as_absence'})
    else: raise AssertionError('Unreadable stat treated as absent')
record = json.loads((HERE / 'observed_counterexample.json').read_text())
assert record['observations']
assert all(r['current_start_ticks'] != r['original_start_ticks'] for r in record['observations'])
assert any(r['seed'] == 303 and r['current_process_name'] == 'lean' for r in record['observations'])
assert len(checks) == 9
with (HERE / 'controls_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'controls': checks,
                       'real_counterexample_receipt_sha256': hashlib.sha256((HERE / 'observed_counterexample.json').read_bytes()).hexdigest(),
                       'helper_sha256': hashlib.sha256((HERE / 'retirement_identity.py').read_bytes()).hexdigest(),
                       'original_live_identity_guard_preserved': True, 'processes_signaled_or_modified': False}, indent=2) + '\n')
print('Nine controls pass, including actual live-identity refusal and three observed reused PIDs.')
