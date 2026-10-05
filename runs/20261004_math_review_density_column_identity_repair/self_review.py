"""Distinct fixture recount and full verification of the density identity repair."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
before = json.loads((HERE / 'before.json').read_text())
after = json.loads((HERE / 'after.json').read_text())
assert hashlib.sha256((HERE / 'before_compare_mnu_posteriors.py').read_bytes()).hexdigest() == before['comparison_source_sha256']
assert hashlib.sha256((ROOT / 'scripts/compare_mnu_posteriors.py').read_bytes()).hexdigest() == after['comparison_source_sha256']
assert before['records']['valid'] == after['records']['valid']
for name in ['duplicate', 'conflicting']:
    lines = [line.split() for line in (HERE / 'fixtures' / (name + '.1.txt')).read_text().splitlines()
             if line.strip() and not line.startswith('#')]
    mass = [float(row[2]) for row in lines]
    other = [float(row[3]) for row in lines]
    peak = before['records'][name]['mode']
    assert len(lines) == 300 and max(mass) < peak
    assert min(other) <= peak <= max(other)
    assert not after['records'][name]['accepted']
impact = json.loads((HERE / 'impact_receipt.json').read_text())
assert impact['valid_bundle_count'] == 37 and not impact['all_smoothed_density_grids_recomputed']
for entry in impact['records']:
    assert entry['mass_validation_accepted'] and entry['GetDist_arguments_unchanged'] and entry['chain_files_unchanged']
    for source in entry['sources']:
        assert hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest() == source['sha256']
output = (HERE / 'math_check_stdout.txt').read_text()
assert '132 passed' in output and 'Build completed successfully' in output
public = set()
for path in (ROOT / 'lean/trunc_gauss_proof/TruncGaussProof').glob('*.lean'):
    public.update(re.findall(r'^theorem (\w+)', path.read_text(), re.M))
assert len(public) == 74
axioms = {n: {a.strip() for a in re.split(r',\s*', values.strip()) if a.strip()}
          for n, values in re.findall(r"'TruncGaussProof\.(\w+)' depends on axioms: \[([^\]]*)\]", output)}
assert set(axioms) == public
assert all(values <= {'propext', 'Classical.choice', 'Quot.sound'} for values in axioms.values())
for name in ['before_stderr.txt', 'after_stderr.txt', 'math_check_stderr.txt']:
    assert not (HERE / name).read_bytes()
assert not subprocess.check_output(['git', 'diff', 'ffdaf4b', '--name-only', '--',
    'paper', 'docs/findings/canonical_results.json'], cwd=ROOT)
assert json.loads((HERE / 'runtime_observation.json').read_text())['owned_live_samplers'] == 28
out = {'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_no_independent_agent',
       'scope': 'comparison_KDE_coordinate_identity_refusal_and_valid_input_compatibility',
       'reproduced_wrong_coordinate_readouts': 2, 'unchanged_valid_density_grid': True,
       'valid_bundle_validation_and_downstream_argument_checks': 37,
       'all_37_smoothed_density_grids_recomputed': False,
       'Python_tests_passed': 132, 'Lean_exported_theorems_axiom_checked': 74,
       'managed_phases': [{'session': 51183, 'phase': 'before_actual_GetDist_reproduction', 'exit_code': 0},
                          {'session': 85806, 'phase': 'after_actual_GetDist_control', 'exit_code': 0},
                          {'session': 91713, 'phase': 'combined_make_math_check', 'exit_code': 0}],
       'posterior_or_native_accuracy_claim_strength_changed': False,
       'Lean_sources_changed': False, 'paper_modified': False, 'owned_live_samplers_verified': 28,
       'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
                 and not any(part.startswith('cache_') for part in p.parts)
                 and p.name != 'validation_receipt.json']
                + [{'path': str(p), 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
                   for p in ['scripts/compare_mnu_posteriors.py', 'tests/test_math_repairs.py',
                             'scripts/extract_mnu_limits.py']]}
with (HERE / 'validation_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2) + '\n')
print('Two wrong-column readouts refused; valid grid unchanged; 37 compatibility checks; 132 tests and 74 axiom outputs verified.')
