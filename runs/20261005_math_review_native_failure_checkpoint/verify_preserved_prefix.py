"""Freeze terminal diagnostic evidence and verify exactly the saved-prefix scope."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep = ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation'
contract = json.loads((prep / 'reproduction_contract.json').read_text())
helper = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
assert sha(helper) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
spec = importlib.util.spec_from_file_location('diagnostic_identity', helper)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
archives = {
    2003: ROOT / 'runs/20261005_math_review_CAMB_upper20_seed2003_exact_failure_reproduction',
    2004: ROOT / 'runs/20261005_math_review_CAMB_upper20_seed2004_preserved_prefix_failure_reproduction',
}
records = []
for seed, archive in archives.items():
    entry = contract['entries'][str(seed)]
    launch = json.loads((prep / f'seed{seed}/launch_receipt.json').read_text())
    absent = identity.observe_retired_identity(launch['pid'], launch['process_start_ticks'])
    assert absent['original_identity_absent']
    if seed == 2004:
        archive.mkdir(exist_ok=False)
    else:
        assert (archive / 'verification_attempt_failure_receipt.json').is_file()
    files = []
    for source, target in [(ROOT / launch['run_dir'], archive / 'terminal_replay_bundle'),
                           (prep / f'seed{seed}', archive / 'recording_bundle')]:
        if seed == 2004:
            shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for path in sorted(source.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            frozen = target / path.relative_to(source)
            assert sha(path) == sha(frozen)
            files.append({'source': str(path.relative_to(ROOT)), 'frozen': str(frozen.relative_to(ROOT)),
                          'sha256': sha(frozen), 'bytes': frozen.stat().st_size})
    for path, digest in entry['implementation_sha256'].items():
        assert sha(ROOT / path) == digest
    assert sha(entry['module']) == entry['module_sha256']
    assert sha(entry['wrapper']) == entry['wrapper_sha256']
    original_root = ROOT / ('runs/20261004_math_review_upper_prior_seed2003_native_failure_v2' if seed == 2003
                           else 'runs/20261004_math_review_upper_prior_seed2004_native_failure')
    terminal = json.loads((original_root / 'terminal_receipt.json').read_text())
    for file in terminal['terminal_output_files']:
        assert sha(ROOT / file['frozen']) == file['sha256']
    original = next((original_root / 'terminal_bundle/chains').glob('*.1.txt'))
    replay = next((archive / 'terminal_replay_bundle/chains').glob('*.1.txt'))
    original_bytes, replay_bytes = original.read_bytes(), replay.read_bytes()
    assert original_bytes.endswith(b'\n') and replay_bytes.endswith(b'\n')
    assert replay_bytes.startswith(original_bytes)
    old, new = np.loadtxt(original), np.loadtxt(replay)
    assert np.array_equal(old, new[:len(old)])
    assert old.shape[1] == new.shape[1] == 15
    failure = json.loads((archive / 'recording_bundle/failed_proposal.json').read_text())
    assert failure['exception_type'] == 'ValueError'
    assert failure['error'] == 'provider spectrum tt must be finite and 1D.'
    assert failure['error'] in (archive / 'terminal_replay_bundle/stderr.txt').read_text()
    cfg = yaml.safe_load((archive / 'terminal_replay_bundle/resolved.yaml').read_text())
    assert sha(ROOT / entry['run_dir'] / 'resolved.yaml') == entry['effective_config_sha256']
    assert all(cfg['params'][name]['prior']['min'] < value < cfg['params'][name]['prior']['max']
               for name, value in failure['sampled'].items())
    with np.load(archive / 'recording_bundle/failed_provider_spectra.npz') as z:
        assert set(z.files) == {'ell', 'tt', 'ee', 'bb', 'te', 'et'}
        assert np.array_equal(z['ell'], np.arange(4101))
        spectra = {}
        for name in ['tt', 'ee', 'bb', 'te', 'et']:
            a = z[name]
            assert a.shape == (4101,)
            assert np.array_equal(a[:2], [0., 0.]) and np.isnan(a[2:]).all()
            spectra[name] = {'dimensions': 1, 'nan_count': int(np.isnan(a).sum()), 'inf_count': int(np.isinf(a).sum())}
    record = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed,
              'managed_session': 39055 if seed == 2003 else 62208, 'actual_terminal_exit_code': 1,
              'identity_observation': absent, 'terminal_replay_files': files,
              'original_saved_chain': str(original.relative_to(ROOT)), 'original_saved_chain_sha256': sha(original),
              'replay_saved_chain': str(replay.relative_to(ROOT)), 'replay_saved_chain_sha256': sha(replay),
              'original_saved_rows': len(old), 'replay_saved_rows': len(new),
              'additional_replay_saved_rows': len(new) - len(old), 'all_original_saved_bytes_preserved_as_prefix': True,
              'all_original_saved_binary64_values_equal': True,
              'original_unflushed_tail_or_exact_original_failing_proposal_known': False,
              'entire_internal_trajectory_equality_proved': False,
              'sampled': failure['sampled'], 'sampled_point_strictly_inside_declared_prior': True,
              'captured_spectra': spectra, 'validation_cause_at_replayed_point': 'NaNs, with valid one-dimensional arrays',
              'posterior_qualified': False, 'native_error_counted_as_posterior_rejection': False,
              'review_type': 'self_review_no_independent_agent',
              'scope': 'same seeded diagnostic exception preserving every original saved row; unsaved original trajectory unavailable'}
    with (archive / 'preserved_prefix_verification.json').open('x') as f:
        f.write(json.dumps(record, indent=2, allow_nan=False) + '\n')
    records.append({'seed': seed, 'receipt': str((archive / 'preserved_prefix_verification.json').relative_to(ROOT)),
                    'receipt_sha256': sha(archive / 'preserved_prefix_verification.json')})
    print(seed, len(old), 'original saved rows exactly preserved;', len(new)-len(old), 'extra replay rows; captured NaNs.', flush=True)
with (HERE / 'terminal_reproduction_index.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
                        'live_diagnostic_reproduction_workers': 0}, indent=2) + '\n')
