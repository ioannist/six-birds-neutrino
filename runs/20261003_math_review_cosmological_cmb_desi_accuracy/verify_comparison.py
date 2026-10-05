"""Reconcile the completed controlled audit and its original source selection."""
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
sys.path.insert(0, str(ROOT / 'scripts'))
from run_cosmological_audit import get_model
paths = {'controlled': HERE,
         'warm': ROOT / 'runs/20261003_math_review_cosmological_cmb_desi_warm',
         'multistart': ROOT / 'runs/20261003_math_review_cosmological_cmb_desi'}
native = {label: json.loads((path / 'accounting_verification.json').read_text())
          for label, path in paths.items()}
stored = json.loads((HERE / 'metrics.json').read_text())
cfg = yaml.safe_load((HERE / 'resolved.yaml').read_text())
expected_precision = {
    'tol_ncdm_bg': 1e-8, 'tol_perturbations_integration': 1e-6,
    'perturbations_sampling_stepsize': .01, 'tol_ncdm_synchronous': 1e-6,
    'tol_ncdm_newtonian': 1e-6, 'l_logstep': 1.026, 'l_linstep': 25,
}
baseline_cfg = deepcopy(cfg)
for name, value in expected_precision.items():
    assert baseline_cfg['theory']['classy']['extra_args'].pop(name) == value
assert baseline_cfg['theory']['classy']['extra_args'].pop('l_max_scalars') == 4095
for label in ['warm', 'multistart']:
    assert baseline_cfg == yaml.safe_load((paths[label] / 'resolved.yaml').read_text())
effective = {}
for label, model_cfg in [('controlled', cfg), ('baseline', baseline_cfg)]:
    with get_model(model_cfg, stop_at_error=True) as model:
        theory = model.theory['classy']
        effective[label] = {'requested_Cl': deepcopy(theory.requested()['Cl']),
                            'extra_args': deepcopy(theory.extra_args)}
        assert theory.extra_args['l_max_scalars'] == 4095
        assert max(theory.requested()['Cl'].values()) == 4095
controlled_extra = deepcopy(effective['controlled']['extra_args'])
for name, value in expected_precision.items():
    assert controlled_extra.pop(name) == value
assert controlled_extra == effective['baseline']['extra_args']
assert effective['controlled']['requested_Cl'] == effective['baseline']['requested_Cl']
inputs = json.loads((HERE / 'inputs.json').read_text())
for lens in ['A', 'B']:
    assert hashlib.sha256(Path(inputs['config' + lens]).read_bytes()).hexdigest() == inputs['sha256' + lens]
original_runner = subprocess.check_output(
    ['git', 'show', inputs['source_commit'] + ':scripts/run_cosmological_audit.py'], cwd=ROOT)
assert hashlib.sha256(original_runner).hexdigest() == inputs['runner_sha256']
assert set(native['controlled']) == set(stored['directions']) == {'B_given_A', 'A_given_B'}
results = {}
for direction, verified in native['controlled'].items():
    value = verified['joint_candidate_delta_chi2']
    assert np.isclose(value, stored['directions'][direction]['joint_candidate_delta_chi2'],
                      atol=1e-7, rtol=1e-10)
    assert verified['fixed_source_coordinates_verified']
    assert verified['candidate_reference_nesting_verified']
    assert verified['fresh_endpoint_spectra_verified']
    assert stored['directions'][direction]['optimization_success']
    results[direction] = {
        'joint_candidate_delta_chi2': value,
        'percent_change': {
            label: 100 * (value / native[label][direction]['joint_candidate_delta_chi2'] - 1)
            for label in ['warm', 'multistart']},
        'signed_spt_delta_chi2': verified['signed_component_delta_chi2'][
            'lensB' if direction == 'B_given_A' else 'lensA'],
        'spt_native_reconstruction_error': verified['spt_native_reconstruction_error'],
        'largest_positive_group': verified['top_groups'][0],
    }
original_A = stored['fits']['lensA']
improved_A = stored['directions']['A_given_B']['reference_candidate']
gain = improved_A['loglike'] - original_A['loglike']
assert gain > 0
forward = stored['directions']['B_given_A']
assert all(forward['cross_candidate']['point'][name] == original_A['point'][name]
           for name in forward['shared_parameters'])
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'completed_declared_source_candidate_transfers_not_a_global_or_posterior_certificate',
    'only_declared_precision_settings_differ': True,
    'explicit_l_max_scalars_equals_derived_baseline': True,
    'effective_theory_settings': effective,
    'executed_original_runner_hash_matches_source_commit': True,
    'source_sha256': {
        label + '/' + name: hashlib.sha256((path / name).read_bytes()).hexdigest()
        for label, path in paths.items()
        for name in ['metrics.json', 'resolved.yaml', 'accounting_verification.json']},
    'directions': results,
    'A_reference_gain_over_original_source_loglike': gain,
    'A_original_source_mass_eV': original_A['point']['mnu_sample'],
    'A_improved_reference_mass_eV': improved_A['point']['mnu_sample'],
    'improved_A_source_forward_replay_pending': True,
    'posterior_convergence_certified': False,
    'global_optimum_certified': False,
    'numerical_accuracy_certified': False,
}
(HERE / 'comparison_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
