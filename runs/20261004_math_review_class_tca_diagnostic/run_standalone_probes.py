"""Run the separate diagnostic executable without modifying the inference backend."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / 'build_manifest.json').read_text())
binary = Path(manifest['scratch_package']) / 'class'
source = HERE / 'exact_failure.ini'
repaired = HERE / 'background_quadrature.ini'
repaired.write_text(source.read_text().replace('exact_failure_', 'background_quadrature_')
                    + 'tol_ncdm_bg = 1e-8\n')
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'distinct_standalone_driver_and_build_at_exact_archived_physics',
           'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
           'build_completed_exit_code': 0, 'build_managed_session': 19050,
           'omp_num_threads': 4, 'active_inference_library_changed': False,
           'posterior_accuracy_certified': False, 'cases': {}}
environment = dict(os.environ, OMP_NUM_THREADS='4')
for mode, input_path in [('exact_failure', source), ('background_quadrature', repaired)]:
    out = HERE / f'{mode}_stdout.txt'
    err = HERE / f'{mode}_stderr.txt'
    started = time.monotonic()
    with out.open('w') as stdout, err.open('w') as stderr:
        result = subprocess.run([str(binary), str(input_path)], stdout=stdout, stderr=stderr,
                                env=environment, check=False)
    receipt['cases'][mode] = {
        'exit_code': result.returncode, 'elapsed_seconds': time.monotonic() - started,
        'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
        'stdout_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
        'stderr_sha256': hashlib.sha256(err.read_bytes()).hexdigest(),
    }
(HERE / 'standalone_replay_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt['cases'], indent=2))
assert receipt['cases']['exact_failure']['exit_code'] == 1
assert 'dkappa=-nan' in (HERE / 'exact_failure_stderr.txt').read_text()
assert receipt['cases']['background_quadrature']['exit_code'] == 0
assert not (HERE / 'background_quadrature_stderr.txt').read_text()
