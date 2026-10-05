"""Enforce frozen config, implementation, proposal and native identities."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
seed=int(sys.argv[1]);folder=HERE/f'seed{seed}'
e=json.loads((folder/'preparation_receipt.json').read_text())
proof=json.loads((folder/'initial_point_verification.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
import camb
import cobaya.theories.camb.camb as wrapper
module=Path(camb.baseconfig.camblib._name).resolve()
assert proof['native_initial_point_verified'] and proof['initial_point']==e['initial_point']
assert proof['upstream_forced_fresh_likes_and_priors_exact']
assert str(module)==e['module'] and sha(module)==e['module_sha256']==proof['module_sha256']
assert str(Path(wrapper.__file__).resolve())==e['wrapper'] and sha(wrapper.__file__)==e['wrapper_sha256']
assert importlib.metadata.version('camb')==e['solver_version'] and importlib.metadata.version('cobaya')==e['Cobaya_version']
assert sha(ROOT/e['config'])==e['config_sha256']==proof['config_sha256']
assert sha(ROOT/e['control'])==e['control_sha256']
assert sha(ROOT/e['proposal']['path'])==e['proposal']['sha256']
for path,digest in e['implementation_sha256'].items(): assert sha(ROOT/path)==digest
assert os.getpriority(os.PRIO_PROCESS, 0) == 5
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']: assert os.environ[key]=='1'
assert not (ROOT/e['run_dir']).exists()
stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
receipt={'utc':datetime.now(timezone.utc).isoformat(),'seed':seed,'lens':e['lens'],'group':e['group'],
    'pid':os.getpid(),'process_start_ticks':int(stat[19]),'module':str(module),'module_sha256':sha(module),
    'solver_version':e['solver_version'],'Cobaya_version':e['Cobaya_version'],'wrapper_sha256':e['wrapper_sha256'],
    'config_sha256':e['config_sha256'],'proposal_sha256':e['proposal']['sha256'],
    'implementation_sha256':e['implementation_sha256'],'initial_point_verification_sha256':sha(folder/'initial_point_verification.json'),
    'run_dir':e['run_dir'],'fresh_rng_and_output':True,'old_prefix_appended':False,'posterior_certified':False,
    'environment':{k:os.environ[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','PYTHONPATH']}}
with (folder/'launch_receipt.json').open('x') as f: f.write(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
sys.path.insert(0,str(ROOT/'scripts'))
sys.argv=[str(ROOT/'scripts/run_cobaya.py'),'--config',str(ROOT/e['config']),'--outdir',str(ROOT/e['run_dir']),'--seed',str(seed)]
runpy.run_path(str(ROOT/'scripts/run_cobaya.py'),run_name='__main__')
