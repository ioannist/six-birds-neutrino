from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
preparation = json.loads((HERE / 'preparation_receipt.json').read_text())
receipt = json.loads((HERE / 'scout_receipt.json').read_text())
assert receipt['planned_selected_points'] == receipt['tested_selected_points'] == 12
assert not receipt['stopped_on_first_exception']
original = json.loads((ROOT / preparation['source_terminal_receipts'][0]).read_text())
config_file = next(r for r in original['terminal_output_files'] if r['source'].endswith('/resolved.yaml'))
assert sha(ROOT / config_file['frozen']) == config_file['sha256']
cfg = yaml.safe_load((ROOT / config_file['frozen']).read_text())
assert 'prior' not in cfg
bounds = {name: block['prior'] for name, block in cfg['params'].items()
          if isinstance(block, dict) and 'prior' in block}
prior = -math.fsum(math.log(b['max'] - b['min']) for b in bounds.values())
for index, (planned, actual) in enumerate(zip(preparation['planned_selected_points'], receipt['records'], strict=True)):
    assert actual['index'] == index and actual['status'] == 'finite_evaluation'
    assert all(actual[k] == planned[k] for k in ['source_seed', 'label', 'sampled'])
    assert set(actual['sampled']) == set(bounds)
    assert all(b['min'] < actual['sampled'][name] < b['max'] for name, b in bounds.items())
    assert all(math.isfinite(v) for v in [actual['logpost'], *actual['loglikes'], *actual['logpriors']])
    assert len(actual['logpriors']) == 1 and abs(actual['logpriors'][0] - prior) < 1e-13
    assert abs(actual['logpost'] - math.fsum([*actual['logpriors'], *actual['loglikes']])) < 1e-9
    assert not (HERE / f'point{index:02d}' / 'failed_proposal.json').exists()
assert not (HERE / 'scout_stderr.txt').read_bytes()
with (HERE / 'self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                       'review_type': 'distinct_self_review_not_independent_agent',
                       'scout_receipt_sha256': sha(HERE / 'scout_receipt.json'),
                       'selected_prior_interior_points_verified': 12,
                       'normalized_uniform_prior_and_posterior_component_accounting_verified': True,
                       'selected_mass_16_and_19_eV_and_low_CDM_points_finite': True,
                       'actual_original_failed_proposal_identified': False,
                       'native_failure_cause_or_uniform_support_established': False,
                       'posterior_qualified': False}, indent=2, allow_nan=False) + '\n')
print('Twelve-point scout self-review passed; failed transition and uniform support remain unresolved.')
