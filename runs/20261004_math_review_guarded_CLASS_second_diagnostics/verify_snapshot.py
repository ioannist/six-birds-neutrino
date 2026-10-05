"""Verify frozen histories, recorded builds, cohort separation and diagnostics."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE / 'snapshot_receipt.json').read_text())
assert len(receipt['files']) == 16 and len(receipt['configurations']) == 32
assert len(receipt['native_backend_witnesses']) == 16
assert not receipt['precision_cohorts_pooled'] and not receipt['unmodified_backend_histories_included']
assert not receipt['parent_histories_appended'] and not receipt['diagnostic_gates_changed']
assert not receipt['grid12_trial_included']
previous_path=ROOT/receipt['previous_snapshot_receipt']
assert hashlib.sha256(previous_path.read_bytes()).hexdigest()==receipt['previous_snapshot_receipt_sha256']
previous=json.loads(previous_path.read_text());previous_files={f['source']:f for f in previous['files']}
assert set(receipt['growth_fractions_by_cohort'])=={'quad_A','quad_B','medium_A','medium_B'}
assert all(g>=.2 for g in receipt['growth_fractions_by_cohort'].values())
for f in receipt['files']:
    earlier=previous_files[f['source']]
    assert (ROOT/f['snapshot']).read_bytes().startswith((ROOT/earlier['snapshot']).read_bytes())
script = ROOT / 'scripts/diagnose_cobaya_chains.py'

assert hashlib.sha256(script.read_bytes()).hexdigest() == receipt['diagnostic_script_sha256']
earlier_roots = [ROOT / 'runs/20261004_math_review_class_backend_transition/fresh_saved_rows',
                 ROOT / 'runs/20261004_math_review_class_python_repair/guarded_initial_rows']
prior_prefixes = {p.name: p for base in earlier_roots for p in base.rglob('*.1.txt')}
prior_witnesses = []
for item in receipt['files']:
    saved = (ROOT / item['snapshot']).read_bytes()
    assert len(saved) == item['snapshot_bytes']
    assert hashlib.sha256(saved).hexdigest() == item['sha256']
    assert saved.endswith(b'\n') and (ROOT / item['source']).read_bytes().startswith(saved)
    before_path = prior_prefixes[Path(item['source']).name]
    before = before_path.read_bytes()
    assert saved.startswith(before)
    prior_witnesses.append({'path': str(before_path.relative_to(ROOT)),
                            'sha256': hashlib.sha256(before).hexdigest()})
    rows = np.atleast_2d(np.loadtxt(BytesIO(saved)))
    assert len(rows) == item['stored_rows'] and np.all(np.isfinite(rows))
    assert np.all(rows[:, 0] > 0) and np.all(rows[:, 0] == np.floor(rows[:, 0]))
    assert int(rows[int(.2 * len(rows)):, 0].sum()) == item['retained_represented_steps']
for item in receipt['configurations'] + receipt['native_backend_witnesses']:
    original, saved = [(ROOT / item[key]).read_bytes() for key in ['source', 'snapshot']]
    assert hashlib.sha256(original).hexdigest() == item['source_sha256']
    assert hashlib.sha256(saved).hexdigest() == item['snapshot_sha256']
    if Path(item['source']).name == 'resolved.yaml':
        cfg = yaml.safe_load(original)
        cfg['output'] = str((ROOT / item['snapshot']).parent / 'chains' / Path(cfg['output']).name)
        assert cfg == yaml.safe_load(saved)
    else:
        assert saved == original
hashes = {r['native_module_sha256'] for r in receipt['native_backend_witnesses']}
assert len(hashes) == 1
expected = {'quad_A': [1301, 1302, 1303, 1304], 'quad_B': [1305, 1306, 1307, 1308],
            'medium_A': [1201, 1401, 1402, 1406], 'medium_B': [1403, 1404, 1405, 1407]}
summaries, configs = {}, {}
for group, seeds in expected.items():
    completion = json.loads((HERE / (group + '_completion.json')).read_text())
    assert completion['command'] == receipt['diagnostic_commands'][group] and completion['exit_code'] == 0
    result = json.loads((HERE / (group + '_diagnostics.json')).read_text())
    assert result['seeds'] == seeds and result['burnin_fraction_of_stored_rows'] == .2
    assert result['native_backend_identity_scope'] == 'recorded_native_module_hash_agreement_not_uniform_solver_accuracy'
    assert {r['module_sha256'] for r in result['native_backend_provenance']} == hashes
    for record in result['native_backend_provenance']:
        assert len(record['witnesses']) == 1
        witness = record['witnesses'][0]
        assert hashlib.sha256(Path(witness['path']).read_bytes()).hexdigest() == witness['sha256']
    cfg = yaml.safe_load((HERE / group / f'seed{seeds[0]}' / 'resolved.yaml').read_text())
    configs[group] = cfg
    parameters = {n for n, b in cfg['params'].items() if isinstance(b, dict) and 'prior' in b}
    assert set(result['diagnostics']) == parameters
    for name, diagnostic in result['diagnostics'].items():
        assert 'error' not in diagnostic and diagnostic['n_chains'] == 4
        assert diagnostic['draws_per_chain'] == receipt['draws_per_chain_by_cohort'][group]
        for key in ['rank_folded_split_rhat', 'bulk_ess', 'tail_ess_05_95', 'quantile_ess', 'quantile_mcse']:
            assert np.isfinite(diagnostic[key])
        assert not diagnostic['mathematical_convergence_certificate']
    assert result['diagnostics']['mnu_sample']['quantile_mcse_limit'] == .001
    assert result['all_diagnostic_thresholds_pass'] == all(
        d['diagnostic_thresholds_pass'] for d in result['diagnostics'].values())
    mass = result['diagnostics']['mnu_sample']
    summaries[group] = {k: mass[k] for k in ['draws_per_chain', 'rank_folded_split_rhat', 'bulk_ess',
                                          'tail_ess_05_95', 'quantile_ess', 'quantile_mcse', 'diagnostic_thresholds_pass']}
    summaries[group]['all_parameter_gates_pass'] = result['all_diagnostic_thresholds_pass']
    summaries[group]['sampled_parameter_count'] = len(parameters)
    summaries[group]['passing_parameter_count'] = sum(d['diagnostic_thresholds_pass'] for d in result['diagnostics'].values())
for lens in ['A', 'B']:
    quad, medium = [deepcopy(configs[p + '_' + lens]) for p in ['quad', 'medium']]
    for cfg in [quad, medium]:
        cfg['theory']['classy']['extra_args'] = {}
    assert {k: quad.get(k) for k in ['likelihood', 'theory', 'prior']} == {
        k: medium.get(k) for k in ['likelihood', 'theory', 'prior']}
    clean = lambda c: {n: {k: v for k, v in b.items() if k not in ['ref', 'proposal']}
                      if isinstance(b, dict) else b for n, b in c['params'].items()}
    assert clean(quad) == clean(medium)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': receipt['scope'],
       'cohort_mass_diagnostics': summaries, 'native_module_sha256': next(iter(hashes)),
       'prior_guarded_native_verified_prefixes_preserved': prior_witnesses,
       'snapshot_receipt_sha256': hashlib.sha256((HERE / 'snapshot_receipt.json').read_bytes()).hexdigest(),
       'precision_cohorts_pooled': False, 'grid12_trial_included':False,
       'growth_fractions_by_cohort':receipt['growth_fractions_by_cohort'],
       'physical_model_matching_checked_within_each_lens': True,
       'diagnostic_gates_changed': False, 'posterior_convergence_proved': False,
       'uniform_solver_accuracy_proved': False, 'paper_modified': False,
       'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
                 and p.name not in ['completion_verification.json', 'self_review_receipt.json']]}
with (HERE / 'completion_verification.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps(summaries, indent=2))
