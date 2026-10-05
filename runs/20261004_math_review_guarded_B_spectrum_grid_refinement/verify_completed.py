"""Check identical-coordinate spectrum-grid refinement with fixed dynamics."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
selection=json.loads((HERE/'selection_receipt.json').read_text())
launch=json.loads((HERE/'launch_receipt.json').read_text())
for file in launch['files']+selection['sources']:
    assert hashlib.sha256((ROOT/file['path']).read_bytes()).hexdigest()==file['sha256']
parent_path=ROOT/selection['parent_verification']
assert hashlib.sha256(parent_path.read_bytes()).hexdigest()==selection['parent_verification_sha256']
parent=json.loads(parent_path.read_text())
for file in parent['files']:
    assert hashlib.sha256((ROOT/file['path']).read_bytes()).hexdigest()==file['sha256']
parent_dir=parent_path.parent
base=yaml.safe_load((parent_dir/'grid_only/input.yaml').read_text())
anchor=json.loads((parent_dir/'grid_only/evaluation/metrics.json').read_text())['records']
records={'grid12':anchor}
spectral_changes={}
for job in launch['jobs']:
    variant=job['variant'];folder=HERE/variant
    assert not (folder/'stderr.txt').read_bytes()
    runtime=json.loads((folder/'evaluation/runtime_state.json').read_text())
    assert runtime['pid']==job['pid'] and not Path('/proc',str(job['pid'])).exists()
    assert runtime['status']=='complete_selected_factor_check_not_accuracy_certificate'
    assert runtime['module_sha256']==selection['native_module_sha256']==job['module_sha256']
    assert hashlib.sha256(Path(runtime['module']).read_bytes()).hexdigest()==runtime['module_sha256']
    cfg=yaml.safe_load((folder/'input.yaml').read_text())
    expected=json.loads(json.dumps(base))
    expected['theory']['classy']['extra_args'].update(selection['grid_targets'][variant])
    assert cfg==expected
    data=json.loads((folder/'evaluation/metrics.json').read_text())
    assert data['variant']==variant and set(data['records'])==set(anchor)
    spectral_changes[variant]={}
    for label,record in data['records'].items():
        assert record['point']==anchor[label]['point']
        assert set(record['native_chi2'])==set(anchor[label]['native_chi2']) and len(record['native_chi2'])==6
        assert np.all(np.isfinite(list(record['native_chi2'].values())))
        coverage=record['requested_spectrum_ell_max']
        assert coverage==anchor[label]['requested_spectrum_ell_max']
        assert coverage=={'tt':4095,'te':4095,'ee':4095,'bb':4095,'pp':2500}
        relative={}
        with np.load(folder/'evaluation'/(label+'_spectra.npz')) as new, np.load(
                parent_dir/'grid_only/evaluation'/(label+'_spectra.npz')) as old:
            assert set(new.files)==set(old.files)==set(coverage)
            for spec,n in coverage.items():
                a,b=old[spec],new[spec]
                assert a.shape==b.shape==(n+1,) and np.all(np.isfinite(b))
                use=np.arange(n+1)>=2
                if spec in ['tt','ee','pp']:
                    assert np.all(a[use]>0.)
                    relative[spec]=float(np.max(np.abs((b[use]-a[use])/a[use])))
        spectral_changes[variant][label]=relative
    records[variant]=data['records']
responses,components,offsets={},{},{}
for variant,data in records.items():
    a,b=[data[label]['native_chi2'] for label in ['quad_q50','quad_q50_mass_plus']]
    components[variant]={k:b[k]-a[k] for k in a}
    responses[variant]=sum(components[variant].values())
    offsets[variant]={label:sum(record['native_chi2'][k]-anchor[label]['native_chi2'][k]
                               for k in record['native_chi2']) for label,record in data.items()}
result={'utc':datetime.now(timezone.utc).isoformat(),'scope':'two_fixed_B_mass_coordinates_spectrum_grid_levels12_6_3',
        'managed_exits':[{'variant':j['variant'],'session':j['session'],'exit_code':0} for j in launch['jobs']],
        'native_mass_plus_0_01_responses':responses,'native_component_mass_responses':components,
        'mass_response_changes':{'grid6_minus_grid12':responses['grid6']-responses['grid12'],
                                 'grid3_minus_grid6':responses['grid3']-responses['grid6']},
        'native_chi2_offsets_relative_to_grid12':offsets,
        'maximum_fractional_spectrum_changes_relative_to_grid12':spectral_changes,
        'physical_likelihood_prior_and_dynamics_settings_unchanged':True,
        'grid12_anchor_reused_not_new_evaluation':True,'convergence_rate_or_uniform_error_bound_certified':False,
        'posterior_convergence_certified':False,'paper_modified':False,
        'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
                 and p.name not in ['completion_verification.json','self_review_receipt.json']]}
(HERE/'completion_verification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:result[k] for k in ['native_mass_plus_0_01_responses','mass_response_changes','native_chi2_offsets_relative_to_grid12']},indent=2))
