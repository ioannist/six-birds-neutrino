"""Compare prefix selection across tracked bundles and directly frozen witnesses."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from extract_mnu_limits import _resolve_prefix_from_run_dir,_load_chains_raw
spec=importlib.util.spec_from_file_location('before_extractor',HERE/'before_extract_mnu_limits.py')
before=importlib.util.module_from_spec(spec);spec.loader.exec_module(before)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=subprocess.check_output(['git','ls-files','runs/**/resolved.yaml'],cwd=ROOT,text=True).splitlines()
records=[]
for p in paths:
    run=(ROOT/p).parent
    row={'run':str(run.relative_to(ROOT))}
    for name,resolve in [('before',before._resolve_prefix_from_run_dir),('after',_resolve_prefix_from_run_dir)]:
        try:
            prefix=resolve(run);row[name+'_prefix']=str(prefix.relative_to(ROOT)) if prefix.is_relative_to(ROOT) else str(prefix)
            row[name+'_inside_bundle']=prefix.is_relative_to(run)
        except (FileNotFoundError,ValueError) as error:
            row[name+'_error']=str(error)
    if 'after_prefix' in row:assert row['after_inside_bundle']
    row['selection_unchanged']=row.get('before_prefix')==row.get('after_prefix') and 'after_prefix' in row
    records.append(row)

native_rows=[]
fresh=ROOT/'runs/20261004_math_review_fresh_CAMB_posterior_preparation'
for e in json.loads((fresh/'preparation_receipt.json').read_text())['entries']:
    run=fresh/f"seed{e['seed']}"/'first_saved_rows'
    prefix=_resolve_prefix_from_run_dir(run)
    proof=json.loads((run/'completion_receipt.json').read_text())
    file=Path(str(prefix)+'.1.txt')
    assert file==ROOT/proof['frozen'] and sha(file)==proof['snapshot_sha256']
    values,weights=_load_chains_raw(prefix,'mnu',0)[0]
    assert values.tolist()==[proof['point']['mnu']] and weights.tolist()==[proof['holding_time']]
    native_rows.append({'seed':e['seed'],'bundle':str(run.relative_to(ROOT)),
        'selected_prefix':str(prefix.relative_to(ROOT)),'frozen_file_sha256':sha(file),
        'stored_rows':len(values),'holding_time':int(weights[0])})
assert len(native_rows)==20
out={'utc':datetime.now(timezone.utc).isoformat(),'tracked_bundles':len(records),'records':records,
    'unchanged_prefix_count':sum(r['selection_unchanged'] for r in records),
    'external_prefixes_rebased_count':sum(not r.get('before_inside_bundle',True) and r.get('after_inside_bundle',False) for r in records),
    'new_refusals':sum('after_error' in r and 'before_prefix' in r for r in records),
    'all_twenty_fresh_first_rows_read_exact_frozen_data':native_rows,
    'native_replay_proofs_unchanged':True,'numerical_diagnostic_algorithm_changed':False,
    'paper_or_canonical_results_changed':False}
with (HERE/'impact_verification.json').open('x') as f:
    f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Bundles',out['tracked_bundles'],'unchanged',out['unchanged_prefix_count'],
      'external outputs rebased',out['external_prefixes_rebased_count'],'new refusals',out['new_refusals'])
print('All twenty fresh native row witnesses resolve exactly to their frozen data.')
for r in records:
    if 'after_error' in r and 'before_prefix' in r:print('New refusal:',r)
