"""Launch a fresh grid12 trial only after its native target replay succeeds."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

import classy._classy as native

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
prep = json.loads((HERE / 'preparation_receipt.json').read_text())
proof = json.loads((HERE / 'initial_point_verification.json').read_text())
assert proof['initial_point_finite_native_target_verified']
assert proof['initial_point'] == prep['initial_point']
assert proof['config_sha256'] == prep['config_sha256']
module = Path(native.__file__).resolve()
assert module == Path(prep['native_module_path']).resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(module) == prep['native_module_sha256'] == proof['module_sha256']
assert sha(ROOT / prep['config']) == prep['config_sha256']
assert sha(ROOT / prep['covariance']) == prep['covariance_sha256'] == proof['covariance_sha256']
assert os.environ['OMP_NUM_THREADS'] == '4'
assert not (ROOT / prep['outdir']).exists() and not (HERE / 'launch_receipt.json').exists()
stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(), 'seed': prep['seed'], 'pid': os.getpid(),
    'process_start_ticks': int(stat[19]), 'cohort': 'grid12', 'lens': 'B',
    'outdir': prep['outdir'], 'module': str(module), 'module_sha256': prep['native_module_sha256'],
    'config_sha256': prep['config_sha256'], 'covariance_sha256': prep['covariance_sha256'],
    'native_initial_point_verification_sha256': sha(HERE / 'initial_point_verification.json'),
    'implementation_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__),
        ROOT / 'scripts/run_cobaya.py', ROOT / 'src/sbt_spt_audit/samplers.py',
        ROOT / 'src/sbt_spt_audit/mcmc.py', ROOT / 'src/sbt_spt_audit/metrics.py']},
    'environment': {k: os.environ.get(k) for k in ['PYTHONPATH', 'OMP_NUM_THREADS',
        'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']},
    'fresh_rng_and_output': True, 'historical_prefix_appended': False,
    'existing_sampler_modified_or_stopped': False,
    'pilot_covariance_is_not_a_certified_posterior_covariance': True,
    'posterior_convergence_or_uniform_accuracy_certified': False,
}
with (HERE / 'launch_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
sys.argv = [str(ROOT / 'scripts/run_cobaya.py'), '--config', str(ROOT / prep['config']),
            '--outdir', str(ROOT / prep['outdir']), '--seed', str(prep['seed'])]
runpy.run_path(str(ROOT / 'scripts/run_cobaya.py'), run_name='__main__')
