"""Selected successful stored rows are controls, not certificates of the failed transition."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model
from verify_chain_targets import compare_native_row

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract = json.loads((HERE / 'reproduction_contract.json').read_text())
first = contract['entries']['2003']
receipt = json.loads((ROOT / first['terminal_receipt']).read_text())
resolved_file = next(e for e in receipt['terminal_output_files'] if e['source'].endswith('/resolved.yaml'))
assert sha(ROOT / resolved_file['frozen']) == resolved_file['sha256']
cfg = yaml.safe_load((ROOT / resolved_file['frozen']).read_text())
assert cfg['theory']['camb'].pop('class') == 'sbt_spt_audit.boltzmann.FreshCAMB'
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
records = []
with get_model(model_cfg, stop_at_error=True) as model:
    for seed in ['2003', '2004']:
        entry = contract['entries'][seed]
        terminal = json.loads((ROOT / entry['terminal_receipt']).read_text())
        assert sha(ROOT / entry['terminal_receipt']) == entry['terminal_receipt_sha256']
        chain = next(e for e in terminal['terminal_output_files'] if e['source'].endswith('.1.txt'))
        path = ROOT / chain['frozen']
        assert sha(path) == chain['sha256']
        raw = path.read_bytes()
        header = raw.decode().splitlines()[0].lstrip('#').split()
        rows = np.loadtxt(BytesIO(raw), ndmin=2)
        indices = np.unique(np.linspace(0, len(rows) - 1, 3, dtype=int))
        for index in indices:
            check = compare_native_row(header, rows[index], model, 1e-9, 0)
            records.append({'seed': int(seed), 'row_index': int(index), 'chain_sha256': chain['sha256'], **check})
            print(seed, 'selected saved row', int(index), 'verified', flush=True)
assert len(records) == 6
with (HERE / 'terminal_rows_replay_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
                       'upstream_original_CAMB_forced_fresh': True, 'atol': 1e-9, 'rtol': 0,
                       'scope': 'six selected successful stored rows; failed proposal and uniform solver support remain unresolved',
                       'posterior_qualified': False}, indent=2, allow_nan=False) + '\n')
