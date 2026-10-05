"""Review reused native witnesses and output-only rebasing in all three recoveries."""
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for group, ordinal in [('old_A3200', 'seventh'), ('old_B4095', 'seventh'), ('current_A3200', 'eighth')]:
    new = ROOT / f'runs/20261004_math_review_fresh_CAMB_{ordinal}_{group}_diagnostics_v2'
    preparation = json.loads((new / 'recovery_preparation_receipt.json').read_text())
    old = ROOT / preparation['failed_root']
    assert sha(old / 'snapshot_receipt.json') == preparation['source_snapshot_receipt_sha256']
    before = json.loads((old / 'snapshot_receipt.json').read_text())
    after = json.loads((new / 'snapshot_receipt.json').read_text())
    assert before['group'] == after['group'] == group
    for field in before:
        if field not in ['families', 'diagnostic_command']:
            assert before[field] == after[field]
    assert after['diagnostic_command'] == [s.replace(str(old), str(new)) for s in before['diagnostic_command']]
    for a, b in zip(before['families'], after['families'], strict=True):
        assert {k: v for k, v in a.items() if k not in ['snapshot', 'snapshot_resolved_sha256']} == {
            k: v for k, v in b.items() if k not in ['snapshot', 'snapshot_resolved_sha256']}
        assert Path(a['snapshot']).read_bytes() == Path(b['snapshot']).read_bytes()
        old_cfg = yaml.safe_load((Path(a['snapshot']).parent.parent / 'resolved.yaml').read_text())
        new_cfg = yaml.safe_load((Path(b['snapshot']).parent.parent / 'resolved.yaml').read_text())
        assert old_cfg.pop('output') != new_cfg.pop('output') and old_cfg == new_cfg
    stage = ROOT / preparation['source_native_stage_completion']
    assert sha(stage) == preparation['source_native_stage_completion_sha256']
    assert json.loads(stage.read_text())['exit_code'] == 0
    assert sha(new / 'native_rows_verification.json') == sha(old / 'native_rows_verification.json') == preparation['source_native_receipt_sha256']
    native = json.loads((new / 'native_rows_verification.json').read_text())
    families = {f['seed']: f for f in after['families']}
    assert len(native['records']) == len(families) == 4
    for record in native['records']:
        f = families[record['seed']]
        assert record['file_sha256'] == f['snapshot_sha256']
        raw = Path(f['snapshot']).read_bytes()
        header = raw.decode().splitlines()[0].lstrip('#').split()
        rows = np.loadtxt(BytesIO(raw), ndmin=2)
        expected_indices = np.linspace(0, len(rows) - 1, 3, dtype=int).tolist()
        assert [r['row_index'] for r in record['checks']] == expected_indices
        for check in record['checks']:
            row = rows[check['row_index']]
            assert all(value == row[header.index(name)] for name, value in check['point'].items())
            assert max(abs(value) for value in check['fresh_minus_recorded'].values()) == 0
    old_worker = (old / 'run_verification.py').read_text()
    new_worker = (new / 'run_verification.py').read_text()
    a, b = preparation['worker_only_change']
    assert new_worker.replace(b, a, 1) == old_worker
    review = json.loads((new / 'self_review_receipt.json').read_text())
    assert len(review['all_seven_parameter_gate_sets_reconstructed']) == 7
    assert review['snapshot_receipt_sha256'] == sha(new / 'snapshot_receipt.json')
    assert review['native_row_verification_sha256'] == sha(new / 'native_rows_verification.json')
    for name in ['run_diagnostic.py', 'verify_snapshot.py']:
        assert json.loads((new / (name + '.completion.json')).read_text())['exit_code'] == 0
        assert not (new / (name + '.stderr.txt')).read_bytes()
    with (new / 'recovery_self_review_receipt.json').open('x') as f:
        f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                           'review_type': 'distinct_self_review_not_independent_agent', 'group': group,
                           'unchanged_frozen_rows_and_all_target_provenance_verified': True,
                           'only_snapshot_output_path_rebased': True,
                           'twelve_selected_native_points_and_components_reused_exactly': True,
                           'original_native_stage_exit0_verified': True,
                           'remaining_two_stages_exit0_verified': True,
                           'all_seven_parameter_gate_sets_reconstructed': True,
                           'native_stage_reexecuted_on_identical_rows': False,
                           'gates_or_target_changed': False, 'posterior_qualified': False},
                          indent=2, allow_nan=False) + '\n')
    print(group, 'recovery self-review passed', flush=True)
