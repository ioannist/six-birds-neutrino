"""Capture the helium-cutoff failure in isolated executables with unchanged inputs."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / 'build_manifest.json').read_text())
package = Path(manifest['scratch_package'])
scratch = package.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
library = scratch / 'trace_invalid.so'
compile_command = ['gcc', '-shared', '-fPIC', '-g', '-O0', str(HERE / 'trace_invalid.c'),
                   '-o', str(library), '-lm']
subprocess.run(compile_command, check=True)
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'isolated_native_diagnostics_exact_failed_point_no_inference_change',
           'trapped_exception': 'FE_INVALID_only_overflow_not_trapped',
           'signal_handler_exit_code': 136, 'compile_command': compile_command,
           'trace_source_sha256': sha(HERE / 'trace_invalid.c'),
           'trace_library_sha256': sha(library),
           'input_sha256': sha(HERE / 'exact_failure.ini'),
           'active_inference_backend_changed': False, 'cases': {}}
cases = [('first_invalid', package / 'class', True),
         ('lu_first_invalid', scratch / 'class_lu_diagnostic', True),
         ('jacobian_first_invalid', scratch / 'class_lu_diagnostic_jacobian', True),
         ('helium_first_invalid', scratch / 'class_lu_diagnostic_helium', True),
         ('helium_untrapped', scratch / 'class_lu_diagnostic_helium', False)]
for name, binary, trapped in cases:
    environment = dict(os.environ, OMP_NUM_THREADS='1')
    environment.pop('LD_PRELOAD', None)
    if trapped:
        environment['LD_PRELOAD'] = str(library)
    out, err = HERE / (name + '_stdout.txt'), HERE / (name + '_stderr.txt')
    started = time.monotonic()
    with out.open('w') as stdout, err.open('w') as stderr:
        result = subprocess.run([str(binary), str(HERE / 'exact_failure.ini')],
                                env=environment, stdout=stdout, stderr=stderr, check=False)
    assert result.returncode == (136 if trapped else 1)
    case = {'binary': str(binary), 'binary_sha256': sha(binary), 'trapped': trapped,
            'exit_code': result.returncode, 'elapsed_seconds': time.monotonic() - started,
            'stdout_sha256': sha(out), 'stderr_sha256': sha(err)}
    if trapped:
        offsets = re.findall(re.escape(str(binary)) + r'\(\+(0x[0-9a-f]+)\)', err.read_text())
        assert offsets
        command = ['addr2line', '-f', '-C', '-e', str(binary)] + offsets
        frame_file = HERE / (name + '_frames.txt')
        frame_file.write_text(subprocess.check_output(command, text=True))
        case.update(frame_command=command, frames_sha256=sha(frame_file))
    receipt['cases'][name] = case
text = (HERE / 'helium_first_invalid_stderr.txt').read_text()
def quantities(label):
    line = next(x for x in text.splitlines() if x.startswith(label + ' '))
    return dict(piece.split('=', 1) for piece in line.split()[1:])
helium, jacobian = quantities('NONFINITE_HELIUM_RATE'), quantities('NONFINITE_JACOBIAN')
base = float(jacobian['y_j']) * float(helium['fHe'])
perturbed = float(helium['xHeII'])
limit = float(helium['limit'])
assert base < limit <= perturbed
assert float(jacobian['increment']) > 0
assert float(jacobian['f_base']) == 0
assert jacobian['f_perturbed'] == '-inf' and helium['rate'] == 'inf'
assert float(helium['z']) == -float(jacobian['t'])
assert 'scalar initial conditions assume tight-coupling' in (HERE / 'helium_untrapped_stdout.txt').read_text()
receipt['cutoff_crossing'] = {
    'base_xHeII': base, 'perturbed_xHeII': perturbed, 'cutoff': limit,
    'relative_base_offset_from_cutoff': base / limit - 1,
    'relative_perturbed_offset_from_cutoff': perturbed / limit - 1,
    'redshift': float(helium['z']), 'positive_increment': float(jacobian['increment']),
    'base_helium_rate_zero': True, 'perturbed_helium_rate_nonfinite': True,
    'helium_excited_level_exponent_46090_over_Trad': 46090 / float(helium['Trad']),
}
(HERE / 'invalid_probe_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps(receipt['cutoff_crossing'], indent=2))
