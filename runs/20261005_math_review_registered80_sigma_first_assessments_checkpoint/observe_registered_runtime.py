"""Account for every registration, keeping unknown exits separate from native failures."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
baseline_path = ROOT / 'runs/20261005_math_review_sigma_time_v3_checkpoint/all_runtime_verification.json'
baseline = json.loads(baseline_path.read_text())
prior = {r['seed']: r for r in baseline['records']}
helper = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/retirement_identity.py'
assert sha(helper) == '962ff3e07cddcd5711284bdaecf19ab9b7581674754a57f46fd6ad9e03fac620'
spec = importlib.util.spec_from_file_location('registered_identity', helper)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
keys = ['guarded_solver_posterior_trials', 'guarded_quadrature_posterior_chains',
        'guarded_medium_posterior_chains', 'guarded_grid12_posterior_trials',
        'fresh_CAMB_posterior_chains', 'upper_prior_posterior_chains', 'native_candidate_posterior_chains', 'guarded_CLASS_fresh_recovery_trials', 'CLASS_recovery_companion_posterior_chains', 'CLASS_fresh_B_posterior_chains']
entries = [e for key in keys for e in state[key]]
assert len(entries) == len({e['seed'] for e in entries}) == 80
records = []
for e in entries:
    owned = prior[e['seed']] if e['seed'] < 2100 else e
    if e.get('status', '').startswith('terminal_'):
        terminal_path = ROOT / e['terminal_receipt']
        assert sha(terminal_path) == e['terminal_receipt_sha256']
        terminal = json.loads(terminal_path.read_text())
        absent = identity.observe_retired_identity(e['pid'], owned['process_start_ticks'])
        assert absent['original_identity_absent']
        for file in terminal['terminal_output_files']:
            assert sha(ROOT / file['source']) == sha(ROOT / file['frozen']) == file['sha256']
        unknown = terminal.get('exit_reason', 'native_failure') is None
        if unknown:
            assert terminal['exit_code'] is None and not terminal['native_failure_established']
        else:
            assert terminal['exit_code'] == 1
        records.append({'seed': e['seed'], 'pid': e['pid'], 'process_start_ticks': owned['process_start_ticks'],
            'status': 'terminal_exit_reason_unavailable_preserved' if unknown else 'terminal_native_failure_preserved',
            'terminal_receipt': e['terminal_receipt'], 'terminal_receipt_sha256': sha(terminal_path),
            'identity_observation': absent, 'exit_code': terminal['exit_code'],
            'retained_represented_steps': terminal.get('retained_represented_steps', owned['retained_represented_steps']),
            'posterior_qualified': False, 'native_error_is_posterior_rejection': False})
        continue
    proc = Path('/proc', str(e['pid']))
    stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    assert stat[0] != 'Z' and int(stat[19]) == owned['process_start_ticks']
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    assert command == owned['command']
    module = owned['module']
    assert module in (proc / 'maps').read_text() and sha(module) == owned['module_sha256']
    run = ROOT / e['run_dir']
    assert not (run / 'stderr.txt').read_bytes()
    if e.get('config'):
        assert sha(ROOT / e['config']) == e['config_sha256']
        assert sha(run / 'resolved.yaml') == e['effective_config_sha256']
        assert sha(run / 'solver_backend.json') == e['native_backend_receipt_sha256']
    if e['seed'] >= 2100:
        assert e.get('first_saved_row_receipt')
    if e['seed'] >= 2100 and e.get('first_saved_row_receipt'):
        proof_path = ROOT / e['first_saved_row_receipt']
        assert sha(proof_path) == e['first_saved_row_receipt_sha256']
        proof = json.loads(proof_path.read_text())
        assert proof['native_row_verified'] and proof['module_sha256'] == e['module_sha256']
        activation_name = ('sigma_time_v3_posterior_activation' if e['seed'] < 2200 else
                           'CLASS_fresh_recovery_activation' if e['seed'] < 2300 else
                           'CLASS_recovery_cohort_activation' if e['seed'] < 2400 else
                           'CLASS_fresh_B_activation')
        assert not (ROOT / f'runs/20261005_math_review_{activation_name}' / f'seed{e["seed"]}' / 'launcher_stderr.txt').read_bytes()
    chain = next((run / 'chains').glob('*.1.txt'), None)
    assert chain is not None
    raw = chain.read_bytes() if chain is not None else b''
    raw = raw[:raw.rfind(b'\n') + 1]
    weights = [Fraction(line.split()[0]) for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
    assert weights and all(w > 0 and w.denominator == 1 for w in weights)
    records.append({'seed': e['seed'], 'pid': e['pid'], 'process_start_ticks': owned['process_start_ticks'],
        'command': command, 'module': module, 'module_sha256': sha(module), 'status': 'live_same_owned_native_identity',
        'retained_represented_steps': sum(int(w) for w in weights[len(weights) // 5:]),
        'group': e.get('group'), 'posterior_qualified': False})
by_seed = {r['seed']: r for r in records}
growth = {}
groups = {k: v['seeds'] for k, v in baseline['growth_by_cohort'].items()}
groups.update({g: [e['seed'] for e in entries if e.get('group') == g]
               for g in {e['group'] for e in state['native_candidate_posterior_chains']}})
groups.update({g: c['seeds'] for g, c in state['fresh_CLASS_recovery_cohorts'].items()})
for group, seeds in groups.items():
    assert len(seeds) == 4
    subset = [by_seed[seed] for seed in seeds]
    terminal = [r['seed'] for r in subset if r['status'] != 'live_same_owned_native_identity']
    trigger = baseline['growth_by_cohort'].get(group, {}).get('next_assessment_trigger', 1000)
    matches = [state.get(key, {})[group] for key in ['fresh_CAMB_production_assessments',
               'native_candidate_production_assessments', 'fresh_CLASS_recovery_production_assessments']
               if group in state.get(key, {})]
    assert len(matches) <= 1
    if matches:
        trigger = matches[0]['next_minimum_history']
    minimum = min(r['retained_represented_steps'] for r in subset)
    growth[group] = {'seeds': seeds, 'minimum_saved_postburn_history': minimum, 'next_assessment_trigger': trigger,
                     'terminal_family_seeds': terminal, 'assessment_eligible': not terminal,
                     'due': not terminal and minimum >= trigger}
assert len(growth) == 20
live = [r for r in records if r['status'] == 'live_same_owned_native_identity']
terminal = [r for r in records if r['status'] != 'live_same_owned_native_identity']
with (HERE / 'combined_runtime_verification.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'records': records, 'registered_families': 80,
        'owned_live_samplers': len(live), 'terminal_families': len(terminal), 'growth_by_cohort': growth,
        'baseline_runtime_sha256': sha(baseline_path), 'terminal_causes_not_inferred': True,
        'recovery_trials_by_target': {g: [e['seed'] for e in state['guarded_CLASS_fresh_recovery_trials'] if e['group']==g] for g in ['medium_A', 'quad_A']},
        'fresh_recovery_cohorts_declared_but_not_qualified': True,
        'posterior_or_prior_stability_certified': False, 'native_error_is_posterior_rejection': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Registered families', len(records), 'live', len(live), 'terminal', len(terminal))
print('Due eligible cohorts', [g for g, v in growth.items() if v['due']])
