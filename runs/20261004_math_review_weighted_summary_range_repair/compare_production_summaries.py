"""Compare every frozen production family against the preserved old reader."""
from datetime import datetime,timezone
import hashlib,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
import yaml
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import extract_mnu_limits as current
spec=importlib.util.spec_from_file_location('preserved_reader',HERE/'before_extract_mnu_limits.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
selected=[]
for group,root in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items():
 r=json.loads((ROOT/root/'snapshot_receipt.json').read_text())
 selected.extend((group,ROOT/f['snapshot'],'mnu_sample') for f in r['files'])
for group,a in state['fresh_CAMB_production_assessments'].items():
 r=json.loads((ROOT/a['root']/'snapshot_receipt.json').read_text())
 selected.extend((group,Path(f['snapshot']),'mnu') for f in r['families'])
assert len(selected)==36
records=[]
for group,chain,param in selected:
 prefix=chain.with_suffix('').with_suffix('')
 cfg=yaml.safe_load((chain.parent.parent/'resolved.yaml').read_text())
 assert cfg['params'][param]['prior']['min']==0
 before=old._load_chains_raw(prefix,param,.2)
 after=current._load_chains_raw(prefix,param,.2)
 assert len(before)==len(after)==1
 v,w=after[0];ov,ow=before[0]
 assert np.array_equal(v,ov) and np.array_equal(w,ow)
 original={'median':old._weighted_quantile(v,w,.5),'p95':old._weighted_quantile(v,w,.95),
           'boundary_fraction':float(w[v<=.001].sum()/w.sum()),'histogram_mode':old._weighted_hist_mode(v,w)}
 repaired={'median':current._weighted_quantile(v,w,.5),'p95':current._weighted_quantile(v,w,.95),
           'boundary_fraction':current._weighted_boundary_fraction(v,w,.001),'histogram_mode':current._weighted_hist_mode(v,w)}
 for k in ['median','p95','boundary_fraction']:assert original[k]==repaired[k],(group,k)
 diff=abs(original['histogram_mode']-repaired['histogram_mode'])
 assert diff<=math.ulp(original['histogram_mode']),(group,'mode',original,repaired)
 records.append({'group':group,'chain':str(chain.relative_to(ROOT)),'chain_sha256':sha(chain),
                 'original':original,'repaired':repaired,'histogram_mode_absolute_difference':diff,
                 'histogram_mode_difference_in_old_ULPs':diff/math.ulp(original['histogram_mode'])})
with (HERE/'production_summary_replay_receipt.json').open('x') as f:
 f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,'families':36,
                    'all_medians_p95_and_boundary_fractions_identical':True,
                    'all_histogram_modes_within_one_ULP':True,
                    'maximum_histogram_mode_change_ULPs':max(r['histogram_mode_difference_in_old_ULPs'] for r in records),
                    'reader_source_sha256':sha(ROOT/'scripts/extract_mnu_limits.py'),
                    'historical_reader_source_sha256':sha(HERE/'before_extract_mnu_limits.py'),
                    'posterior_qualification_inferred':False},indent=2)+'\n')
print('All 36 production medians, p95s and boundary fractions identical; max mode change ULPs',max(r['histogram_mode_difference_in_old_ULPs'] for r in records))
