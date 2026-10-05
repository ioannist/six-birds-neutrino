"""Freeze a single declared target only after its saved-history trigger passes."""
import argparse
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
from io import BytesIO
import json
from math import ceil
from pathlib import Path
import sys
import numpy as np
import yaml
from contract_compatibility import require_compatible_previous

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract=json.loads((HERE/'assessment_contract.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('group',choices=sorted(contract['groups']))
parser.add_argument('--outdir',type=Path,required=True);parser.add_argument('--previous',type=Path)
args=parser.parse_args();out=args.outdir.resolve();entries=contract['groups'][args.group]
assert len(entries)==4 and len({e['seed'] for e in entries})==4
assert not out.exists()
for path,digest in contract['diagnostic_source_sha256'].items():assert sha(ROOT/path)==digest
previous=json.loads(args.previous.read_text()) if args.previous else None
threshold=contract['first_minimum_retained_represented_steps']
if previous:
    assert previous['group']==args.group
    require_compatible_previous(contract,sha(HERE/'assessment_contract.json'),previous['contract_sha256'],ROOT)
    threshold=ceil(Fraction(*contract['later_growth_factor'])*previous['minimum_retained_represented_steps'])
old_files={r['seed']:r for r in previous['families']} if previous else {}
families=[];cached={}
for e in entries:
    seed=e['seed'];proc=Path('/proc',str(e['pid']))
    stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
    assert stat[0]!='Z' and int(stat[19])==e['process_start_ticks']
    assert (proc/'cmdline').read_bytes().replace(b'\0',b' ').decode()==e['command']
    assert e['module'] in (proc/'maps').read_text() and sha(e['module'])==e['module_sha256']
    for path,digest in e['implementation_sha256'].items():assert sha(ROOT/path)==digest
    run=ROOT/e['run_dir'];assert not (run/'stderr.txt').read_bytes()
    assert sha(ROOT/e['config'])==e['config_sha256'] and sha(run/'resolved.yaml')==e['effective_config_sha256']
    assert sha(run/'input.yaml')==e['config_sha256']
    assert sha(run/'solver_backend.json')==e['native_backend_receipt_sha256']
    source=next((run/'chains').glob('*.1.txt'));raw=source.read_bytes();raw=raw[:raw.rfind(b'\n')+1]
    header=raw.decode().splitlines()[0].lstrip('#').split();assert len(header)==len(set(header)) and header[0]=='weight'
    rows=np.loadtxt(BytesIO(raw),ndmin=2)
    assert len(rows)>=contract['native_rows_per_family']
    assert rows.shape[1]==len(header) and np.isfinite(rows).all()
    assert np.all(rows[:,0]>0) and np.all(rows[:,0]==np.floor(rows[:,0]))
    cfg=yaml.safe_load((run/'resolved.yaml').read_text())
    for name,block in cfg['params'].items():
        if isinstance(block,dict) and 'prior' in block:
            values=rows[:,header.index(name)]
            assert np.all(values>=block['prior']['min']) and np.all(values<=block['prior']['max'])
    weights=[Fraction(line.split()[0]) for line in raw.decode().splitlines() if line.strip() and not line.startswith('#')]
    assert all(w.denominator==1 and w>0 for w in weights)
    retained=sum(int(w) for w in weights[len(weights)//5:])
    if previous:
        old=old_files[seed];prefix=Path(old['snapshot']).read_bytes()
        assert hashlib.sha256(prefix).hexdigest()==old['snapshot_sha256'] and raw.startswith(prefix)
    first=ROOT/e['first_saved_row_receipt'];first_proof=json.loads(first.read_text())
    assert raw.startswith((ROOT/first_proof['frozen']).read_bytes())
    cached[seed]=(raw,cfg,source)
    families.append({'seed':seed,'source':str(source.relative_to(ROOT)),'snapshot':str(out/f'seed{seed}'/'chains'/source.name),
        'snapshot_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'stored_rows':len(rows),
        'retained_represented_steps':retained,'pid':e['pid'],'process_start_ticks':e['process_start_ticks'],
        'native_module_sha256':e['module_sha256'],'solver_version':e['solver_version'],
        'source_resolved_sha256':sha(run/'resolved.yaml'),'source_input_sha256':sha(run/'input.yaml'),
        'source_backend_sha256':sha(run/'solver_backend.json'),
        'first_saved_native_verification_sha256':sha(first)})
minimum=min(r['retained_represented_steps'] for r in families)
if minimum<threshold:
    print(json.dumps({'group':args.group,'minimum_retained_represented_steps':minimum,'threshold':threshold,
        'snapshot_written':False,'scope':'live identity and saved-growth check only'},indent=2));raise SystemExit(3)
out.mkdir(parents=True)
commands=[sys.executable,str(ROOT/'scripts/diagnose_cobaya_chains.py')]
for e in entries:
    raw,cfg,source=cached[e['seed']];run=ROOT/e['run_dir'];dest=out/f"seed{e['seed']}";(dest/'chains').mkdir(parents=True)
    (dest/'chains'/source.name).write_bytes(raw)
    for name in ['input.yaml','solver_backend.json']:(dest/name).write_bytes((run/name).read_bytes())
    updated=source.with_name(source.name.removesuffix('.1.txt')+'.updated.yaml')
    (dest/'chains'/updated.name).write_bytes(updated.read_bytes())
    cfg['output']=str(dest/'chains'/source.name.removesuffix('.1.txt'))
    (dest/'resolved.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    family=next(r for r in families if r['seed']==e['seed'])
    family['snapshot_resolved_sha256']=sha(dest/'resolved.yaml')
    family['snapshot_updated_sha256']=sha(dest/'chains'/updated.name)
    commands+=['--run-dir',str(dest)]
commands+=['--burnin-frac','.2','--quantile-mcse-limit','.001','--relative-quantile-mcse-limit','.05',
           '--output',str(out/'diagnostics.json')]
receipt={'utc':datetime.now(timezone.utc).isoformat(),'group':args.group,'families':families,
    'minimum_retained_represented_steps':minimum,'assessment_trigger':threshold,
    'previous_snapshot_receipt':str(args.previous.resolve()) if args.previous else None,
    'previous_snapshot_sha256':sha(args.previous) if args.previous else None,
    'previous_contract_sha256':previous['contract_sha256'] if previous else None,
    'predecessor_contract_compatibility_checked':bool(previous),
    'contract_sha256':sha(HERE/'assessment_contract.json'),'diagnostic_command':commands,
    'individually_frozen_complete_prefixes_not_atomic_sampler_checkpoint':True,
    'posterior_convergence_certified':False,'targets_pooled':False}
with (out/'snapshot_receipt.json').open('x') as f:f.write(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
print(args.group,'snapshot ready, minimum saved postburn steps',minimum,flush=True)
