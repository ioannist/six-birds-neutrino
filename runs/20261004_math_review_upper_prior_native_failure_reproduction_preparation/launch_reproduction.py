"""Attempt original seeded trajectory in an isolated diagnostic output directory."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
seed = int(sys.argv[1])
assert seed in [2003, 2004]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract_path = HERE / 'reproduction_contract.json'
contract = json.loads(contract_path.read_text())
entry = contract['entries'][str(seed)]
for path, digest in contract['worker_source_sha256'].items():
    assert sha(ROOT / path) == digest
for path, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert sha(ROOT / entry['config']) == entry['config_sha256']
assert sha(ROOT / entry['terminal_receipt']) == entry['terminal_receipt_sha256']
assert sha(entry['module']) == entry['module_sha256']
assert sha(entry['wrapper']) == entry['wrapper_sha256']
assert importlib.metadata.version('camb') == entry['solver_version']
assert importlib.metadata.version('cobaya') == entry['Cobaya_version']
assert os.getpriority(os.PRIO_PROCESS, 0) == 10
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    assert os.environ[key] == '1'
folder = HERE / f'seed{seed}'
assert folder.is_dir() and not (folder / 'launch_receipt.json').exists()
run_dir = ROOT / f'runs/20261004_math_review_upper_prior_seed{seed}_seeded_failure_reproduction'
assert not run_dir.exists()
from cobaya.model import Model
from failure_recording import call_and_record
original = Model.logposterior
def recorded_logposterior(self, values, *args, **kwargs):
    return call_and_record(original, self, values, folder, *args, **kwargs)
Model.logposterior = recorded_logposterior
stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed, 'pid': os.getpid(),
           'process_start_ticks': int(stat[19]), 'run_dir': str(run_dir.relative_to(ROOT)),
           'contract_sha256': sha(contract_path), 'native_module_sha256': sha(entry['module']),
           'source_config_sha256': sha(ROOT / entry['config']), 'scheduling_nice': 10,
           'scope': 'attempted seeded diagnostic reproduction; exact prefix equality must be verified',
           'original_failed_prefix_appended': False, 'posterior_qualified': False,
           'successful_logposterior_calls_return_original_result': True,
           'failure_recording_rethrows_original_exception': True}
with (folder / 'launch_receipt.json').open('x') as f:
    f.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
sys.path.insert(0, str(ROOT / 'scripts'))
sys.argv = [str(ROOT / 'scripts/run_cobaya.py'), '--config', str(ROOT / entry['config']),
            '--outdir', str(run_dir), '--seed', str(seed)]
runpy.run_path(str(ROOT / 'scripts/run_cobaya.py'), run_name='__main__')
