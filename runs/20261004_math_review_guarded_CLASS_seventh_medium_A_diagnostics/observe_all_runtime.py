def observe_primary():
    """Verify all remaining inference identities after retiring old CAMB cache policy."""
    from datetime import datetime, timezone
    from fractions import Fraction
    import hashlib
    import json
    from pathlib import Path
    import re
    HERE = Path(__file__).resolve().parent
    ROOT = HERE.parents[1]
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
    old = {r['seed']: r for r in json.loads((ROOT / 'runs/20261004_math_review_fresh_CAMB_posterior_preparation/final_runtime_verification.json').read_text())['records']}
    entries = []
    for key in ['guarded_solver_posterior_trials', 'guarded_quadrature_posterior_chains', 'guarded_medium_posterior_chains', 'guarded_grid12_posterior_trials']:
        entries += state[key]
    records = []
    for e in entries + state['fresh_CAMB_posterior_chains']:
        seed = e['seed']
        pid = e['pid']
        proc = Path('/proc', str(pid))
        prior = e if seed >= 1700 else old[seed]
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        assert stat[0] != 'Z' and int(stat[19]) == prior['process_start_ticks']
        command = (proc / 'cmdline').read_bytes().replace(b'\x00', b' ').decode()
        assert command == prior['command']
        module = e['module'] if seed >= 1700 else prior['module']
        assert module in (proc / 'maps').read_text() and sha(module) == e['native_module_sha256']
        run = ROOT / e['run_dir']
        assert not (run / 'stderr.txt').read_bytes()
        if seed >= 1700:
            assert not (ROOT / f'runs/20261004_math_review_fresh_CAMB_posterior_preparation/seed{seed}/launcher_stderr.txt').read_bytes()
            assert sha(ROOT / e['config']) == e['config_sha256'] and sha(run / 'resolved.yaml') == e['effective_config_sha256']
        progress = re.findall('Progress @ ([^\\n]+) : (\\d+) steps taken, and (\\d+) accepted', (run / 'stdout.txt').read_text())
        record = {'seed': seed, 'pid': pid, 'process_start_ticks': prior['process_start_ticks'], 'command': command, 'module': module, 'module_sha256': sha(module), 'status': 'live_same_owned_native_identity'}
        if progress:
            utc, steps, accepted = progress[-1]
            record['latest_progress'] = {'utc': utc, 'steps': int(steps), 'accepted': int(accepted)}
        chain = next((run / 'chains').glob('*.1.txt'))
        raw = chain.read_bytes()
        raw = raw[:raw.rfind(b'\n') + 1]
        weights = [Fraction(l.split()[0]) for l in raw.decode().splitlines() if l.strip() and (not l.startswith('#'))]
        assert all((w > 0 and w.denominator == 1 for w in weights))
        record['retained_represented_steps'] = sum((int(w) for w in weights[len(weights) // 5:]))
        record['group'] = e.get('group')
        records.append(record)
    assert len(records) == len({r['pid'] for r in records}) == 40
    retired = json.loads((ROOT / 'runs/20261004_math_review_fresh_CAMB_posterior_preparation/old_policy_retirement_receipt.json').read_text())
    for r in retired['records']:
        assert not Path('/proc', str(r['pid'])).exists()
    thresholds = {'quad_A': ([1301, 1302, 1303, 1304], 4991), 'quad_B': ([1305, 1306, 1307, 1308], 4114), 'medium_A': ([1201, 1401, 1402, 1406], 1180), 'medium_B': ([1403, 1404, 1405, 1407], 977), 'grid12_B': ([1501, 1502, 1503, 1504], 1000)}
    for cohort in ['quad_A', 'quad_B', 'medium_A', 'medium_B']:
        seeds, unused = thresholds[cohort]
        thresholds[cohort] = (seeds, state['guarded_CLASS_next_assessment_minimum_history'][cohort])
    for group in ['old_A3200', 'old_B4095', 'current_A4095', 'current_B4095', 'current_A3200']:
        assessment = state.get('fresh_CAMB_production_assessments', {}).get(group)
        threshold = assessment['next_minimum_history'] if assessment else 1000
        thresholds[group] = ([r['seed'] for r in records if r['group'] == group], threshold)
    growth = {}
    for group, (seeds, threshold) in thresholds.items():
        subset = [r for r in records if r['seed'] in seeds]
        assert len(subset) == 4
        minimum = min((r['retained_represented_steps'] for r in subset))
        growth[group] = {'seeds': seeds, 'minimum_saved_postburn_history': minimum, 'next_assessment_trigger': threshold, 'due': minimum >= threshold}
        print(group, minimum, 'trigger', threshold, 'due', minimum >= threshold)
    return {'utc': datetime.now(timezone.utc).isoformat(), 'records': records, 'owned_live_samplers': 40, 'fresh_CAMB_SPT_live': 20, 'guarded_CLASS_live': 20, 'old_policy_CAMB_SPT_live': 0, 'all_16_old_policy_processes_absent': True, 'posterior_convergence_certified': False, 'growth_by_cohort': growth}

from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
primary = observe_primary()
assert primary['owned_live_samplers'] == 40
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
entries = state['upper_prior_posterior_chains']
assert len(entries) == 8
wide_records = []
for e in entries:
    proc = Path('/proc', str(e['pid']))
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert stat[0] != 'Z' and int(stat[19]) == e['process_start_ticks']
    assert os.getpriority(os.PRIO_PROCESS, e['pid']) == e['scheduling_nice'] == 5
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    assert command == e['command']
    assert e['module'] in (proc / 'maps').read_text() and sha(e['module']) == e['module_sha256']
    assert sha(e['wrapper']) == e['wrapper_sha256']
    for path, digest in e['implementation_sha256'].items(): assert sha(ROOT / path) == digest
    run = ROOT / e['run_dir']
    assert sha(ROOT / e['config']) == e['config_sha256']
    assert sha(run / 'resolved.yaml') == e['effective_config_sha256']
    assert sha(run / 'solver_backend.json') == e['native_backend_receipt_sha256']
    assert not (run / 'stderr.txt').read_bytes()
    assert not (ROOT / e['launch_receipt']).with_name('launcher_stderr.txt').read_bytes()
    proof = json.loads((ROOT / e['first_saved_row_receipt']).read_text())
    assert proof['native_row_verified'] and proof['module_sha256'] == e['module_sha256']
    chain = next((run / 'chains').glob('*.1.txt'))
    raw = chain.read_bytes(); raw = raw[:raw.rfind(b'\n') + 1]
    assert raw.startswith((ROOT / proof['frozen']).read_bytes())
    weights = [Fraction(line.split()[0]) for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
    assert weights and all(w > 0 and w.denominator == 1 for w in weights)
    progress = re.findall(r'Progress @ ([^\n]+) : (\d+) steps taken, and (\d+) accepted', (run / 'stdout.txt').read_text())
    record = {'seed': e['seed'], 'pid': e['pid'], 'process_start_ticks': e['process_start_ticks'],
              'command': command, 'module': e['module'], 'module_sha256': e['module_sha256'],
              'status': 'live_same_owned_native_identity', 'group': e['group'], 'scheduling_nice': 5,
              'retained_represented_steps': sum(int(w) for w in weights[len(weights) // 5:])}
    if progress:
        utc, steps, accepted = progress[-1]
        record['latest_progress'] = {'utc': utc, 'steps': int(steps), 'accepted': int(accepted)}
    wide_records.append(record)
records = primary['records'] + wide_records
assert len(records) == len({r['pid'] for r in records}) == len({r['seed'] for r in records}) == 48
growth = dict(primary['growth_by_cohort'])
for group in ['upper20_A4095', 'upper20_B4095']:
    subset = [r for r in wide_records if r['group'] == group]
    assert len(subset) == 4
    assessment = state.get('upper_prior_production_assessments', {}).get(group)
    threshold = assessment['next_minimum_history'] if assessment else 1000
    minimum = min(r['retained_represented_steps'] for r in subset)
    growth[group] = {'seeds': [r['seed'] for r in subset], 'minimum_saved_postburn_history': minimum,
                     'next_assessment_trigger': threshold, 'due': minimum >= threshold}
    print(group, minimum, 'trigger', threshold, 'due', minimum >= threshold)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'records': records, 'owned_live_samplers': 48,
       'primary_owned_live_samplers': 40, 'upper_prior_owned_live_samplers': 8,
       'fresh_CAMB_SPT_live': 28, 'guarded_CLASS_live': 20, 'old_policy_CAMB_SPT_live': 0,
       'all_16_old_policy_processes_absent': True, 'growth_by_cohort': growth,
       'posterior_convergence_certified': False, 'prior_insensitivity_certified': False}
with (HERE / 'all_runtime_verification.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('48 original owned native identities verified: 40 primary and 8 wider-prior controls.')
