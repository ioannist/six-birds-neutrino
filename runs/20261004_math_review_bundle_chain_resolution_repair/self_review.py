"""Distinct adversarial recount of selection impact and complete validation."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from extract_mnu_limits import _resolve_prefix_from_run_dir
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=json.loads((HERE/'before_receipt.json').read_text())
assert sha(HERE/'before_extract_mnu_limits.py')==before['sha256']
assert '5 failed, 1 passed' in (HERE/'before_tests_stdout.txt').read_text()
assert '101 passed' in (HERE/'targeted_tests_stdout.txt').read_text()
assert not (HERE/'targeted_tests_stderr.txt').read_bytes()
log=(HERE/'math_check_stdout.txt').read_text()
assert '175 passed' in log and 'Build completed successfully' in log
axioms=re.findall(r"'([^']+)' depends on axioms:\s*\[([^\]]*)\]",log)
assert len(axioms)==74 and len({name for name,_ in axioms})==74
assert all(set(a.strip() for a in values.split(','))<={'propext','Classical.choice','Quot.sound'} for _,values in axioms)
assert not (HERE/'math_check_stderr.txt').read_bytes()
impact=json.loads((HERE/'impact_verification.json').read_text())
assert len(impact['records'])==impact['tracked_bundles']==547
unchanged,rebased,refused=0,0,0
for r in impact['records']:
    run=ROOT/r['run']
    if 'after_prefix' in r:
        prefix=_resolve_prefix_from_run_dir(run)
        assert prefix==ROOT/r['after_prefix'] and prefix.is_relative_to(run)
        unchanged+=r['selection_unchanged']
        rebased+=not r.get('before_inside_bundle',True)
    elif 'before_prefix' in r:
        refused+=1
        assert not list(run.rglob('*.1.txt')) and not list(run.rglob('*.2.txt'))
        prefix=ROOT/r['before_prefix']
        # No local chain with the declared prefix, even for single-file output.
        assert not (run/'chains'/f'{prefix.name}.txt').is_file() and not (run/f'{prefix.name}.txt').is_file()
        try:_resolve_prefix_from_run_dir(run)
        except FileNotFoundError:pass
        else:raise AssertionError('Empty bundle unexpectedly resolves')
assert unchanged==impact['unchanged_prefix_count']==441
assert rebased==impact['external_prefixes_rebased_count']==70
assert refused==impact['new_refusals']==27
for r in impact['all_twenty_fresh_first_rows_read_exact_frozen_data']:
    run=ROOT/r['bundle'];prefix=_resolve_prefix_from_run_dir(run)
    assert prefix==ROOT/r['selected_prefix'] and sha(Path(str(prefix)+'.1.txt'))==r['frozen_file_sha256']
    assert r['stored_rows']==1 and r['holding_time']>0
replay=json.loads((HERE/'latest_CLASS_replay_receipt.json').read_text())
assert len(replay['records'])==4
for r in replay['records']:
    assert sha(ROOT/r['original_report'])==r['original_sha256']
    assert sha(ROOT/r['replayed_report'])==r['replayed_sha256']
    assert json.loads((ROOT/r['original_report']).read_text())==json.loads((ROOT/r['replayed_report']).read_text())
runtime=json.loads((HERE/'runtime_observation.json').read_text())
assert runtime['owned_live_samplers']==40 and runtime['fresh_CAMB_SPT_live']==runtime['guarded_CLASS_live']==20
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT,text=True)
with (HERE/'self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'self_review_no_independent_agent',
        'old_failure_reproduced':True,'tracked_bundles_checked':547,'unchanged_prefixes':441,
        'external_outputs_rebased_to_local_chains':70,'new_refusals_without_local_chain_data':27,
        'twenty_first_native_rows_read_from_exact_frozen_data':True,'four_latest_CLASS_reports_exactly_unchanged':True,
        'make_math_check':{'session':76779,'exit_code':0,'Python_tests':175,'Lean_public_axiom_outputs':74},
        'targeted_tests':{'session':28458,'exit_code':0,'passed':101},
        'before_tests':{'session':93196,'exit_code':1,'expected_failed':5,'passed':1},
        'impact_verification':{'session':40549,'exit_code':0},'CLASS_replay':{'session':63645,'exit_code':0},
        'source_sha256':{p:sha(ROOT/p) for p in ['scripts/extract_mnu_limits.py','tests/test_bundle_chain_resolution.py']},
        'native_inference_and_acceptance_gates_changed':False,'paper_and_canonical_unchanged':True,
        'posterior_convergence_or_uniform_solver_accuracy_certified':False},indent=2,allow_nan=False)+'\n')
print('Self-review passes: 547 bundles, 20 frozen native rows, four unchanged CLASS reports, 175 Python tests and 74 Lean outputs.')
