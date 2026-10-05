"""Review terminal identities, preserved bundles, and unchanged validated source."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
retirement=json.loads((HERE/'old_policy_retirement_receipt.json').read_text())
handles={r['session']:r for r in json.loads((HERE/'terminal_handle_observations.json').read_text())}
assert len(retirement['records'])==16
assert sum(r['signal_requested_by_agent'] for r in retirement['records'])==10
checked=[]
for r in retirement['records']:
    assert not Path('/proc',str(r['pid'])).exists() and r['scientific_process_absent']
    assert not r['successful_completion'] and not r['every_old_chain_individually_proven_incorrect']
    if r['signal_requested_by_agent']:
        h=handles[r['managed_session']]
        assert h['status']=='fulfilled' and h['result']['exit_code']==143
        code=143
    else:
        assert r['terminal_cause']=='unknown' and r['managed_handle_status']=='unavailable'
        code=None
    for file in r['files']:
        assert sha(ROOT/file['source'])==sha(ROOT/file['archive'])==file['sha256']
        assert (ROOT/file['archive']).stat().st_size==file['bytes']
    checked.append({'seed':r['seed'],'preserved_files':len(r['files']),'verified_exit_code':code,
                    'unknown_stop_before_retirement':not r['signal_requested_by_agent']})
prior=json.loads((ROOT/'runs/20261004_math_review_CAMB_fresh_transfer_repair/self_review_receipt.json').read_text())
for p,digest in prior['source_sha256'].items():assert sha(ROOT/p)==digest
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT,text=True)
runtime=json.loads((HERE/'final_runtime_verification.json').read_text())
assert runtime['owned_live_samplers']==40 and runtime['fresh_CAMB_SPT_live']==20 and runtime['guarded_CLASS_live']==20
assert runtime['all_16_old_policy_processes_absent']
with (HERE/'retirement_self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'self_review_no_independent_agent',
        'checked':checked,'all_static_old_bundles_match_sources':True,'ten_managed_SIGTERM_exits_verified_143':True,
        'six_other_terminal_causes_unknown':True,'validated_production_sources_unchanged_since_168_python_and_74_Lean_checks':True,
        'runtime_verification_sha256':sha(HERE/'final_runtime_verification.json'),'posterior_replacement_certified':False,
        'paper_and_canonical_unchanged':True},indent=2,allow_nan=False)+'\n')
print('Retirement self-review passes: ten exits 143, six unknown stops, all bundles preserved, source and paper unchanged.')
