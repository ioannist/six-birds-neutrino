"""Distinct self-review of the native launch guard and completed validation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
text=(HERE/'math_check_stdout.txt').read_text()
assert '158 passed' in text and 'Build completed successfully' in text
axioms=re.findall(r"'([^']+)' depends on axioms: \[([^]]*)\]",text,re.S)
assert len(axioms)==len({name for name,_ in axioms})==74
for name,found in axioms:
    assert {x.strip() for x in found.split(',') if x.strip()} <= {'propext','Classical.choice','Quot.sound'}
assert not (HERE/'math_check_stderr.txt').read_bytes()
old=json.loads((HERE/'native_1.6.5_receipt.json').read_text())
current=json.loads((HERE/'native_2.0.4_receipt.json').read_text())
assert [r['accepted'] for r in old['records']]==[True,True]
assert [r['accepted'] for r in current['records']]==[False,True]
assert old['native_sha256'] != current['native_sha256']
implementation=ROOT/'scripts/run_cobaya.py'
assert old['implementation_sha256']==current['implementation_sha256']==sha(implementation)
protected=subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT,text=True)
assert not protected.strip()
before=(HERE/'before_run_cobaya.py').read_text()
after=implementation.read_text()
start=before.index('def _validate_classy_backend(')
end=before.index('\ndef _write_summary(',start)
assert before[start:end].strip()==after[after.index('def _validate_classy_backend('):after.index('\ndef _validate_native_backend(')].strip()
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'make_math_check_session':35519,'make_math_check_exit_code':0,
     'python_tests':158,'public_Lean_exports':74,'Lean_build_passed':True,
     'axioms':{name:found.split(',') for name,found in axioms},
     'actual_archived_native_accepted_current_native_rejected_for_archived_contract':True,
     'both_actual_matching_native_contracts_accepted':True,
     'preexisting_CLASS_guard_function_unchanged':True,
     'new_tests_cover_rejection_before_output_creation':10,
     'paper_and_canonical_unchanged_since_pre_review':True,
     'native_accuracy_and_cache_correctness_proved_by_this_guard':False,
     'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [implementation,ROOT/'tests/test_native_backend_launch.py',HERE/'native_probe.py',HERE/'math_check_stdout.txt',HERE/'math_check_stderr.txt',HERE/'native_1.6.5_receipt.json',HERE/'native_2.0.4_receipt.json']}}
with (HERE/'self_review.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2)+'\n')
print('158 Python tests, Lean build/74 exports, native positive/negative controls, CLASS guard and protected artifacts checked.')
