"""Enforce fresh recovery configuration and native preflight identity."""
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
seed = int(sys.argv[1])
folder = HERE / f'seed{seed}'
entry = json.loads((folder / 'preparation_receipt.json').read_text())
proof = json.loads((folder / 'native_preflight_receipt.json').read_text())
review = json.loads((HERE / 'preparation_self_review_receipt.json').read_text())
assert review['both_recovery_targets_rederived'] and proof['selected_terminal_row_native_match']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
import classy
module = Path(importlib.import_module(classy.Class.__module__).__file__).resolve()
assert str(module) == entry['module'] and sha(module) == entry['module_sha256'] == proof['module_sha256']
assert sha(ROOT / entry['config']) == entry['config_sha256'] == proof['config_sha256']
assert sha(ROOT / entry['proposal']) == entry['proposal_sha256']
assert sha(ROOT / entry['terminal_receipt']) == entry['terminal_receipt_sha256']
assert sha(ROOT / entry['build_receipt']) == entry['build_receipt_sha256']
for path, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert os.environ['OMP_NUM_THREADS'] == entry['OMP_NUM_THREADS']
assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['MKL_NUM_THREADS'] == '1'
assert os.getpriority(os.PRIO_PROCESS, 0) == entry['scheduling_nice'] == 5
assert not (ROOT / entry['run_dir']).exists()
stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed, 'parent_seed': entry['parent_seed'],
    'pid': os.getpid(), 'process_start_ticks': int(stat[19]), 'module': str(module), 'module_sha256': sha(module),
    'config_sha256': entry['config_sha256'], 'proposal_sha256': entry['proposal_sha256'],
    'implementation_sha256': entry['implementation_sha256'], 'run_dir': entry['run_dir'],
    'preflight_sha256': sha(folder / 'native_preflight_receipt.json'),
    'preparation_review_sha256': sha(HERE / 'preparation_self_review_receipt.json'),
    'fresh_rng_and_output': True, 'old_prefix_appended': False, 'exact_resume_asserted': False,
    'posterior_qualified': False, 'environment': {k: os.environ[k] for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'PYTHONPATH']}}
with (folder / 'launch_receipt.json').open('x') as f:
    f.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
sys.argv = [str(ROOT / 'scripts/run_cobaya.py'), '--config', str(ROOT / entry['config']),
            '--outdir', str(ROOT / entry['run_dir']), '--seed', str(seed)]
runpy.run_path(str(ROOT / 'scripts/run_cobaya.py'), run_name='__main__')
