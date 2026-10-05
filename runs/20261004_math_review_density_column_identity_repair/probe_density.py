"""Reproduce ambiguous GetDist readout and compare unchanged valid grids."""
import hashlib
import json
from pathlib import Path
import sys

import getdist
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import compare_mnu_posteriors as comparison

phase = sys.argv[1]
assert phase in ['before', 'after']
getdist.cache_dir = str(HERE / ('cache_' + phase))
fixtures = HERE / 'fixtures'
fixtures.mkdir(exist_ok=True)
first = np.linspace(.01, .03, 300)
other = np.linspace(4.7, 4.9, 300)
rows = np.column_stack([np.ones(300), np.zeros(300), first, other])
records = {}
for name, header, metadata in [
    ('valid', '# weight minuslogpost mnu other', 'mnu mass\nother other\n'),
    ('duplicate', None, 'mnu mass\nmnu* duplicated_mass\n'),
    ('conflicting', '# weight minuslogpost mnu other', 'other other\nmnu mass\n'),
]:
    prefix = fixtures / name
    chain = Path(str(prefix) + '.1.txt')
    meta = Path(str(prefix) + '.paramnames')
    if phase == 'before':
        np.savetxt(chain, rows, header=header.lstrip('# ') if header else '')
        meta.write_text(metadata)
    try:
        density = comparison._load_density(prefix, 0)
        packed = np.column_stack([density.x, density.P])
        record = {'accepted': True, 'mode': float(density.x[np.argmax(density.P)]),
                  'density_grid_sha256': hashlib.sha256(packed.tobytes()).hexdigest()}
    except ValueError as error:
        record = {'accepted': False, 'error': str(error)}
    if phase == 'before':
        assert record['accepted']
        assert (.01 <= record['mode'] <= .03) if name == 'valid' else (4.7 <= record['mode'] <= 4.9)
    elif name == 'valid':
        previous = json.loads((HERE / 'before.json').read_text())['records']['valid']
        assert record == previous
    else:
        assert not record['accepted']
    records[name] = record
out = {'phase': phase, 'records': records,
       'comparison_source_sha256': hashlib.sha256((ROOT / 'scripts/compare_mnu_posteriors.py').read_bytes()).hexdigest(),
       'GetDist_version': getdist.__version__, 'valid_mass_column_range': [float(first.min()), float(first.max())]}
with (HERE / (phase + '.json')).open('x') as handle:
    handle.write(json.dumps(out, indent=2) + '\n')
print(json.dumps(records, indent=2))
