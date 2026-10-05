"""Verify selected target closures and compare precision-dependent mass changes."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
selection = json.loads((HERE/'selection_receipt.json').read_text())
launch = json.loads((HERE/'launch_receipt.json').read_text())
for item in launch['files'] + selection['files']:
    path = item.get('snapshot',item.get('path'))
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == item['sha256']
assert hashlib.sha256(Path(selection['native_module_path']).read_bytes()).hexdigest() == selection['native_module_sha256']
comparisons, closures = {}, []
for lens in ['A','B']:
    folder = HERE/lens
    assert not (folder/'stderr.txt').read_bytes()
    runtime = json.loads((folder/'evaluation/runtime_state.json').read_text())
    assert runtime['status']=='complete_sampled_sensitivity_control_not_error_certificate'
    assert not Path('/proc',str(runtime['pid'])).exists()
    data = json.loads((folder/'evaluation/metrics.json').read_text())
    assert data['backend']=='classy' and not data['posterior_accuracy_certified'] and not data['interval_error_certified']
    configs = [yaml.safe_load((folder/'evaluation'/name).read_text()) for name in ['baseline.yaml','selected_reference_settings.yaml']]
    allowed = set(json.loads((folder/'precision_settings.json').read_text())['settings'])
    base,refined = configs
    assert base['theory']['classy']['path']==refined['theory']['classy']['path']=='global'
    assert base['theory']['classy']['extra_args']['l_max_scalars'] == refined['theory']['classy']['extra_args']['l_max_scalars'] == 4095
    clean = lambda cfg: {**cfg,'theory':{'classy':{**cfg['theory']['classy'],
        'extra_args':{k:v for k,v in cfg['theory']['classy']['extra_args'].items() if k not in allowed}}}}
    assert clean(base)==clean(refined)
    points = json.loads((folder/'points.json').read_text())
    assert len(points)==4
    for variant in ['baseline','selected_reference_settings']:
        assert set(data['records'][variant])==set(points)
        for label,record in data['records'][variant].items():
            assert record['point']==points[label] and len(record['native_chi2'])==6
            # The tool records the likelihood's requested TT/EE coverage.
            # A requests 3200; B requests 4095, despite a common solver l_max.
            assert record['spectrum_ell_max']=={'tt':3200 if lens=='A' else 4095,'ee':3200 if lens=='A' else 4095}
            assert np.all(np.isfinite(list(record['native_chi2'].values())))
    for entry in selection['selections']:
        if entry['lens']!=lens: continue
        raw = (ROOT/entry['frozen_chain']).read_bytes()
        header = raw.decode().splitlines()[0].lstrip('#').split()
        rows = np.atleast_2d(np.loadtxt(BytesIO(raw)))
        row = rows[entry['stored_row_zero_based']]
        point = {n:float(row[header.index(n)]) for n in points[entry['label']]}
        assert point==points[entry['label']]
        variant = 'baseline' if entry['point_is_from_target']=='quad' else 'selected_reference_settings'
        fresh = data['records'][variant][entry['label']]['native_chi2']
        assert set(fresh) <= set(entry['native_chi2_recorded'])
        errors = {n:fresh[n]-entry['native_chi2_recorded'][n] for n in fresh}
        assert max(map(abs,errors.values()))==0.
        closures.append({'lens':lens,'label':entry['label'],'variant':variant,
                         'native_likelihood_components_checked':6,'maximum_absolute_discrepancy':0.,
                         'prior_or_posterior_recomputed':False})
    offset = points['quad_q50_mass_plus']
    assert {k:v for k,v in offset.items() if k!='mnu_sample'} == {
        k:v for k,v in points['quad_q50'].items() if k!='mnu_sample'}
    assert np.isclose(offset['mnu_sample']-points['quad_q50']['mnu_sample'],.01,rtol=0,atol=1e-17)
    total_changes = {label:sum(record['native_chi2_change'].values())
                     for label,record in data['refined_minus_baseline'].items()}
    within = {}
    for variant in ['baseline','selected_reference_settings']:
        a,b=[data['records'][variant][name]['native_chi2'] for name in ['quad_q50','quad_q50_mass_plus']]
        expected={n:b[n]-a[n] for n in a}
        assert data['within_setting_point_changes'][variant]['quad_q50_mass_plus_minus_quad_q50']==expected
        within[variant]=sum(expected.values())
    comparisons[lens]={'refined_minus_baseline_total_native_chi2':total_changes,
                       'selected_point_offset_range':max(total_changes.values())-min(total_changes.values()),
                       'local_mass_plus_0_01_total_native_chi2_changes':within,
                       'local_mass_change_precision_discrepancy':within['selected_reference_settings']-within['baseline'],
                       'posterior_accuracy_certified':False}
paths = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
         and p.name not in ['completion_verification.json','self_review_receipt.json']]
result={'utc':datetime.now(timezone.utc).isoformat(),'scope':'six_selected_guarded_chain_coordinates_and_two_local_mass_offsets',
        'managed_exits':[{'lens':'A','session':64201,'exit_code':0},{'lens':'B','session':27270,'exit_code':0}],
        'target_closures':closures,'comparisons':comparisons,
        'settings_only_changes_verified':True,'uniform_numerical_accuracy_certified':False,
        'posterior_convergence_certified':False,'priors_or_posterior_recomputed':False,
        'paper_modified':False,'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]}
(HERE/'completion_verification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(comparisons,indent=2,allow_nan=False))
