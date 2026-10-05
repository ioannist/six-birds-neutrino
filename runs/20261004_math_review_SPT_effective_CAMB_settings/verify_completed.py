"""Check frozen coordinates, effective settings and native numerical differences."""
import ast
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
selection = json.loads((HERE/'selection_receipt.json').read_text())
for s in selection['sources']:
    assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest() == s['sha256']
# Check both adapters actually derive requests from native ell support.
for adapter_path in [HERE/'pre_review_adapter.py', ROOT/'src/sbt_spt_audit/likelihoods/candl_cobaya.py']:
    parsed = ast.parse(adapter_path.read_text())
    cls = next(n for n in parsed.body if isinstance(n, ast.ClassDef) and n.name == 'CandlCobayaLikelihood')
    req = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'get_requirements')
    assert all(ast.get_source_segment(adapter_path.read_text(), req).count('"'+n+'"') == 1 for n in ['tt','te','ee','bb'])
    assert 'self._lmax_required = int(np.max(self._ells))' in adapter_path.read_text()
assert 'self.provider.get_param(key)' in (HERE/'pre_review_adapter.py').read_text()
reports = {}
for target in ['A', 'B']:
    record = json.loads((HERE/target/'evaluation_receipt.json').read_text())
    runtime = record['runtime']
    for path_key, hash_key in [('CAMB_module', 'CAMB_module_sha256'), ('Cobaya_CAMB_wrapper', 'Cobaya_CAMB_wrapper_sha256')]:
        assert hashlib.sha256(Path(runtime[path_key]).read_bytes()).hexdigest() == runtime[hash_key]
    assert not (HERE/target/'stderr.txt').read_bytes()
    old, new = [record['records'][s] for s in ['original_style', 'restoration_style']]
    assert old['requested_Cl'] == new['requested_Cl'] == {n: 3200 if target == 'A' else 4095 for n in ['tt','te','ee','bb']}
    assert old['effective_CAMB_extra_args']['lmax'] == (3200 if target == 'A' else 4095)
    assert new['effective_CAMB_extra_args']['lmax'] == 4095
    for key in ['internal_prior_policy', 'fixed_scalar_defaults', 'sampled_scalar_inputs', 'native_dataset_path']:
        assert old[key] == new[key]
    assert set(old['sampled_scalar_inputs']) <= set(selection['records'][target]['points']['original_median'])
    differences, spectral = {}, {}
    for label, point in selection['records'][target]['points'].items():
        a, b = old['evaluations'][label], new['evaluations'][label]
        assert a['point'] == b['point'] == point
        assert a['logpriors'] == b['logpriors']
        for v in [a, b]:
            assert abs(v['chi2_total']-sum(v['chi2_components'].values())) < 1e-10
            assert abs(v['logposterior']-(-v['chi2_total']/2+sum(v['logpriors']))) < 1e-10
        differences[label] = {'total_chi2_restoration_minus_original_style': b['chi2_total']-a['chi2_total'],
            'component_chi2_restoration_minus_original_style': {n: b['chi2_components'][n]-a['chi2_components'][n] for n in a['chi2_components']}}
        spectral[label] = {}
        with np.load(HERE/target/'original_style'/(label+'_spectra.npz')) as ca, np.load(HERE/target/'restoration_style'/(label+'_spectra.npz')) as cb:
            for name in ca.files:
                assert ca[name].shape == cb[name].shape
                delta = np.abs(ca[name]-cb[name])
                spectral[label][name] = {'max_abs_Cl_difference_microK2': float(np.max(delta)),
                                        'largest_abs_difference_ell': int(np.argmax(delta)),
                                        'bit_identical': bool(np.array_equal(ca[name],cb[name]))}
    for label, choice in selection['records'][target]['point_selection'].items():
        raw = (ROOT/choice['source_chain']).read_text().splitlines()
        header = next(line for line in raw if line.startswith('#')).lstrip('#').split()
        rows = [line.split() for line in raw if line.strip() and not line.startswith('#')]
        point = selection['records'][target]['points'][label]
        assert point == {n: float(rows[choice['stored_row_index']][header.index(n)]) for n in point}
        kept = rows[len(rows)//5:]
        q, m = Fraction(choice['mass_quantile']), Fraction(rows[choice['stored_row_index']][header.index('mnu')])
        total = sum(Fraction(row[0]) for row in kept)
        below = sum(Fraction(row[0]) for row in kept if Fraction(row[header.index('mnu')]) < m)
        inclusive = sum(Fraction(row[0]) for row in kept if Fraction(row[header.index('mnu')]) <= m)
        assert below < q*total <= inclusive
    med, plus = 'restoration_median', 'restoration_median_mass_plus_001'
    response = {s: record['records'][s]['evaluations'][plus]['chi2_total']-record['records'][s]['evaluations'][med]['chi2_total'] for s in record['records']}
    reports[target] = {'current_versions': runtime['versions'], 'archived_versions': selection['archived_versions'][target],
        'original_style_effective_lmax': old['effective_CAMB_extra_args']['lmax'],
        'restoration_style_effective_lmax': new['effective_CAMB_extra_args']['lmax'],
        'native_Cl_requirements': old['requested_Cl'], 'sampled_Candl_scalar_inputs': old['sampled_scalar_inputs'],
        'native_chi2_differences': differences, 'supported_spectral_differences': spectral,
        'median_mass_plus_001_chi2_response': response,
        'mass_response_change': response['restoration_style']-response['original_style'],
        'max_absolute_selected_chi2_change': max(abs(d['total_chi2_restoration_minus_original_style']) for d in differences.values())}
assert reports['A']['current_versions'] == reports['B']['current_versions']
assert all(v['archived_versions']['archived_CAMB'] == '1.6.5' for v in reports.values())
assert all(v['current_versions']['camb'] == '2.0.4' for v in reports.values())
out = {'utc': datetime.now(timezone.utc).isoformat(), 'reports': reports,
       'selected_native_evaluations': 20, 'actual_original_stack_replayed': False,
       'historical_lmax_directly_observed': False,
       'archived_configuration_style_reconstructed_on_current_stack': True,
       'posterior_quantile_sensitivity_or_uniform_accuracy_certified': False,
       'original_to_restored_p95_difference_attributed_to_lmax': False,
       'original_to_restored_p95_difference_attributed_entirely_to_sampling': False,
       'historical_package_versions_and_native_data_identity_remaining_obligation': True,
       'material_claim_revision_adopted': False, 'paper_modified': False}
with (HERE/'comparison_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False)+'\n')
print(json.dumps({k: {n: v[n] for n in ['original_style_effective_lmax','restoration_style_effective_lmax','max_absolute_selected_chi2_change','mass_response_change']} for k,v in reports.items()}, indent=2))
