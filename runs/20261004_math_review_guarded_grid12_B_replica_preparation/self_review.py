"""Check exact target equality and provenance of all four distinct starts."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / 'preparation_receipt.json').read_text())
base_path = ROOT / receipt['reference_config']
assert hashlib.sha256(base_path.read_bytes()).hexdigest() == receipt['reference_config_sha256']
base = yaml.safe_load(base_path.read_text())
clean = lambda params: {n: {k: v for k, v in p.items() if k not in ['ref', 'proposal']}
                       if isinstance(p, dict) else p for n, p in params.items()}
records, points = [], [tuple(p['ref'] for p in base['params'].values() if isinstance(p, dict) and 'prior' in p)]
names = [n for n, p in base['params'].items() if isinstance(p, dict) and 'prior' in p]
for prep in receipt['records']:
    cfg_path = ROOT / prep['config']
    assert hashlib.sha256(cfg_path.read_bytes()).hexdigest() == prep['config_sha256']
    cfg = yaml.safe_load(cfg_path.read_text())
    assert clean(cfg['params']) == clean(base['params'])
    assert cfg['theory'] == base['theory'] and cfg['likelihood'] == base['likelihood']
    assert cfg.get('prior') == base.get('prior') and cfg['packages_path'] == base['packages_path']
    options = deepcopy(cfg['sampler'])
    options['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] = 1501
    assert options == base['sampler']
    source = ROOT / prep['initialization_source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == prep['initialization_source_sha256']
    rows = np.atleast_2d(np.loadtxt(source))
    header = source.read_text().splitlines()[0].lstrip('#').split()
    point = {n: float(rows[prep['stored_row_zero_based'], header.index(n)]) for n in names}
    assert point == prep['initial_point']
    assert all(cfg['params'][n]['ref'] == x for n, x in point.items())
    points.append(tuple(point[n] for n in names))
    records.append({'seed': prep['seed'], 'source': prep['initialization_source'],
                    'mass_eV': point['mnu_sample'], 'all_target_definitions_match': True})
assert len(set(points)) == 4 and {r['seed'] for r in records} == {1502, 1503, 1504}
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_review',
       'scope': 'configuration_and_initialization_provenance_not_native_or_convergence_evidence',
       'preparation_receipt_sha256': hashlib.sha256((HERE / 'preparation_receipt.json').read_bytes()).hexdigest(),
       'self_review_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'records': records, 'four_distinct_starts': True,
       'initializations_are_not_posterior_draws_or_independence_certificates': True,
       'sampler_rules_changed_except_distinct_seeds': False, 'different_precision_histories_pooled': False,
       'native_checks_required_before_launch': True}
with (HERE / 'self_review_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('All three replica inputs match the exact seed-1501 target and sampler rules.')
