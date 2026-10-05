from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
REPRO = ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation'
contract = json.loads((REPRO / 'reproduction_contract.json').read_text())
outdir = HERE / 'later_prefixes'
outdir.mkdir(exist_ok=False)
records = []
for seed, entry in contract['entries'].items():
    launch = json.loads((REPRO / f'seed{seed}/launch_receipt.json').read_text())
    proc = Path('/proc', str(launch['pid']))
    before = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert before[0] != 'Z' and int(before[19]) == launch['process_start_ticks']
    assert os.getpriority(os.PRIO_PROCESS, launch['pid']) == 10
    run = ROOT / launch['run_dir']
    assert not (run / 'stderr.txt').read_bytes()
    source = next((run / 'chains').glob('*.1.txt'))
    raw = source.read_bytes()
    raw = raw[:raw.rfind(b'\n') + 1]
    terminal = json.loads((ROOT / entry['terminal_receipt']).read_text())
    original_entry = next(e for e in terminal['terminal_output_files'] if e['source'].endswith('.1.txt'))
    original = ROOT / original_entry['frozen']
    assert sha(original) == original_entry['sha256']
    assert original.read_bytes().startswith(raw)
    original_rows = np.loadtxt(original, ndmin=2)
    rows = np.loadtxt(BytesIO(raw), ndmin=2)
    assert len(rows) > 0 and np.array_equal(rows, original_rows[:len(rows)])
    frozen = outdir / f'seed{seed}.1.txt'
    with frozen.open('xb') as f:
        f.write(raw)
    progress = re.findall(r'Progress @ ([^\n]+) : (\d+) steps taken, and (\d+) accepted',
                          (run / 'stdout.txt').read_text())
    after = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert after[0] != 'Z' and int(after[19]) == launch['process_start_ticks']
    records.append({'seed': int(seed), 'pid': launch['pid'], 'process_start_ticks': int(after[19]),
                    'complete_stored_rows': len(rows), 'frozen': str(frozen.relative_to(ROOT)),
                    'frozen_sha256': sha(frozen), 'original_chain_sha256': sha(original),
                    'original_chain': str(original.relative_to(ROOT)),
                    'exact_byte_prefix': True, 'every_saved_binary64_value_equal': True,
                    'latest_logged_progress': progress[-1], 'whole_failed_trajectory_verified': False})
with (HERE / 'later_prefix_verification.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
                       'scope': 'later saved trajectory prefixes only; complete failing transition still pending',
                       'posterior_qualified': False}, indent=2, allow_nan=False) + '\n')
print('Exact later saved prefixes verified:', [(r['seed'], r['complete_stored_rows']) for r in records])
