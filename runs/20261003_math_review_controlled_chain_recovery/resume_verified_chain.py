"""Resume a terminated precise chain after verifying its preserved endpoints.

Uses a fresh recorded RNG seed. This is a continuation of the sampled target,
not a reconstruction of the interrupted trajectory or its unwritten states.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.run import run


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def main():
    seed = int(sys.argv[1])
    receipt = json.loads((HERE / 'termination_receipt.json').read_text())
    entries = [entry for entry in receipt['records'] if entry['seed'] == seed]
    assert len(entries) == 1
    entry = entries[0]
    saved = HERE / f'seed{seed}'
    source = ROOT / entry['run_dir']
    proof_path = saved / 'native_target_verification.json'
    proof = json.loads(proof_path.read_text())
    assert proof['atol'] == 1e-7 and proof['rtol'] == 1e-10
    assert len(proof['chains']) == 1
    chain = proof['chains'][0]
    assert [check['row_index'] for check in chain['checks']] == [0, chain['total_stored_rows'] - 1]
    saved_chain = Path(chain['file'])
    assert hashlib.sha256(saved_chain.read_bytes()).hexdigest() == chain['file_sha256']
    live_chain = source / 'chains' / saved_chain.name
    assert live_chain.read_bytes() == saved_chain.read_bytes()
    terminal = json.loads((source / 'runtime_state.json').read_text())
    assert terminal['status'] == 'terminated_exit_143_partial_chain_preserved'
    try:
        os.kill(entry['pid'], 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError('Original PID still exists; do not duplicate a sampler.')
    cfg = yaml.safe_load((source / 'resolved.yaml').read_text())
    original_cfg_hash = hashlib.sha256((source / 'resolved.yaml').read_bytes()).hexdigest()
    assert original_cfg_hash == entry['source_file_sha256'][f'seed{seed}/resolved.yaml']
    options = cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
    assert options['seed'] == seed
    options['seed'] = entry['resume_seed']
    cfg['resume'] = True
    (saved / 'resume_input.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False))
    write(saved / 'resume_start.json', {
        'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
        'resume_seed': entry['resume_seed'], 'original_seed': seed,
        'original_config_sha256': original_cfg_hash,
        'native_verification_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
        'pre_resume_chain_sha256': chain['file_sha256'],
        'pre_resume_rows': chain['total_stored_rows'],
        'sampled_target_unchanged': True,
        'uninterrupted_rng_trajectory_reconstructed': False,
        'posterior_convergence_verified': False,
    })
    terminal.update(status='resuming_verified_native_target_no_posterior_claims',
                    previous_pid=entry['pid'], pid=os.getpid(), resume_seed=entry['resume_seed'])
    write(source / 'runtime_state.json', terminal)
    try:
        _, sampler = run(cfg, no_mpi=True, stop_at_error=True)
        assert sampler.seed == entry['resume_seed']
        assert np.all(np.isfinite(sampler.collection.data.to_numpy(dtype=float)))
    except Exception as error:
        terminal.update(status='resume_failed_partial_chain_preserved', error=str(error))
        write(source / 'runtime_state.json', terminal)
        raise
    terminal.update(status='resumed_sampler_terminal_requires_independent_diagnostics')
    write(source / 'runtime_state.json', terminal)


if __name__ == '__main__':
    main()
