"""Check frozen A histories and execution of the unchanged convergence gates."""
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
old_path = ROOT / receipt['previous_snapshot_receipt']
assert hashlib.sha256(old_path.read_bytes()).hexdigest() == receipt['previous_snapshot_receipt_sha256']
old = json.loads(old_path.read_text())
old_files = {f['source']: f for f in old['files']}
old_cfg = {f['source']: f for f in old['configurations']}
assert len(receipt['files']) == 6 and len(receipt['configurations']) == 12
assert receipt['growth_fraction'] >= .2
assert not receipt['SPT_B_reassessed'] and not receipt['CLASS_cohorts_included']
assert not receipt['diagnostic_gates_changed']
for item in receipt['files']:
    saved = (ROOT / item['snapshot']).read_bytes()
    assert len(saved) == item['snapshot_bytes']
    assert hashlib.sha256(saved).hexdigest() == item['sha256']
    original_prefix = (ROOT / item['source']).read_bytes()[:len(saved)]
    assert original_prefix == saved and saved.endswith(b'\n')
    before = (ROOT / old_files[item['source']]['snapshot']).read_bytes()
    assert hashlib.sha256(before).hexdigest() == old_files[item['source']]['sha256']
    assert saved.startswith(before)
    rows = np.atleast_2d(np.loadtxt(BytesIO(saved)))
    assert len(rows) == item['stored_rows'] and np.all(np.isfinite(rows))
    assert np.all(rows[:, 0] > 0) and np.all(rows[:, 0] == np.floor(rows[:, 0]))
    assert int(rows[int(.2*len(rows)):, 0].sum()) == item['retained_represented_steps']
    assert item['trajectory_scope'] == 'uninterrupted_saved_prefix'
    assert item['active_segment_seed'] == item['original_seed']
for item in receipt['configurations']:
    original = (ROOT / item['source']).read_bytes()
    saved = (ROOT / item['snapshot']).read_bytes()
    assert hashlib.sha256(original).hexdigest() == item['source_sha256'] == old_cfg[item['source']]['source_sha256']
    assert hashlib.sha256(saved).hexdigest() == item['snapshot_sha256']
    if Path(item['source']).name == 'input.yaml':
        assert saved == original
    else:
        cfg = yaml.safe_load(original)
        cfg['output'] = str((ROOT / item['snapshot']).parent / 'chains' / Path(cfg['output']).name)
        assert cfg == yaml.safe_load(saved)
script = ROOT / 'scripts/diagnose_cobaya_chains.py'
assert hashlib.sha256(script.read_bytes()).hexdigest() == receipt['diagnostic_script_sha256']
completion = json.loads((HERE / 'chain_A_completion.json').read_text())
assert completion['command'] == receipt['diagnostic_commands']['chain_A']
assert completion['exit_code'] == 0
result = json.loads((HERE / 'chain_A_diagnostics.json').read_text())
assert sorted(result['seeds']) == [301, 302, 303, 304, 401, 402]
assert result['burnin_fraction_of_stored_rows'] == .2
assert set(result['diagnostics']) == {'omegabh2', 'omegach2', 'H0', 'logA', 'ns', 'tau', 'mnu'}
for name, diagnostic in result['diagnostics'].items():
    assert 'error' not in diagnostic and diagnostic['n_chains'] == 6
    assert diagnostic['draws_per_chain'] == receipt['current_draws_per_chain']
    for key in ['rank_folded_split_rhat', 'bulk_ess', 'tail_ess_05_95', 'quantile_ess', 'quantile_mcse']:
        assert np.isfinite(diagnostic[key])
    assert not diagnostic['mathematical_convergence_certificate']
assert result['diagnostics']['mnu']['quantile_mcse_limit'] == .005
assert result['all_diagnostic_thresholds_pass'] == all(d['diagnostic_thresholds_pass'] for d in result['diagnostics'].values())
out = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'SPT_A_snapshot_integrity_and_diagnostic_execution',
       'completed_families_401_402_retained': True, 'source_configurations_unchanged_since_tenth': True,
       'diagnostic_gates_changed': False, 'SPT_B_reassessed': False, 'CLASS_cohorts_included': False,
       'exit_code': 0, 'all_diagnostic_thresholds_pass': result['all_diagnostic_thresholds_pass'],
       'passed_parameters': [n for n,d in result['diagnostics'].items() if d['diagnostic_thresholds_pass']],
       'mass_diagnostics': result['diagnostics']['mnu'],
       'snapshot_receipt_sha256': hashlib.sha256((HERE/'snapshot_receipt.json').read_bytes()).hexdigest(),
       'diagnostics_sha256': hashlib.sha256((HERE/'chain_A_diagnostics.json').read_bytes()).hexdigest(),
       'posterior_convergence_proved': False}
with (HERE / 'completion_verification.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps(out, indent=2, allow_nan=False))
