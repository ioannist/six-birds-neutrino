"""Witness the previous CAMB pooling bypass and check actual valid cohorts."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import diagnose_cobaya_chains as current
spec=importlib.util.spec_from_file_location('previous_diagnose',HERE/'before_diagnose.py')
previous=importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
old_path=ROOT/'runs/20261004_math_review_SPT_archived_solver_version_control/A/evaluation_receipt.json'
new_path=ROOT/'runs/20261004_math_review_SPT_effective_CAMB_settings/A/evaluation_receipt.json'
old_runtime=json.loads(old_path.read_text())['runtime']
new_runtime=json.loads(new_path.read_text())['runtime']
records=[]
for case in ['different_native_builds','different_recorded_versions','matching_recorded_targets']:
    runs,configs=[],[]
    for i,runtime in enumerate([old_runtime,old_runtime if case=='matching_recorded_targets' else new_runtime]):
        run=HERE/'fixtures'/case/str(i)
        run.mkdir(parents=True)
        prefix=run/'sample'
        cfg={'theory':{'camb':{}},'output':str(prefix)}
        (run/'resolved.yaml').write_text(yaml.safe_dump(cfg))
        if case!='different_recorded_versions':
            (run/'solver_backend.json').write_text(json.dumps({'module_sha256':runtime['CAMB_module_sha256'],
                'solver_version':runtime['versions']['camb']},indent=2)+'\n')
        Path(str(prefix)+'.updated.yaml').write_text(yaml.safe_dump({'theory':{'camb':{'version':runtime['versions']['camb']}}}))
        runs.append(run);configs.append(cfg)
    before=previous._native_backend_provenance(runs,configs)
    assert before==([], 'configuration_only_native_build_identity_not_recorded')
    try:
        after=current._native_backend_provenance(runs,configs)
    except ValueError as error:
        after={'rejected':True,'error':str(error)}
    if case=='matching_recorded_targets':
        assert not isinstance(after,dict) and len(after[0])==2
    else:
        assert after['rejected']
    records.append({'case':case,'scope':'provenance_only_fixtures_not_inference_chains',
        'before_guard_accepted_incompatible_evidence':case!='matching_recorded_targets',
        'before':before,'after':after})

state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
cohorts={}
for target in ['A','B']:
    parent=ROOT/state['latest_SPT_'+target+'_diagnostic_bundle']
    cohorts['SPT_'+target]=sorted(parent.glob('chain_'+target+'_seed*'))
for key,parent in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items():
    cohorts[key]=sorted((ROOT/parent/key).glob('seed*'))
cohorts['grid12_B_initial_rows']=[ROOT/f'runs/20261004_math_review_guarded_grid12_trial_B_seed{s}/first_saved_rows' for s in [1501,1502,1503,1504]]
impact={}
for group,runs in cohorts.items():
    cfgs=[yaml.safe_load((run/'resolved.yaml').read_text()) for run in runs]
    result=current._native_backend_provenance(runs,cfgs)
    impact[group]={'runs':[str(run.relative_to(ROOT)) for run in runs],
                   'accepted':True,'guard_result':result,
                   'resolved_sources':[{'path':str((run/'resolved.yaml').relative_to(ROOT)),
                                        'sha256':hashlib.sha256((run/'resolved.yaml').read_bytes()).hexdigest()} for run in runs]}
assert sum(len(v['runs']) for v in impact.values())==32
# Live saved updated metadata give same version within each existing SPT target.
live_versions={}
for target in ['A','B']:
    entries=[e for e in state['restoration_chains'] if e['kind']=='spt_desi' and e['lens']==target]
    runs=[ROOT/e['run_dir'] for e in entries]
    cfgs=[yaml.safe_load((run/'resolved.yaml').read_text()) for run in runs]
    result=current._native_backend_provenance(runs,cfgs)
    assert len(result[0])==6 and {x['solver_version'] for x in result[0]}=={'2.0.4'}
    live_versions[target]=result
out={'utc':datetime.now(timezone.utc).isoformat(),'negative_and_positive_controls':records,
     'valid_cohort_impact':impact,'valid_frozen_or_first_row_bundle_count':32,
     'existing_SPT_version_evidence':live_versions,'rank_algorithms_or_empirical_gates_modified':False,
     'earlier_native_sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [old_path,new_path]],
     'legacy_native_identity_assumption_retained_and_explicit':True}
with (HERE/'probe_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Old guard bypass witnessed; mixed CAMB builds/versions rejected; 32 valid bundles and 12 SPT version records accepted.')
