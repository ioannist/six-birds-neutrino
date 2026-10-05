"""Launch only after source, native control and preparation reviews close."""
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
folder = HERE / f'seed{seed}'
entry = json.loads((folder / 'preparation_receipt.json').read_text())
proof = json.loads((folder / 'initial_point_verification.json').read_text())
combined_path = ROOT / 'runs/20261005_math_review_sigma_time_v3_packaged/combined_policy_self_review_receipt.json'
combined = json.loads(combined_path.read_text())
review_path = HERE / 'preparation_self_review_receipt.json'
review = json.loads(review_path.read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert combined['selected_CMB_controls'] == 20 and combined['warnings_remaining'] == 0
assert combined['policy_sha256'] == entry['policy_sha256'] == sha(ROOT / entry['policy'])
assert combined['module_sha256'] == entry['module_sha256']
assert review['all_sixteen_initial_points_verified'] and review['source_targets_rederived']
assert review['combined_policy_review_sha256'] == sha(combined_path)
assert proof['native_initial_point_verified'] and proof['initial_point'] == entry['initial_point']
assert proof['upstream_forced_fresh_likes_and_priors_exact'] and proof['provider_arrays_exact']
import camb
import cobaya.theories.camb.camb as wrapper
module = Path(camb.baseconfig.camblib._name).resolve()
assert str(module) == entry['module'] and sha(module) == entry['module_sha256'] == proof['module_sha256']
assert camb.__version__ == entry['solver_version'] == importlib.metadata.version('camb')
assert importlib.metadata.version('cobaya') == entry['Cobaya_version']
assert str(Path(wrapper.__file__).resolve()) == entry['wrapper'] and sha(wrapper.__file__) == entry['wrapper_sha256']
assert sha(ROOT / entry['config']) == entry['config_sha256'] == proof['config_sha256']
assert sha(ROOT / entry['build_receipt']) == entry['build_receipt_sha256']
assert sha(ROOT / entry['proposal']['path']) == entry['proposal']['sha256']
for path, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
assert os.getpriority(os.PRIO_PROCESS, 0) == 5
assert all(os.environ[k] == '1' for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'])
assert os.environ['LD_LIBRARY_PATH'] == entry['required_LD_LIBRARY_PATH']
assert not (ROOT / entry['run_dir']).exists()
stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed, 'lens': entry['lens'], 'group': entry['group'],
    'pid': os.getpid(), 'process_start_ticks': int(stat[19]), 'module': str(module), 'module_sha256': sha(module),
    'solver_version': entry['solver_version'], 'Cobaya_version': entry['Cobaya_version'],
    'wrapper_sha256': entry['wrapper_sha256'], 'config_sha256': entry['config_sha256'],
    'proposal_sha256': entry['proposal']['sha256'], 'implementation_sha256': entry['implementation_sha256'],
    'policy_sha256': entry['policy_sha256'], 'build_receipt_sha256': entry['build_receipt_sha256'],
    'combined_policy_review_sha256': sha(combined_path), 'preparation_self_review_sha256': sha(review_path),
    'initial_point_verification_sha256': sha(folder / 'initial_point_verification.json'),
    'run_dir': entry['run_dir'], 'fresh_rng_and_output': True, 'old_prefix_appended': False,
    'production_adopted': False, 'posterior_certified': False,
    'environment': {k: os.environ[k] for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'PYTHONPATH', 'LD_LIBRARY_PATH']}}
with (folder / 'launch_receipt.json').open('x') as f:
    f.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
sys.path.insert(0, str(ROOT / 'scripts'))
sys.argv = [str(ROOT / 'scripts/run_cobaya.py'), '--config', str(ROOT / entry['config']),
            '--outdir', str(ROOT / entry['run_dir']), '--seed', str(seed)]
runpy.run_path(str(ROOT / 'scripts/run_cobaya.py'), run_name='__main__')
