"""Challenge source-contract transitions before adopting the updated workflow."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from contract_compatibility import require_compatible_previous

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
current = json.loads((HERE / 'assessment_contract.json').read_text())
current_sha = sha(HERE / 'assessment_contract.json')
preparation = json.loads((HERE / 'preparation_receipt.json').read_text())
previous_sha = preparation['source_contract_sha256']
require_compatible_previous(current, current_sha, previous_sha, ROOT)
for predecessor in preparation['predecessor_contract_sha256']:
    require_compatible_previous(current, current_sha, predecessor, ROOT)
require_compatible_previous(current, current_sha, current_sha, ROOT)
assert current['first_minimum_retained_represented_steps'] == 1000
assert current['later_growth_factor'] == [6, 5]
assert current['absolute_mass_quantile_MCSE_limit'] == .001

cases = {}
for name in ['native_identity', 'configuration_identity', 'first_history_trigger',
             'later_growth_factor', 'native_replay_tolerance', 'unreviewed_reader',
             'extra_source_permission', 'validation_receipt_hash']:
    altered = deepcopy(current)
    if name == 'native_identity':
        altered['groups']['current_A3200'][0]['module_sha256'] = '0'*64
    elif name == 'configuration_identity':
        altered['groups']['current_A3200'][0]['config_sha256'] = '0'*64
    elif name == 'first_history_trigger':
        altered['first_minimum_retained_represented_steps'] = 8
    elif name == 'later_growth_factor':
        altered['later_growth_factor'] = [11, 10]
    elif name == 'native_replay_tolerance':
        altered['native_replay_atol'] = .002
    elif name == 'unreviewed_reader':
        altered['diagnostic_source_sha256']['scripts/diagnose_cobaya_chains.py'] = '0'*64
    elif name == 'extra_source_permission':
        altered['compatible_predecessor_contracts'][previous_sha]['allowed_reader_source_updates'].append('src/sbt_spt_audit/mcmc.py')
    else:
        altered['compatible_predecessor_contracts'][previous_sha]['validation_receipt_sha256'] = '0'*64
    try:
        require_compatible_previous(altered, current_sha, previous_sha, ROOT)
    except ValueError as error:
        cases[name] = str(error)
    else:
        raise AssertionError(f'Unsafe predecessor transition accepted: {name}')
try:
    require_compatible_previous(current, current_sha, '0'*64, ROOT)
except ValueError as error:
    cases['unknown_predecessor'] = str(error)
else:
    raise AssertionError('Unknown predecessor accepted')
assert len(cases) == 9

record = current['compatible_predecessor_contracts'][previous_sha]
replay = json.loads((ROOT / record['validation_receipt']).read_text())
assert len(replay['records']) == 9 and replay['all_requested_reports_identical']
for report in replay['records']:
    old, new = ROOT / report['original'], ROOT / report['replayed']
    assert sha(old) == report['original_sha256'] and sha(new) == report['replayed_sha256']
    assert json.loads(old.read_text()) == json.loads(new.read_text())
for prepared in preparation['scripts']:
    assert sha(ROOT / prepared['source']) == prepared['source_sha256']
    assert sha(ROOT / prepared['prepared']) == prepared['prepared_sha256']
for script in ['prepare_snapshot.py', 'verify_native_rows.py', 'run_diagnostic.py',
               'verify_snapshot.py', 'contract_compatibility.py']:
    compile((HERE / script).read_text(), str(HERE / script), 'exec')
growth = json.loads((HERE / 'growth_branch_receipt.json').read_text())
assert len(growth['records']) == 5
outcomes = {}
for entry in growth['records']:
    assert entry['exit_code'] in [0, 3]
    assert not (HERE / ('growth_'+entry['group']+'_stderr.txt')).read_bytes()
    output = ROOT / entry['outdir']
    if entry['exit_code'] == 3:
        assert not output.exists()
        observed = json.loads((HERE / ('growth_'+entry['group']+'_stdout.txt')).read_text())
        assert not observed['snapshot_written']
        assert observed['minimum_retained_represented_steps'] < observed['threshold']
        outcomes[entry['group']] = observed
    else:
        receipt = json.loads((output / 'snapshot_receipt.json').read_text())
        assert receipt['contract_sha256'] == current_sha
        assert receipt['minimum_retained_represented_steps'] >= receipt['assessment_trigger']
        outcomes[entry['group']] = {'snapshot_written': True,
                                   'minimum_retained_represented_steps': receipt['minimum_retained_represented_steps'],
                                   'threshold': receipt['assessment_trigger']}
with (HERE / 'preparation_self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                       'reviewer': 'distinct_self_review_not_independent_agent',
                       'current_contract_sha256': current_sha,
                       'verified_predecessor_contract_sha256': preparation['predecessor_contract_sha256'],
                       'nine_unsafe_transitions_refused': cases,
                       'nine_latest_reports_recounted_equal': True,
                       'five_real_growth_branches': outcomes,
                       'physical_targets_native_identities_and_gates_unchanged': True,
                       'growth_counter_reset': False,
                       'posterior_qualified': False,
                       'workflow_source_sha256': {p.name: sha(p) for p in HERE.glob('*.py')}},
                      indent=2, allow_nan=False) + '\n')
print('Predecessor transition self-review passes: nine unsafe changes refused and nine reports unchanged.')
