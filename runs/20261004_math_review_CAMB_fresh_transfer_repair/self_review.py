"""Distinct self-review of the spectrum defect, production repair and native rows."""
from copy import deepcopy
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
production=ROOT/'src/sbt_spt_audit/boltzmann.py'
summary=[]
for v in ['1.6.5','2.0.4']:
    spectra=json.loads((HERE/('native_spectra_'+v+'_receipt.json')).read_text())
    assert len(spectra['records'])==4
    for r in spectra['records']:
        p=HERE/r['arrays'];assert sha(p)==r['arrays_sha256']
        with np.load(p) as data:
            for key,record in r['spectra'].items():
                before,after=data['returned_'+key],data['fresh_'+key]
                assert before.shape==after.shape==tuple(record['shape'])
                assert np.all(np.isfinite(before)) and np.all(np.isfinite(after))
                difference=before-after
                assert float(np.max(np.abs(difference)))==record['max_absolute_difference']
                assert int(np.count_nonzero(difference))==record['nonidentical_entries']
                assert bool(np.array_equal(before,after))==record['exactly_equal']
                assert hashlib.sha256(before.tobytes()).hexdigest()==record['before_sha256']
                assert hashlib.sha256(after.tobytes()).hexdigest()==record['after_sha256']
        assert r['returned_logpriors']==r['fresh_logpriors']
        if r['lens']=='A' and r['transfer_cache_size']==1:
            assert r['cached_minus_fresh_chi2'][0]!=0
            assert r['spectra']['tt']['nonidentical_entries']>0
        else:
            assert all(s['exactly_equal'] for s in r['spectra'].values())
            assert r['cached_minus_fresh_chi2']==[0.,0.]
    adapter=json.loads((HERE/('adapter_'+v+'_receipt.json')).read_text())
    assert adapter['CAMB_version']==v and len(adapter['records'])==74
    assert adapter['all74_selected_results_exact'] and adapter['production_adapter_sha256']==sha(production)
    for r in adapter['records']:
        assert r['exactly_equal'] and r['adapter_cached']==r['upstream_forced_fresh']
    for lens in ['A','B']:
        selected=[r for r in adapter['records'] if r['lens']==lens]
        assert [r['call'] for r in selected]==list(range(37))
        assert [r['call'] for r in selected if r['adapter_cached']['logpost'] is None]==[14]
    for c in adapter['configs']:
        modified=deepcopy(c['adapter_config'])
        assert modified['theory']['camb'].pop('class')=='sbt_spt_audit.boltzmann.FreshCAMB'
        assert modified==c['reference_config']
    assert all(r['posterior_results_exactly_equal'] and r['spectra_exactly_equal'] for r in adapter['interleaved'])
    sampler=json.loads((HERE/('sampler_'+v+'_receipt.json')).read_text())
    launch=json.loads((HERE/('sampler_'+v+'_launch.json')).read_text())
    assert not Path('/proc',str(launch['pid'])).exists()
    assert sampler['native_sha256']==adapter['native_sha256']==spectra['native_sha256']==launch['native_sha256']
    assert sha(Path(launch['native_path']))==launch['native_sha256']
    assert sampler['production_adapter_sha256']==sha(production)
    assert sampler['all_rows_match_fresh_within_predeclared_1e_minus9']
    assert {r['lens'] for r in sampler['records']}=={'A','B'}
    for r in sampler['records']:
        p=ROOT/r['chain'];assert sha(p)==r['chain_sha256']
        header=p.read_text().splitlines()[0].lstrip('#').split()
        assert len(header)==len(set(header))
        rows=np.atleast_2d(np.loadtxt(p));assert len(rows)==r['stored_rows']==2
        assert np.all(np.isfinite(rows)) and np.all(rows[:,0]>0) and np.all(rows[:,0]==np.floor(rows[:,0]))
        assert r['sampler_transfer_helper_class']=='FreshCAMBTransfers'
        for check in r['checks']:
            assert check['exactly_equal'] and check['within_fixed_1e_minus9']
            assert all(delta==0 for delta in check['fresh_minus_stored'].values())
        updated=yaml.safe_load(p.with_name('finite_probe.updated.yaml').read_text())
        assert str(updated['theory']['camb']['version'])==v
        assert updated['theory']['camb']['class']=='sbt_spt_audit.boltzmann.FreshCAMB'
    summary.append({'CAMB_version':v,'finite_target_comparisons':72,'prior_rejected_comparisons':2,
                    'interleaved_model_recipes':2,'actual_finite_MCMC_rows_exact_to_upstream_fresh':4,
                    'native_module_sha256':launch['native_sha256'],'finite_probe_process_absent':True})
text=(HERE/'math_check_stdout.txt').read_text()
assert '168 passed' in text and 'Build completed successfully' in text
axioms=re.findall(r"'([^']+)' depends on axioms: \[([^]]*)\]",text,re.S)
assert len(axioms)==len({name for name,_ in axioms})==74
assert all({a.strip() for a in found.split(',') if a.strip()} <= {'propext','Classical.choice','Quot.sound'} for _,found in axioms)
assert not (HERE/'math_check_stderr.txt').read_bytes()
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT,text=True).strip()
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'native_spectrum_isolation_sessions':{'1.6.5':5968,'2.0.4':84456},
     'native_adapter_validation_sessions':{'1.6.5':5304,'2.0.4':8777},
     'native_sampler_validation_sessions':{'1.6.5':73403,'2.0.4':93722},'all_native_session_exit_codes':0,
     'make_math_check_session':24592,'make_math_check_exit_code':0,'python_tests':168,
     'Lean_build_passed':True,'public_Lean_axiom_exports_checked':74,'summary':summary,
     'native_cached_A_spectrum_defect_reproduced_both_versions':True,
     'production_adapter_preserves_selected_upstream_fresh_target_both_recipes_versions':True,
     'sampler_cache_resizing_cannot_reenable_transfer_reuse_in_adapter':True,
     'selected_controls_are_uniform_native_accuracy_or_convergence_certificate':False,
     'historical_inference_chains_repaired_by_changing_future_code':False,
     'new_inference_cohorts_launched':False,'main_claim_or_paper_revision_adopted':False,
     'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [production,ROOT/'scripts/run_cobaya.py',ROOT/'scripts/run_cosmological_audit.py',ROOT/'scripts/build_cmb_bao_proposal.py',ROOT/'tests/test_fresh_camb_transfers.py',ROOT/'tests/test_native_backend_launch.py',HERE/'math_check_stdout.txt']}}
with (HERE/'self_review_receipt.json').open('x') as h:h.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('148 target comparisons and8 native sampler rows exact; 168 Python tests and Lean/74 exports pass; historical posterior repair remains open.')
