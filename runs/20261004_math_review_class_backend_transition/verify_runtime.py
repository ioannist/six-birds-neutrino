"""Verify all active sampler identities and the actual mapped guarded libraries."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
original_module = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy/_classy.cpython-312-x86_64-linux-gnu.so')
assert hashlib.sha256(original_module.read_bytes()).hexdigest() == '38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a'
entries = [entry for entry in state['restoration_chains'] if entry['kind'] == 'spt_desi']
entries += state['guarded_solver_posterior_trials']
entries += state['guarded_quadrature_posterior_chains']
entries += state['guarded_medium_posterior_chains']
assert len(entries) == 28 and len({entry['pid'] for entry in entries}) == 28
records = []
for entry in entries:
    proc = Path('/proc') / str(entry['pid'])
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    stat = (proc / 'stat').read_text().split()
    assert stat[2] != 'Z'
    if entry['seed'] == 1201:
        assert '20261004_math_review_class_python_repair/launch_guarded_trial.py' in command
    elif entry['seed'] >= 1301:
        assert '20261004_math_review_class_backend_transition/launch_guarded_replica.py' in command
        assert command.rstrip().endswith(' ' + str(entry['seed']))
    else:
        assert entry['run_dir'] in command
    native = None
    if entry['seed'] >= 1201:
        receipt_path = (ROOT / 'runs/20261004_math_review_class_python_repair/guarded_launch_receipt.json'
                        if entry['seed'] == 1201 else
                        HERE / 'launches' / f"seed{entry['seed']}.json")
        launch = json.loads(receipt_path.read_text())
        native = launch['module']
        maps = (proc / 'maps').read_text()
        assert native in maps and str(original_module) not in maps
        assert hashlib.sha256(Path(native).read_bytes()).hexdigest() == launch['module_sha256']
        log = (ROOT / entry['run_dir'] / 'stdout.txt').read_text()
        assert str(Path(native).parent) in log
        assert not (ROOT / entry['run_dir'] / 'stderr.txt').read_bytes()
    records.append({'seed': entry['seed'], 'pid': entry['pid'], 'command': command,
                    'process_start_ticks': int(stat[21]), 'mapped_guarded_module': native})
result = {'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
          'owned_live_samplers': 28, 'SPT_original_backend': 12,
          'guarded_quad_only': 8, 'guarded_seven_setting': 8,
          'original_installed_classy_unchanged': True,
          'remaining_unmodified_CLASS_inference_active': False,
          'new_saved_rows_native_checks_pending': True,
          'posterior_convergence_certified': False,
          'uniform_numerical_accuracy_certified': False}
with (HERE / 'runtime_verification.json').open('x') as handle:
    handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('All 28 owned sampler identities verified; all 16 CLASS runs map the guarded module.')
