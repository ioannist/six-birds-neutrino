"""Strictly replay three selected snapshot rows using upstream fresh transfers."""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.metadata
from io import BytesIO
import json
from pathlib import Path
import sys
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'src'))
from verify_chain_targets import compare_native_row
from cobaya.model import get_model
import importlib
import classy
wrapper = importlib.import_module('cobaya.theories.classy.classy')

parser=argparse.ArgumentParser();parser.add_argument('snapshot',type=Path);args=parser.parse_args()
out=args.snapshot.resolve();receipt=json.loads((out/'snapshot_receipt.json').read_text())
contract=json.loads((HERE/'assessment_contract.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(HERE/'assessment_contract.json')==receipt['contract_sha256']
entries=contract['groups'][receipt['group']];expected=entries[0]
for path,digest in contract['diagnostic_source_sha256'].items():assert sha(ROOT/path)==digest
module=Path(importlib.import_module(classy.Class.__module__).__file__).resolve()
assert str(module)==expected['module'] and sha(module)==expected['module_sha256']
assert classy.__version__==expected['loaded_CLASS_version']
assert sha(ROOT/expected['build_receipt'])==expected['build_receipt_sha256']
assert importlib.metadata.version('cobaya')==expected['Cobaya_version']
assert str(Path(wrapper.__file__).resolve())==expected['wrapper'] and sha(wrapper.__file__)==expected['wrapper_sha256']
cfg=yaml.safe_load((out/f"seed{expected['seed']}"/'resolved.yaml').read_text())
assert set(cfg['theory'])=={'classy'} and cfg['theory']['classy'].get('class') is None
model_cfg={k:deepcopy(cfg[k]) for k in ['theory','likelihood','params','packages_path','prior'] if k in cfg}
records=[]
with get_model(model_cfg,stop_at_error=True) as model:
    for family in receipt['families']:
        path=Path(family['snapshot']);raw=path.read_bytes();assert sha(path)==family['snapshot_sha256']
        header=raw.decode().splitlines()[0].lstrip('#').split();assert len(header)==len(set(header))
        rows=np.loadtxt(BytesIO(raw),ndmin=2);assert len(rows)==family['stored_rows']
        indices=np.unique(np.linspace(0,len(rows)-1,min(len(rows),contract['native_rows_per_family']),dtype=int))
        checks=[{'row_index':int(i),**compare_native_row(header,rows[i],model,
            contract['native_replay_atol'],contract['native_replay_rtol'])} for i in indices]
        records.append({'seed':family['seed'],'file_sha256':sha(path),'checks':checks})
        print(family['seed'],'selected native rows verified',flush=True)
with (out/'native_rows_verification.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'group':receipt['group'],'records':records,
        'module_sha256':sha(module),'solver_version':expected['solver_version'],
        'loaded_CLASS_version':classy.__version__,
        'atol':contract['native_replay_atol'],'rtol':contract['native_replay_rtol'],
        'upstream_original_class_forced_fresh':True,'scope':'selected rows; no uniform accuracy or convergence certificate'},indent=2,allow_nan=False)+'\n')
