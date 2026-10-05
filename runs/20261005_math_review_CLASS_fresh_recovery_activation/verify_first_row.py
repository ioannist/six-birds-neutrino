"""Freeze and replay one first complete row from the same owned recovery process."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREPARATION = ROOT / 'runs/20261005_math_review_CLASS_fresh_recovery_preparation'
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_chain_targets import compare_native_row
from cobaya.model import get_model

seed = int(sys.argv[1])
entry = next(e for e in json.loads((HERE / 'activation_verification.json').read_text())['records'] if e['seed'] == seed)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
run = ROOT / entry['run_dir']
chain = run / 'chains' / f'CLASS_fresh_recovery_{entry["group"]}_seed{seed}.1.txt'
proc = Path('/proc', str(entry['pid']))
deadline = time.monotonic() + 1800
while True:
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert stat[0] != 'Z' and int(stat[19]) == entry['process_start_ticks']
    assert (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode() == entry['command']
    assert entry['module'] in (proc / 'maps').read_text() and sha(entry['module']) == entry['module_sha256']
    assert not (run / 'stderr.txt').read_bytes() and not (HERE / f'seed{seed}/launcher_stderr.txt').read_bytes()
    if chain.exists():
        lines = chain.read_bytes().splitlines(keepends=True)
        first = next((i for i, line in enumerate(lines) if line.endswith(b'\n') and line.strip() and not line.startswith(b'#')), None)
        if first is not None:
            raw = b''.join(lines[:first + 1])
            break
    assert time.monotonic() < deadline, 'Observation timeout; inspect same process, do not restart.'
    print(seed, 'same owned process waiting for first saved row', flush=True)
    time.sleep(15)
out = HERE / f'seed{seed}/first_saved_row'
(out / 'chains').mkdir(parents=True)
frozen = out / 'chains' / chain.name
with frozen.open('xb') as f:
    f.write(raw)
for name in ['input.yaml', 'resolved.yaml', 'solver_backend.json']:
    with (out / name).open('xb') as f:
        f.write((run / name).read_bytes())
header = raw.decode().splitlines()[0].lstrip('#').split()
row = raw.decode().splitlines()[-1].split()
assert len(header) == len(set(header)) == len(row)
values = dict(zip(header, row))
weight = Fraction(values['weight'])
assert weight > 0 and weight.denominator == 1
assert np.isfinite([float(v) for v in values.values()]).all()
point = {name: float(values[name]) for name in entry['initial_point']}
cfg = yaml.safe_load((out / 'resolved.yaml').read_text())
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
with get_model(model_cfg, stop_at_error=True) as model:
    check = compare_native_row(header, np.array([float(v) for v in row]), model, 1e-9, 0)
assert chain.read_bytes().startswith(raw)
with (out / 'completion_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed, 'parent_seed': entry['parent_seed'],
        'point': point, 'holding_time': int(weight), 'source': str(chain.relative_to(ROOT)),
        'frozen': str(frozen.relative_to(ROOT)), 'snapshot_sha256': sha(frozen),
        'module_sha256': entry['module_sha256'], 'config_sha256': entry['config_sha256'],
        'native_row_verified': True, 'native_check': check, 'complete_source_prefix_preserved': True,
        'scope': 'Selected first saved native row; not exact resume, independent posterior evidence or convergence certificate.'},
        f, indent=2, allow_nan=False)
    f.write('\n')
print(seed, 'first complete native row replayed', check['fresh_minus_recorded'], flush=True)
