"""Verify frozen first rows and retain the unresolved native discrepancy."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
prep=json.loads((HERE/'preparation_receipt.json').read_text())
probe=json.loads((HERE/'saved_row_discrepancy_probe.json').read_text())
verified,failed=[],[]
rows=[]
for e in prep['entries']:
    folder=HERE/('seed'+str(e['seed']))/'first_saved_rows'
    file,=(folder/'chains').glob('*.1.txt')
    raw=file.read_bytes()
    assert raw.endswith(b'\n') and (ROOT/e['run_dir']/'chains'/file.name).read_bytes().startswith(raw)
    lines=raw.decode().splitlines();header=lines[0].lstrip('#').split()
    assert len(set(header))==len(header)
    data=[line.split() for line in lines if line.strip() and not line.startswith('#')]
    assert len(data)==1 and len(data[0])==len(header)
    row=dict(zip(header,data[0]))
    weight=Fraction(row['weight']);assert weight>0 and weight.denominator==1
    point={n:float(row[n]) for n in e['initial_point']}
    assert float(row['As'])==1e-10*np.exp(point['logA'])
    cfg=yaml.safe_load((folder/'resolved.yaml').read_text())
    assert cfg['theory']['camb']['extra_args']['lmax']==(3200 if e['lens']=='A' else 4095)
    backend=json.loads((folder/'solver_backend.json').read_text())
    assert backend['module_sha256']==e['module_sha256'] and backend['solver_version']=='1.6.5'
    updated,=(folder/'chains').glob('*.updated.yaml')
    assert yaml.safe_load(updated.read_text())['theory']['camb']['version']=='1.6.5'
    result=probe['records'][str(e['seed'])]
    assert result['fresh_model']['frozen_chain_sha256']==hashlib.sha256(raw).hexdigest()
    assert result['fresh_model']['point']==result['shared_model']['point']==point
    assert result['fresh_model']['components']==result['shared_model']['components']
    discrepancy=result['fresh_model']['discrepancies']
    total=sum(result['fresh_model']['components'].values())
    assert total-float(row['chi2'])==discrepancy['total_chi2']
    if max(abs(v) for v in discrepancy.values())<=1e-9:
        verified.append(e['seed'])
    else:
        failed.append(e['seed'])
        assert discrepancy['logprior']==0 and discrepancy['sbt_spt_audit.likelihoods.desi_dr2_bao.DESIDR2BAOGaussian']==0
        assert discrepancy['logposterior']==-discrepancy['total_chi2']/2
    rows.append({'seed':e['seed'],'point':point,'holding_time':int(weight),
                 'frozen_chain':str(file.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),
                 'native_discrepancies':discrepancy,'native_replay_passed':e['seed'] in verified})
assert verified==[1601,1602,1603,1605,1606,1607,1608] and failed==[1604]
controls={}
for version in ['1.6.5','2.0.4']:
    for prefix in ['transfer_cache_','posterior_path_transfer_cache_']:
        file=HERE/(prefix+version+'_receipt.json')
        c=json.loads(file.read_text())
        assert c['same_slow_coordinates_only_logA_and_ns_changed']
        assert c['reused_minus_fresh_total_chi2']==0
        assert c['records']['fast_move_reused_transfer']['point']==rows[3]['point']
        controls[prefix+version]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
            'reused_minus_fresh_total_chi2':c['reused_minus_fresh_total_chi2'],
            'reused_minus_stored_total_chi2':c['reused_minus_stored_total_chi2']}
assert controls['transfer_cache_1.6.5']['reused_minus_stored_total_chi2']==rows[3]['native_discrepancies']['total_chi2']
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'all_eight_first_rows_frozen_with_matching_backend_metadata':True,'first_native_rows_passed':verified,
     'first_native_rows_failed':failed,'rows':rows,'simple_cached_and_posterior_path_controls':controls,
     'simple_transfer_reuse_alone_reproduces_failed_saved_likelihood':False,
     'cause_of_stored_vs_native_mismatch_established':False,
     'all_archived_solver_chains_qualified_for_inference':False,'native_replay_tolerance_relaxed':False,
     'no_unverified_archived_posterior_readout_reported':True,'paper_modified':False,
     'native_sessions':{'initial_A':2579,'initial_B':23423,'first_rows_failed':38435,'fresh_and_shared_triage':25531,
        'simple_cache_old':73201,'simple_cache_current':99582,'posterior_path_old':59327,'posterior_path_current':26072}}
with (HERE/'partial_rows_self_review.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Seven first native rows pass; seed1604 SPT chi2 discrepancy remains unresolved; simple cache hypothesis not established.')
