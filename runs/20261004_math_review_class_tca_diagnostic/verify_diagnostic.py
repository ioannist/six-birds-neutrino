"""Verify saved diagnostic evidence, exact input scope, and current process identities."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = json.loads((HERE / 'build_manifest.json').read_text())
tables = json.loads((HERE / 'native_table_receipt.json').read_text())
standalone = json.loads((HERE / 'standalone_replay_receipt.json').read_text())
assert sha(Path(tables['native_module'])) == tables['native_module_sha256']
assert tables['native_module_sha256'] == '38255c7a5eb3f52c960a6fccf657e00874e93a52ec5987807443c33ce0c09c5a'
assert sha(Path(manifest['original_package']) / 'source/perturbations.c') == manifest['original_source_sha256']
assert sha(Path(manifest['scratch_package']) / 'source/perturbations.c') == manifest['diagnostic_source_sha256']
assert sha(Path(manifest['scratch_package']) / 'class') == standalone['binary_sha256']
source = ROOT / 'runs/20261004_math_review_class_tca_failure_seed505/failed_class_arguments.json'
assert sha(source) == tables['source_sha256'] == manifest['exact_failed_arguments_sha256']
arguments = json.loads(source.read_text())['translated_class_arguments']
assert tables['cases']['default']['arguments'] == arguments
assert tables['cases']['background_quadrature']['arguments'] == dict(arguments, tol_ncdm_bg=1e-8)
for mode, case in tables['cases'].items():
    for name, table in case['tables'].items():
        path = HERE / table['file']
        assert sha(path) == table['sha256']
        with np.load(path) as archive:
            assert set(archive.files) == set(table['columns'])
            for column, values in table['columns'].items():
                assert int((~np.isfinite(archive[column])).sum()) == values['nonfinite_count']
                if mode == 'background_quadrature' or name == 'background':
                    assert values['nonfinite_count'] == 0
thermo = tables['cases']['default']['tables']['thermodynamics']['columns']
assert thermo['x_e']['nonfinite_count'] == thermo["kappa' [Mpc^-1]"]['nonfinite_count'] == 22
assert thermo['g [Mpc^-1]']['nonfinite_count'] == thermo['g [Mpc^-1]']['rows'] == 28333
for mode, case in standalone['cases'].items():
    for key, suffix in [('input', '.ini'), ('stdout', '_stdout.txt'), ('stderr', '_stderr.txt')]:
        assert sha(HERE / (mode + suffix)) == case[key + '_sha256']
assert standalone['cases']['exact_failure']['exit_code'] == 1
assert standalone['cases']['background_quadrature']['exit_code'] == 0
assert 'dkappa=-nan' in (HERE / 'exact_failure_stderr.txt').read_text()
assert 'scalar initial conditions assume tight-coupling' in (HERE / 'exact_failure_stdout.txt').read_text()
default_input = dict(line.split(' = ', 1) for line in (HERE / 'exact_failure.ini').read_text().splitlines())
repaired_input = dict(line.split(' = ', 1) for line in (HERE / 'background_quadrature.ini').read_text().splitlines())
default_input.pop('root')
repaired_input.pop('root')
assert default_input == {key: str(value) for key, value in arguments.items()}
assert repaired_input == dict(default_input, tol_ncdm_bg='1e-8')
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
entries = [x for x in state['restoration_chains'] if x['kind'] == 'spt_desi']
for key in ('quadrature_repaired_posterior_chains', 'controlled_precision_posterior_chains',
            'controlled_precision_dragging_trials', 'controlled_precision_learned_proposal_trials'):
    entries.extend(state[key])
assert len(entries) == 28 and len({x['pid'] for x in entries}) == 28
records = []
for entry in entries:
    proc = Path('/proc') / str(entry['pid'])
    cmd = (proc / 'cmdline').read_bytes().split(b'\0')
    if 'recovery_dir' in entry:
        expected = [entry['recovery_dir'] + '/resume_verified_chain.py', str(entry['seed'])]
    else:
        expected = ['scripts/run_cobaya.py', '--outdir', entry['run_dir'], '--seed', str(entry['seed'])]
    assert all(x.encode() in cmd for x in expected), (entry['seed'], cmd)
    assert (proc / 'cwd').resolve() == ROOT
    rows = sum(sum(bool(line.strip()) and not line.startswith('#') for line in path.open())
               for path in (ROOT / entry['run_dir'] / 'chains').glob('*.txt'))
    records.append({'seed': entry['seed'], 'pid': entry['pid'], 'owned_identity_live': True,
                    'stored_rows_in_full_source_files': rows,
                    'fresh_segment_only_required': 'recovery_dir' in entry})
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'evidence_and_input_scope_verified': True, 'owned_sampler_identities': records,
           'active_native_backend_unchanged': True, 'posterior_convergence_certified': False,
           'uniform_numerical_accuracy_certified': False,
           'root_numerical_cause_before_low_redshift_thermodynamics_nonfinite_values_established': False}
(HERE / 'verification_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Saved diagnostic evidence verified; all 28 owned samplers live; native inference backend unchanged.')
