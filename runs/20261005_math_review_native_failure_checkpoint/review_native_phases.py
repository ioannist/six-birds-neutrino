"""Distinct self-review of captured-array phase and nonlinear-model controls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
triage = ROOT / 'runs/20261004_math_review_CAMB204_source_failure_triage'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
records = []
for seed in [2003, 2004]:
    folder = triage / f'seed{seed}_phase_classification'
    phase = json.loads((folder / 'phase_classification.json').read_text())
    assert phase['isolated_point_status'] == 'exception'
    assert phase['error'] == 'provider spectrum tt must be finite and 1D.'
    assert sha(folder / 'native_arrays.npz') == phase['native_arrays_sha256']
    assert sha(ROOT / phase['capture']) == phase['capture_sha256']
    with np.load(folder / 'native_arrays.npz') as z:
        for label in ['unlensed_scalar', 'lensed_scalar', 'lens_potential']:
            a = z[label]
            v = phase['native_spectra'][label]
            assert list(a.shape) == v['shape']
            assert bool(np.isfinite(a).all()) == v['all_finite']
            assert int(np.isnan(a).sum()) == v['nan_count']
            assert int(np.isinf(a).sum()) == v['inf_count'] == 0
        assert np.isfinite(z['unlensed_scalar']).all()
        assert np.isnan(z['lensed_scalar'][2:]).all()
        assert np.isnan(z['lens_potential'][2:]).all()
        original = {label: z[label].copy() for label in ['unlensed_scalar', 'lensed_scalar', 'lens_potential']}
    ablation_folder = triage / f'seed{seed}_nonlinear_ablation'
    summary = json.loads((ablation_folder / 'ablation_summary.json').read_text())
    assert summary['sampled'] == phase['sampled']
    assert summary['native_module_sha256'] == phase['original_native_module_sha256']
    base = (ablation_folder / 'original_mead2020_params.txt').read_text()
    for r in summary['records']:
        variant = r['variant']
        params_file = ablation_folder / f'{variant}_params.txt'
        assert sha(params_file) == r['parameters_sha256']
        expected = base
        if variant == 'linear_lensing':
            assert base.count('NonLinear = NonLinear_lens') == 1
            expected = base.replace('NonLinear = NonLinear_lens', 'NonLinear = NonLinear_none', 1)
        elif variant != 'original_mead2020':
            assert base.count('halofit_version = mead2020') == 1
            expected = base.replace('halofit_version = mead2020', 'halofit_version = ' + variant, 1)
        assert params_file.read_text() == expected
        path = ablation_folder / f'{variant}_arrays.npz'
        assert sha(path) == r['arrays_sha256'] and r['status'] == 'arrays_returned'
        with np.load(path) as z:
            for label in original:
                assert bool(np.isfinite(z[label]).all()) == r[label]['all_finite']
                assert int(np.isnan(z[label]).sum()) == r[label]['nan_count']
                assert np.array_equal(z[label], original[label], equal_nan=True) == r[label]['equal_to_original_with_nan']
                if variant == 'original_mead2020':
                    assert np.array_equal(z[label], original[label], equal_nan=True)
            assert np.isfinite(z['unlensed_scalar']).all()
            if variant in ['linear_lensing', 'takahashi']:
                assert all(np.isfinite(z[label]).all() for label in original)
            else:
                assert np.isnan(z['lens_potential'][2:]).all()
                assert np.isnan(z['lensed_scalar'][2:]).all()
    records.append({'seed': seed, 'captured_mass_eV': phase['sampled']['mnu'],
                    'phase_receipt_sha256': sha(folder / 'phase_classification.json'),
                    'ablation_receipt_sha256': sha(ablation_folder / 'ablation_summary.json'),
                    'isolated_fresh_model_failure_verified': True,
                    'native_original_direct_replay_arrays_equal': True,
                    'finite_unlensed_nonfinite_lens_potential_and_lensed': True,
                    'finite_linear_lensing_and_takahashi_controls': True,
                    'NaN_mead2020_and_mead2016_controls': True})

for prep_name in ['verbose_trace_preparation.json', 'feedback_trace_preparation.json']:
    prep = json.loads((triage / prep_name).read_text())
    source, target = ROOT / prep['source'], ROOT / prep['script']
    assert sha(source) == prep['source_sha256'] and sha(target) == prep['script_sha256']
    text = target.read_text()
    for old, new in reversed(prep['changes']):
        assert text.count(new) == 1
        text = text.replace(new, old, 1)
    assert text.encode() == source.read_bytes()
for scope in ['verbose', 'feedback']:
    with np.load(triage / f'seed2003_{scope}_phase_classification/native_arrays.npz') as z, \
            np.load(triage / 'seed2003_phase_classification/native_arrays.npz') as old:
        assert set(z.files) == set(old.files)
        assert all(np.array_equal(z[label], old[label], equal_nan=True) for label in z.files)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'records': records, 'all_ablation_parameter_changes_exactly_scoped': True,
       'stock_feedback_serial_branch_arrays_match_selected_original': True,
       'direct_HM_verbose_flag_reset_by_native_FeedbackLevel': True,
       'failure_localization': 'HMcode nonlinear lensing path at two selected prior-interior captured points',
       'first_invalid_native_operation_identified': False,
       'solver_repair_or_uniform_support_proved': False, 'posterior_qualified': False,
       'ablation_model_used_as_production_fallback': False}
with (HERE / 'native_phase_self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Both isolated captured failures and eight scoped native ablations verified; HMcode mechanism and repair pending.')
