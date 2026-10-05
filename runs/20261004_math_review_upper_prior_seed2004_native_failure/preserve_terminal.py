from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
entry = next(e for e in state['upper_prior_posterior_chains'] if e['seed'] == 2004)
helper = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
assert sha(helper) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
spec = importlib.util.spec_from_file_location('identity', helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
absence = module.observe_retired_identity(entry['pid'], entry['process_start_ticks'])
assert absence['original_identity_absent']
source = ROOT / entry['run_dir']
files = []
sources = [(p, HERE / 'terminal_bundle' / p.relative_to(source))
           for p in sorted(source.rglob('*')) if p.is_file()]
launch = ROOT / entry['launch_receipt']
sources += [(p, HERE / 'launch_bundle' / p.name) for p in
            [ROOT / entry['config'], launch, launch.with_name('launcher_stdout.txt'),
             launch.with_name('launcher_stderr.txt')]]
for original, frozen in sources:
    frozen.parent.mkdir(parents=True, exist_ok=True)
    assert not frozen.exists()
    before = sha(original)
    shutil.copyfile(original, frozen)
    assert before == sha(original) == sha(frozen)
    files.append({'source': str(original.relative_to(ROOT)),
                  'frozen': str(frozen.relative_to(ROOT)),
                  'bytes': frozen.stat().st_size, 'sha256': before})
stderr = (source / 'stderr.txt').read_text()
assert stderr == 'ValueError: provider spectrum tt must be finite and 1D.\n'
assert 'cobaya_success: False' in (source / 'summary.md').read_text()
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(), 'seed': 2004,
    'pid': entry['pid'], 'process_start_ticks': entry['process_start_ticks'],
    'managed_session': 26593, 'exit_code': 1,
    'managed_session_status': 'closed_exit1_polled_current_goal_turn',
    'identity_observation': absence, 'run_dir': entry['run_dir'],
    'error_type': 'ValueError', 'error': 'provider spectrum tt must be finite and 1D.',
    'stderr_exact': stderr,
    'last_logged_progress': {'utc': '2026-10-04 22:57:56', 'steps': 622, 'accepted': 225},
    'terminal_output_files': files, 'registered_entry': entry,
    'exact_failing_proposal_available': False, 'checkpoint_contains_RNG_state': False,
    'posterior_qualified': False, 'numerical_failure_is_not_prior_or_posterior_rejection': True,
    'original_prefix_appended_to_new_policy': False, 'original_scientific_process_modified': False,
}
with (HERE / 'terminal_receipt.json').open('x') as f:
    f.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('Terminal seed2004 outputs frozen:', len(files), 'files; native failure explicit.')
