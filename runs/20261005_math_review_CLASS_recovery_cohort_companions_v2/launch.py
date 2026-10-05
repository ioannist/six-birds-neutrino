"""Start a fresh companion only after all six preflights and preparation review pass."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
seed = int(sys.argv[1])
folder = HERE / f'seed{seed}'
entry = json.loads((folder / 'preparation_receipt.json').read_text())
proof = json.loads((folder / 'native_preflight_receipt.json').read_text())
review = json.loads((HERE / 'preparation_self_review_receipt.json').read_text())
assert review['six_fresh_companions_reconstructed']
assert review['launcher_sha256'] == sha(__file__)
assert review['preparation_sha256'] == sha(HERE / 'preparation_receipt.json')
record = next(r for r in review['records'] if r['seed'] == seed)
assert record['native_preflight_sha256'] == sha(folder / 'native_preflight_receipt.json')
assert proof['fresh_initial_point_finite'] and proof['wrong_native_contract_refused']
assert proof['config_sha256'] == entry['config_sha256'] == sha(ROOT / entry['config'])
assert sha(ROOT / entry['proposal']) == entry['proposal_sha256']
assert sha(ROOT / entry['source_config']) == entry['source_config_sha256']
assert sha(ROOT / entry['anchor_config']) == entry['anchor_config_sha256']
assert sha(ROOT / entry['build_receipt']) == entry['build_receipt_sha256']
for path, digest in entry['implementation_sha256'].items():
    assert sha(ROOT / path) == digest
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import run_cobaya as launcher
import yaml
cfg = yaml.safe_load((ROOT / entry['config']).read_text())
backend = launcher._validate_native_backend(cfg)
assert backend['module_sha256'] == proof['module_sha256'] == entry['module_sha256']
assert os.environ['OMP_NUM_THREADS'] == entry['OMP_NUM_THREADS']
assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['MKL_NUM_THREADS'] == '1'
assert os.getpriority(os.PRIO_PROCESS, 0) == entry['scheduling_nice'] == 5
assert not (ROOT / entry['run_dir']).exists()
stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
with (folder / 'launch_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed,
        'pid': os.getpid(), 'process_start_ticks': int(stat[19]), 'group': entry['group'],
        'module': backend['module'], 'module_sha256': backend['module_sha256'],
        'config_sha256': entry['config_sha256'], 'run_dir': entry['run_dir'],
        'preflight_sha256': sha(folder / 'native_preflight_receipt.json'),
        'preparation_self_review_sha256': sha(HERE / 'preparation_self_review_receipt.json'),
        'fresh_rng_and_output': True, 'old_prefix_appended': False,
        'independent_PRNG_streams_or_stationarity_proved': False, 'posterior_qualified': False},
        f, indent=2, allow_nan=False)
    f.write('\n')
sys.argv = [str(ROOT / 'scripts/run_cobaya.py'), '--config', str(ROOT / entry['config']),
            '--outdir', str(ROOT / entry['run_dir']), '--seed', str(seed)]
runpy.run_path(str(ROOT / 'scripts/run_cobaya.py'), run_name='__main__')
