"""Record exact saved holding times and unchanged assessment triggers."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
state=json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
previous=json.loads((HERE/'runtime_observation.json').read_text())
identity={r['seed']:r for r in previous['records']}
groups={
    'quad_A':[e for e in state['guarded_quadrature_posterior_chains'] if e['lens']=='A'],
    'quad_B':[e for e in state['guarded_quadrature_posterior_chains'] if e['lens']=='B'],
    'medium_A':[e for e in state['guarded_medium_posterior_chains'] if e['lens']=='A']+state['guarded_solver_posterior_trials'],
    'medium_B':[e for e in state['guarded_medium_posterior_chains'] if e['lens']=='B'],
    'grid12_B':state['guarded_grid12_posterior_trials']}
for e in state['fresh_CAMB_posterior_chains']:groups.setdefault(e['group'],[]).append(e)
thresholds={'quad_A':4157,'quad_B':4114,'medium_A':1180,'medium_B':812,'grid12_B':1000}
thresholds.update({e['group']:1000 for e in state['fresh_CAMB_posterior_chains']})
records={}
for group,entries in groups.items():
    families=[]
    for e in entries:
        r=identity[e['seed']];proc=Path('/proc',str(e['pid']))
        stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
        assert stat[0]!='Z' and int(stat[19])==r['process_start_ticks']
        command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert command==r['command']
        assert r['module'] in (proc/'maps').read_text()
        path=next((ROOT/e['run_dir']/'chains').glob('*.1.txt'))
        raw=path.read_bytes();complete=raw[:raw.rfind(b'\n')+1]
        rows=[line.split() for line in complete.decode().splitlines() if line.strip() and not line.startswith('#')]
        weights=[Fraction(row[0]) for row in rows]
        assert all(w.denominator==1 and w>0 for w in weights)
        represented=sum(int(w) for w in weights[len(weights)//5:])
        families.append({'seed':e['seed'],'pid':e['pid'],'stored_complete_rows':len(rows),
            'retained_represented_steps':represented,'read_complete_prefix_bytes':len(complete),
            'read_prefix_sha256':hashlib.sha256(complete).hexdigest()})
    minimum=min(r['retained_represented_steps'] for r in families)
    records[group]={'families':families,'minimum_retained_represented_steps':minimum,
        'next_assessment_threshold':thresholds[group],'assessment_due':minimum>=thresholds[group]}
with (HERE/'growth_observation.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,
        'owned_live_samplers_verified':sum(len(v['families']) for v in records.values()),
        'burnin_fraction_of_stored_rows':.2,'grid12_first_assessment_trigger_declared':1000,
        'trigger_role':'work scheduling only; unchanged diagnostic acceptance gates',
        'posterior_convergence_certified':False},indent=2,allow_nan=False)+'\n')
print(json.dumps({g:{k:v[k] for k in ['minimum_retained_represented_steps','next_assessment_threshold','assessment_due']} for g,v in records.items()},indent=2))
