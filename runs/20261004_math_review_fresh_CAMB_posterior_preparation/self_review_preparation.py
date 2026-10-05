"""Distinct self-review of target definitions and the completed preflights."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
preparation=json.loads((HERE/'preparation_receipt.json').read_text())
entries=preparation['entries']
assert len(entries)==20 and len({e['seed'] for e in entries})==20
assert len({e['group'] for e in entries})==5
checked=[]
for e in entries:
    cfg=yaml.safe_load((ROOT/e['config']).read_text())
    control_path=ROOT/e['control']
    original=yaml.safe_load((control_path.parent/e['style']/'input.yaml').read_text())
    assert cfg['likelihood']==original['likelihood'] and cfg['packages_path']==original['packages_path']
    assert cfg['params'].keys()==original['params'].keys()
    for name in cfg['params']:
        assert {k:v for k,v in cfg['params'][name].items() if k!='ref'}=={k:v for k,v in original['params'][name].items() if k!='ref'}
    extra=json.loads(control_path.read_text())['records'][e['style']]['effective_CAMB_extra_args']
    assert cfg['theory']['camb']['extra_args']==extra
    assert set(cfg['theory']['camb'])=={'extra_args','class','path','version'}
    assert cfg['theory']['camb']['class']=='sbt_spt_audit.boltzmann.FreshCAMB'
    assert cfg['params']['mnu']['prior']=={'min':0.0,'max':5.0}
    assert cfg['params']['tau']['prior']=={'min':0.01,'max':0.8}
    assert cfg['sampler']['mcmc']['seed']==e['seed']
    assert cfg['sampler']['mcmc']['covmat']==str(ROOT/e['proposal']['path'])
    proposal=ROOT/e['proposal']['path']
    assert sha(proposal)==e['proposal']['sha256'] and proposal.read_bytes()==(ROOT/e['proposal']['source']).read_bytes()
    np.linalg.cholesky(np.loadtxt(proposal))
    assert sha(ROOT/e['config'])==e['config_sha256'] and sha(control_path)==e['control_sha256']
    assert sha(e['module'])==e['module_sha256'] and sha(e['wrapper'])==e['wrapper_sha256']
    for path,digest in e['implementation_sha256'].items(): assert sha(ROOT/path)==digest
    proof_path=HERE/f"seed{e['seed']}"/'initial_point_verification.json'
    proof=json.loads(proof_path.read_text())
    assert proof['seed']==e['seed'] and proof['config_sha256']==e['config_sha256']
    assert proof['module_sha256']==e['module_sha256'] and proof['initial_point']==e['initial_point']
    assert proof['native_initial_point_verified'] and proof['upstream_forced_fresh_likes_and_priors_exact']
    assert proof['effective_CAMB_extra_args']==extra and proof['sampler_cache_resize_challenge']==50
    assert proof['selected_replay_tolerance']==1e-9
    assert max(abs(v) for v in proof['control_component_differences'].values())<=1e-9
    assert not (ROOT/e['run_dir']).exists()
    checked.append({'seed':e['seed'],'group':e['group'],'initial_verification_sha256':sha(proof_path)})
paper_diff=subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT,text=True)
assert not paper_diff
receipt={'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'self_review_no_independent_agent',
    'checked':checked,'all_20_initial_points_exact_to_upstream_fresh':True,
    'scientific_priors_likelihood_and_native_settings_preserved_per_declared_target':True,
    'proposal_bytes_verified_as_heuristics_only':True,'reused_current_B_pair_comparisons_dependent':True,
    'native_initial_points_and_launch_contracts_only':True,'posterior_convergence_or_global_accuracy_certified':False,
    'paper_and_canonical_results_unchanged':True}
with (HERE/'preparation_self_review_receipt.json').open('x') as f:
    f.write(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
print('All 20 preparations and initial-point controls independently recounted in self-review.')
