"""Archive the recorded post-recovery segments without historical prefixes."""
import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
destination = args.destination.resolve()
if destination.exists():
    raise ValueError('Refusing to overwrite an existing segment snapshot.')
boundaries_path = HERE / 'segment_boundaries.json'
boundaries = json.loads(boundaries_path.read_text())['segments']
prepared = []
for seed, boundary in boundaries.items():
    saved = HERE / f'seed{seed}'
    old_chain = next((saved / 'chains').glob('*.txt'))
    old = old_chain.read_bytes()
    assert len(old) == boundary['historical_prefix_byte_count']
    assert hashlib.sha256(old).hexdigest() == boundary['historical_chain_sha256']
    source = ROOT / boundary['source_run_dir'] / 'chains' / old_chain.name
    raw = source.read_bytes()
    complete = raw[:raw.rfind(b'\n') + 1]
    if not complete.startswith(old):
        raise ValueError(f'Seed {seed}: historical prefix changed.')
    header = complete.splitlines(keepends=True)[0]
    assert header.startswith(b'#')
    segment = header + complete[len(old):]
    if not segment[len(header):].strip():
        raise ValueError(f'Seed {seed}: no saved post-recovery rows.')
    matrix = np.atleast_2d(np.loadtxt(BytesIO(segment)))
    assert np.all(np.isfinite(matrix))
    assert np.all(matrix[:, 0] > 0) and np.all(matrix[:, 0] == np.floor(matrix[:, 0]))
    original_config = (saved / 'resume_input.yaml').read_bytes()
    config = yaml.safe_load(original_config)
    assert config['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] == boundary['resume_seed']
    config.pop('resume', None)
    config['output'] = str(destination / f'seed{seed}' / 'chains' / old_chain.name.removesuffix('.1.txt'))
    prepared.append((seed, old_chain.name, segment, yaml.safe_dump(config, sort_keys=False).encode(), {
        'original_seed': int(seed), 'resume_seed': boundary['resume_seed'],
        'source': str(source.relative_to(ROOT)),
        'first_source_row_index': boundary['first_post_recovery_row_index'],
        'saved_segment_rows': len(matrix), 'segment_sha256': hashlib.sha256(segment).hexdigest(),
        'source_complete_prefix_sha256': hashlib.sha256(complete).hexdigest(),
        'resume_input_sha256': hashlib.sha256(original_config).hexdigest(),
        'historical_prefix_preserved': True,
    }))
destination.mkdir(parents=True)
records = {}
for seed, name, segment, config, record in prepared:
    folder = destination / f'seed{seed}'
    (folder / 'chains').mkdir(parents=True)
    (folder / 'chains' / name).write_bytes(segment)
    for config_name in ['input.yaml', 'resolved.yaml']:
        (folder / config_name).write_bytes(config)
    record['snapshot_config_sha256'] = hashlib.sha256(config).hexdigest()
    records[seed] = record
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'recorded_saved_post_recovery_segments_no_convergence_claim',
    'segment_count': len(records),
    'boundary_manifest_sha256': hashlib.sha256(boundaries_path.read_bytes()).hexdigest(),
    'records': records, 'burn_in_must_be_applied_within_each_segment': True,
    'uninterrupted_rng_trajectory_reconstructed': False,
    'posterior_convergence_verified': False,
}
(destination / 'segment_snapshot_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps({seed: item['saved_segment_rows'] for seed, item in records.items()}))
