"""Archive startup evidence and complete early rows for independent native checks."""
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
destination = HERE / 'first_saved_row_snapshots'
assert not destination.exists()
manifest = json.loads((HERE / 'manifest.json').read_text())
sampler_name = 'sbt_spt_audit.samplers.FullPrecisionMCMC'
prepared = []
for entry in manifest['runs']:
    run = ROOT / entry['outdir']
    runtime = json.loads((run / 'runtime_state.json').read_text())
    assert entry['outdir'].encode() in (Path('/proc') / str(runtime['pid']) / 'cmdline').read_bytes()
    original_bytes = (run / 'resolved.yaml').read_bytes()
    config = yaml.safe_load(original_bytes)
    input_config = yaml.safe_load((ROOT / entry['config']).read_text())
    reconstructed = deepcopy(config)
    reconstructed.pop('output')
    reconstructed.pop('packages_path')
    assert reconstructed == input_config
    assert config['sampler'][sampler_name]['seed'] == entry['seed']
    assert config['theory']['classy']['extra_args']['tol_ncdm_bg'] == 1e-8
    actual_config = yaml.safe_load(next((run / 'chains').glob('*.updated.yaml')).read_text())
    options = actual_config['sampler'][sampler_name]
    assert options['temperature'] == 1
    assert options['oversample_thin'] is False and options['oversample_power'] == 0
    assert options['Rminus1_stop'] == .01 and options['Rminus1_cl_stop'] == .05
    stdout = (run / 'stdout.txt').read_bytes()
    assert b'Sampling!' in stdout and b"All parameters' covariance loaded from given covmat." in stdout
    assert not (run / 'stderr.txt').read_bytes()
    chain = next((run / 'chains').glob('*.txt'))
    raw = chain.read_bytes()
    complete = raw[:raw.rfind(b'\n') + 1]
    rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
    assert len(rows) >= 2 and np.all(np.isfinite(rows))
    assert np.all(rows[:, 0] > 0) and np.all(rows[:, 0] == np.floor(rows[:, 0]))
    folder = destination / f"seed{entry['seed']}"
    config['output'] = str(folder / 'chains' / chain.name.removesuffix('.1.txt'))
    config_bytes = yaml.safe_dump(config, sort_keys=False).encode()
    prepared.append((entry, folder, chain.name, complete, config_bytes, stdout, {
        'seed': entry['seed'], 'source': str(chain.relative_to(ROOT)),
        'snapshot': str((folder / 'chains' / chain.name).relative_to(ROOT)),
        'stored_rows': len(rows), 'chain_sha256': hashlib.sha256(complete).hexdigest(),
        'resolved_source_sha256': hashlib.sha256(original_bytes).hexdigest(),
        'snapshot_config_sha256': hashlib.sha256(config_bytes).hexdigest(),
        'startup_stdout_sha256': hashlib.sha256(stdout).hexdigest(),
        'actual_seed_covariance_and_integer_holding_options_verified': True,
        'actual_temperature': 1, 'native_saved_row_checks_pending': True}))
records = []
for entry, folder, name, chain, config, stdout, record in prepared:
    (folder / 'chains').mkdir(parents=True)
    (folder / 'chains' / name).write_bytes(chain)
    (folder / 'resolved.yaml').write_bytes(config)
    (folder / 'input.yaml').write_bytes((ROOT / entry['outdir'] / 'input.yaml').read_bytes())
    (folder / 'startup_snapshot.txt').write_bytes(stdout)
    records.append(record)
output = {'utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'early_quad_target_native_checks_pending_no_posterior_claim',
          'records': records, 'fresh_files_without_legacy_prefixes': True,
          'posterior_convergence_verified': False, 'posterior_accuracy_certified': False}
(destination / 'snapshot_receipt.json').write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
print(json.dumps({entry['seed']: entry['stored_rows'] for entry in records}))
