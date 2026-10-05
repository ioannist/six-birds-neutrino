from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
helper = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
assert sha(helper) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
spec = importlib.util.spec_from_file_location('terminal_identity', helper)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
summaries = []
for seed, session in [(2007, 77899), (2008, 89790)]:
    entry = next(e for e in state['upper_prior_posterior_chains'] if e['seed'] == seed)
    absence = identity.observe_retired_identity(entry['pid'], entry['process_start_ticks'])
    assert absence['original_identity_absent']
    folder = HERE / f'seed{seed}'
    folder.mkdir(exist_ok=False)
    source = ROOT / entry['run_dir']
    launch = ROOT / entry['launch_receipt']
    sources = [(p, folder / 'terminal_bundle' / p.relative_to(source)) for p in sorted(source.rglob('*')) if p.is_file()]
    sources += [(p, folder / 'launch_bundle' / p.name) for p in
                [ROOT / entry['config'], launch, launch.with_name('launcher_stdout.txt'), launch.with_name('launcher_stderr.txt')]]
    files = []
    for original, frozen in sources:
        frozen.parent.mkdir(parents=True, exist_ok=True)
        before = sha(original)
        shutil.copyfile(original, frozen)
        assert before == sha(original) == sha(frozen)
        files.append({'source': str(original.relative_to(ROOT)), 'frozen': str(frozen.relative_to(ROOT)),
                      'bytes': frozen.stat().st_size, 'sha256': before})
    bundle = folder / 'terminal_bundle'
    error = (bundle / 'stderr.txt').read_text()
    assert error == 'ValueError: provider spectrum tt must be finite and 1D.\n'
    assert 'cobaya_success: False' in (bundle / 'summary.md').read_text()
    utc, steps, accepted = re.findall(r'Progress @ ([^\n]+) : (\d+) steps taken, and (\d+) accepted',
                                      (bundle / 'stdout.txt').read_text())[-1]
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'seed': seed, 'pid': entry['pid'],
               'process_start_ticks': entry['process_start_ticks'], 'managed_session': session, 'exit_code': 1,
               'managed_session_status': 'closed_exit1_polled_current_goal_turn', 'run_dir': entry['run_dir'],
               'identity_observation': absence, 'registered_entry': entry, 'terminal_output_files': files,
               'error_type': 'ValueError', 'error': error.strip().removeprefix('ValueError: '), 'stderr_exact': error,
               'last_logged_progress': {'utc': utc, 'steps': int(steps), 'accepted': int(accepted)},
               'exact_failing_proposal_available': False, 'checkpoint_contains_RNG_state': False,
               'numerical_failure_is_not_prior_or_posterior_rejection': True, 'posterior_qualified': False,
               'original_scientific_process_modified': False}
    with (folder / 'terminal_receipt.json').open('x') as f:
        f.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')

    # Separate verification of copied witnesses and terminal-state interpretation.
    for e in files:
        assert sha(ROOT / e['source']) == sha(ROOT / e['frozen']) == e['sha256']
    checkpoint = yaml.safe_load(next((bundle / 'chains').glob('*.checkpoint')).read_text())
    fields = next(iter(checkpoint['sampler'].values()))
    assert set(fields) == {'converged', 'Rminus1_last', 'burn_in', 'mpi_size'} and not fields['converged']
    raw = next((bundle / 'chains').glob('*.1.txt')).read_bytes()
    assert raw.endswith(b'\n')
    rows = [line.split() for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
    weights = [Fraction(row[0]) for row in rows]
    assert all(w > 0 and w.denominator == 1 for w in weights)
    first = json.loads((ROOT / entry['first_saved_row_receipt']).read_text())
    assert raw.startswith((ROOT / first['frozen']).read_bytes())
    review = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
              'terminal_receipt_sha256': sha(folder / 'terminal_receipt.json'), 'immutable_terminal_files_checked': len(files),
              'stored_rows': len(rows), 'represented_steps': sum(int(w) for w in weights),
              'retained_represented_steps': sum(int(w) for w in weights[len(weights) // 5:]),
              'first_saved_native_witness_prefix_preserved': True, 'RNG_or_failed_proposal_in_checkpoint': False,
              'resume_from_checkpoint_supported_by_saved_state': False, 'native_failure_is_posterior_rejection': False,
              'posterior_qualified': False}
    with (folder / 'self_review_receipt.json').open('x') as f:
        f.write(json.dumps(review, indent=2, allow_nan=False) + '\n')
    summaries.append({'seed': seed, 'terminal_receipt': str((folder / 'terminal_receipt.json').relative_to(ROOT)),
                      'terminal_receipt_sha256': sha(folder / 'terminal_receipt.json'), 'stored_rows': len(rows),
                      'retained_represented_steps': review['retained_represented_steps']})
    print(seed, 'terminal exit1 preserved:', len(rows), 'rows;', review['retained_represented_steps'], 'retained steps')
with (HERE / 'completion_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'summaries': summaries,
                       'failure_causes_beyond_spectrum_validation_unresolved': True,
                       'prior_or_posterior_rejection_inferred': False, 'posterior_qualified': False}, indent=2) + '\n')
