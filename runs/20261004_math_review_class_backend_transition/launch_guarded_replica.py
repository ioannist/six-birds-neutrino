"""Launch one fresh replacement after its archived endpoints pass native evaluation."""
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    seed = int(sys.argv[1])
    preparation = json.loads((HERE / 'preparation_receipt.json').read_text())
    entries = [entry for entry in preparation['records'] if entry['replacement_seed'] == seed]
    assert len(entries) == 1
    entry = entries[0]
    terminal = json.loads((HERE / 'managed_termination_receipt.json').read_text())
    assert next(record for record in terminal['records'] if record['seed'] == entry['seed'])['exit_code'] == 143
    proof_path = HERE / 'parent_native_checks' / f'seed{seed}.json'
    proof = json.loads(proof_path.read_text())
    module = Path(importlib.import_module(classy.Class.__module__).__file__)
    expected = '7a5d736220b3d236f3dc7c89944d025fe3e4c7cb4c8e4473ef807c898fc71539'
    assert sha(module) == expected == proof['module_sha256']
    config = ROOT / entry['config']
    covariance = ROOT / entry['covariance']
    chain = ROOT / entry['archived_chain']
    assert sha(config) == entry['config_sha256'] == proof['config_sha256']
    assert sha(covariance) == entry['covariance_sha256']
    assert sha(chain) == entry['archived_chain_sha256'] == proof['chain_sha256']
    assert proof['fresh_initial_point_finite_native_target_verified']
    assert len(proof['checks']) == 2 and proof['checks'][-1]['point'] == entry['fixed_initial_point']
    assert os.environ['OMP_NUM_THREADS'] == str(entry['replacement_omp_threads'])
    assert not (ROOT / entry['outdir']).exists()
    proc = Path('/proc') / str(entry['pid'])
    if proc.exists():
        stat = (proc / 'stat').read_text().split()
        assert int(stat[21]) != entry['process_start_ticks'] or stat[2] == 'Z'
    receipt = {
        'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed, 'pid': os.getpid(),
        'cohort': entry['cohort'], 'lens': entry['lens'], 'outdir': entry['outdir'],
        'parent_family_seed': entry['seed'], 'parent_active_segment_seed': entry.get('resume_seed', entry['seed']),
        'module': str(module), 'module_sha256': expected,
        'config_sha256': sha(config), 'covariance_sha256': sha(covariance),
        'native_parent_verification_sha256': sha(proof_path),
        'implementation_sha256': {
            str(path.relative_to(ROOT)): sha(path) for path in
            [Path(__file__), ROOT / 'scripts/run_cobaya.py', ROOT / 'src/sbt_spt_audit/samplers.py',
             ROOT / 'src/sbt_spt_audit/mcmc.py', ROOT / 'src/sbt_spt_audit/metrics.py',
             ROOT / 'src/sbt_spt_audit/likelihoods/desi_dr2_bao.py']},
        'environment': {key: os.environ.get(key) for key in
                        ['PYTHONPATH', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                         'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']},
        'fresh_rng_and_output': True, 'historical_prefix_appended': False,
        'full_domain_original_backend_identity_asserted': False,
        'posterior_convergence_certified': False,
        'uniform_numerical_accuracy_certified': False,
    }
    folder = HERE / 'launches'
    folder.mkdir(exist_ok=True)
    with (folder / f'seed{seed}.json').open('x') as handle:
        handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    sys.argv = [str(ROOT / 'scripts/run_cobaya.py'), '--config', str(config),
                '--outdir', str(ROOT / entry['outdir']), '--seed', str(seed)]
    runpy.run_path(str(ROOT / 'scripts/run_cobaya.py'), run_name='__main__')


if __name__ == '__main__':
    main()
