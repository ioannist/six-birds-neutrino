"""Compile and exercise the actual pinned transfer-list implementation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BACKEND = Path('/mnt/8tb/six-birds-ml/tmp/neutrino_class_finite_jacobian_20261004/python_backend/classy')
BUILD = Path('/mnt/8tb/six-birds-ml/tmp/neutrino_B_unit_grid_probe_20261004')
BUILD.mkdir(exist_ok=True)
includes = ['-I' + str(BACKEND / p) for p in [
    'include', 'external/HyRec2020', 'external/RecfastCLASS',
    'external/heating', 'external/Halofit', 'external/HMcode']]
commands = [
    ['g++', '-O2', '-ffunction-sections', '-fdata-sections', *includes,
     '-c', str(BACKEND / 'source/transfer.c'), '-o', str(BUILD / 'transfer.o')],
    ['g++', '-O2', *includes, str(HERE / 'grid_probe.c'), str(BUILD / 'transfer.o'),
     str(BACKEND / 'build/common.o'),
     '-Wl,--gc-sections', '-lm', '-o', str(BUILD / 'grid_probe')],
]
logs = []
for command in commands:
    result = subprocess.run(command, text=True, capture_output=True)
    logs.append({'command': command, 'returncode': result.returncode,
                 'stdout': result.stdout, 'stderr': result.stderr})
    (HERE / 'grid_build_calls.json').write_text(json.dumps(logs, indent=2) + '\n')
    assert result.returncode == 0, result.stderr
controls = []
for step, rescaling, lmax, expected in [
    (1., .5, 4095, True), (1., .999999999999, 6142, True),
    (1., 1., 6142, True), (1., 1.000000000001, 6142, True),
    (1., 2., 4095, True), (1.00325, 1., 6142, False),
]:
    result = subprocess.run([str(BUILD / 'grid_probe'), str(step), str(rescaling), str(lmax)],
                            capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['consecutive'] == expected
    controls.append(data)
sources = [BACKEND / 'source/transfer.c', BACKEND / 'source/thermodynamics.c',
           BACKEND / 'include/precisions.h', BACKEND / 'include/transfer.h',
           BACKEND / 'include/common.h', BACKEND / 'build/common.o',
           HERE / 'grid_probe.c', Path(__file__)]
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'actual_CLASS_transfer_list_function_zero_mode_count_isolates_list_construction',
    'compiler_calls': logs, 'controls': controls,
    'source_identity': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                        for p in sources],
    'binary': str(BUILD / 'grid_probe'),
    'binary_sha256': hashlib.sha256((BUILD / 'grid_probe').read_bytes()).hexdigest(),
    'source_condition': 'l_logstep=1 gives increment=MAX(int(l*(pow(1,rescaling)-1)),1)=1; '
                        'l_linstep*rescaling>1 retains the logarithmic loop through lmax-1, then appends lmax',
    'actual_native_geometry_still_to_be_checked': True,
    'all_other_numerical_errors_eliminated': False,
}
(HERE / 'grid_source_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(controls, indent=2))
