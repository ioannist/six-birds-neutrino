"""Distinct structural and witness review of the read-only retirement repair."""
from datetime import datetime, timezone
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
preparation = json.loads((HERE / 'observer_preparation_receipt.json').read_text())
reviewed = []
for record in preparation['records']:
    source, destination = ROOT / record['source'], ROOT / record['destination']
    assert sha(source) == record['source_sha256']
    assert sha(destination) == record['destination_sha256']
    reversed_text = destination.read_text()
    for old, new in reversed(record['retirement_block_changes']):
        assert reversed_text.count(new) == 1
        reversed_text = reversed_text.replace(new, old, 1)
    if destination.name == 'observe_all_runtime.py':
        for replacement in [
            "'retired_identity_observations': retired_identity_observations, ",
            "'retired_identity_observations': primary['retired_identity_observations'], ",
        ]:
            assert reversed_text.count(replacement) == 1
            reversed_text = reversed_text.replace(replacement, '', 1)
        assert reversed_text.count('all_16_old_policy_process_identities_absent') == 2
        reversed_text = reversed_text.replace('all_16_old_policy_process_identities_absent',
                                              'all_16_old_policy_processes_absent')
    assert reversed_text.encode() == source.read_bytes()
    reviewed.append({'source': record['source'], 'destination': record['destination'],
                     'reverse_bytes_equal': True})
baseline_path = ROOT / 'runs/20261004_math_review_fresh_CAMB_posterior_preparation/runtime_before_preparation.json'
manifest = json.loads((ROOT / preparation['baseline_manifest']).read_text())
pin = next(e for e in manifest['files'] if e['path'] == str(baseline_path.relative_to(ROOT)))
assert sha(baseline_path) == pin['sha256'] == preparation['identity_baseline_sha256']
baseline = {e['seed']: e for e in json.loads(baseline_path.read_text())['records']}
retired = json.loads((ROOT / 'runs/20261004_math_review_fresh_CAMB_posterior_preparation/old_policy_retirement_receipt.json').read_text())['records']
retry = ROOT / preparation['class_observer_retry']
assert sha(retry) == preparation['class_observer_retry_sha256'] == sha(HERE / 'observe_primary_runtime.py')
runtime_path = retry.with_name('runtime_observation.json')
runtime = json.loads(runtime_path.read_text())
assert runtime['owned_live_samplers'] == len(runtime['records']) == 40
observations = {e['seed']: e for e in runtime['retired_identity_observations']}
assert set(observations) == {e['seed'] for e in retired}
for e in retired:
    b, o = baseline[e['seed']], observations[e['seed']]
    assert e['pid'] == b['pid'] == o['pid']
    assert o['expected_start_ticks'] == b['process_start_ticks'] > 0
    assert o['original_identity_absent']
    if 'process_start_ticks' in e:
        assert e['process_start_ticks'] == b['process_start_ticks']
    if 'observed_start_ticks' in o:
        assert o['observed_start_ticks'] != o['expected_start_ticks']
    else:
        assert o['status'] == 'PID_not_present'
controls = json.loads((HERE / 'controls_receipt.json').read_text())
assert len(controls['controls']) == 9
assert controls['helper_sha256'] == sha(HERE / 'retirement_identity.py') == preparation['helper_sha256']
assert controls['controls'][0]['observation']['original_identity_absent'] is False
assert controls['controls'][1]['observation']['original_identity_absent'] is True
assert controls['real_counterexample_receipt_sha256'] == sha(HERE / 'observed_counterexample.json')
helper_ast = ast.parse((HERE / 'retirement_identity.py').read_text())
for n in ast.walk(helper_ast):
    if isinstance(n, ast.Call):
        name = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, 'id', '')
        assert name not in ['kill', 'killpg', 'system', 'Popen', 'run', 'write_text', 'write_bytes']
combined_failure = json.loads((HERE / 'combined_runtime_failure_receipt.json').read_text())
assert combined_failure['exit_code'] == 1 and combined_failure['failed_seed'] == 2003
assert not (HERE / 'all_runtime_verification.json').exists()
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'reversed_observers': reviewed, 'primary40_success_receipt': str(runtime_path.relative_to(ROOT)),
       'primary40_success_receipt_sha256': sha(runtime_path), 'original_identity_baseline_manifest_pin_verified': True,
       'retired_identity_witnesses_checked': 16, 'negative_and_boundary_controls_checked': 9,
       'live_checks_or_science_gates_weakened': False, 'helper_signals_or_mutates_processes': False,
       'combined48_attempt_terminal_seed2003_separately_classified': True,
       'uniform_native_accuracy_or_posterior_convergence_certified': False}
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Retirement repair self-review passed: unchanged live checks, 16 identity witnesses, nine controls.')
