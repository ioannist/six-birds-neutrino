"""Freeze complete fresh rows and actual sampler options for a guarded cohort group."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
group = sys.argv[1]
assert group in ['quad_A', 'quad_B', 'medium_A', 'medium_B']
prepared = json.loads((HERE / 'preparation_receipt.json').read_text())
entries = [entry for entry in prepared['records'] if entry['cohort'] + '_' + entry['lens'] == group]
destination = HERE / 'fresh_saved_rows' / group
assert not destination.exists()
records, artifacts = [], []
for entry in entries:
    seed = entry['replacement_seed']
    run = ROOT / entry['outdir']
    launch = json.loads((HERE / 'launches' / f'seed{seed}.json').read_text())
    proc = Path('/proc') / str(launch['pid'])
    assert launch['module'] in (proc / 'maps').read_text()
    original = (run / 'resolved.yaml').read_bytes()
    cfg = yaml.safe_load(original)
    reconstructed = deepcopy(cfg)
    reconstructed.pop('output')
    assert reconstructed == yaml.safe_load((ROOT / entry['config']).read_text())
    actual = next((run / 'chains').glob('*.updated.yaml')).read_bytes()
    options = yaml.safe_load(actual)['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
    assert options['seed'] == seed and options['temperature'] == 1
    assert options['oversample_thin'] is False
    for key in ['drag', 'oversample_power', 'learn_proposal', 'Rminus1_stop', 'Rminus1_cl_stop', 'Rminus1_cl_level', 'max_samples']:
        assert options[key] == cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC'].get(key, False if key == 'drag' else options[key])
    stdout = (run / 'stdout.txt').read_bytes()
    assert b'Sampling!' in stdout and b"All parameters' covariance loaded from given covmat." in stdout
    assert not (run / 'stderr.txt').read_bytes()
    chain = next((run / 'chains').glob('*.txt'))
    raw = chain.read_bytes()
    complete = raw[:raw.rfind(b'\n')+1]
    rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
    assert len(rows) >= 2, f'Seed {seed} has fewer than two saved rows; wait, do not restart'
    assert np.isfinite(rows).all() and (rows[:, 0] > 0).all() and (rows[:, 0] == np.floor(rows[:, 0])).all()
    folder = destination / f'seed{seed}'
    cfg['output'] = str(folder / 'chains' / chain.name.removesuffix('.1.txt'))
    config = yaml.safe_dump(cfg, sort_keys=False).encode()
    artifacts.append((folder, chain.name, complete, config, stdout, actual, (run / 'input.yaml').read_bytes()))
    records.append({'seed': seed, 'source': str(chain.relative_to(ROOT)),
                    'snapshot': str((folder / 'chains' / chain.name).relative_to(ROOT)),
                    'stored_rows': len(rows), 'chain_sha256': hashlib.sha256(complete).hexdigest(),
                    'source_config_sha256': hashlib.sha256(original).hexdigest(),
                    'snapshot_config_sha256': hashlib.sha256(config).hexdigest(),
                    'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
                    'actual_options_sha256': hashlib.sha256(actual).hexdigest(),
                    'module_sha256': launch['module_sha256'],
                    'actual_blocking': options['blocking'],
                    'actual_dragging_lines': [line for line in stdout.decode().splitlines() if '] * ' in line]})
for folder, name, chain, config, stdout, actual, inputs in artifacts:
    (folder / 'chains').mkdir(parents=True)
    (folder / 'chains' / name).write_bytes(chain)
    (folder / 'resolved.yaml').write_bytes(config)
    (folder / 'input.yaml').write_bytes(inputs)
    (folder / 'startup_stdout.txt').write_bytes(stdout)
    (folder / 'actual_updated.yaml').write_bytes(actual)
result = {'utc': datetime.now(timezone.utc).isoformat(), 'group': group, 'records': records,
          'historical_prefixes_appended': False, 'native_saved_row_checks_pending': True,
          'sampler_stopping_and_integer_holding_options_verified': True,
          'posterior_convergence_certified': False}
(destination / 'snapshot_receipt.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps({record['seed']: record['stored_rows'] for record in records}))
