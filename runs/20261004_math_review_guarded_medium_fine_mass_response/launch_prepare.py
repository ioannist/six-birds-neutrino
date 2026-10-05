"""Prepare a finer numerical target at the same two declared mass coordinates."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = HERE.parent/'20261004_math_review_guarded_posterior_precision'
completed = json.loads((PARENT/'completion_verification.json').read_text())
for record in completed['files']:
    assert hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()==record['sha256']
assert len(completed['managed_exits'])==2 and all(r['exit_code']==0 for r in completed['managed_exits'])
previous = json.loads((PARENT/'selection_receipt.json').read_text())
settings = {'scope':'declared_finer_neutrino_integration_and_spectrum_grid_control',
            'derivation':'tighten five tolerance/grid controls from the completed seven-setting target; retain background quadrature and default integrator',
            'settings':{'tol_ncdm_bg':1e-8,'tol_perturbations_integration':1e-7,
                        'perturbations_sampling_stepsize':.005,'tol_ncdm_synchronous':1e-7,
                        'tol_ncdm_newtonian':1e-7,'l_logstep':1.013,'l_linstep':12},
            'uniform_error_certified':False}
sources = []
for lens in ['A','B']:
    out = HERE/lens
    out.mkdir()
    config_path = PARENT/lens/'evaluation/selected_reference_settings.yaml'
    points_path = PARENT/lens/'points.json'
    cfg = yaml.safe_load(config_path.read_text())
    points = json.loads(points_path.read_text())
    points = {name:points[name] for name in ['quad_q50','quad_q50_mass_plus']}
    assert cfg['theory']['classy']['path']=='global'
    for name,text in [('input.yaml',yaml.safe_dump(cfg,sort_keys=False)),
                      ('points.json',json.dumps(points,indent=2,allow_nan=False)+'\n'),
                      ('precision_settings.json',json.dumps(settings,indent=2,allow_nan=False)+'\n')]:
        (out/name).write_text(text)
    sources += [{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in [config_path,points_path]]
receipt = {'utc':datetime.now(timezone.utc).isoformat(),'scope':'two_lenses_identical_fixed_median_and_mass_plus_coordinates_medium_vs_fine',
           'parent_verified_comparison':str((PARENT/'completion_verification.json').relative_to(ROOT)),
           'parent_verified_comparison_sha256':hashlib.sha256((PARENT/'completion_verification.json').read_bytes()).hexdigest(),
           'native_module_path':previous['native_module_path'],'native_module_sha256':previous['native_module_sha256'],
           'mass_offset_eV':.01,'sources':sources,'posterior_accuracy_certified':False,'posterior_convergence_certified':False}
(HERE/'selection_receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
print('Identical A/B median and +0.01 eV coordinates prepared for medium-versus-fine controls.')
