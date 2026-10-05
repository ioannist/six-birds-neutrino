"""Replay the second failure under its exact precision, and test the isolated repair."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
diagnostic = ROOT / 'runs/20261004_math_review_class_tca_diagnostic'
manifest = json.loads((diagnostic / 'build_manifest.json').read_text())
package = Path(manifest['scratch_package'])
scratch = package.parent
arguments = json.loads((HERE / 'failed_class_arguments.json').read_text())['translated_class_arguments']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
input_path = HERE / 'exact_failure.ini'
prefix = scratch / 'seed701_finite_retry_'
input_path.write_text('\n'.join(f'{key} = {value}' for key, value in arguments.items())
                      + '\nroot = ' + str(prefix) + '\nwrite thermodynamics = yes\n')
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'second_native_failure_exact_physics_and_seven_setting_precision_isolated_solver_checks',
           'arguments': arguments, 'input_sha256': sha(input_path),
           'active_inference_backend_changed': False, 'posterior_convergence_certified': False,
           'uniform_numerical_accuracy_certified': False, 'cases': {}}
for name, binary, trapped in [
    ('original', package / 'class', False),
    ('helium_trace', scratch / 'class_lu_diagnostic_helium', True),
    ('finite_retry', scratch / 'class_ndf_finite_retry', False),
]:
    environment = dict(os.environ, OMP_NUM_THREADS='8')
    environment.pop('LD_PRELOAD', None)
    if trapped:
        environment['LD_PRELOAD'] = str(scratch / 'trace_invalid.so')
    out, err = HERE / (name + '_stdout.txt'), HERE / (name + '_stderr.txt')
    started = time.monotonic()
    with out.open('w') as stdout, err.open('w') as stderr:
        result = subprocess.run([str(binary), str(input_path)], env=environment,
                                stdout=stdout, stderr=stderr, check=False)
    receipt['cases'][name] = {'binary_sha256': sha(binary), 'exit_code': result.returncode,
                              'elapsed_seconds': time.monotonic() - started,
                              'stdout_sha256': sha(out), 'stderr_sha256': sha(err)}
    (HERE / 'isolated_replay_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
outputs = {}
for file in sorted(prefix.parent.glob(prefix.name + '*.dat')):
    values = np.loadtxt(file)
    artifact = HERE / (file.name.split('_00_', 1)[-1] + '.npz')
    np.savez_compressed(artifact, values=values)
    outputs[file.name] = {'source': str(file), 'source_sha256': sha(file),
                          'artifact': artifact.name, 'artifact_sha256': sha(artifact),
                          'shape': list(values.shape), 'nonfinite_values': int((~np.isfinite(values)).sum())}
receipt['finite_retry_outputs'] = outputs
(HERE / 'isolated_replay_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
assert receipt['cases']['original']['exit_code'] == 1
assert receipt['cases']['helium_trace']['exit_code'] == 136
assert receipt['cases']['finite_retry']['exit_code'] == 0 and outputs
assert all(x['nonfinite_values'] == 0 for x in outputs.values())
