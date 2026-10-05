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
    identity_path = ROOT / 'runs/20261004_math_review_fresh_CAMB_posterior_preparation/runtime_before_preparation.json'
    assert sha(identity_path) == 'd066a446fc5d25fb6cb6418071cb62a174649f3ab0cd6e9ca2cd9e2183f6d5ce'
    identity_baseline = {r['seed']: r for r in json.loads(identity_path.read_text())['records']}
    helper_path = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
    assert sha(helper_path) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
    import importlib.util
    identity_spec = importlib.util.spec_from_file_location('review_retirement_identity', helper_path)
    identity_module = importlib.util.module_from_spec(identity_spec)
    identity_spec.loader.exec_module(identity_module)
    retired_identity_observations = []
    for retired_record in retired['records']:
        baseline = identity_baseline[retired_record['seed']]
        assert baseline['pid'] == retired_record['pid']
        if 'process_start_ticks' in retired_record:
            assert baseline['process_start_ticks'] == retired_record['process_start_ticks']
        retired_observation = identity_module.observe_retired_identity(retired_record['pid'], baseline['process_start_ticks'])
        assert retired_observation['original_identity_absent'], 'Original retired process identity remains present.'
        retired_identity_observations.append({'seed': retired_record['seed'], **retired_observation})
    assert len(retired_identity_observations) == len({r['seed'] for r in retired_identity_observations}) == 16
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
    return {'utc': datetime.now(timezone.utc).isoformat(), 'records': records, 'owned_live_samplers': 40, 'fresh_CAMB_SPT_live': 20, 'guarded_CLASS_live': 20, 'old_policy_CAMB_SPT_live': 0, 'all_16_old_policy_process_identities_absent': True, 'retired_identity_observations': retired_identity_observations, 'posterior_convergence_certified': False, 'growth_by_cohort': growth}

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
    if e['seed'] in [2003, 2004]:
        terminal_path = ROOT / {2003: 'runs/20261004_math_review_upper_prior_seed2003_native_failure_v2/terminal_receipt.json', 2004: 'runs/20261004_math_review_upper_prior_seed2004_native_failure/terminal_receipt.json'}[e['seed']]
        assert sha(terminal_path) == {2003: 'a08c9435e740684e57926a56a4105a4e77f233c5c3a803b2a3886f6c7dd02900', 2004: '8a3b35ae7d3ad47469b603c6be6fdcbd9944d10e5f5e64ca331edf1e383f82c1'}[e['seed']]
        terminal = json.loads(terminal_path.read_text())
        assert e['status'] == 'terminal_exit1_nonfinite_TT_spectrum_preserved_recovery_pending'
        assert e['terminal_exit_code'] == terminal['exit_code'] == 1
        assert e['terminal_receipt_sha256'] == sha(terminal_path)
        assert not e['posterior_qualified']
        for key in ['seed', 'pid', 'process_start_ticks', 'group', 'config_sha256',
                    'effective_config_sha256', 'module_sha256', 'wrapper_sha256', 'initial_point']:
            assert e[key] == terminal['registered_entry'][key]
        helper_path = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
        assert sha(helper_path) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
        import importlib.util
        spec = importlib.util.spec_from_file_location('terminal_identity', helper_path)
        identity = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(identity)
        absence = identity.observe_retired_identity(e['pid'], e['process_start_ticks'])
        assert absence['original_identity_absent'], 'Terminal original process identity remains present.'
        for file in terminal['terminal_output_files']:
            assert sha(ROOT / file['source']) == sha(ROOT / file['frozen']) == file['sha256']
        assert sha(terminal_path.with_name('self_review_receipt.json')) == {2003: '0ef19c2fb3d10f34c2f4072e0bf6d96ea8cd70106583250ba164058e4a101977', 2004: '542253ac75087ee23cb0edaedf6bcf6cc2ec4cb5a22c3fc24ec63acf337f55e9'}[e['seed']]
        review = json.loads(terminal_path.with_name('self_review_receipt.json').read_text())
        assert review['terminal_receipt_sha256'] == sha(terminal_path)
        assert not review['posterior_qualified'] and not review['native_failure_is_posterior_rejection']
        wide_records.append({'seed': e['seed'], 'pid': e['pid'], 'process_start_ticks': e['process_start_ticks'],
                             'module': e['module'], 'module_sha256': e['module_sha256'], 'group': e['group'],
                             'status': 'terminal_native_failure_preserved', 'exit_code': 1,
                             'retained_represented_steps': review['retained_represented_steps'],
                             'terminal_receipt': str(terminal_path.relative_to(ROOT)),
                             'terminal_receipt_sha256': sha(terminal_path), 'identity_observation': absence,
                             'posterior_qualified': False, 'native_failure_is_posterior_rejection': False})
        continue
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
assert sum(r['status'] == 'live_same_owned_native_identity' for r in wide_records) == 6
assert [r['seed'] for r in wide_records if r['status'] == 'terminal_native_failure_preserved'] == [2003, 2004]
records = primary['records'] + wide_records
assert len(records) == len({r['pid'] for r in records}) == len({r['seed'] for r in records}) == 48
growth = dict(primary['growth_by_cohort'])
for group in ['upper20_A4095', 'upper20_B4095']:
    subset = [r for r in wide_records if r['group'] == group]
    assert len(subset) == 4
    assessment = state.get('upper_prior_production_assessments', {}).get(group)
    threshold = assessment['next_minimum_history'] if assessment else 1000
    minimum = min(r['retained_represented_steps'] for r in subset)
    complete_live_family = all(r['status'] == 'live_same_owned_native_identity' for r in subset)
    growth[group] = {'seeds': [r['seed'] for r in subset], 'minimum_saved_postburn_history': minimum,
                     'next_assessment_trigger': threshold, 'due': minimum >= threshold and complete_live_family,
                     'assessment_eligible': complete_live_family,
                     'terminal_family_seeds': [r['seed'] for r in subset if r['status'] != 'live_same_owned_native_identity']}
    print(group, minimum, 'trigger', threshold, 'due', growth[group]['due'], 'eligible', complete_live_family)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'records': records, 'registered_sampler_families': 48, 'owned_live_samplers': 46, 'terminal_sampler_families': 2,
       'primary_owned_live_samplers': 40, 'upper_prior_owned_live_samplers': 6,
       'fresh_CAMB_SPT_live': 26, 'guarded_CLASS_live': 20, 'old_policy_CAMB_SPT_live': 0,
       'all_16_old_policy_process_identities_absent': True, 'retired_identity_observations': primary['retired_identity_observations'], 'growth_by_cohort': growth,
       'posterior_convergence_certified': False, 'prior_insensitivity_certified': False}
with (HERE / 'all_runtime_verification.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('48 registered families accounted for: 40 primary and 6 wider-prior live; seeds2003/2004 explicitly terminal.')
