"""Check that the decision record does not turn incomplete evidence into a result."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
path = HERE / 'decision_packet.json'
packet = read(path)
for s in packet['sources']:
    assert sha(ROOT / s['path']) == s['sha256']
assert not packet['material_claim_revision_adopted'] and not packet['paper_or_canonical_modified']
magnitude = packet['magnitude']
assert magnitude['original_canonical_shift_eV'] == 0.10860629275736843
assert not magnitude['current_qualified_numeric_replacement_available']
assert not magnitude['restoration_of_original_point109_guaranteed']
for e in magnitude['original_archived_chain_diagnostics'].values():
    assert e['chains'] == 1 and e['scalar_split_Rhat'] > 1.05 and e['scalar_ESS_proxy'] < 400
    assert not e['posterior_qualified']
assert 'suspended' in magnitude['historical_current_stack_shift_scope']
for e in magnitude['fresh_validated_policy_comparisons'].values():
    d = read(ROOT / e['diagnostics'])
    assert not d['all_diagnostic_thresholds_pass'] and not e['posterior_qualified']
    assert e['mass_quantile_MCSE_eV'] == d['diagnostics']['mnu']['quantile_mcse']
    assert e['mass_quantile_MCSE_limit_eV'] == 0.001
local = packet['localization']
forward = local['full_CMB_same_source_pair']['B_given_A']['range_signed_deltaQ']
reverse = local['full_CMB_same_source_pair']['A_given_B']['range_signed_deltaQ']
assert max(forward, key=forward.get) == 'EE'
assert max(reverse, key=reverse.get) == 'TT' and reverse['TE'] < 0
assert max(local['SPT_only_B_given_A'], key=local['SPT_only_B_given_A'].get) == 'TT'
assert not local['broad_full_CMB_TT_dominance_established']
assert not local['global_profile_optimality_or_pure_packaging_causality_proved']
assert 'More chain history alone does not change' in local['restoration_route']
assert 'Do not promote the suspended' in magnitude['future_narrowing_route']
with (HERE / 'self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'distinct_self_review_not_independent_agent', 'packet_sha256': sha(path),
        'all_sources_bound': True, 'suspended_numeric_readout_not_promoted': True,
        'both_directions_and_baselines_reconstructed': True,
        'future_localization_scope_and_magnitude_restore_routes_distinguished': True,
        'current_numeric_replacement_or_broad_TT_statement_adopted': False,
        'paper_modified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Decision record reviewed: no current qualified replacement or broad TT result smuggled in.')
