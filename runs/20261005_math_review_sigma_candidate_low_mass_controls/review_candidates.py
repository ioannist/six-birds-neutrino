"""Review candidate source scope and selected high/low-mass comparisons."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
candidate_roots = {level: ROOT / f'runs/20261005_math_review_CAMB204_sigma_integration_candidate{level}'
                   for level in [12, 14]}
p = json.loads((candidate_roots[12] / 'source_preparation.json').read_text())
source12 = (candidate_roots[12] / 'candidate_halofit.f90').read_text()
assert sha(candidate_roots[12] / 'candidate_halofit.f90') == p['candidate_sha256']
text = source12
for old, new in reversed(p['changes']):
    assert text.count(new) == 1
    text = text.replace(new, old, 1)
assert text.encode() == Path(p['original_source']).read_bytes()
q = json.loads((candidate_roots[14] / 'source_preparation.json').read_text())
source14 = (candidate_roots[14] / 'candidate_halofit.f90').read_text()
assert sha(candidate_roots[14] / 'candidate_halofit.f90') == q['candidate_sha256']
old, new = q['change']
assert source14.count(new) == 1 and source14.replace(new, old, 1) == source12

def compare_arrays(a, b):
    result = {}
    with np.load(a) as left, np.load(b) as right:
        assert set(left.files) == set(right.files)
        for key in left.files:
            x, y = left[key], right[key]
            assert x.shape == y.shape and np.isfinite(x).all() and np.isfinite(y).all()
            delta = float(np.max(np.abs(x-y)))
            scale = float(np.max(np.abs(y)))
            result[key] = {'maximum_absolute_difference': delta,
                           'relative_to_reference_array_maximum': delta/scale if scale else (0. if delta == 0 else None)}
    return result

high_mass = []
for seed in [2003, 2004]:
    values = []
    for level in [12, 14]:
        folder = candidate_roots[level] / f'seed{seed}_phase_classification'
        v = json.loads((folder / 'phase_classification.json').read_text())
        assert v['isolated_point_status'] == 'finite_evaluation'
        assert v['numerical_settings_changed']
        assert sha(folder / 'native_arrays.npz') == v['native_arrays_sha256']
        assert sha(v['debug_module']) == v['debug_module_sha256']
        assert sha(ROOT / v['capture']) == v['capture_sha256']
        assert all(t['all_finite'] for t in v['provider_spectra'].values())
        assert all(t['all_finite'] for t in v['native_spectra'].values())
        components = v['finite_target_components']
        assert abs(components['logpost']-sum(components['logpriors'])-sum(components['loglikes'])) < 1e-9
        values.append(v)
    x, y = values
    assert x['sampled'] == y['sampled'] and x['native_parameters'] == y['native_parameters']
    assert x['finite_target_components']['logpriors'] == y['finite_target_components']['logpriors']
    assert x['finite_target_components']['loglikes'][1] == y['finite_target_components']['loglikes'][1]
    high_mass.append({'seed': seed, 'mass_eV': x['sampled']['mnu'],
                      'candidate12_minus14_logpost': x['finite_target_components']['logpost']-y['finite_target_components']['logpost'],
                      'all_provider_and_native_spectra_finite': True,
                      'arrays': compare_arrays(candidate_roots[12] / f'seed{seed}_phase_classification/native_arrays.npz',
                                               candidate_roots[14] / f'seed{seed}_phase_classification/native_arrays.npz')})

selection = json.loads((HERE / 'selection_receipt.json').read_text())
evaluations = {}
for variant in ['original_debug', 'candidate12', 'candidate14']:
    receipt = json.loads((HERE / variant / 'evaluation_receipt.json').read_text())
    assert receipt['selection_receipt_sha256'] == sha(HERE / 'selection_receipt.json')
    assert sha(receipt['native_module']) == receipt['native_module_sha256']
    assert len(receipt['records']) == len(selection['records']) == 6
    assert not (HERE / f'{variant}_stderr.txt').read_bytes()
    for index, (record, selected) in enumerate(zip(receipt['records'], selection['records'])):
        assert record['selection_index'] == index and record['point'] == selected['point']
        assert sha(ROOT / record['provider_arrays']) == record['provider_arrays_sha256']
        assert abs(record['logpost']-sum(record['logpriors'])-sum(record['loglikes'])) < 1e-9
    evaluations[variant] = receipt
assert len({r['evaluation_config_sha256'] for r in evaluations.values()}) == 1
low_mass = []
for index, selected in enumerate(selection['records']):
    a, b, c = [evaluations[v]['records'][index] for v in ['original_debug', 'candidate12', 'candidate14']]
    assert a['logpriors'] == b['logpriors'] == c['logpriors']
    assert a['loglikes'][1] == b['loglikes'][1] == c['loglikes'][1]
    low_mass.append({'selection_index': index, 'mass_eV': selected['point']['mnu'],
                     'original_debug_minus_candidate12_logpost': a['logpost']-b['logpost'],
                     'candidate12_minus14_logpost': b['logpost']-c['logpost'],
                     'original_debug_vs_candidate12_arrays': compare_arrays(ROOT/a['provider_arrays'], ROOT/b['provider_arrays']),
                     'candidate12_vs14_arrays': compare_arrays(ROOT/b['provider_arrays'], ROOT/c['provider_arrays'])})
production = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/camb/camblib.so')
assert sha(production) == '306640a8948cd5246fc9b21e76525f6adebdff5ba3bc792a57d50bba67225ad5'
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'high_mass': high_mass, 'low_mass': low_mass,
       'maximum_high_mass_candidate12_vs14_logpost_difference': max(abs(v['candidate12_minus14_logpost']) for v in high_mass),
       'maximum_low_mass_candidate12_vs14_logpost_difference': max(abs(v['candidate12_minus14_logpost']) for v in low_mass),
       'maximum_low_mass_original_debug_vs_candidate12_logpost_difference': max(abs(v['original_debug_minus_candidate12_logpost']) for v in low_mass),
       'candidate_physical_integrand_and_nonlinear_model_changed': False,
       'candidate_sigma_stopping_parameters_changed': True,
       'source_changes_reversed_exactly': True, 'all_selected_candidate_evaluations_finite': True,
       'BAO_component_and_priors_identical_in_selected_comparisons': True,
       'production_module_unchanged': True, 'production_adopted': False,
       'uniform_numerical_accuracy_or_full_prior_support_proved': False,
       'posterior_qualified': False, 'scope': selection['scope']}
with (HERE / 'candidate_comparison_self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Reviewed two formerly failing points and six low-mass controls across both refinement candidates and original debug source.')
