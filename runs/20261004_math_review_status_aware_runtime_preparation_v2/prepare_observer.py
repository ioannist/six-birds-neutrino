from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source = ROOT / 'runs/20261004_math_review_retired_PID_identity_repair/observe_all_runtime.py'
assert sha(source) == 'd3b14ba547bac2fbb2914ab5b6136257b297fc060ab7a06d9e7a96762a9fa7a8'
terminal_path = ROOT / 'runs/20261004_math_review_upper_prior_seed2003_native_failure_v2/terminal_receipt.json'
terminal_sha = sha(terminal_path)
terminal_review = terminal_path.with_name('self_review_receipt.json')
changes = []
text = source.read_text()
def change(old, new):
    global text
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    changes.append([old, new])

branch = '''    if e['seed'] == 2003:
        terminal_path = ROOT / 'runs/20261004_math_review_upper_prior_seed2003_native_failure_v2/terminal_receipt.json'
        assert sha(terminal_path) == TERMINAL_SHA
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
        assert sha(terminal_path.with_name('self_review_receipt.json')) == TERMINAL_REVIEW_SHA
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
'''.replace('TERMINAL_REVIEW_SHA', repr(sha(terminal_review))).replace('TERMINAL_SHA', repr(terminal_sha))
change("for e in entries:\n    proc = Path('/proc', str(e['pid']))",
       "for e in entries:\n" + branch + "    proc = Path('/proc', str(e['pid']))")
change("records = primary['records'] + wide_records",
       "assert sum(r['status'] == 'live_same_owned_native_identity' for r in wide_records) == 7\n"
       "assert [r['seed'] for r in wide_records if r['status'] == 'terminal_native_failure_preserved'] == [2003]\n"
       "records = primary['records'] + wide_records")
change("    growth[group] = {'seeds': [r['seed'] for r in subset], 'minimum_saved_postburn_history': minimum,\n"
       "                     'next_assessment_trigger': threshold, 'due': minimum >= threshold}",
       "    complete_live_family = all(r['status'] == 'live_same_owned_native_identity' for r in subset)\n"
       "    growth[group] = {'seeds': [r['seed'] for r in subset], 'minimum_saved_postburn_history': minimum,\n"
       "                     'next_assessment_trigger': threshold, 'due': minimum >= threshold and complete_live_family,\n"
       "                     'assessment_eligible': complete_live_family,\n"
       "                     'terminal_family_seeds': [r['seed'] for r in subset if r['status'] != 'live_same_owned_native_identity']}" )
change("\n    print(group, minimum, 'trigger', threshold, 'due', minimum >= threshold)",
       "\n    print(group, minimum, 'trigger', threshold, 'due', growth[group]['due'], 'eligible', complete_live_family)")
change("'records': records, 'owned_live_samplers': 48,",
       "'records': records, 'registered_sampler_families': 48, 'owned_live_samplers': 47, 'terminal_sampler_families': 1,")
change("'primary_owned_live_samplers': 40, 'upper_prior_owned_live_samplers': 8,",
       "'primary_owned_live_samplers': 40, 'upper_prior_owned_live_samplers': 7,")
change("'fresh_CAMB_SPT_live': 28,", "'fresh_CAMB_SPT_live': 27,")
change("print('48 original owned native identities verified: 40 primary and 8 wider-prior controls.')",
       "print('48 registered families accounted for: 40 primary and 7 wider-prior live; seed2003 explicitly terminal.')")
reverse = text
for old, new in reversed(changes):
    assert reverse.count(new) == 1
    reverse = reverse.replace(new, old, 1)
assert reverse.encode() == source.read_bytes()
with (HERE / 'observe_all_runtime.py').open('x') as f:
    f.write(text)
with (HERE / 'preparation_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'source': str(source.relative_to(ROOT)),
                       'source_sha256': sha(source), 'observer_sha256': sha(HERE / 'observe_all_runtime.py'),
                       'terminal_receipt_sha256': terminal_sha, 'terminal_self_review_sha256': sha(terminal_review),
                       'changes': changes, 'reverse_byte_identity': True,
                       'all_primary40_and_remaining_wide_live_checks_preserved': True,
                       'all48_families_accounted_for': True, 'terminal_failure_does_not_count_as_live_or_rejection': True},
                      indent=2, allow_nan=False) + '\n')
print('Status-aware observer prepared; terminal family preserved and native qualification remains false.')
