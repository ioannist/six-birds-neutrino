"""Verify saved trajectory segments, configuration transformations, and diagnostics."""
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
previous = json.loads((HERE.parent / '20261003_math_review_chain_snapshots_ninth' /
                       'snapshot_receipt.json').read_text())
old_files = {item['source']: item for item in previous['files']}
old_configs = {item['source']: item for item in previous['configurations']}
recovery = HERE.parent / '20261003_math_review_default_chain_recovery'
boundary_file = recovery / 'segment_boundaries.json'
boundaries = json.loads(boundary_file.read_text())['segments']


def digest(data):
    return hashlib.sha256(data).hexdigest()


assert len(receipt['files']) == 12 and len(receipt['configurations']) == 24
assert receipt['diagnostic_script_sha256'] == digest(
    (ROOT / 'scripts/diagnose_cobaya_chains.py').read_bytes())
checks = []
for item in receipt['files']:
    snapshot = (ROOT / item['snapshot']).read_bytes()
    assert digest(snapshot) == item['sha256']
    assert len(snapshot) == item['snapshot_bytes'] and snapshot.endswith(b'\n')
    captured = (ROOT / item['source']).read_bytes()[:item['complete_bytes']]
    assert digest(captured) == item['source_complete_sha256']
    previous_snapshot = (ROOT / old_files[item['source']]['snapshot']).read_bytes()
    assert digest(previous_snapshot) == old_files[item['source']]['sha256']
    assert captured.startswith(previous_snapshot)
    if item['trajectory_scope'] == 'post_recovery_segment':
        seed = str(item['original_seed'])
        boundary = boundaries[seed]
        historical = next((recovery / f'seed{seed}' / 'chains').glob('*.txt')).read_bytes()
        assert digest(historical) == boundary['historical_chain_sha256']
        assert len(historical) == boundary['historical_prefix_byte_count']
        assert captured.startswith(historical)
        assert snapshot == captured.splitlines(keepends=True)[0] + captured[len(historical):]
        assert item['historical_saved_rows_excluded'] == boundary['historical_saved_rows']
        assert item['active_segment_seed'] == boundary['resume_seed']
    else:
        assert item['trajectory_scope'] == 'uninterrupted_saved_prefix'
        assert snapshot == captured and item['historical_saved_rows_excluded'] == 0
    matrix = np.atleast_2d(np.loadtxt(BytesIO(snapshot)))
    assert len(matrix) == item['stored_rows'] and np.all(np.isfinite(matrix))
    assert np.all(matrix[:, 0] > 0) and np.all(matrix[:, 0] == np.floor(matrix[:, 0]))
    checks.append({key: item[key] for key in (
        'source', 'stored_rows', 'trajectory_scope', 'historical_saved_rows_excluded',
        'original_seed', 'active_segment_seed')})

for item in receipt['configurations']:
    original = (ROOT / item['source']).read_bytes()
    saved = (ROOT / item['snapshot']).read_bytes()
    assert digest(original) == item['source_sha256'] == old_configs[item['source']]['source_sha256']
    assert digest(saved) == item['snapshot_sha256']
    if item['recovery_configuration_source']:
        resume = (ROOT / item['recovery_configuration_source']).read_bytes()
        assert digest(resume) == item['recovery_configuration_sha256']
        cfg = yaml.safe_load(resume)
        original_seed = Path(item['recovery_configuration_source']).parent.name.removeprefix('seed')
        assert cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] == boundaries[original_seed]['resume_seed']
        cfg.pop('resume', None)
    elif Path(item['source']).name == 'input.yaml':
        assert saved == original
        continue
    else:
        cfg = yaml.safe_load(original)
    cfg['output'] = str((ROOT / item['snapshot']).parent / 'chains' / Path(cfg['output']).name)
    assert yaml.safe_load(saved) == cfg

groups = {}
for group, command in receipt['diagnostic_commands'].items():
    completion = json.loads((HERE / f'{group}_completion.json').read_text())
    assert completion['exit_code'] == 0 and completion['command'] == command
    data = (HERE / f'{group}_diagnostics.json').read_bytes()
    result = json.loads(data)
    expected_seeds = sorted(item['active_segment_seed'] for item in receipt['files']
                            if Path(item['snapshot']).parents[1].name.startswith(group + '_seed'))
    assert sorted(result['seeds']) == expected_seeds
    assert result['burnin_fraction_of_stored_rows'] == 0.2
    assert len(result['diagnostics']) == (10 if group.startswith('cmb_') else 7)
    for diagnostic in result['diagnostics'].values():
        assert 'error' not in diagnostic
        assert diagnostic['n_chains'] == len(expected_seeds)
        for key in ['rank_folded_split_rhat', 'bulk_ess', 'tail_ess_05_95',
                    'quantile_ess', 'quantile_mcse']:
            assert np.isfinite(diagnostic[key])
        assert not diagnostic['mathematical_convergence_certificate']
    assert result['all_diagnostic_thresholds_pass'] == all(
        d['diagnostic_thresholds_pass'] for d in result['diagnostics'].values())
    groups[group] = {'diagnostics_sha256': digest(data), 'exit_code': 0,
                     'all_diagnostic_thresholds_pass': result['all_diagnostic_thresholds_pass'],
                     'passed_parameters': [name for name, d in result['diagnostics'].items()
                                           if d['diagnostic_thresholds_pass']],
                     'mass_diagnostics': result['diagnostics']['mnu_sample' if group.startswith('cmb_') else 'mnu']}

output = {'utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'saved_segment_integrity_and_diagnostic_execution',
          'boundary_manifest_sha256': digest(boundary_file.read_bytes()),
          'snapshot_receipt_sha256': digest((HERE / 'snapshot_receipt.json').read_bytes()),
          'checks': checks, 'source_configurations_unchanged_since_ninth': True,
          'SPT_target_only': True, 'CLASS_cohorts_included': False,
          'restarted_families_use_fresh_segments_only': True, 'groups': groups,
          'all_diagnostic_thresholds_pass': all(g['all_diagnostic_thresholds_pass'] for g in groups.values()),
          'posterior_convergence_verified': False}
target = HERE / 'completion_verification.json'
assert not target.exists()
target.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
print(json.dumps(groups, indent=2, allow_nan=False))
