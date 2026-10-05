"""Verify a complete two-factor native likelihood comparison at fixed points."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
selection=json.loads((HERE/'selection_receipt.json').read_text())
launch=json.loads((HERE/'launch_receipt.json').read_text())
for item in launch['files']:
    assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
parent_path=ROOT/selection['parent_verification']
assert hashlib.sha256(parent_path.read_bytes()).hexdigest()==selection['parent_verification_sha256']
parent_receipt=json.loads(parent_path.read_text())
for file in parent_receipt['files']:
    assert hashlib.sha256((ROOT/file['path']).read_bytes()).hexdigest()==file['sha256']
parent=parent_path.parent
old=json.loads((parent/'B/evaluation/metrics.json').read_text())
base=yaml.safe_load((parent/'B/evaluation/baseline.yaml').read_text())
fine=yaml.safe_load((parent/'B/evaluation/selected_reference_settings.yaml').read_text())
records={'medium':old['records']['baseline'],'fine':old['records']['selected_reference_settings']}
for job in launch['jobs']:
    variant=job['variant'];folder=HERE/variant
    assert not (folder/'stderr.txt').read_bytes()
    runtime=json.loads((folder/'evaluation/runtime_state.json').read_text())
    assert runtime['pid']==job['pid'] and not Path('/proc',str(job['pid'])).exists()
    assert runtime['status']=='complete_selected_factor_check_not_accuracy_certificate'
    assert runtime['module_sha256']==job['module_sha256']==selection['native_module_sha256']
    assert hashlib.sha256(Path(runtime['module']).read_bytes()).hexdigest()==runtime['module_sha256']
    cfg=yaml.safe_load((folder/'input.yaml').read_text())
    expected=json.loads(json.dumps(base))
    for name in selection['changed_controls'][variant]:
        expected['theory']['classy']['extra_args'][name]=fine['theory']['classy']['extra_args'][name]
    assert cfg==expected
    data=json.loads((folder/'evaluation/metrics.json').read_text())
    assert data['variant']==variant and not data['posterior_accuracy_certified']
    assert set(data['records'])==set(records['medium'])
    for label,record in data['records'].items():
        assert record['point']==records['medium'][label]['point']==records['fine'][label]['point']
        assert set(record['native_chi2'])==set(records['medium'][label]['native_chi2'])
        assert len(record['native_chi2'])==6 and np.all(np.isfinite(list(record['native_chi2'].values())))
        coverage=record['requested_spectrum_ell_max']
        assert coverage=={'tt':4095,'te':4095,'ee':4095,'bb':4095,'pp':2500}
        with np.load(folder/'evaluation'/(label+'_spectra.npz')) as spectra:
            assert set(spectra.files)==set(coverage)
            assert all(spectra[k].shape==(n+1,) and np.all(np.isfinite(spectra[k])) for k,n in coverage.items())
    records[variant]=data['records']
responses,components={},{}
for variant,data in records.items():
    a,b=[data[name]['native_chi2'] for name in ['quad_q50','quad_q50_mass_plus']]
    components[variant]={k:b[k]-a[k] for k in a}
    responses[variant]=sum(components[variant].values())
interaction=responses['fine']-responses['grid_only']-responses['dynamics_only']+responses['medium']
result={'utc':datetime.now(timezone.utc).isoformat(),'scope':'selected_B_two_factor_precision_response_comparison',
        'managed_exits':[{'variant':j['variant'],'session':j['session'],'exit_code':0} for j in launch['jobs']],
        'native_mass_plus_0_01_responses':responses,'native_component_mass_responses':components,
        'factor_effects_relative_to_medium':{k:responses[k]-responses['medium'] for k in ['grid_only','dynamics_only','fine']},
        'nonadditive_factor_interaction':interaction,'fine_minus_grid_only_mass_response':responses['fine']-responses['grid_only'],
        'reused_medium_and_fine_anchors_not_new_evaluations':True,'physical_models_priors_and_likelihoods_unchanged':True,
        'uniform_accuracy_or_posterior_convergence_certified':False,'paper_modified':False,
        'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
                 and p.name not in ['completion_verification.json','self_review_receipt.json']]}
(HERE/'completion_verification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:result[k] for k in ['native_mass_plus_0_01_responses','factor_effects_relative_to_medium',
                                     'nonadditive_factor_interaction','fine_minus_grid_only_mass_response']},indent=2))
