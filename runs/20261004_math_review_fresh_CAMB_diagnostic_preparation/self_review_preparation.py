"""Review prepared contracts and actual no-snapshot insufficient-history controls."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract=json.loads((HERE/'assessment_contract.json').read_text())
assert len(contract['groups'])==5 and sum(len(es) for es in contract['groups'].values())==20
assert contract['first_minimum_retained_represented_steps']==1000
assert contract['native_replay_atol']==1e-9 and contract['native_replay_rtol']==0
assert contract['native_rows_per_family']==3 and contract['burnin_fraction_of_stored_rows']==.2
assert contract['absolute_mass_quantile_MCSE_limit']==.001 and contract['relative_other_parameter_MCSE_limit']==.05
assert not contract['targets_pooled'] and not contract['reused_B_pair_comparisons_independent']
for p,digest in contract['diagnostic_source_sha256'].items():assert sha(ROOT/p)==digest
review=[]
for group,entries in contract['groups'].items():
    assert len(entries)==len({e['seed'] for e in entries})==4
    assert len({(e['module_sha256'],e['solver_version'],e['wrapper_sha256']) for e in entries})==1
    configurations=[yaml.safe_load((ROOT/e['config']).read_text()) for e in entries]
    first=configurations[0]
    for cfg in configurations:
        assert cfg['theory']==first['theory'] and cfg['likelihood']==first['likelihood']
        assert cfg['theory']['camb']['class']=='sbt_spt_audit.boltzmann.FreshCAMB'
        clean=lambda c:{n:{k:v for k,v in b.items() if k!='ref'} for n,b in c['params'].items()}
        assert clean(cfg)==clean(first)
    result=json.loads((HERE/f'final_growth_{group}_stdout.txt').read_text())
    assert result['group']==group and result['threshold']==1000 and not result['snapshot_written']
    assert result['minimum_retained_represented_steps']<1000
    assert not (HERE/f'final_growth_{group}_stderr.txt').read_bytes()
    assert not (ROOT/f'runs/20261004_math_review_fresh_CAMB_first_{group}_diagnostics').exists()
    for e in entries:
        assert sha(ROOT/e['config'])==e['config_sha256'] and e['native_first_saved_row_verified']
        assert json.loads((ROOT/e['first_saved_row_receipt']).read_text())['native_row_verified']
    review.append({'group':group,'observed_minimum_history':result['minimum_retained_represented_steps'],
        'insufficient_history_exit_code':3,'assessment_snapshot_created':False})
sources=[HERE/n for n in ['prepare_snapshot.py','verify_native_rows.py','run_diagnostic.py','verify_snapshot.py']]
for source in sources:compile(source.read_text(),str(source),'exec')
with (HERE/'preparation_self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'self_review_no_independent_agent',
        'groups_checked':review,'contract_sha256':sha(HERE/'assessment_contract.json'),
        'workflow_source_sha256':{p.name:sha(p) for p in sources},
        'syntax_and_insufficient_history_branches_verified':True,
        'first_full_snapshot_native_and_diagnostic_workflow_exercised':False,
        'first_assessments_remain_pending':True,'posterior_convergence_certified':False},indent=2,allow_nan=False)+'\n')
print('Five target contracts and no-write growth controls pass; full snapshot/native/diagnostic execution remains pending.')
