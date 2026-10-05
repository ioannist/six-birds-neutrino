"""Check the paper's stated high-ell range using signed full-precision rows.

Range sums are additive allocations of the residual quadratic, not separate
likelihoods, independent block chi-square variables, or causal attributions.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
run_names = [
    'cosmological_spt_desi', 'cosmological_spt_desi_staging',
    'cosmological_cmb_desi_warm', 'cosmological_cmb_desi_tau_control',
    'cosmological_cmb_desi_staging', 'cosmological_cmb_desi',
    'cosmological_cmb_desi_accuracy',
]
results, hashes = {}, {}
for name in run_names:
    directory = ROOT / 'runs' / ('20261003_math_review_' + name)
    paths = {key: directory / filename for key, filename in
             [('metrics', 'metrics.json'), ('verification', 'accounting_verification.json')]}
    data = {key: json.loads(path.read_text()) for key, path in paths.items()}
    hashes[name] = {key: hashlib.sha256(path.read_bytes()).hexdigest()
                    for key, path in paths.items()}
    assert set(data['metrics']['directions']) == set(data['verification']) == {'B_given_A', 'A_given_B'}
    results[name] = {}
    for direction, original in data['metrics']['directions'].items():
        verified = data['verification'][direction]
        assert verified['fresh_endpoint_spectra_verified']
        assert np.isclose(original['joint_candidate_delta_chi2'],
                          verified['joint_candidate_delta_chi2'], atol=1e-7, rtol=1e-10)
        edges = original['ell_edges']
        assert all(math.isfinite(value) for value in edges)
        assert all(a < b for a, b in zip(edges[:-1], edges[1:]))
        first, last = edges.index(2000.), edges.index(3000.)
        assert first < last
        grid = original['spt_deltaQ_by_spec_ell']
        assert set(grid) == {'TT', 'TE', 'EE'}
        for values in grid.values():
            assert len(values) == len(edges) - 1 and all(math.isfinite(value) for value in values)
        ledger = verified['ledger']
        assert ledger['method'] == 'r_i_times_full_precision_r_i_signed_cross_term_allocation'
        all_bands = {spec: math.fsum(values) for spec, values in grid.items()}
        grid_sum = math.fsum(all_bands.values())
        assert np.isclose(grid_sum, ledger['deltaQ_heatmap'], atol=1e-7, rtol=1e-10)
        assert np.isclose(grid_sum + ledger['unlocalized_deltaQ'], ledger['deltaQ_full'],
                          atol=1e-7, rtol=1e-10)
        high_ell = {spec: math.fsum(values[first:last]) for spec, values in grid.items()}
        largest = max(high_ell, key=high_ell.get)
        results[name][direction] = {
            'signed_totals_effective_ell_2000_inclusive_3000_exclusive': high_ell,
            'largest_signed_sector_in_stated_range': largest,
            'signed_totals_all_reported_bands': all_bands,
            'largest_positive_individual_group': verified['top_groups'][0],
            'unlocalized_deltaQ': ledger['unlocalized_deltaQ'],
            'full_covariance_quadratic_sum_reconciles': True,
        }
paper_sources = ['abstract.tex', 'results_audits.tex', 'discussion.tex', 'conclusion.tex']
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'signed_sector_aggregation_over_the_papers_stated_high_ell_range_at_verified_candidates',
    'paper_claim_source_sha256': {
        name: hashlib.sha256((ROOT / 'paper/sections' / name).read_bytes()).hexdigest()
        for name in paper_sources},
    'native_source_sha256': hashes,
    'results': results,
    'interpretation': 'The specified high-ell range and the largest individual group are checked separately. Reported-band sums omit the explicitly retained unlocalized rows. None is an independent block likelihood or a causal allocation.',
    'global_optimum_certified': False,
    'posterior_convergence_certified': False,
    'paper_modified': False,
}
(HERE / 'range_verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({name: {direction: record['signed_totals_effective_ell_2000_inclusive_3000_exclusive']
                         for direction, record in directions.items()}
                  for name, directions in results.items()}, indent=2))
