"""Self-review statement coverage, endpoint controls and transitive axioms."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
module = ROOT / 'lean/trunc_gauss_proof/TruncGaussProof/GaussianQuantile.lean'
new = set(re.findall(r'^theorem (\w+)', module.read_text(), re.M))
assert new == {'truncatedGaussianLaw_cdf_continuous', 'truncatedGaussianLaw_cdf_lt_one',
               'truncatedGaussianLaw_existsUnique_quantile'}
public = set()
for path in (ROOT / 'lean/trunc_gauss_proof/TruncGaussProof').glob('*.lean'):
    source = path.read_text()
    names = set(re.findall(r'^theorem (\w+)', source, re.M))
    assert not public.intersection(names)
    assert not re.search(r'^\s*(axiom|opaque)\b|\b(sorry|admit)\b', source, re.M)
    public.update(names)
assert len(public) == 74
printed = set(re.findall(r'^#print axioms TruncGaussProof\.(\w+)',
    (ROOT / 'lean/trunc_gauss_proof/AuditAxioms.lean').read_text(), re.M))
assert printed == public
stdout = (HERE / 'math_check_stdout.txt').read_text()
assert '130 passed' in stdout and 'Build completed successfully' in stdout
axioms = {n: {a.strip() for a in re.split(r',\s*', values.strip()) if a.strip()}
          for n, values in re.findall(r"'TruncGaussProof\.(\w+)' depends on axioms: \[([^\]]*)\]", stdout)}
allowed = {'propext', 'Classical.choice', 'Quot.sound'}
assert set(axioms) == public and all(a <= allowed for a in axioms.values())
assert len(re.findall(r'^example\b', (HERE / 'GaussianQuantileReview.lean').read_text(), re.M)) == 9
for name in ['build_stderr.txt', 'full_module_build_stderr.txt',
             'formal_review_stdout.txt', 'formal_review_stderr.txt', 'math_check_stderr.txt']:
    assert not (HERE / name).read_bytes(), name
assert not subprocess.check_output(['git', 'diff', 'ffdaf4b', '--name-only', '--',
                                   'paper', 'docs/findings/canonical_results.json'], cwd=ROOT)
runtime = json.loads((HERE / 'runtime_observation.json').read_text())
assert runtime['owned_live_samplers'] == 28
growth = json.loads((HERE / 'growth_observation.json').read_text())
assert not any(r['assessment_due'] for r in growth['progress'].values())
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
for lens in ['A', 'B']:
    diagnostic = ROOT / state['latest_SPT_' + lens + '_diagnostic_bundle'] / ('chain_' + lens + '_diagnostics.json')
    assert json.loads(diagnostic.read_text())['all_diagnostic_thresholds_pass']
for group, bundle in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items():
    assert not json.loads((ROOT / bundle / (group + '_diagnostics.json')).read_text())['all_diagnostic_thresholds_pass']

phases = [
    {'session': 48816, 'phase': 'initial_elaboration_three_errors', 'exit_code': 1},
    {'session': 3105, 'phase': 'continuity_and_quantile_existence_module', 'exit_code': 0},
    {'session': 21552, 'phase': 'three_theorem_module', 'exit_code': 0},
    {'session': 40580, 'phase': 'initial_formal_review_Dirac_rational_comparison_unclosed', 'exit_code': 1},
    {'session': 34238, 'phase': 'nine_formal_controls', 'exit_code': 0},
    {'session': 18459, 'phase': 'combined_make_math_check', 'exit_code': 0},
]
out = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'reviewer': 'distinct_self_review_no_independent_agent',
    'scope': 'quantile_existence_uniqueness_for_actual_integral_constructed_halfline_Gaussian_law',
    'new_exported_theorems': sorted(new), 'exported_theorems_axiom_checked': 74,
    'allowed_transitive_axioms': sorted(allowed), 'Python_tests_passed': 130,
    'formal_controls': 9, 'managed_phases': phases,
    'continuity_bridge': 'derived zero singleton mass, measure_cdf and Stieltjes jump formula',
    'existence_bridge': 'derived probability law, CDF limit one, finite interval intermediate value theorem',
    'uniqueness_bridge': 'positive quantile coordinate and previously derived strict increase on physical halfline',
    'quantile_scope': 'every real mean; positive sigma; every 0<q<1; exactly one positive finite coordinate with CDF q',
    'endpoint_scope': 'CDF zero on nonpositive coordinates; strictly below one at all finite coordinates',
    'substantive_excluded_case': 'zero-variance actual Gaussian Dirac law has no coordinate attaining CDF 19/20',
    'prior_interpretation': 'constant prior on physical halfline',
    'finite_upper_gate_quantile_law_proved': False,
    'numerical_inversion_or_floating_point_error_certificate': False,
    'cosmological_Gaussianity_or_MCMC_convergence_certified': False,
    'production_Python_changed': False, 'paper_modified': False,
    'material_claim_revision_adopted': False, 'owned_live_samplers_verified': 28,
    'new_diagnostic_assessment_due_at_observation': False,
    'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted((ROOT / 'lean/trunc_gauss_proof').rglob('*.lean')) if '.lake' not in p.parts]
             + [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
                and p.name != 'validation_receipt.json'],
}
with (HERE / 'validation_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Three new theorem endpoints, nine formal controls, 130 Python tests, and all 74 transitive axiom outputs verified.')
