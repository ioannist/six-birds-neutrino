"""Verify medium-target replay and the same-coordinate finer mass-response test."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
selection = json.loads((HERE/'selection_receipt.json').read_text())
launch = json.loads((HERE/'launch_receipt.json').read_text())
for item in launch['files'] + selection['sources']:
    assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
parent_path = ROOT/selection['parent_verified_comparison']
assert hashlib.sha256(parent_path.read_bytes()).hexdigest()==selection['parent_verified_comparison_sha256']
parent = parent_path.parent
assert hashlib.sha256(Path(selection['native_module_path']).read_bytes()).hexdigest()==selection['native_module_sha256']
comparisons, closures = {}, []
for job in launch['jobs']:
    lens = job['lens']
    folder = HERE/lens
    assert not (folder/'stderr.txt').read_bytes()
    runtime = json.loads((folder/'evaluation/runtime_state.json').read_text())
    assert runtime['pid']==job['pid'] and not Path('/proc',str(job['pid'])).exists()
    assert runtime['status']=='complete_sampled_sensitivity_control_not_error_certificate'
    data = json.loads((folder/'evaluation/metrics.json').read_text())
    old = json.loads((parent/lens/'evaluation/metrics.json').read_text())
    configs = [yaml.safe_load((folder/'evaluation'/name).read_text()) for name in ['baseline.yaml','selected_reference_settings.yaml']]
    base,refined = configs
    original = yaml.safe_load((parent/lens/'evaluation/selected_reference_settings.yaml').read_text())
    assert base==original
    allowed = set(data['precision_settings_source']['settings'])
    assert len(allowed)==7
    clean = lambda cfg:{**cfg,'theory':{'classy':{**cfg['theory']['classy'],
        'extra_args':{k:v for k,v in cfg['theory']['classy']['extra_args'].items() if k not in allowed}}}}
    assert clean(base)==clean(refined)
    a,b=[cfg['theory']['classy']['extra_args'] for cfg in configs]
    changed={k for k in allowed if a.get(k)!=b.get(k)}
    assert len(changed)==6 and 'tol_ncdm_bg' not in changed
    points = json.loads((folder/'points.json').read_text())
    assert set(points)=={'quad_q50','quad_q50_mass_plus'}
    coverage = {'tt':3200 if lens=='A' else 4095,'ee':3200 if lens=='A' else 4095}
    for variant in ['baseline','selected_reference_settings']:
        assert set(data['records'][variant])==set(points)
        for label,record in data['records'][variant].items():
            assert record['point']==points[label]==old['records']['selected_reference_settings'][label]['point']
            assert record['spectrum_ell_max']==coverage
            assert len(record['native_chi2'])==6 and np.all(np.isfinite(list(record['native_chi2'].values())))
    for label in points:
        new_values=data['records']['baseline'][label]['native_chi2']
        old_values=old['records']['selected_reference_settings'][label]['native_chi2']
        assert set(new_values)==set(old_values)
        errors={k:new_values[k]-old_values[k] for k in new_values}
        assert max(map(abs,errors.values()))==0.
        closures.append({'lens':lens,'label':label,'native_components':6,'maximum_replay_absolute_discrepancy':0.,
                         'prior_or_posterior_recomputed':False})
    response={}
    for variant in ['baseline','selected_reference_settings']:
        a,b=[data['records'][variant][label]['native_chi2'] for label in ['quad_q50','quad_q50_mass_plus']]
        delta={k:b[k]-a[k] for k in a}
        assert data['within_setting_point_changes'][variant]['quad_q50_mass_plus_minus_quad_q50']==delta
        response[variant]=sum(delta.values())
    offsets={label:sum(record['native_chi2_change'].values()) for label,record in data['refined_minus_baseline'].items()}
    comparisons[lens]={'fine_minus_medium_native_chi2':offsets,
                       'local_mass_plus_0_01_native_chi2_changes':response,
                       'mass_response_discrepancy':response['selected_reference_settings']-response['baseline'],
                       'changed_numerical_controls':sorted(changed),'likelihood_requested_spectrum_coverage':coverage}
paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
       and p.name not in ['completion_verification.json','self_review_receipt.json']]
result={'utc':datetime.now(timezone.utc).isoformat(),'scope':'four_same-coordinate_mass_response_evaluations_under_medium_and_fine_targets',
        'managed_exits':[{'lens':j['lens'],'session':j['exec_session'],'exit_code':0} for j in launch['jobs']],
        'medium_target_closures':closures,'comparisons':comparisons,
        'uniform_numerical_accuracy_certified':False,'posterior_convergence_certified':False,
        'prior_or_posterior_recomputed':False,'paper_modified':False,
        'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]}
(HERE/'completion_verification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(comparisons,indent=2,allow_nan=False))
