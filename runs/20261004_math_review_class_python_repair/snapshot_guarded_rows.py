"""Freeze early guarded-trial rows and actual sampler activation for native checks."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
launch = json.loads((HERE / 'guarded_launch_receipt.json').read_text())
run = ROOT / launch['outdir']
destination = HERE / 'guarded_initial_rows'
assert not destination.exists()
proc = Path('/proc') / str(launch['pid'])
assert launch['module'] in (proc / 'maps').read_text()
assert hashlib.sha256(Path(launch['module']).read_bytes()).hexdigest() == launch['module_sha256']
original_config = (run / 'resolved.yaml').read_bytes()
config = yaml.safe_load(original_config)
reconstructed = deepcopy(config)
reconstructed.pop('output')
assert reconstructed == yaml.safe_load((HERE / 'A_seed1201.yaml').read_text())
actual_raw = next((run / 'chains').glob('*.updated.yaml')).read_bytes()
actual = yaml.safe_load(actual_raw)
options = actual['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
assert options['seed'] == 1201 and options['drag'] is True
assert options['temperature'] == 1 and options['oversample_thin'] is False
assert options['oversample_power'] == .4 and options['learn_proposal'] is True
assert options['Rminus1_stop'] == .01 and options['Rminus1_cl_stop'] == .05
assert options['Rminus1_cl_level'] == .95 and options['max_samples'] == 20000
stdout = (run / 'stdout.txt').read_bytes()
assert b'Sampling!' in stdout and b'Dragging with number of interpolating steps:' in stdout
assert b"All parameters' covariance loaded from given covmat." in stdout
assert str(Path(launch['module']).parent).encode() in stdout
assert not (run / 'stderr.txt').read_bytes()
chain = next((run / 'chains').glob('*.txt'))
raw = chain.read_bytes()
complete = raw[:raw.rfind(b'\n') + 1]
rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
assert len(rows) >= 2, 'Wait for at least two actual saved rows; never restart on this observation'
assert np.isfinite(rows).all()
assert (rows[:, 0] > 0).all() and (rows[:, 0] == np.floor(rows[:, 0])).all()
(destination / 'chains').mkdir(parents=True)
config['output'] = str(destination / 'chains' / chain.name.removesuffix('.1.txt'))
saved_config = yaml.safe_dump(config, sort_keys=False).encode()
(destination / 'resolved.yaml').write_bytes(saved_config)
(destination / 'input.yaml').write_bytes((run / 'input.yaml').read_bytes())
(destination / 'chains' / chain.name).write_bytes(complete)
(destination / 'startup_snapshot.txt').write_bytes(stdout)
(destination / 'actual_updated.yaml').write_bytes(actual_raw)
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': 1201,
           'source': str(chain.relative_to(ROOT)), 'stored_rows': len(rows),
           'chain_sha256': hashlib.sha256(complete).hexdigest(),
           'resolved_source_sha256': hashlib.sha256(original_config).hexdigest(),
           'snapshot_config_sha256': hashlib.sha256(saved_config).hexdigest(),
           'actual_updated_sha256': hashlib.sha256(actual_raw).hexdigest(),
           'startup_stdout_sha256': hashlib.sha256(stdout).hexdigest(),
           'module_sha256': launch['module_sha256'],
           'actual_saved_blocking_option': options['blocking'],
           'actual_saved_drag_limits_option': options['drag_limits'],
           'actual_dragging_activation_lines': [line for line in stdout.decode().splitlines()
                                                if '] * ' in line],
           'sampler_activation_and_stopping_options_verified': True,
           'native_saved_row_checks_pending': True,
           'historical_prefix_appended': False,
           'posterior_convergence_certified': False}
(destination / 'snapshot_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(f"Archived {len(rows)} guarded rows and actual dragging activation.")
