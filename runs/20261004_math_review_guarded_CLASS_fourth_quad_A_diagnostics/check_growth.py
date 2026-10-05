"""Check complete saved prefixes against the next recorded assessment thresholds."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
audit = json.loads((ROOT / 'runs/20261004_math_review_adaptive_history_scope/adaptation_receipt.json').read_text())
entries = [e for e in state['restoration_chains'] if e['kind'] == 'spt_desi']
for key in ['guarded_solver_posterior_trials', 'guarded_quadrature_posterior_chains', 'guarded_medium_posterior_chains']:
    entries += state[key]
entries = {e['seed']: e for e in entries}
records, groups = [], {}
for record in audit['records']:
    entry = entries[record['seed']]
    path, = (ROOT / entry['run_dir'] / 'chains').glob('*.1.txt')
    raw = path.read_bytes()
    raw = raw[:raw.rfind(b'\n') + 1]
    assert raw.startswith((ROOT / record['frozen_chain']).read_bytes())
    rows = [line.split() for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
    weights = [Fraction(row[0]) for row in rows[len(rows)//5:]]
    assert all(w > 0 and w.denominator == 1 for w in weights)
    n = int(sum(weights))
    group = record['cohort']
    groups.setdefault(group, []).append(n)
    records.append({'seed': record['seed'], 'cohort': group, 'complete_saved_prefix_sha256': hashlib.sha256(raw).hexdigest(),
                    'stored_rows': len(rows), 'postburn_represented_steps': n})
thresholds = {**{'SPT_' + k: v for k, v in state['next_SPT_diagnostic_minimum_represented_steps'].items()},
              **state['guarded_CLASS_next_assessment_minimum_history']}
progress = {k: {'minimum_saved_postburn_history': min(v), 'required': thresholds[k],
                'assessment_due': min(v) >= thresholds[k]} for k, v in groups.items()}
out = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'individual_saved_prefix_observations_not_new_diagnostics',
       'progress': progress, 'records': records, 'unwritten_holding_times_reconstructed': False,
       'existing_diagnostic_receipts_changed': False}
with (HERE / 'growth_observation.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2) + '\n')
print(json.dumps(progress, indent=2))
