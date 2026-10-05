"""Check the isolated repair at the failure point under two declared precisions."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np

HERE = Path(__file__).resolve().parent
build = json.loads((HERE / 'finite_retry_build_receipt.json').read_text())
binary = Path(build['binary'])
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(binary) == build['binary_sha256']
base = (HERE / 'exact_failure.ini').read_text().splitlines()
base = [line for line in base if not line.startswith('root = ')]
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'binary_sha256': sha(binary),
           'scope': 'isolated_candidate_repair_at_one_fixed_native_point',
           'active_inference_backend_changed': False, 'uniform_numerical_accuracy_certified': False,
           'posterior_convergence_certified': False, 'cases': {}}
environment = dict(os.environ, OMP_NUM_THREADS='4')
environment.pop('LD_PRELOAD', None)
for mode in ['default', 'background_quadrature']:
    prefix = binary.parent / (mode + '_finite_retry_')
    assert not list(prefix.parent.glob(prefix.name + '*.dat'))
    lines = list(base) + ['root = ' + str(prefix), 'write thermodynamics = yes']
    if mode == 'background_quadrature':
        lines.append('tol_ncdm_bg = 1e-8')
    input_path = HERE / (mode + '_finite_retry.ini')
    input_path.write_text('\n'.join(lines) + '\n')
    out, err = HERE / (mode + '_finite_retry_stdout.txt'), HERE / (mode + '_finite_retry_stderr.txt')
    started = time.monotonic()
    with out.open('w') as stdout, err.open('w') as stderr:
        result = subprocess.run([str(binary), str(input_path)], env=environment,
                                stdout=stdout, stderr=stderr, check=False)
    outputs = {}
    for file in sorted(prefix.parent.glob(prefix.name + '*.dat')):
        values = np.loadtxt(file)
        artifact = HERE / (mode + '_finite_retry_' + file.name.split('_00_', 1)[-1] + '.npz')
        np.savez_compressed(artifact, values=values)
        outputs[file.name] = {'source': str(file), 'source_sha256': sha(file),
                              'artifact': artifact.name, 'artifact_sha256': sha(artifact),
                              'shape': list(values.shape), 'nonfinite_values': int((~np.isfinite(values)).sum())}
    receipt['cases'][mode] = {'exit_code': result.returncode, 'elapsed_seconds': time.monotonic() - started,
                              'input_sha256': sha(input_path), 'stdout_sha256': sha(out), 'stderr_sha256': sha(err),
                              'retry_primary_count': err.read_text().count('RETRY_NONFINITE_PRIMARY'),
                              'retry_secondary_count': err.read_text().count('RETRY_NONFINITE_SECONDARY'),
                              'outputs': outputs}
    (HERE / 'finite_retry_replay_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt['cases'], indent=2))
for mode, case in receipt['cases'].items():
    assert case['exit_code'] == 0 and case['outputs'], mode
    assert any('thermodynamics' in name for name in case['outputs'])
    assert all(x['nonfinite_values'] == 0 for x in case['outputs'].values())
assert receipt['cases']['default']['retry_primary_count'] > 0
