"""Recount frozen data, native components and all unchanged acceptance gates."""
import argparse
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from math import ceil,isfinite
from pathlib import Path
import yaml
from contract_compatibility import require_compatible_previous

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('snapshot',type=Path);args=parser.parse_args()
out=args.snapshot.resolve();receipt=json.loads((out/'snapshot_receipt.json').read_text())
contract=json.loads((HERE/'assessment_contract.json').read_text())
assert receipt['contract_sha256']==sha(HERE/'assessment_contract.json')
entries={e['seed']:e for e in contract['groups'][receipt['group']]}
assert len(receipt['families'])==4 and {f['seed'] for f in receipt['families']}==set(entries)
previous=None
if receipt['previous_snapshot_receipt']:
    previous_path=Path(receipt['previous_snapshot_receipt'])
    assert sha(previous_path)==receipt['previous_snapshot_sha256']
    previous=json.loads(previous_path.read_text())
    assert previous['group']==receipt['group']
    assert receipt['previous_contract_sha256']==previous['contract_sha256']
    require_compatible_previous(contract,sha(HERE/'assessment_contract.json'),previous['contract_sha256'],ROOT)
    expected_trigger=ceil(Fraction(*contract['later_growth_factor'])*previous['minimum_retained_represented_steps'])
    assert receipt['predecessor_contract_compatibility_checked']
else:
    expected_trigger=contract['first_minimum_retained_represented_steps']
assert receipt['assessment_trigger']==expected_trigger
previous_families={f['seed']:f for f in previous['families']} if previous else {}
native=json.loads((out/'native_rows_verification.json').read_text())
assert native['group']==receipt['group'] and native['atol']==1e-9 and native['rtol']==0
assert native['upstream_original_class_forced_fresh']
checks={r['seed']:r for r in native['records']};lengths=[]
for f in receipt['families']:
    e=entries[f['seed']];path=Path(f['snapshot']);raw=path.read_bytes();dest=path.parent.parent
    assert raw.endswith(b'\n') and len(raw)==f['bytes'] and sha(path)==f['snapshot_sha256']
    assert (ROOT/f['source']).read_bytes().startswith(raw)
    assert raw.decode().splitlines()[0].lstrip('#').split()[0]=='weight'
    if previous:
        old=previous_families[f['seed']];prefix=Path(old['snapshot']).read_bytes()
        assert sha(Path(old['snapshot']))==old['snapshot_sha256'] and raw.startswith(prefix)
    rows=[l.split() for l in raw.decode().splitlines() if l.strip() and not l.startswith('#')]
    weights=[Fraction(r[0]) for r in rows];assert len(rows)==f['stored_rows']
    assert all(w.denominator==1 and w>0 for w in weights)
    retained=sum(int(w) for w in weights[len(weights)//5:]);assert retained==f['retained_represented_steps']
    lengths.append(retained)
    assert sha(dest/'resolved.yaml')==f['snapshot_resolved_sha256']
    assert sha(dest/'input.yaml')==f['source_input_sha256'] and sha(dest/'solver_backend.json')==f['source_backend_sha256']
    original=yaml.safe_load((ROOT/e['run_dir']/'resolved.yaml').read_text())
    assert sha(ROOT/e['run_dir']/'resolved.yaml')==f['source_resolved_sha256']
    original['output']=str(path.with_suffix('').with_suffix(''))
    assert yaml.safe_load((dest/'resolved.yaml').read_text())==original
    updated=path.with_name(path.name.removesuffix('.1.txt')+'.updated.yaml')
    assert sha(updated)==f['snapshot_updated_sha256']
    check=checks[f['seed']];assert check['file_sha256']==f['snapshot_sha256'] and len(check['checks'])==3
    for row in check['checks']:
        assert all(isfinite(v) and abs(v)<=1e-9 for v in row['fresh_minus_recorded'].values())
assert len(lengths)==4 and min(lengths)==receipt['minimum_retained_represented_steps']>=receipt['assessment_trigger']
completed=json.loads((out/'diagnostic_completion.json').read_text())
assert completed['command']==receipt['diagnostic_command'] and completed['exit_code']==0
result=json.loads((out/'diagnostics.json').read_text())
assert result['seeds']==sorted(entries) and result['burnin_fraction_of_stored_rows']==.2
assert set(result['diagnostics'])=={'omegabh2','omegach2','H0','logA','ns','tau','mnu'}
assert {r['module_sha256'] for r in result['native_backend_provenance']}=={native['module_sha256']}
assert {r['solver_version'] for r in result['native_backend_provenance']}=={native['solver_version']}
gates={}
for name,d in result['diagnostics'].items():
    if 'error' in d:
        assert not d['diagnostic_thresholds_pass'];gates[name]={'error':d['error'],'pass':False};continue
    assert d['n_chains']==4 and d['draws_per_chain']==min(lengths)
    p,limit=d['quantile_mcse'],d['quantile_mcse_limit']
    fixed={'separate_starts':d['n_chains']>=2,
        'finite':all(d[k] is not None and isfinite(d[k]) for k in ['rank_folded_split_rhat','bulk_ess','tail_ess_05_95','quantile_ess','quantile_mcse']),
        'Rhat':d['rank_folded_split_rhat']<=1.01,'bulk_ESS':d['bulk_ess']>=400,
        'tail_ESS':d['tail_ess_05_95']>=400,'quantile_ESS':d['quantile_ess']>=400,
        'MCSE':0<p<=limit,'chronological_drift':d['quantile_half_difference']<=4*max(p,limit),
        'equalized_selection':abs(d['quantile_full_draws']-d['quantile_retained_draws'])<=2*max(p,limit)}
    assert all(fixed.values())==d['diagnostic_thresholds_pass'];gates[name]={'gates':fixed,'pass':all(fixed.values())}
assert result['all_diagnostic_thresholds_pass']==all(g['pass'] for g in gates.values())
assert result['diagnostics']['mnu'].get('quantile_mcse_limit',.001)==.001
with (out/'self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'self_review_no_independent_agent',
        'group':receipt['group'],'retained_represented_steps':lengths,'all_seven_parameter_gate_sets_reconstructed':gates,
        'next_minimum_history':ceil(Fraction(6,5)*min(lengths)),
        'snapshot_receipt_sha256':sha(out/'snapshot_receipt.json'),'native_row_verification_sha256':sha(out/'native_rows_verification.json'),
        'diagnostics_sha256':sha(out/'diagnostics.json'),'posterior_convergence_or_uniform_accuracy_proved':False,
        'different_targets_or_cache_policies_pooled':False},indent=2,allow_nan=False)+'\n')
print(receipt['group'],'exact data and native recount passes; parameter gates', {n:g['pass'] for n,g in gates.items()})
