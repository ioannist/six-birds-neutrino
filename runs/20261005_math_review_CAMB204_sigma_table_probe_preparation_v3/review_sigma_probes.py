"""Reconstruct sigma-probe provenance and the coarse-grid stopping witnesses."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
first = ROOT / 'runs/20261005_math_review_CAMB204_sigma_probe_preparation'
second = ROOT / 'runs/20261005_math_review_CAMB204_sigma_probe_preparation_v2'
p = json.loads((first / 'source_preparation.json').read_text())
original = Path(p['original_source']).read_text()
assert sha(p['original_source']) == p['original_sha256']
source1 = (first / 'sigma_probe_halofit.f90').read_text()
assert sha(first / 'sigma_probe_halofit.f90') == p['instrumented_sha256']
text = source1
audit_block = p['appended_audit_integrator'] + '\n\n    end module NonLinear'
assert text.count(audit_block) == 1
text = text.replace(audit_block, '    end module NonLinear', 1)
for old, new in reversed(p['changes']):
    assert text.count(new) == 1
    text = text.replace(new, old, 1)
assert text == original
c = json.loads((second / 'correction_receipt.json').read_text())
source2 = (second / 'sigma_probe_halofit.f90').read_text()
assert sha(second / 'sigma_probe_halofit.f90') == c['corrected_source_sha256']
start = source2.index('    function integrate_audit(')
head, tail = source2[:start], source2[start:]
for old, new in reversed(c['changes']):
    assert tail.count(new) == 1
    tail = tail.replace(new, old, 1)
assert head + tail == source1
v = json.loads((HERE / 'source_preparation.json').read_text())
source3 = (HERE / 'sigma_table_probe_halofit.f90').read_text()
assert sha(HERE / 'sigma_table_probe_halofit.f90') == v['instrumented_sha256']
text = source3
for old, new in reversed(v['changes']):
    assert text.count(new) == 1
    text = text.replace(new, old, 1)
assert text == source2

def function(text, name):
    start = text.index('    function ' + name + '(')
    end = text.index('    end function ' + name, start) + len('    end function ' + name)
    return text[start:end]
audit = function(source2, 'integrate_audit').replace('integrate_audit', 'integrate')
audit = audit.replace('cosm, acc, minimum_level, stopping_level)', 'cosm, acc)', 1)
audit = audit.replace('integer, intent(in) :: minimum_level', 'integer, parameter :: jmin = 5', 1)
audit = audit.replace('j >= minimum_level', 'j >= jmin', 1)
audit = '\n'.join(line for line in audit.splitlines()
                  if not line.strip().startswith('stopping_level =') and
                  line.strip() != 'integer, intent(out) :: stopping_level')
assert [line.strip() for line in audit.splitlines()] == [line.strip() for line in function(original, 'integrate').splitlines()]

records = []
for seed, anomaly in [(2003, 9), (2004, 21)]:
    text = (HERE / f'seed{seed}_stdout.txt').read_text()
    assert (HERE / f'seed{seed}_stderr.txt').read_text().strip() == 'ERROR STOP AUDIT after direct and refined sigma probes before invalid fractional power'
    node_lines = [l for l in text.splitlines() if l.startswith('AUDIT_SIGMA_NODE ')]
    table_lines = [l for l in text.splitlines() if l.startswith('AUDIT_SIGMA_TABLE ')]
    assert [int(l.split()[1]) for l in node_lines] == list(range(1, 257))
    assert [int(l.split()[1]) for l in table_lines] == list(range(1, 65))
    nodes = np.array([[float(x) for x in l.split()[2:]] for l in node_lines])
    table = np.array([[float(x) for x in l.split()[2:]] for l in table_lines])
    assert nodes.shape == (256, 7) and table.shape == (64, 7)
    assert np.isfinite(nodes).all() and np.isfinite(table).all()
    assert (nodes[:, :5] > 0).all() and (table[:, :5] > 0).all()
    assert (np.diff(nodes[:, 0]) > 0).all() and (np.diff(table[:, 0]) > 0).all()
    assert (np.diff(nodes[:, 1]) > 0).any()
    assert (np.diff(nodes[:, 3]) < 0).all() and (np.diff(nodes[:, 4]) < 0).all()
    assert (nodes[:, 5] >= 12).all() and (nodes[:, 6] >= 14).all()
    assert (table[:, 6] >= 14).all()
    # Repeat of original table construction, including exp(log(sqrt(I))).
    assert np.max(np.abs(table[:, 1]/table[:, 2]-1)) < 1e-14
    assert np.array_equal(table[:, 2], table[:, 3])
    steps = np.array([[float(x) for x in l.split()[1:]] for l in text.splitlines()
                      if l.startswith('AUDIT_INTEGRATION_STEP ')])
    radius = table[anomaly-1, 0]
    short = steps[(np.abs(steps[:, 0]-radius) < 1e-14) & (steps[:, 2] == 5)]
    refined = steps[(np.abs(steps[:, 0]-radius) < 1e-14) & (steps[:, 2] == 14)]
    assert np.array_equal(short[:, 3], np.arange(1, 6))
    assert refined[-1, 3] == table[anomaly-1, 6]
    assert np.array_equal(short[:, 4:], refined[:5, 4:])
    relative_stop = abs(short[-1, 4]/short[-1, 5]-1)
    assert relative_stop < float(np.float32(1e-4))
    next_ratio = refined[5, 4]/refined[4, 4]
    assert next_ratio > 3
    with (HERE / f'seed{seed}_reviewed_sigma_arrays.npz').open('xb') as f:
        np.savez_compressed(f, nodes=nodes, table=table, integration_steps=steps)
    records.append({'seed': seed, 'all_node_count': len(nodes), 'table_point_count': len(table),
                    'table_anomaly_index': anomaly, 'anomalous_radius_Mpc_per_h': radius,
                    'original_table_sigma_at_failure_redshift': table[anomaly-1, 1],
                    'refined_table_sigma_at_failure_redshift': table[anomaly-1, 4],
                    'coarse_stop_level': int(short[-1, 3]), 'coarse_stop_grid_points': 17,
                    'coarse_relative_adjacent_estimate_change': relative_stop,
                    'next_refinement_integral_ratio': next_ratio,
                    'refined_stopping_level': int(table[anomaly-1, 6]),
                    'interpolated_node_sigma_increases': int((np.diff(nodes[:, 1]) > 0).sum()),
                    'default_direct_node_sigma_increases': int((np.diff(nodes[:, 2]) > 0).sum()),
                    'refined12_node_sigma_increases': int((np.diff(nodes[:, 3]) > 0).sum()),
                    'refined14_node_sigma_increases': int((np.diff(nodes[:, 4]) > 0).sum()),
                    'maximum_node_LUT_vs_default_direct_relative_difference': float(np.max(np.abs(nodes[:, 1]/nodes[:, 2]-1))),
                    'maximum_node_refined12_vs14_relative_difference': float(np.max(np.abs(nodes[:, 3]/nodes[:, 4]-1))),
                    'stdout_sha256': sha(HERE / f'seed{seed}_stdout.txt'),
                    'reviewed_arrays_sha256': sha(HERE / f'seed{seed}_reviewed_sigma_arrays.npz')})
production = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/camb/camblib.so')
assert sha(production) == '306640a8948cd5246fc9b21e76525f6adebdff5ba3bc792a57d50bba67225ad5'
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'records': records, 'source_changes_reversed_exactly': True,
       'audit_integrator_numerical_statements_match_original': True,
       'coarse_grid_adjacent_agreement_does_not_establish_integral_error_bound': True,
       'empirical_refinement_agreement_is_uniform_error_certificate': False,
       'production_module_unchanged': True, 'posterior_qualified': False}
with (HERE / 'sigma_probe_self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Reviewed all512 node probes and128 table points; both anomalous integrals stop at17 points before a >3x next-grid change.')
