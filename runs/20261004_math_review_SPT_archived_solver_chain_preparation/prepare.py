"""Prepare four fresh starts per archived-version SPT numerical target."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONTROL=ROOT/'runs/20261004_math_review_SPT_archived_solver_version_control'
install=json.loads((CONTROL/'isolated_install_receipt.json').read_text())
comparison=json.loads((CONTROL/'comparison_receipt.json').read_text())
selection=json.loads((ROOT/'runs/20261004_math_review_SPT_effective_CAMB_settings/selection_receipt.json').read_text())
hash_file=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries=[]
labels=['original_median','original_p95','restoration_median','restoration_p95']
for target,start in [('A',1601),('B',1605)]:
    base=yaml.safe_load((CONTROL/target/'original_style/input.yaml').read_text())
    evaluated=json.loads((CONTROL/target/'evaluation_receipt.json').read_text())
    for seed,label in zip(range(start,start+4),labels):
        point=selection['records'][target]['points'][label]
        native=evaluated['records']['original_style']['evaluations'][label]
        assert native['point']==point
        folder=HERE/('seed'+str(seed));folder.mkdir()
        cfg=deepcopy(base)
        cfg.pop('debug',None)
        cfg['run_name']=f'archived_CAMB_{target}_seed{seed}'
        cfg['theory']['camb']['extra_args']['lmax']=3200 if target=='A' else 4095
        cfg['theory']['camb']['path']='global'
        cfg['theory']['camb']['version']='1.6.5'
        for name,value in point.items():
            cfg['params'][name]['ref']=value
            prior=cfg['params'][name]['prior']
            assert prior['min'] <= value <= prior['max']
        cfg['sampler']={'mcmc':{'seed':seed,'max_samples':20000,'learn_proposal':True,
            'Rminus1_stop':.01,'Rminus1_cl_stop':.05,'Rminus1_cl_level':.95,
            'oversample_power':0,'oversample_thin':False}}
        cfg['notes']={'math_review':'Fresh archived-version solver target; current Python/adapter/data. Native selected-row reproduction does not certify historical identity or posterior precision.',
                      'camb_backend':{'module_sha256':install['CAMB_native_module_sha256'],'solver_version':'1.6.5'},
                      'source_initial_point':label,'source_control':str((CONTROL/target/'evaluation_receipt.json').relative_to(ROOT)),
                      'cosmological_mass_prior':'uniform[0,5] eV, unchanged',
                      'native_Cl_requirement':3200 if target=='A' else 4095}
        path=folder/'input.yaml';path.write_text(yaml.safe_dump(cfg,sort_keys=False))
        outdir=ROOT/f'runs/20261004_math_review_archived_CAMB_chain_{target}_seed{seed}'
        assert not outdir.exists()
        entry={'seed':seed,'lens':target,'kind':'spt_desi_archived_solver','config':str(path.relative_to(ROOT)),
            'config_sha256':hash_file(path),'run_dir':str(outdir.relative_to(ROOT)),
            'initial_point':point,'initial_point_label':label,'source_native_control_sha256':hash_file(CONTROL/target/'evaluation_receipt.json'),
            'module':install['CAMB_native_module'],'module_sha256':install['CAMB_native_module_sha256'],
            'solver_version':'1.6.5','Cobaya_version':'3.6.1',
            'wrapper':evaluated['runtime']['Cobaya_CAMB_wrapper'],'wrapper_sha256':evaluated['runtime']['Cobaya_CAMB_wrapper_sha256'],
            'launch_receipt':str((folder/'launch_receipt.json').relative_to(ROOT))}
        (folder/'preparation_receipt.json').write_text(json.dumps(entry,indent=2,allow_nan=False)+'\n')
        entries.append(entry)
assert len(entries)==8 and len({e['seed'] for e in entries})==8
out={'utc':datetime.now(timezone.utc).isoformat(),'entries':entries,'same_scientific_priors_and_likelihood_definitions_as_original':True,
     'original_effective_lmax_explicit_A3200_B4095':True,'fresh_rng_and_output_required':True,
     'original_environment_or_historical_data_identity_certified':False,
     'qualified_current_solver_histories_pooled':False,'posterior_convergence_certified':False,
     'source_receipts':[{'path':str(p.relative_to(ROOT)),'sha256':hash_file(p)} for p in
        [CONTROL/'isolated_install_receipt.json',CONTROL/'comparison_receipt.json',CONTROL/'self_review_receipt.json']]}
with (HERE/'preparation_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Prepared eight fresh archived-version chains; native initial verification required before launch.')
