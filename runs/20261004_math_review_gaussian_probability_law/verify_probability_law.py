"""Check exact statement coverage and fresh combined proof/test evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LEAN = ROOT / 'lean/trunc_gauss_proof'
sources = sorted((LEAN / 'TruncGaussProof').glob('*.lean'))
public = {name for p in sources for name in re.findall(r'^(?:theorem|lemma)\s+(\w+)', p.read_text(), re.M)}
printed = set(re.findall(r'^#print axioms TruncGaussProof\.(\w+)', (LEAN / 'AuditAxioms.lean').read_text(), re.M))
assert public == printed and len(public) == 65
for p in sources:
    assert not re.search(r'\b(?:sorry|admit)\b|^axiom\s', p.read_text(), re.M)
stdout = (HERE / 'math_check_stdout.txt').read_text()
assert '119 passed' in stdout and 'Build completed successfully' in stdout
assert not (HERE / 'math_check_stderr.txt').read_bytes()
checked = re.findall(r"'TruncGaussProof\.(\w+)' depends on axioms: \[([^\]]*)\]", stdout)
assert len(checked) == 65 and {name for name, _ in checked} == public
allowed = {'propext', 'Classical.choice', 'Quot.sound'}
for name, axioms in checked:
    assert set(a.strip() for a in axioms.split(',') if a.strip()) <= allowed
new = {n for n in public if n.startswith('truncatedGaussianLaw_')}
assert new == {'truncatedGaussianLaw_isProbability', 'truncatedGaussianLaw_absolutelyContinuous',
               'truncatedGaussianLaw_negative_halfline', 'truncatedGaussianLaw_singleton',
               'truncatedGaussianLaw_boundary_interval_pos'}
review = HERE / 'GaussianMeasureReview.lean'
assert len(re.findall(r'^example\b', review.read_text(), re.M)) == 10
assert not (HERE / 'ten_example_formal_review_stdout.txt').read_bytes()
assert not (HERE / 'ten_example_formal_review_stderr.txt').read_bytes()
assert not subprocess.run(['git', 'diff', 'ffdaf4b', '--name-only', '--', 'paper'],
                          cwd=ROOT, text=True, capture_output=True, check=True).stdout
paths = [*sources, LEAN / 'TruncGaussProof.lean', LEAN / 'AuditAxioms.lean',
         LEAN / 'lean-toolchain', LEAN / 'lakefile.toml', LEAN / 'lake-manifest.json']
paths += [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
          and p.name not in ['validation_receipt.json', 'self_review_receipt.json']]
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'exact_Gaussian_density_to_probability_law_no_atom_and_positive_boundary_interval',
    'new_exported_theorems': sorted(new), 'total_exported_theorems_axiom_checked': 65,
    'allowed_transitive_axioms': sorted(allowed), 'python_tests_passed': 119,
    'formal_review_examples': 10,
    'managed_phases': [{'session': 87890, 'phase': 'first_build_membership_conversion_failure', 'exit_code': 1},
                       {'session': 45315, 'phase': 'four_lemma_build', 'exit_code': 0},
                       {'session': 50793, 'phase': 'positive_interval_build', 'exit_code': 0},
                       {'session': 58014, 'phase': 'nine_example_review', 'exit_code': 0},
                       {'session': 70788, 'phase': 'expanded_review_sqrt_rewrite_mismatch', 'exit_code': 1},
                       {'session': 84852, 'phase': 'ten_example_review', 'exit_code': 0},
                       {'session': 76253, 'phase': 'make_math_check', 'exit_code': 0}],
    'normalization_bridge': 'law is Lebesgue measure with the integral-derived nonnegative density; total mass follows from its actual integral one',
    'sigma_scope': 'positive sigma for probability normalization and interval positivity; no-atom and negative-support identities hold for the constructed measure at all real sigma',
    'zero_sigma_control': 'constructed integral-derived measure is zero and not a probability law; actual zero-variance Gaussian is a Dirac atom',
    'readout_distinction': 'constraint-offset probability of a boundary mode differs from posterior singleton mass at zero; one explicit formal example proves positive mode frequency with zero singleton mass',
    'native_cosmological_Gaussianity_or_convergence_certified': False,
    'uniform_floating_point_density_accuracy_certified': False, 'finite_upper_gate_or_varying_prior_covered': False,
    'paper_modified': False,
    'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted(set(paths))],
}
with (HERE / 'validation_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('119 Python tests; 65 exported theorems; 10 formal review controls; only allowed standard axioms.')
