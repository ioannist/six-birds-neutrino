from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt = json.loads((HERE / 'terminal_receipt.json').read_text())
assert receipt['seed'] == 2003 and receipt['exit_code'] == 1
assert receipt['identity_observation']['original_identity_absent']
for e in receipt['terminal_output_files']:
    assert sha(ROOT / e['source']) == sha(ROOT / e['frozen']) == e['sha256']
    assert (ROOT / e['frozen']).stat().st_size == e['bytes']
bundle = HERE / 'terminal_bundle'
assert (bundle / 'stderr.txt').read_text() == receipt['stderr_exact']
assert 'cobaya_success: False' in (bundle / 'summary.md').read_text()
progress = re.findall(r'Progress @ ([^\n]+) : (\d+) steps taken, and (\d+) accepted',
                      (bundle / 'stdout.txt').read_text())
utc, steps, accepted = progress[-1]
assert {'utc': utc, 'steps': int(steps), 'accepted': int(accepted)} == receipt['last_logged_progress']
checkpoint = yaml.safe_load(next((bundle / 'chains').glob('*.checkpoint')).read_text())
fields = next(iter(checkpoint['sampler'].values()))
assert set(fields) == {'converged', 'Rminus1_last', 'burn_in', 'mpi_size'}
assert not fields['converged']
chain = next((bundle / 'chains').glob('*.1.txt'))
raw = chain.read_bytes()
assert raw.endswith(b'\n')
rows = [line.split() for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
weights = [Fraction(row[0]) for row in rows]
assert weights and all(w > 0 and w.denominator == 1 for w in weights)
first = json.loads((ROOT / receipt['registered_entry']['first_saved_row_receipt']).read_text())
assert raw.startswith((ROOT / first['frozen']).read_bytes())
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'terminal_receipt_sha256': sha(HERE / 'terminal_receipt.json'),
       'immutable_terminal_files_checked': len(receipt['terminal_output_files']),
       'stored_rows': len(rows), 'represented_steps': sum(int(w) for w in weights),
       'retained_represented_steps': sum(int(w) for w in weights[len(weights) // 5:]),
       'first_saved_native_witness_prefix_preserved': True, 'RNG_or_failed_proposal_in_checkpoint': False,
       'resume_from_checkpoint_supported_by_saved_state': False,
       'native_failure_is_posterior_rejection': False, 'posterior_qualified': False}
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Terminal self-review passed:', len(rows), 'stored rows;', out['retained_represented_steps'], 'retained represented steps.')
