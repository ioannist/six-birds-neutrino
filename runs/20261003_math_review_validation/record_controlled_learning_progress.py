"""Record owned controlled samplers' proposal-learning evidence without changing them."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
assert not args.output.exists()
state = json.loads((HERE / 'review_state.json').read_text())
chains = state['controlled_precision_posterior_chains'] + state['controlled_precision_dragging_trials']
assert len(chains) == 6
records = []
for chain in chains:
    proc = Path('/proc') / str(chain['pid'])
    command = (proc / 'cmdline').read_bytes()
    assert chain['recovery_dir'].encode() in command and str(chain['seed']).encode() in command
    assert not next(line.split(':', 1)[1].strip() for line in (proc / 'status').read_text().splitlines()
                    if line.startswith('State:')).startswith('Z')
    recovery = ROOT / chain['recovery_dir'] / f"seed{chain['seed']}"
    run = ROOT / chain['run_dir']
    config_file = next((run / 'chains').glob('*.updated.yaml'))
    config_bytes = config_file.read_bytes()
    sampler = yaml.safe_load(config_bytes)['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
    assert sampler['learn_proposal']
    raw = (recovery / 'resume_stdout.txt').read_bytes()
    complete = raw[:raw.rfind(b'\n') + 1]
    lines = complete.decode().splitlines()
    mean_checks = [i for i, line in enumerate(lines) if 'Convergence of means: R-1 =' in line]
    assert mean_checks
    index = mean_checks[-1]
    rminus1 = float(re.search(r'R-1 = ([0-9.eE+-]+)', lines[index]).group(1))
    following = lines[index + 1:]
    waiting = any('Convergence less than requested for updates' in line for line in following)
    updates = [line for line in lines if 'Updated covariance matrix of proposal pdf.' in line]
    covmat = next((run / 'chains').glob('*.covmat'))
    original = recovery / 'chains' / covmat.name
    unchanged = covmat.read_bytes() == original.read_bytes()
    if waiting:
        assert rminus1 > sampler['learn_proposal_Rminus1_max']
    progress = next(line for line in reversed(lines) if 'Progress @ ' in line)
    records.append({'seed': chain['seed'], 'active_segment_seed': chain['resume_seed'],
                    'pid': chain['pid'], 'process_identity_verified': True,
                    'latest_progress_line': progress, 'latest_mean_check_line': lines[index],
                    'latest_internal_Rminus1': rminus1,
                    'learn_proposal_Rminus1_max': sampler['learn_proposal_Rminus1_max'],
                    'Rminus1_stop': sampler['Rminus1_stop'],
                    'Rminus1_cl_stop': sampler['Rminus1_cl_stop'],
                    'latest_learning_check_skipped_above_max': waiting,
                    'proposal_updates_in_fresh_segment': len(updates),
                    'saved_covariance_unchanged_from_recovery': unchanged,
                    'current_covariance_sha256': hashlib.sha256(covmat.read_bytes()).hexdigest(),
                    'updated_config_sha256': hashlib.sha256(config_bytes).hexdigest(),
                    'captured_log_prefix_byte_count': len(complete),
                    'captured_log_prefix_sha256': hashlib.sha256(complete).hexdigest()})
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'proposal_learning_progress_no_multichain_convergence_claim',
           'records': records, 'sampler_configuration_changed': False,
           'posterior_convergence_verified': False}
args.output.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps(records, indent=2))
