"""Verify the actual trial configuration and loaded proposal at sampler startup."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
manifest = json.loads((HERE / 'manifest.json').read_text())
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
trials = {entry['seed']: entry for entry in state['controlled_precision_learned_proposal_trials']}
records = []
sampler_name = 'sbt_spt_audit.samplers.FullPrecisionMCMC'
for entry in manifest['records']:
    runtime = trials[entry['seed']]
    proc = Path('/proc') / str(runtime['pid'])
    assert runtime['run_dir'].encode() in (proc / 'cmdline').read_bytes()
    run = ROOT / runtime['run_dir']
    raw = (run / 'resolved.yaml').read_bytes()
    resolved = yaml.safe_load(raw)
    original_run = ROOT / f"runs/20261003_math_review_cmb_accuracy_chain_{entry['lens']}_seed{entry['source_seed']}"
    original = yaml.safe_load((original_run / 'resolved.yaml').read_bytes())
    options = resolved['sampler'][sampler_name]
    assert options['seed'] == entry['seed']
    covariance = Path(options['covmat']).read_bytes()
    assert hashlib.sha256(covariance).hexdigest() == entry['covariance_sha256']
    reconstructed = deepcopy(resolved)
    for key in ['run_name', 'output']:
        reconstructed[key] = original[key]
    for key in ['seed', 'covmat']:
        reconstructed['sampler'][sampler_name][key] = original['sampler'][sampler_name][key]
    reconstructed['notes']['proposal_scope'] = original['notes']['proposal_scope']
    assert reconstructed == original
    stdout = (run / 'stdout.txt').read_bytes()
    assert b'All parameters\' covariance loaded from given covmat.' in stdout
    assert b'Sampling!' in stdout
    assert f'SEEDED with seed {entry["seed"]}'.encode() in stdout
    assert not (run / 'stderr.txt').read_bytes()
    captured = HERE / f"{entry['lens']}_seed{entry['seed']}_startup_snapshot.txt"
    assert not captured.exists()
    captured.write_bytes(stdout)
    records.append({'lens': entry['lens'], 'seed': entry['seed'], 'pid': runtime['pid'],
                    'actual_target_configuration_reconstruction_pass': True,
                    'actual_seed_verified': True, 'all_parameter_covariance_loaded': True,
                    'covariance_sha256': entry['covariance_sha256'],
                    'resolved_configuration_sha256': hashlib.sha256(raw).hexdigest(),
                    'startup_snapshot_sha256': hashlib.sha256(stdout).hexdigest(),
                    'native_saved_row_checks_pending': True})
output = HERE / 'activation_verification.json'
assert not output.exists()
output.write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'actual_native_target_configuration_and_proposal_activation', 'records': records,
    'efficiency_improvement_verified': False, 'posterior_convergence_verified': False},
    indent=2, allow_nan=False) + '\n')
print(json.dumps(records, indent=2))
