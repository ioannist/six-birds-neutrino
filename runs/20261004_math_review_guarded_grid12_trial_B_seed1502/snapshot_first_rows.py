"""Freeze up to two initial complete saved rows without altering the sampler."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
from io import BytesIO
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
run = HERE / 'run'
prep = json.loads((HERE / 'preparation_receipt.json').read_text())
cfg = yaml.safe_load((run / 'resolved.yaml').read_text())
source = Path(cfg['output'] + '.1.txt')
raw = source.read_bytes()
lines = raw[:raw.rfind(b'\n') + 1].splitlines(keepends=True)
assert len(lines) >= 2 and lines[0].startswith(b'#')
selected = b''.join(lines[:3])
rows = np.atleast_2d(np.loadtxt(BytesIO(selected)))
assert 1 <= len(rows) <= 2 and np.all(np.isfinite(rows))
assert np.all(rows[:, 0] > 0) and np.all(rows[:, 0] == np.floor(rows[:, 0]))
folder = HERE / 'first_saved_rows'
folder.mkdir()
(folder / 'chains').mkdir()
target = folder / 'chains' / source.name
target.write_bytes(selected)
files = [{'source': str(source.relative_to(ROOT)), 'snapshot': str(target.relative_to(ROOT)),
          'sha256': hashlib.sha256(selected).hexdigest()}]
for name in ['input.yaml', 'resolved.yaml', 'runtime_state.json', 'solver_backend.json']:
    data = (run / name).read_bytes()
    if name == 'resolved.yaml':
        rewritten = yaml.safe_load(data)
        rewritten['output'] = str(folder / 'chains' / Path(cfg['output']).name)
        saved = yaml.safe_dump(rewritten, sort_keys=False).encode()
    else:
        saved = data
    (folder / name).write_bytes(saved)
    files.append({'source': str((run / name).relative_to(ROOT)),
                  'snapshot': str((folder / name).relative_to(ROOT)),
                  'source_sha256': hashlib.sha256(data).hexdigest(),
                  'sha256': hashlib.sha256(saved).hexdigest()})
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': prep['seed'],
           'stored_rows': len(rows), 'chain_sha256': hashlib.sha256(selected).hexdigest(),
           'scope': 'initial_complete_saved_prefix_not_a_convergence_snapshot',
           'mutable_history_changed': False, 'files': files}
with (folder / 'snapshot_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2) + '\n')
print(f'Frozen {len(rows)} initial saved rows.')
