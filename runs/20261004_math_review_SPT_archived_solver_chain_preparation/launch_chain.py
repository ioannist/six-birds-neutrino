"""Enforce the exact isolated solver before creating fresh sampler output."""
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
seed=int(sys.argv[1])
folder=HERE/('seed'+str(seed))
e=json.loads((folder/'preparation_receipt.json').read_text())
proof=json.loads((folder/'initial_point_verification.json').read_text())
assert proof['native_initial_point_verified'] and proof['initial_point']==e['initial_point']
import camb
import cobaya
import cobaya.theories.camb.camb as wrapper
module=Path(camb.baseconfig.camblib._name).resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert str(module)==e['module'] and sha(module)==e['module_sha256']==proof['module_sha256']
assert str(Path(wrapper.__file__).resolve())==e['wrapper'] and sha(wrapper.__file__)==e['wrapper_sha256']
assert importlib.metadata.version('camb')=='1.6.5' and importlib.metadata.version('cobaya')=='3.6.1'
assert sha(ROOT/e['config'])==e['config_sha256']==proof['config_sha256']
assert os.environ['OMP_NUM_THREADS']=='1'
assert not (ROOT/e['run_dir']).exists()
stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
receipt={'utc':datetime.now(timezone.utc).isoformat(),'seed':seed,'lens':e['lens'],'pid':os.getpid(),
    'process_start_ticks':int(stat[19]),'module':str(module),'module_sha256':e['module_sha256'],
    'solver_version':'1.6.5','Cobaya_version':'3.6.1','wrapper_sha256':e['wrapper_sha256'],
    'config_sha256':e['config_sha256'],'initial_point_verification_sha256':sha(folder/'initial_point_verification.json'),
    'run_dir':e['run_dir'],'environment':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTHONPATH']},
    'implementation_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'scripts/run_cobaya.py',ROOT/'src/sbt_spt_audit/samplers.py']},
    'fresh_rng_and_output':True,'old_prefix_appended':False,'posterior_claims':False}
with (folder/'launch_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
# The helper creates the bundle. A separate immutable native receipt is written
# after its first output appears by the activation verifier, using this launch witness.
sys.path.insert(0,str(ROOT/'scripts'))
sys.argv=[str(ROOT/'scripts/run_cobaya.py'),'--config',str(ROOT/e['config']),
          '--outdir',str(ROOT/e['run_dir']),'--seed',str(seed)]
runpy.run_path(str(ROOT/'scripts/run_cobaya.py'),run_name='__main__')
