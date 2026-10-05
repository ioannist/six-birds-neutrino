"""Distinct recount and rational controls for the adaptation-scope audit."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt_path = HERE / 'adaptation_receipt.json'
receipt = json.loads(receipt_path.read_text())
assert importlib.metadata.version('cobaya') == receipt['upstream_version']
for item in receipt['files']:
    assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
assert hashlib.sha256((ROOT / receipt['runtime_receipt']).read_bytes()).hexdigest() == receipt['runtime_receipt_sha256']

groups = Counter()
for record in receipt['records']:
    raw = (ROOT / record['frozen_chain']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == record['frozen_chain_sha256']
    lines = [line.split() for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
    count = len(lines)
    burn = count // 5
    assert count == record['stored_rows'] and burn == record['discarded_stored_rows']
    weights = [Fraction(line[0]) for line in lines[burn:]]
    assert all(w.denominator == 1 and w > 0 for w in weights)
    assert sum(weights) == record['retained_represented_steps']
    text = (ROOT / record['log_snapshot']).read_text()
    segments = text.split('Updated covariance matrix of proposal pdf.')
    sizes = []
    for before_update in segments[:-1]:
        matches = re.findall(r'Learn \+ convergence test @ ([0-9]+) samples accepted', before_update)
        assert matches
        sizes.append(int(matches[-1]))
    assert sizes == record['logged_update_collection_sizes']
    interior = [n for n in sizes if burn < n < count]
    assert interior == record['updates_strictly_inside_retained_history']
    groups[record['cohort']] += bool(interior)
assert groups == {'SPT_A': 6, 'SPT_B': 6, 'quad_A': 4, 'quad_B': 4, 'medium_A': 0, 'medium_B': 0}

# Stronger control: both component kernels are irreducible and aperiodic.
# For symmetric two-state kernels, detailed balance with the uniform target is
# entry symmetry. The state-selected kernel has identical rows (1/4, 3/4).
q = Fraction
slow = [[q(3, 4), q(1, 4)], [q(1, 4), q(3, 4)]]
fast = [[q(1, 4), q(3, 4)], [q(3, 4), q(1, 4)]]
for kernel in [slow, fast]:
    assert all(sum(row) == 1 and all(p > 0 for p in row) for row in kernel)
    assert kernel[0][1] == kernel[1][0]
    assert [sum(kernel[i][j] / 2 for i in range(2)) for j in range(2)] == [q(1, 2), q(1, 2)]
selected = [fast[0], slow[1]]
assert selected[0] == selected[1] == [q(1, 4), q(3, 4)]
assert [sum(selected[i][j] / 2 for i in range(2)) for j in range(2)] == [q(1, 4), q(3, 4)]

counterexample = {
    'target': ['1/2', '1/2'],
    'slow_kernel': [['3/4', '1/4'], ['1/4', '3/4']],
    'fast_kernel': [['1/4', '3/4'], ['3/4', '1/4']],
    'each_kernel_target_reversible_irreducible_aperiodic': True,
    'selection': 'fast if current state is 0; slow if current state is 1',
    'selected_transition': [['1/4', '3/4'], ['1/4', '3/4']],
    'unique_stationary_distribution': ['1/4', '3/4'],
    'distribution_after_one_step_from_any_initial_distribution': ['1/4', '3/4'],
    'scope': 'refutes arbitrary state-dependent adaptation inference; no claim of this behavior in Cobaya',
}
with (HERE / 'counterexample_strengthening.json').open('x') as handle:
    handle.write(json.dumps(counterexample, indent=2) + '\n')
assert __import__('subprocess').run(['git', 'diff', '--exit-code', 'ffdaf4b', '--', 'paper'], cwd=ROOT, capture_output=True).returncode == 0
out = {
    'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_no_independent_agent',
    'receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    'integer_holding_times_recounted': 28, 'log_update_coordinates_recounted': 28,
    'families_with_internal_updates_by_cohort': dict(groups),
    'source_coordinate_review': 'check_ready uses len(collection); collection adds a stored old point on acceptance; output thinning disabled',
    'fractional_adaptation_counterexample_verified': True,
    'SPT_previous_empirical_gate_results_preserved': True,
    'no_adaptive_MCMC_convergence_or_floating_precision_certificate': True,
    'CLASS_cohorts_remain_provisional': True, 'paper_unchanged_against_pre_review': True,
}
with (HERE / 'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2) + '\n')
print('28 frozen histories and proposal logs recounted; 20 contain retained-history updates; exact controls verified.')
