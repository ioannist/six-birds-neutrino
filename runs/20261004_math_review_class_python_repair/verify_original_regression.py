"""Capture the guard suite's behavior against the original numjac implementation."""
import json
from pathlib import Path
import resource
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
original = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy')
patched = Path(json.loads((HERE / 'preparation_manifest.json').read_text())['package'])
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
with tempfile.TemporaryDirectory(prefix='sbt-original-numjac-') as directory:
    temporary = Path(directory)
    commands = [
        ['gcc', '-std=c11', '-O2', '-I' + str(original / 'include'), '-c',
         str(original / 'tools/evolver_ndf15.c'), '-o', str(temporary / 'original.o')],
        ['gcc', '-std=c11', '-O2', '-I' + str(original / 'include'), '-c',
         str(ROOT / 'tests/native/class_numjac_guard.c'), '-o', str(temporary / 'test.o')],
        ['g++', '-pthread', str(temporary / 'test.o'), str(temporary / 'original.o'),
         str(patched / 'libclass.a'), '-lm', '-o', str(temporary / 'test')],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True)
    result = subprocess.run(['stdbuf', '-oL', str(temporary / 'test')],
                            capture_output=True, text=True)
    cases = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    receipt = {
        'scope': 'isolated_fixture_sensitivity_to_original_numjac',
        'original_numjac_compiled_from_installed_unmodified_source': True,
        'other_native_dependencies_linked_from_private_library': True,
        'commands': commands, 'execution_command': result.args,
        'exit_code': result.returncode,
        'signal': -result.returncode if result.returncode < 0 else None,
        'completed_cases': cases, 'all_seven_cases_completed': len(cases) == 7,
    }
    with (HERE / 'original_native_regression_receipt.json').open('x') as handle:
        handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    (HERE / 'original_native_regression_stdout.txt').write_text(result.stdout)
    (HERE / 'original_native_regression_stderr.txt').write_text(result.stderr)
    assert result.returncode != 0
    assert cases and cases[0]['case'] == 'smooth_linear_control' and cases[0]['ok']
    print('Original smooth control passes; unmodified numjac fails the guard suite.')
