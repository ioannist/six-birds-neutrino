"""Separate the two spectrum-grid controls from four dynamics controls."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = HERE.parent/'20261004_math_review_guarded_medium_fine_mass_response'
proof_path = PARENT/'completion_verification.json'
proof = json.loads(proof_path.read_text())
for file in proof['files']:
    assert hashlib.sha256((ROOT/file['path']).read_bytes()).hexdigest()==file['sha256']
selection = json.loads((PARENT/'selection_receipt.json').read_text())
base = yaml.safe_load((PARENT/'B/evaluation/baseline.yaml').read_text())
fine = yaml.safe_load((PARENT/'B/evaluation/selected_reference_settings.yaml').read_text())
points = json.loads((PARENT/'B/points.json').read_text())
grid = {'l_logstep','l_linstep'}
dynamics = {'tol_perturbations_integration','perturbations_sampling_stepsize',
            'tol_ncdm_synchronous','tol_ncdm_newtonian'}
assert {k for k,v in fine['theory']['classy']['extra_args'].items()
        if base['theory']['classy']['extra_args'].get(k)!=v}==grid|dynamics
for variant, changed in [('grid_only',grid),('dynamics_only',dynamics)]:
    out = HERE/variant
    out.mkdir()
    cfg = deepcopy(base)
    for key in changed:
        cfg['theory']['classy']['extra_args'][key]=fine['theory']['classy']['extra_args'][key]
    (out/'input.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    (out/'points.json').write_text(json.dumps(points,indent=2,allow_nan=False)+'\n')
receipt={'utc':datetime.now(timezone.utc).isoformat(),'scope':'fixed_B_coordinates_numerical_factor_controls',
         'parent_verification':str(proof_path.relative_to(ROOT)),
         'parent_verification_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),
         'native_module_path':selection['native_module_path'],'native_module_sha256':selection['native_module_sha256'],
         'changed_controls':{'grid_only':sorted(grid),'dynamics_only':sorted(dynamics)},
         'previous_medium_and_fine_native_anchors_reused_not_rerun':True,
         'posterior_or_uniform_accuracy_certified':False}
(HERE/'selection_receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
print('Two B precision factors prepared at identical median and mass-offset coordinates.')
