"""Verify owned original samplers and the separately launched guarded trial."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
original_module = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy/_classy.cpython-312-x86_64-linux-gnu.so')
assert hashlib.sha256(original_module.read_bytes()).hexdigest() == '38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a'
launch = json.loads((HERE / 'guarded_launch_receipt.json').read_text())
entries = [x for x in state['restoration_chains'] if x['kind'] == 'spt_desi']
entries += state['controlled_precision_posterior_chains']
entries += [x for x in state['controlled_precision_dragging_trials'] if x['seed'] != 701]
entries += state['controlled_precision_learned_proposal_trials']
entries += state['quadrature_repaired_posterior_chains']
assert len(entries) == 27 and len({x['pid'] for x in entries}) == 27
records = []
for entry in entries:
    proc = Path('/proc') / str(entry['pid'])
    raw = (proc / 'cmdline').read_bytes()
    command = raw.replace(b'\0', b' ').decode()
    identity = str(entry['run_dir']) in command
    if entry.get('resume_seed'):
        argv = raw.rstrip(b'\0').decode().split('\0')
        identity = (str(entry['recovery_dir']) in command and
                    (f"seed{entry['seed']}/resume_input.yaml" in command or
                     argv[-2:] == [str(Path(entry['recovery_dir']) / 'resume_verified_chain.py'),
                                   str(entry['seed'])]))
    assert identity, command
    maps = (proc / 'maps').read_text()
    if entry.get('kind') != 'spt_desi':
        assert str(original_module) in maps and launch['module'] not in maps
    chains = list((ROOT / entry['run_dir'] / 'chains').glob('*.txt'))
    assert len(chains) == 1
    raw_chain = chains[0].read_bytes()
    complete = raw_chain[:raw_chain.rfind(b'\n')+1]
    records.append({'seed': entry['seed'], 'pid': entry['pid'],
                    'command': command, 'run_dir': entry['run_dir'],
                    'process_start_ticks': int((proc / 'stat').read_text().split()[21]),
                    'complete_stored_rows': sum(bool(x.strip()) and not x.startswith(b'#')
                                                for x in complete.splitlines()),
                    'complete_chain_sha256': hashlib.sha256(complete).hexdigest()})
proc = Path('/proc') / str(launch['pid'])
command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
assert '20261004_math_review_class_python_repair/launch_guarded_trial.py' in command
maps = (proc / 'maps').read_text()
assert launch['module'] in maps and str(original_module) not in maps
assert hashlib.sha256(Path(launch['module']).read_bytes()).hexdigest() == launch['module_sha256']
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'original_backend_live_samplers': records,
           'guarded_trial': {'pid': launch['pid'], 'seed': 1201, 'command': command,
                             'native_module_mapped': launch['module'],
                             'native_module_sha256': launch['module_sha256'],
                             'process_start_ticks': int((proc / 'stat').read_text().split()[21])},
           'owned_live_scientific_processes': 28,
           'original_installed_native_module_unchanged': True,
           'guarded_trial_selected_new_rows_verified': False,
           'posterior_convergence_certified': False}
with (HERE / 'runtime_verification.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('27 original-backend samplers and one isolated guarded trial verified live.')
