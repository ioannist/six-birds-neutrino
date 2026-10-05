"""Reconstruct first complete rows and their native component bindings."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREPARATION = ROOT / 'runs/20261005_math_review_sigma_time_v3_posterior_preparation_v2'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries = {e['seed']: e for e in json.loads((PREPARATION / 'preparation_receipt.json').read_text())['entries']}
activation = json.loads((HERE / 'activation_verification.json').read_text())
assert activation['owned_live_fresh_samplers'] == 16 and activation['distinct_targets'] == 4
assert len(activation['records']) == len(entries) == len({e['pid'] for e in activation['records']}) == 16
reports = []
for group in sorted({e['group'] for e in entries.values()}):
    group_path = HERE / f'first_rows_{group}_verification.json'
    check = json.loads(group_path.read_text())
    assert check['group'] == group and check['first_saved_native_rows_verified'] == 4
    assert {r['seed'] for r in check['records']} == {e['seed'] for e in entries.values() if e['group'] == group}
    for r in check['records']:
        entry = entries[r['seed']]
        proof_path = ROOT / r['out'] / 'completion_receipt.json'
        assert r == json.loads(proof_path.read_text())
        frozen = ROOT / r['frozen']
        raw = frozen.read_bytes()
        assert sha(frozen) == r['snapshot_sha256'] and (ROOT / r['source']).read_bytes().startswith(raw)
        lines = raw.decode().splitlines()
        rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
        assert raw.endswith(b'\n') and len(rows) == 1
        header = next(line for line in lines if line.startswith('#')).lstrip('#').split()
        assert len(header) == len(set(header)) == len(rows[0])
        row = dict(zip(header, rows[0]))
        assert all(math.isfinite(float(v)) for v in row.values())
        weight = Fraction(row['weight'])
        assert weight > 0 and weight.denominator == 1 and int(weight) == r['holding_time']
        assert {name: float(row[name]).hex() for name in entry['initial_point']} == {
            name: float(value).hex() for name, value in r['point'].items()}
        assert r['native_row_verified'] and r['module_sha256'] == entry['module_sha256']
        assert r['native_row_replay_tolerance'] == 1e-9 and r['FreshCAMB_exact_to_independent_upstream_fresh']
        assert r['sampler_cache_resize_challenge'] == 50
        errors = r['native_row_replay_discrepancies']
        cfg = yaml.safe_load((ROOT / entry['config']).read_text())
        assert set(errors) == set(cfg['likelihood']) | {'total_chi2', 'logprior', 'logposterior'}
        assert all(math.isfinite(v) and abs(v) <= 1e-9 for v in errors.values())
        snapshot = ROOT / r['out']
        assert sha(snapshot / 'input.yaml') == entry['config_sha256']
        source_cfg = yaml.safe_load((snapshot / 'input.yaml').read_text())
        effective_cfg = yaml.safe_load((snapshot / 'resolved.yaml').read_text())
        assert source_cfg['theory'] == effective_cfg['theory'] and source_cfg['params'] == effective_cfg['params']
        assert source_cfg['likelihood'] == effective_cfg['likelihood']
        assert effective_cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC'] == source_cfg['sampler']['mcmc']
        assert effective_cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] == entry['seed']
        backend = json.loads((snapshot / 'solver_backend.json').read_text())
        assert backend['module_sha256'] == entry['module_sha256'] and backend['module'] == entry['module']
        reports.append({'seed': entry['seed'], 'group': group, 'proof_sha256': sha(proof_path),
                        'frozen_sha256': sha(frozen), 'holding_time_exact_integer': int(weight),
                        'maximum_native_component_error': max(abs(v) for v in errors.values())})
assert len(reports) == 16
with (HERE / 'first_rows_self_review_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'reviewer': 'distinct_self_review_not_independent_agent',
        'records': reports, 'all_sixteen_first_saved_rows_bound': True,
        'maximum_native_component_error': max(r['maximum_native_component_error'] for r in reports),
        'all_four_targets_separate': True, 'old_prefixes_appended': False,
        'posterior_or_uniform_accuracy_certified': False, 'production_adopted': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('All sixteen first saved rows reconstructed and bound to the declared native candidate.')
