"""Verify exact cutoff crossings, isolated repair outputs, and sampler state."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib
import json
from pathlib import Path

import classy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
second = ROOT / 'runs/20261004_math_review_class_tca_failure_seed701'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
module = Path(importlib.import_module(classy.Class.__module__).__file__)
assert sha(module) == json.loads((HERE / 'native_table_receipt.json').read_text())['native_module_sha256']
original_replay = json.loads((HERE / 'standalone_replay_receipt.json').read_text())
original_package = Path(json.loads((HERE / 'build_manifest.json').read_text())['scratch_package'])
assert sha(original_package / 'class') == original_replay['binary_sha256']
crossings = []
for file in [HERE / 'helium_first_invalid_stderr.txt', second / 'helium_trace_stderr.txt']:
    lines = file.read_text().splitlines()
    values = {}
    for label in ['NONFINITE_HELIUM_RATE', 'NONFINITE_JACOBIAN', 'NONFINITE_LU_INPUT']:
        line = next(x for x in lines if x.startswith(label + ' '))
        values[label] = dict(x.split('=', 1) for x in line.split()[1:])
    he, jac, lu = [values[x] for x in ['NONFINITE_HELIUM_RATE', 'NONFINITE_JACOBIAN', 'NONFINITE_LU_INPUT']]
    y, increment, abundance, limit = [float(x) for x in [jac['y_j'], jac['increment'], he['fHe'], he['limit']]]
    perturbed = float(he['x_He'])
    assert perturbed == y + increment and increment > 0
    exact_base = Fraction(y) * Fraction(abundance)
    exact_perturbed = Fraction(perturbed) * Fraction(abundance)
    assert exact_base < Fraction(limit) < exact_perturbed
    assert y * abundance < limit <= perturbed * abundance == float(he['xHeII'])
    assert float(jac['f_base']) == 0 and jac['f_perturbed'] == jac['derivative'] == '-inf'
    assert he['rate'] == 'inf' and lu['dfdy'] == '-inf' and lu['LU'] == 'inf'
    assert float(he['z']) == -float(jac['t']) and float(he['Tmat']) > 0 and float(he['Trad']) > 0
    crossings.append({'source': str(file.relative_to(ROOT)),
                      'exact_binary_rational_products_straddle_cutoff': True,
                      'finite_difference_increment_positive': True, 'base_rate_zero': True,
                      'perturbed_rate_infinite': True, 'redshift': float(he['z'])})
first = json.loads((HERE / 'finite_retry_replay_receipt.json').read_text())
replay2 = json.loads((second / 'isolated_replay_receipt.json').read_text())
build = json.loads((HERE / 'finite_retry_build_receipt.json').read_text())
assert sha(Path(build['binary'])) == build['binary_sha256'] == first['binary_sha256']
assert sha(HERE / 'evolver_ndf15_finite_retry.c') == build['source_sha256']
for mode, case in first['cases'].items():
    assert case['exit_code'] == 0
    for suffix, key in [('.ini', 'input'), ('_stdout.txt', 'stdout'), ('_stderr.txt', 'stderr')]:
        assert sha(HERE / (mode + '_finite_retry' + suffix)) == case[key + '_sha256']
    for output in case['outputs'].values():
        file = HERE / output['artifact']
        assert sha(file) == output['artifact_sha256']
        with np.load(file) as archive:
            assert list(archive['values'].shape) == output['shape'] and np.isfinite(archive['values']).all()
assert first['cases']['default']['retry_primary_count'] == 1
assert first['cases']['background_quadrature']['retry_primary_count'] == 0
control = np.load(HERE / 'background_quadrature_finite_retry_cl_lensed.dat.npz')['values']
original = np.loadtxt(original_package.parent / 'background_quadrature_00_cl_lensed.dat')
assert np.array_equal(control, original)
assert replay2['cases']['original']['exit_code'] == 1
assert replay2['cases']['helium_trace']['exit_code'] == 136
assert replay2['cases']['finite_retry']['exit_code'] == 0
assert replay2['cases']['finite_retry']['binary_sha256'] == build['binary_sha256']
for name, case in replay2['cases'].items():
    for suffix in ['stdout', 'stderr']:
        assert sha(second / (name + '_' + suffix + '.txt')) == case[suffix + '_sha256']
for output in replay2['finite_retry_outputs'].values():
    file = second / output['artifact']
    assert sha(file) == output['artifact_sha256']
    with np.load(file) as archive:
        assert list(archive['values'].shape) == output['shape'] and np.isfinite(archive['values']).all()
termination = json.loads((second / 'termination_receipt.json').read_text())
for name, digest in termination['archive_sha256'].items():
    assert sha(second / name) == digest
assert not Path('/proc/2696207').exists() and termination['managed_exit_code'] == 1
learning_root = ROOT / 'runs/20261004_math_review_quadrature_learning_first'
learning = json.loads((learning_root / 'learning_receipt.json').read_text())
assert len(learning['records']) == 8
for record in learning['records']:
    for name, digest in record['snapshot_sha256'].items():
        assert sha(learning_root / f"seed{record['seed']}" / name) == digest
    assert record['learning_checks_in_snapshot'] == 1 and record['latest_check_skipped_above_maximum']
    assert record['latest_internal_Rminus1'] > record['learn_proposal_Rminus1_max'] == 2
    assert record['proposal_updates_in_snapshot'] == 0
    assert record['covariance_matches_initial_with_text_roundtrip_tolerance']
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
entries = [x for x in state['restoration_chains'] if x['kind'] == 'spt_desi']
for key in ['quadrature_repaired_posterior_chains', 'controlled_precision_posterior_chains',
            'controlled_precision_dragging_trials', 'controlled_precision_learned_proposal_trials']:
    entries += [x for x in state[key] if x['seed'] != 701]
assert len(entries) == 27
for entry in entries:
    proc = Path('/proc') / str(entry['pid'])
    cmd = (proc / 'cmdline').read_bytes().split(b'\0')
    expected = [entry['recovery_dir'] + '/resume_verified_chain.py', str(entry['seed'])] if 'recovery_dir' in entry else ['scripts/run_cobaya.py', '--outdir', entry['run_dir'], '--seed', str(entry['seed'])]
    assert all(x.encode() in cmd for x in expected)
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'exact_cutoff_crossings': crossings,
           'candidate_finite_outputs_at_both_failed_coordinates_verified': True,
           'quadrature_control_saved_lensed_spectra_equal_original_exactly': True,
           'second_failed_chain_archive_hashes_verified': True,
           'all_eight_first_quad_learning_checks_skip_updates_verified': True,
           'current_owned_live_sampler_count': 27, 'active_inference_backend_unchanged': True,
           'uniform_numerical_accuracy_certified': False, 'posterior_convergence_certified': False,
           'candidate_repair_installed_in_inference': False}
(HERE / 'extended_verification_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Both cutoff crossings and candidate repairs verified; 27 owned samplers live; active backend unchanged.')
