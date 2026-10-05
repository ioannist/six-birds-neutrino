"""Check target equality, starts, priors and native preparation witnesses."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
r=json.loads((HERE/'preparation_receipt.json').read_text())
CONTROL=ROOT/'runs/20261004_math_review_SPT_archived_solver_version_control'
counts={};max_difference=0
for target in ['A','B']:
    entries=[e for e in r['entries'] if e['lens']==target]
    assert len(entries)==4 and len({tuple(e['initial_point'].values()) for e in entries})==4
    source=yaml.safe_load((CONTROL/target/'original_style/input.yaml').read_text())
    target_configs=[]
    for e in entries:
        path=ROOT/e['config']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==e['config_sha256']
        cfg=yaml.safe_load(path.read_text())
        assert cfg['likelihood']==source['likelihood']
        for name,b in source['params'].items():
            assert {k:v for k,v in b.items() if k!='ref'}=={k:v for k,v in cfg['params'][name].items() if k!='ref'}
        assert cfg['theory']['camb']['extra_args']=={'num_massive_neutrinos':3,'nnu':3.046,'lmax':3200 if target=='A' else 4095}
        assert cfg['sampler']['mcmc']['seed']==e['seed']
        assert cfg['sampler']['mcmc']['oversample_thin'] is False
        assert cfg['notes']['camb_backend']=={'module_sha256':e['module_sha256'],'solver_version':'1.6.5'}
        proof=json.loads((HERE/('seed'+str(e['seed']))/'initial_point_verification.json').read_text())
        assert proof['native_initial_point_verified'] and proof['initial_point']==e['initial_point']
        assert proof['module_sha256']==e['module_sha256']
        discrepancy=max(abs(v) for v in proof['archived_control_component_discrepancies'].values())
        assert discrepancy<=1e-9
        max_difference=max(max_difference,discrepancy)
        target_configs.append({k:cfg[k] for k in ['likelihood','theory']})
    assert all(cfg==target_configs[0] for cfg in target_configs)
    counts[target]=[e['seed'] for e in entries]
for target in ['A','B']:
    assert not (HERE/('preflight_'+target+'_stderr.txt')).read_bytes()
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'four_distinct_initial_points_and_seeds_each':counts,
     'unchanged_sampled_priors_fixed_nuisances_and_internal_likelihood_definitions':True,
     'initial_native_checks':8,'largest_observed_component_replay_difference':max_difference,
     'selected_native_replay_tolerance':1e-9,'bit_identical_reproduction_claimed':False,
     'native_initial_points_from_other_target_are_starting_coordinates_only':True,
     'two_original_sparse_chain_quantile_points_are_not_qualified_old_quantiles':True,
     'configuration_versions_native_hash_and_original_effective_lmax_distinguished':True,
     'current_qualified_chain_histories_pooled':False,'native_global_accuracy_or_original_environment_identity_certified':False,
     'sampling_or_prior_kernel_replaced':False,'paper_modified':False,
     'preflight_sessions':{'A':{'session':2579,'exit_code':0},'B':{'session':23423,'exit_code':0}}}
with (HERE/'preparation_self_review.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Eight finite native starts; identical target definitions within each lens; replay differences <=',max_difference)
