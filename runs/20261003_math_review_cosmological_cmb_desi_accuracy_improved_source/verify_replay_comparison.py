"""Check the consistent candidate pair and its exact stated-range allocation."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT / 'runs/20261003_math_review_cosmological_cmb_desi_accuracy'
inputs = json.loads((HERE / 'inputs.json').read_text())
for name, digest in inputs['parent_sha256'].items():
    assert hashlib.sha256((PARENT / name).read_bytes()).hexdigest() == digest
for name, digest in inputs['executed_source_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
assert (HERE / 'resolved.yaml').read_bytes() == (PARENT / 'resolved.yaml').read_bytes()
current = json.loads((HERE / 'metrics.json').read_text())
parent = json.loads((PARENT / 'metrics.json').read_text())
native = json.loads((HERE / 'accounting_verification.json').read_text())
parent_native = json.loads((PARENT / 'accounting_verification.json').read_text())
assert set(current['directions']) == set(native) == {'B_given_A'}
assert set(parent['directions']) == set(parent_native) == {'B_given_A', 'A_given_B'}
forward = current['directions']['B_given_A']
reverse = parent['directions']['A_given_B']
reverse_source = reverse.get('source_candidate', parent['fits']['lensB'])
for first, second in [(forward['source_candidate'], reverse['reference_candidate']),
                      (forward['reference_candidate'], reverse_source)]:
    assert first['point'] == second['point']
    assert first['loglike'] == second['loglike']
results = {}
for label, direction, proof in [('B_given_A', forward, native['B_given_A']),
                               ('A_given_B', reverse, parent_native['A_given_B'])]:
    for flag in ['fresh_endpoint_spectra_verified', 'fixed_source_coordinates_verified',
                 'candidate_reference_nesting_verified']:
        assert proof[flag]
    assert direction['optimization_success'] and not direction['global_optimum_certified']
    assert math.isclose(direction['joint_candidate_delta_chi2'], proof['joint_candidate_delta_chi2'], rel_tol=1e-10, abs_tol=1e-7)
    edges = direction['ell_edges']
    assert edges == sorted(set(edges)) and 2000. in edges and 3000. in edges
    grid = direction['spt_deltaQ_by_spec_ell']
    assert set(grid) == {'TT', 'TE', 'EE'}
    assert all(len(values) == len(edges)-1 and all(math.isfinite(v) for v in values) for values in grid.values())
    indices = [i for i in range(len(edges)-1) if 2000. <= edges[i] < 3000.]
    assert [edges[i] for i in indices] == [2000., 2500.]
    assert edges[indices[-1]+1] == 3000.
    totals = {spec: math.fsum(values[i] for i in indices) for spec, values in grid.items()}
    ledger = direction['spt_ledger']
    assert math.isclose(math.fsum(v for values in grid.values() for v in values) + ledger['unlocalized_deltaQ'], ledger['deltaQ_full'], rel_tol=1e-10, abs_tol=1e-7)
    results[label] = {'joint_candidate_delta_chi2': proof['joint_candidate_delta_chi2'],
                     'range_signed_deltaQ': totals, 'range_dominant_allocated_spec': max(totals, key=totals.get),
                     'fresh_native_reconstruction_error': proof['spt_native_reconstruction_error']}
old_forward = parent['directions']['B_given_A']['joint_candidate_delta_chi2']
receipt = {
    'scope': 'consistent_strongest_found_parent_pair_and_stated_range_native_allocation',
    'same_source_reference_pair_in_both_directions': True,
    'legacy_reverse_source_basis': 'retained_parent_B_fit',
    'unchanged_declared_model_configuration': True,
    'source_A_mass_eV': forward['source_candidate']['point']['mnu_sample'],
    'source_B_mass_eV': reverse_source['point']['mnu_sample'],
    'forward_change_from_original_parent_source_percent': 100*(results['B_given_A']['joint_candidate_delta_chi2']/old_forward-1),
    'range_convention': '2000 <= effective_ell < 3000',
    'results': results,
    'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for directory in [HERE, PARENT]
                      for path in [directory/'metrics.json', directory/'accounting_verification.json', directory/'resolved.yaml']},
    'global_optimum_certified': False, 'posterior_convergence_verified': False,
    'independent_chi_square_blocks_or_causal_attribution': False,
}
(HERE / 'comparison_verification.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
print(json.dumps(receipt, indent=2, allow_nan=False))
