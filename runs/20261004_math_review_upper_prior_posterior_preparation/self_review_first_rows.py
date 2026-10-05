"""Recount all closed first-row controls and frozen numerical witnesses."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries=json.loads((HERE/'preparation_receipt.json').read_text())['entries']
by_seed={e['seed']:e for e in entries}
checked=[]
for group in sorted({e['group'] for e in entries}):
    receipt_path=HERE/f'first_rows_{group}_verification.json'
    receipt=json.loads(receipt_path.read_text())
    assert receipt['group']==group and receipt['first_saved_native_rows_verified']==4
    assert not Path('/proc',str(receipt['worker_pid'])).exists()
    assert not (HERE/f'first_rows_{group}_stderr.txt').read_bytes()
    for record in receipt['records']:
        e=by_seed[record['seed']]
        assert record['group']==e['group'] and record['module_sha256']==e['module_sha256']
        assert record['native_row_verified'] and record['FreshCAMB_exact_to_independent_upstream_fresh']
        assert record['native_row_replay_tolerance']==1e-9
        assert max(abs(v) for v in record['native_row_replay_discrepancies'].values())<=1e-9
        snapshot=ROOT/record['frozen'];raw=snapshot.read_bytes()
        assert sha(snapshot)==record['snapshot_sha256'] and (ROOT/record['source']).read_bytes().startswith(raw)
        header=raw.decode().splitlines()[0].lstrip('#').split()
        assert len(header)==len(set(header))
        data=np.loadtxt(snapshot,ndmin=2)
        assert data.shape==(1,len(header)) and np.isfinite(data).all()
        row=dict(zip(header,data[0]));assert row['weight']==record['holding_time']>0
        assert row['weight'].is_integer()
        assert {n:row[n] for n in e['initial_point']}==record['point']
        out=ROOT/record['out']
        backend=json.loads((out/'solver_backend.json').read_text())
        assert backend['module_sha256']==e['module_sha256'] and backend['solver_version']==e['solver_version']
        resolved=yaml.safe_load((out/'resolved.yaml').read_text())
        updated=yaml.safe_load(next((out/'chains').glob('*.updated.yaml')).read_text())
        assert resolved['theory']['camb']['class']==updated['theory']['camb']['class']=='sbt_spt_audit.boltzmann.FreshCAMB'
        assert updated['theory']['camb']['version']==e['solver_version']
        assert resolved['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed']==e['seed']
        assert json.loads((out/'completion_receipt.json').read_text())==record
        checked.append({'seed':record['seed'],'group':group,'first_saved_row_sha256':sha(snapshot),
            'group_receipt_sha256':sha(receipt_path),'maximum_replay_discrepancy':max(abs(v) for v in record['native_row_replay_discrepancies'].values())})
assert len(checked)==8 and {r['seed'] for r in checked}==set(by_seed)
with (HERE/'first_rows_self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'self_review_no_independent_agent',
        'checked':checked,'first_native_rows_verified':8,'distinct_targets':2,
        'all_finite_verification_workers_absent':True,'posterior_convergence_or_uniform_accuracy_certified':False,
        'histories_pooled':False},indent=2,allow_nan=False)+'\n')
print('All 8 first native rows and metadata recounted; both finite workers absent.')
