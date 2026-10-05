"""Launch a fresh trial only with the verified private native solver build."""
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import runpy
import sys

import classy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    build = json.loads((HERE / 'build_verification_receipt.json').read_text())
    prepared = json.loads((HERE / 'recovery_preparation_receipt.json').read_text())
    parent = json.loads((HERE / 'parent_native_target_verification.json').read_text())
    module = Path(importlib.import_module(classy.Class.__module__).__file__)
    config = HERE / 'A_seed1201.yaml'
    outdir = ROOT / prepared['outdir']
    assert str(module) == build['module']
    assert digest(module) == build['module_sha256'] == parent['module_sha256']
    assert digest(config) == prepared['config_sha256'] == parent['config_sha256']
    assert digest(HERE / 'recovery_initial.covmat') == prepared['initial_covariance_sha256']
    assert parent['chain_sha256'] == prepared['parent_chain_sha256']
    assert digest(ROOT / prepared['parent_chain']) == parent['chain_sha256']
    assert len(parent['checks']) == 2
    assert all(all(value == 0 for value in check['fresh_minus_recorded'].values())
               for check in parent['checks'])
    assert not outdir.exists(), 'Fresh output required; historical prefixes must not be appended'
    assert prepared['seed'] == 1201 and not prepared['historical_prefix_appended']
    assert not prepared['new_backend_same_numerical_target_as_unmodified_backend_asserted']
    assert os.environ['OMP_NUM_THREADS'] == '8'
    receipt = {
        'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
        'seed': prepared['seed'], 'outdir': prepared['outdir'],
        'parent_family_seed': 701, 'parent_active_segment_seed': 901,
        'module': str(module), 'module_sha256': digest(module),
        'patch_sha256': digest(ROOT / 'patches/class-3.4.0-finite-jacobian.patch'),
        'config_sha256': digest(config),
        'implementation_sha256': {
            str(path.relative_to(ROOT)): digest(path)
            for path in [Path(__file__), ROOT / 'scripts/run_cobaya.py',
                         ROOT / 'src/sbt_spt_audit/samplers.py',
                         ROOT / 'src/sbt_spt_audit/mcmc.py']},
        'environment': {key: os.environ.get(key) for key in
                        ['PYTHONPATH', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                         'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'XLA_FLAGS']},
        'fresh_segment': True, 'historical_prefix_appended': False,
        'posterior_convergence_certified': False,
        'uniform_numerical_accuracy_certified': False,
    }
    receipt_path = HERE / 'guarded_launch_receipt.json'
    with receipt_path.open('x') as handle:
        handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    sys.argv = [str(ROOT / 'scripts/run_cobaya.py'), '--config', str(config),
                '--outdir', str(outdir), '--seed', str(prepared['seed'])]
    runpy.run_path(str(ROOT / 'scripts/run_cobaya.py'), run_name='__main__')


if __name__ == '__main__':
    main()
