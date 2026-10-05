"""Re-evaluate the saved trial rows with actual pinned native components."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import yaml
import classy._classy as native
from cobaya.model import get_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_chain_targets import compare_native_row
from run_cobaya import _validate_classy_backend

folder = HERE / 'first_saved_rows'
receipt = json.loads((folder / 'snapshot_receipt.json').read_text())
prep = json.loads((HERE / 'preparation_receipt.json').read_text())
module = Path(native.__file__).resolve()
assert module == Path(prep['native_module_path']).resolve()
assert hashlib.sha256(module.read_bytes()).hexdigest() == prep['native_module_sha256']
backend_witness = json.loads((folder / 'solver_backend.json').read_text())
assert backend_witness['module'] == str(module)
assert backend_witness['module_sha256'] == prep['native_module_sha256']
assert hashlib.sha256(Path(backend_witness['build_receipt']).read_bytes()).hexdigest() == backend_witness['build_receipt_sha256']
for f in receipt['files']:
    assert hashlib.sha256((ROOT / f['snapshot']).read_bytes()).hexdigest() == f['sha256']
chain = ROOT / receipt['files'][0]['snapshot']
raw = chain.read_text()
header = raw.splitlines()[0].lstrip('#').split()
assert len(header) == len(set(header))
rows = np.atleast_2d(np.loadtxt(chain))
assert len(rows) == receipt['stored_rows']
cfg = yaml.safe_load((folder / 'resolved.yaml').read_text())
assert _validate_classy_backend(cfg)['module_sha256'] == prep['native_module_sha256']
expected_cfg = yaml.safe_load((HERE / 'input.yaml').read_text())
assert cfg['params'] == expected_cfg['params'] and cfg['theory'] == expected_cfg['theory']
assert cfg['likelihood'] == expected_cfg['likelihood']
cfg.pop('output')
start = time.monotonic()
runtime = {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
           'module': str(module), 'module_sha256': prep['native_module_sha256'],
           'OMP_NUM_THREADS': os.environ['OMP_NUM_THREADS'], 'status': 'running_native_saved_row_verification'}
(folder / 'native_runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
with get_model(cfg, stop_at_error=True) as model:
    assert len(model.likelihood) == 6
    checks = []
    for index, row in enumerate(rows):
        check = compare_native_row(header, row, model, atol=1e-7, rtol=1e-10)
        actual = model.theory['classy'].classy.pars
        masses = [float(m) for m in actual['m_ncdm'].split(',')]
        assert actual['N_ncdm'] == 3 and len(masses) == 3
        assert np.isclose(sum(masses), check['point']['mnu_sample'], rtol=1e-13, atol=0)
        checks.append({'row_index': index, 'CLASS_masses': masses, **check})
        print(f'Native likelihood, prior and posterior pass for saved row {index}.', flush=True)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': prep['seed'],
       'scope': 'selected_initial_saved_rows_all_six_native_likelihoods_prior_and_posterior',
       'module_sha256': prep['native_module_sha256'], 'checks': checks,
       'snapshot_receipt_sha256': hashlib.sha256((folder / 'snapshot_receipt.json').read_bytes()).hexdigest(),
       'elapsed_seconds': time.monotonic() - start,
       'atol': 1e-7, 'rtol': 1e-10, 'every_transition_verified': False,
       'posterior_convergence_or_uniform_accuracy_certified': False}
with (folder / 'native_target_verification.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
runtime['status'] = 'completed_native_saved_row_verification'
(folder / 'native_runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
