"""Replay forward transfer from the strongest completed, verified source found.

Requires the parent accuracy audit and its fresh two-direction verification.
The chosen candidates are numerical candidates, never global certificates.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT / 'runs/20261003_math_review_cosmological_cmb_desi_accuracy'
sys.path.insert(0, str(ROOT / 'scripts'))
from run_cosmological_audit import Audit, get_model, write_json


def main():
    # Refuse execution until the original endpoints have fresh native evidence.
    paths = {name: PARENT / name for name in
             ['metrics.json', 'accounting_verification.json', 'resolved.yaml']}
    data = {name: json.loads(path.read_text()) for name, path in paths.items()
            if path.suffix == '.json'}
    expected = {'B_given_A', 'A_given_B'}
    if set(data['metrics.json']['directions']) != expected or set(
            data['accounting_verification.json']) != expected:
        raise ValueError('Both parent directions require completed native verification.')
    if any(not item['fresh_endpoint_spectra_verified'] for item in
           data['accounting_verification.json'].values()):
        raise ValueError('Parent native endpoint verification is incomplete.')
    if (HERE / 'runtime_state.json').exists() or (HERE / 'metrics.json').exists():
        raise ValueError('Replay already launched; inspect its existing handle instead.')
    stored = data['metrics.json']
    fits = {}
    for lens, direction in [('lensA', 'A_given_B'), ('lensB', 'B_given_A')]:
        candidate = stored['directions'][direction]
        choices = [stored['fits'][lens], candidate['cross_candidate'],
                   candidate['reference_candidate']]
        fits[lens] = deepcopy(max(choices, key=lambda item: item['loglike']))
    (HERE / 'resolved.yaml').write_bytes(paths['resolved.yaml'].read_bytes())
    cfg = yaml.safe_load(paths['resolved.yaml'].read_text())
    write_json(HERE / 'selected_fits.json', fits)
    write_json(HERE / 'inputs.json', {
        'utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'one_direction_replay_at_best_found_parent_candidates',
        'parent_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for name, path in paths.items()},
        'source_commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'executed_source_sha256': {str(path.relative_to(ROOT)):
                                  hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in [Path(__file__), ROOT / 'scripts/run_cosmological_audit.py']},
        'global_optimum_certified': False,
    })
    import os
    write_json(HERE / 'runtime_state.json', {'status': 'running', 'pid': os.getpid()})
    with get_model(cfg, stop_at_error=True) as model:
        audit = Audit(model, cfg, stored['completion_likelihoods'], HERE, 450, .02)
        for lens, fit in fits.items():
            objective, _ = audit.evaluate(fit['point'], lens, cached=False)
            if not np.isclose(objective, fit['loglike'], rtol=1e-10, atol=1e-7):
                raise ValueError(f'{lens}: selected parent candidate does not reproduce.')
        result = audit.direction('lensB', fits['lensA'], fits['lensB'], 'B_given_A')
        updated = deepcopy(stored)
        updated.update(fits=fits, directions={'B_given_A': result},
                       posterior_convergence_verified=False)
        write_json(HERE / 'metrics.json', updated)
    write_json(HERE / 'runtime_state.json', {
        'status': 'completed_candidate_replay_requires_fresh_endpoint_verification',
        'pid': os.getpid(), 'optimization_success': result['optimization_success'],
        'global_optimum_certified': False,
    })
    return 0 if result['optimization_success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
