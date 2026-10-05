"""Densify the angular spectrum grid while holding medium dynamics fixed."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
grid_proof_path=HERE/'grid_source_verification.json'
grid_proof=json.loads(grid_proof_path.read_text())
for file in grid_proof['source_identity']:
    assert hashlib.sha256(Path(file['path']).read_bytes()).hexdigest()==file['sha256']
PARENT=HERE.parent/'20261004_math_review_guarded_B_spectrum_grid_refinement'
proof_path=PARENT/'completion_verification.json'
proof=json.loads(proof_path.read_text())
for file in proof['files']:
    assert hashlib.sha256((ROOT/file['path']).read_bytes()).hexdigest()==file['sha256']
previous=json.loads((PARENT/'selection_receipt.json').read_text())
config_path=PARENT/'grid3/input.yaml'
points_path=PARENT/'grid3/points.json'
base=yaml.safe_load(config_path.read_text())
points=json.loads(points_path.read_text())
assert base['theory']['classy']['extra_args']['l_logstep']==1.00325
assert base['theory']['classy']['extra_args']['l_linstep']==3
targets={'unit_grid':{'l_logstep':1.0}}
for variant,settings in targets.items():
    folder=HERE/variant;folder.mkdir()
    cfg=deepcopy(base)
    cfg['theory']['classy']['extra_args'].update(settings)
    (folder/'input.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    (folder/'points.json').write_text(json.dumps(points,indent=2,allow_nan=False)+'\n')
receipt={'utc':datetime.now(timezone.utc).isoformat(),'scope':'B_two_selected_mass_coordinates_unit_logarithmic_grid',
         'grid_source_verification':str(grid_proof_path.relative_to(ROOT)),
         'grid_source_verification_sha256':hashlib.sha256(grid_proof_path.read_bytes()).hexdigest(),
         'parent_verification':str(proof_path.relative_to(ROOT)),
         'parent_verification_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),
         'native_module_path':previous['native_module_path'],'native_module_sha256':previous['native_module_sha256'],
         'changed_controls':{variant:sorted(values) for variant,values in targets.items()},'grid_targets':targets,
         'dynamics_and_physical_targets_unchanged':True,'previous_grid3_native_anchor_reused_not_new_evaluation':True,
         'uniform_accuracy_or_convergence_certified':False,
         'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [config_path,points_path]]}
(HERE/'selection_receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
print('B unit logarithmic multipole grid prepared with medium dynamics fixed.')
