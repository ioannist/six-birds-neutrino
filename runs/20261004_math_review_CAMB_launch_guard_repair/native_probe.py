"""Validate the actual imported native build without launching inference."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from run_cobaya import _validate_native_backend
import camb

source = ROOT/'runs/20261004_math_review_SPT_archived_solver_chain_preparation/seed1604/input.yaml'
config = yaml.safe_load(source.read_text())
native = Path(camb.baseconfig.camblib._name).resolve()
actual = hashlib.sha256(native.read_bytes()).hexdigest()
expected = config['notes']['camb_backend']['module_sha256']
records = []
try:
    witness = _validate_native_backend(config)
except ValueError as exc:
    assert actual != expected
    records.append({'case':'archived_native_contract','accepted':False,'error':str(exc)})
else:
    assert actual == expected and witness['solver_version']=='1.6.5'
    records.append({'case':'archived_native_contract','accepted':True,'witness':witness})
matching = deepcopy(config)
matching['theory']['camb']['version'] = camb.__version__
matching['notes']['camb_backend'] = {'module_sha256':actual,'solver_version':camb.__version__}
records.append({'case':'matching_actual_native','accepted':True,'witness':_validate_native_backend(matching)})
assert records[-1]['witness']['module_sha256']==actual
out = {'utc':datetime.now(timezone.utc).isoformat(),'records':records,
       'native_path':str(native),'native_sha256':actual,'solver_version':camb.__version__,
       'implementation_sha256':hashlib.sha256((ROOT/'scripts/run_cobaya.py').read_bytes()).hexdigest(),
       'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
       'scope':'actual-import native identity guard; no numerical accuracy or posterior claim',
       'inference_launched':False}
with (HERE/('native_'+camb.__version__+'_receipt.json')).open('x') as handle:
    handle.write(json.dumps(out,indent=2)+'\n')
print(camb.__version__, [(r['case'],r['accepted']) for r in records])
