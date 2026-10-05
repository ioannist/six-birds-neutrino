"""Retire superseded cache-policy samplers after replacement native gates pass."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
proof=json.loads((HERE/'first_rows_self_review_receipt.json').read_text())
assert proof['first_native_rows_verified']==20 and proof['all_finite_verification_workers_absent']
state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
older=[e for e in state['restoration_chains'] if e['kind']=='spt_desi' and e['seed']<400]+state['archived_solver_SPT_posterior_chains']
observed={r['seed']:r for r in json.loads((HERE/'runtime_after_activation_old_cohorts.json').read_text())['records']}
assert len(older)==16
fresh=json.loads((HERE/'activation_verification.json').read_text())['records']
# Replacement identities must still be live at the time of retirement.
for e in fresh:
    proc=Path('/proc',str(e['pid']));stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
    assert stat[0]!='Z' and int(stat[19])==e['process_start_ticks']
    assert e['module'] in (proc/'maps').read_text()
records=[]
for e in older:
    seed=e['seed'];run=ROOT/e['run_dir'];proc=Path('/proc',str(e['pid']))
    resolved=yaml.safe_load((run/'resolved.yaml').read_text())
    assert resolved['theory']['camb'].get('class')!='sbt_spt_audit.boltzmann.FreshCAMB'
    prior=observed[seed]
    absent=prior['status']=='unexpected_process_absent_no_completion_summary'
    record={'seed':seed,'pid':e['pid'],'run_dir':e['run_dir'],'prior_observer_status':prior['status'],
        'managed_session':e.get('session',e.get('exec_session')),'signal_requested_by_agent':False,
        'every_old_chain_individually_proven_incorrect':False,'successful_completion':False,'terminal_exit_code':None}
    if absent:
        assert not proc.exists()
        record.update({'status':'unexpected_process_absent_unknown_cause_partial_bundle_preserved',
                       'terminal_cause':'unknown','managed_handle_status':'unavailable'})
    else:
        stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
        assert stat[0]!='Z' and int(stat[19])==prior['process_start_ticks']
        command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert command==prior['command']
        if prior['mapped_native_module'] is not None:
            assert prior['mapped_native_module'] in (proc/'maps').read_text()
        else:
            assert '/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/camb/camblib.so' in (proc/'maps').read_text()
        record.update({'status':'agent_requested_SIGTERM_superseded_native_transfer_cache_policy',
            'process_start_ticks':prior['process_start_ticks'],'command':command,'signal_requested_by_agent':True,
            'signal_request_utc':datetime.now(timezone.utc).isoformat(),
            'reason':'replacement cohorts pass native first-row replay; old cache policy has selected native counterexamples on both versions; no timeout-based retirement'})
        # Narrow the race between identity verification and signal delivery.
        assert int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])==prior['process_start_ticks']
        os.kill(e['pid'],signal.SIGTERM)
    records.append(record)

deadline=time.monotonic()+120
while any(Path('/proc',str(r['pid'])).exists() for r in records):
    assert time.monotonic()<deadline,'Some signalled process remains; inspect it without escalating automatically.'
    time.sleep(1)
for record in records:
    run=ROOT/record['run_dir'];archive=HERE/'retired_old_policy'/f"seed{record['seed']}";archive.mkdir(parents=True)
    files=[]
    for source in sorted(run.rglob('*')):
        if not source.is_file():continue
        rel=source.relative_to(run);destination=archive/rel;destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as f:f.write(source.read_bytes())
        assert sha(source)==sha(destination)
        files.append({'source':str(source.relative_to(ROOT)),'archive':str(destination.relative_to(ROOT)),
                      'sha256':sha(destination),'bytes':destination.stat().st_size})
    assert files and not Path('/proc',str(record['pid'])).exists()
    record.update({'scientific_process_absent':True,'frozen_bundle':str(archive.relative_to(ROOT)),'files':files})
with (HERE/'old_policy_retirement_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,
        'agent_requested_SIGTERM_count':10,'previously_absent_unknown_cause_count':6,'all_16_outputs_preserved':True,
        'replacement_first_row_verification_sha256':sha(HERE/'first_rows_self_review_receipt.json'),
        'histories_pooled':False,'posterior_bound_replacement_certified':False,'paper_modified':False},indent=2,allow_nan=False)+'\n')
print('Ten superseded samplers stopped; all sixteen old-policy bundles preserved, including six prior unexplained stops.')
