"""Resolve swapped completion labels using original tool launch and exit records."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
# Redacted before publication: the original reads a private local AI-agent session log.
LOG = Path('<private agent session log>')
launch, terminal, replies = None, None, {}
for line_number, line in enumerate(LOG.open(), 1):
    try:
        item = json.loads(line, strict=False)
    except json.JSONDecodeError:
        continue
    if item.get('type') != 'response_item':
        continue
    payload = item['payload']
    if line_number == 1716:
        assert payload['type'] == 'custom_tool_call'
        launch = {'line': line_number, 'utc': item['timestamp'], 'call_id': payload['call_id'],
                  'input': payload['input']}
    if payload.get('call_id') == '<redacted call id>' and payload['type'] == 'custom_tool_call':
        terminal = {'line': line_number, 'utc': item['timestamp'], 'call_id': payload['call_id'],
                    'input': payload['input']}
    if payload['type'] == 'custom_tool_call_output':
        cid = payload['call_id']
        if (launch and cid == launch['call_id']) or (terminal and cid == terminal['call_id']):
            values = []
            for block in payload['output']:
                try:
                    value = json.loads(block.get('text', ''))
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    if value.get('status') == 'fulfilled':
                        value = value['value']
                    values.append(value)
            replies[cid] = {'line': line_number, 'utc': item['timestamp'], 'values': values}
    if launch and terminal and launch['call_id'] in replies and terminal['call_id'] in replies:
        break
assert launch and terminal
jobs = [v for v in replies[launch['call_id']]['values'] if 'seed' in v]
assert [(j['seed'], j['session_id']) for j in jobs] == [(401, 44762), (402, 92240), (403, 19631), (404, 26652)]
assert 'const jobs=[[\'A\',401],[\'A\',402],[\'B\',403],[\'B\',404]]' in launch['input']
assert terminal['input'].index('session_id:92240') < terminal['input'].index('session_id:44762')
exits = replies[terminal['call_id']]['values'][:2]
assert len(exits) == 2
assert all(e['exit_code'] == 0 for e in exits)
receipt_path = ROOT / 'runs/20261004_math_review_spt_sample_cap_completion/completion_receipt.json'
old = json.loads((HERE / 'prior_completion_receipt.json').read_text())
current_receipt = json.loads(receipt_path.read_text())
corrections = []
for entry in old['records']:
    seed = entry['seed']
    job = next(j for j in jobs if j['seed'] == seed)
    runtime = json.loads((ROOT / entry['frozen_bundle'] / 'runtime_state.json').read_text())
    assert runtime['exec_session'] == job['session_id']
    assert entry['managed_session'] != job['session_id']
    for file in entry['files']:
        path = receipt_path.parent / file['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == file['sha256']
    corrections.append({'seed': seed, 'prior_mislabeled_session': entry['managed_session'],
                        'verified_original_session': job['session_id'], 'managed_exit_code': 0,
                        'runtime_scientific_pid': runtime['pid'], 'scientific_bundle_hashes_unchanged': True})
    entry['managed_session'] = job['session_id']
old['session_label_correction'] = str((HERE / 'correction_receipt.json').relative_to(ROOT))
assert current_receipt in [json.loads((HERE / 'prior_completion_receipt.json').read_text()), old]
if current_receipt != old:
    receipt_path.write_text(json.dumps(old, indent=2, allow_nan=False) + '\n')
evidence = {'launch_call': launch, 'launch_reply': replies[launch['call_id']],
            'terminal_call': terminal, 'terminal_reply_metadata': exits,
            'terminal_reply_utc': replies[terminal['call_id']]['utc']}
if (HERE / 'primary_tool_evidence.json').exists():
    assert json.loads((HERE / 'primary_tool_evidence.json').read_text()) == evidence
else:
    (HERE / 'primary_tool_evidence.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
result = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'completion_receipt_seed_to_session_label_correction',
          'corrections': corrections, 'source': 'original launch and terminal tool records in this thread',
          'prior_receipt_sha256': hashlib.sha256((HERE / 'prior_completion_receipt.json').read_bytes()).hexdigest(),
          'corrected_receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
          'primary_tool_evidence_sha256': hashlib.sha256((HERE / 'primary_tool_evidence.json').read_bytes()).hexdigest(),
          'scientific_data_or_diagnostics_changed': False, 'historical_mislabeled_receipt_preserved': True}
if (HERE / 'correction_receipt.json').exists():
    previous = json.loads((HERE / 'correction_receipt.json').read_text())
    assert {k:v for k,v in previous.items() if k != 'utc'} == {k:v for k,v in result.items() if k != 'utc'}
else:
    (HERE / 'correction_receipt.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('Original launch and terminal records confirm 401=44762 and 402=92240; both exits zero.')
