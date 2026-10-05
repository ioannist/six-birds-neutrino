"""Compare isolated archived solver versions with identical current-stack controls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CURRENT = ROOT/'runs/20261004_math_review_SPT_effective_CAMB_settings'
preparation = json.loads((HERE/'preparation_receipt.json').read_text())
selection = json.loads((CURRENT/'selection_receipt.json').read_text())
install = json.loads((HERE/'isolated_install_receipt.json').read_text())
sources, reports = [], {}
def check_source(path):
    sources.append({'path':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for f in preparation['sources']:
    assert hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest() == f['sha256']
    assert (ROOT/f['copy']).read_bytes() == (ROOT/f['path']).read_bytes()
for f in install['wheels']:
    assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest() == f['sha256']
for target in ['A','B']:
    check_source(CURRENT/target/'evaluation_receipt.json')
    current = json.loads((CURRENT/target/'evaluation_receipt.json').read_text())
    old = json.loads((HERE/target/'evaluation_receipt.json').read_text())
    assert old['runtime']['versions']['camb'] == '1.6.5' and old['runtime']['versions']['cobaya'] == '3.6.1'
    for key,h in [('CAMB_module','CAMB_module_sha256'),('Cobaya_CAMB_wrapper','Cobaya_CAMB_wrapper_sha256')]:
        assert hashlib.sha256(Path(old['runtime'][key]).read_bytes()).hexdigest()==old['runtime'][h]
        assert hashlib.sha256(Path(current['runtime'][key]).read_bytes()).hexdigest()==current['runtime'][h]
    assert old['runtime']['CAMB_module_sha256'] == install['CAMB_native_module_sha256']
    assert old['runtime']['versions']['candl-like'] == current['runtime']['versions']['candl-like']
    assert not (HERE/target/'stderr.txt').read_bytes()
    style_controls, crossed, archived_rows = {}, {}, {}
    for style in ['original_style','restoration_style']:
        a,b = old['records'][style],current['records'][style]
        for key in ['requested_Cl','effective_CAMB_extra_args','internal_prior_policy','fixed_scalar_defaults','sampled_scalar_inputs','native_dataset_path']:
            assert a[key] == b[key]
        changes = {}
        for label in selection['records'][target]['points']:
            ea,eb = a['evaluations'][label],b['evaluations'][label]
            assert ea['point']==eb['point'] and ea['logpriors']==eb['logpriors']
            assert np.all(np.isfinite(list(ea['chi2_components'].values())+[ea['logposterior']]))
            changes[label] = {'total_chi2_current_minus_archived_versions':eb['chi2_total']-ea['chi2_total'],
                'component_chi2_current_minus_archived_versions':{n:eb['chi2_components'][n]-ea['chi2_components'][n] for n in ea['chi2_components']},
                'max_abs_supported_Cl_difference_microK2':{}}
            with np.load(HERE/target/style/(label+'_spectra.npz')) as ca,np.load(CURRENT/target/style/(label+'_spectra.npz')) as cb:
                for n in ca.files:
                    assert ca[n].shape==cb[n].shape
                    changes[label]['max_abs_supported_Cl_difference_microK2'][n] = float(np.max(np.abs(cb[n]-ca[n])))
        plus,median = 'restoration_median_mass_plus_001','restoration_median'
        old_response = a['evaluations'][plus]['chi2_total']-a['evaluations'][median]['chi2_total']
        current_response = b['evaluations'][plus]['chi2_total']-b['evaluations'][median]['chi2_total']
        style_controls[style]={'changes':changes,'median_mass_plus_001_responses':{'archived_versions':old_response,'current_versions':current_response},
            'mass_response_change':current_response-old_response,
            'max_absolute_selected_total_chi2_change':max(abs(c['total_chi2_current_minus_archived_versions']) for c in changes.values())}
    for label in selection['records'][target]['points']:
        ea,eb=old['records']['original_style']['evaluations'][label],current['records']['restoration_style']['evaluations'][label]
        crossed[label]={'total_chi2_current_restoration_minus_archived_original_style':eb['chi2_total']-ea['chi2_total'],
            'component_chi2_change':{n:eb['chi2_components'][n]-ea['chi2_components'][n] for n in ea['chi2_components']}}
    for label in ['original_median','original_p95']:
        choice=selection['records'][target]['point_selection'][label]
        path=ROOT/choice['source_chain']
        check_source(path)
        lines=path.read_text().splitlines()
        header=next(line for line in lines if line.startswith('#')).lstrip('#').split()
        rows=[line.split() for line in lines if line.strip() and not line.startswith('#')]
        row=dict(zip(header,rows[choice['stored_row_index']]))
        replay=old['records']['original_style']['evaluations'][label]
        assert all(replay['point'][n]==float(row[n]) for n in replay['point'])
        archived_rows[label]={'stored_total_chi2':float(row['chi2']),
            'fresh_total_chi2_at_stored_coordinates':replay['chi2_total'],
            'fresh_minus_stored_total_chi2':replay['chi2_total']-float(row['chi2']),
            'component_fresh_minus_stored_chi2':{n:replay['chi2_components'][n]-float(row['chi2__'+n]) for n in replay['chi2_components']},
            'fresh_minus_stored_logprior':sum(replay['logpriors'])+float(row['minuslogprior']),
            'fresh_minus_stored_logposterior':replay['logposterior']+float(row['minuslogpost']),
            'stored_coordinates_rounded_original_binary_not_available':True}
    reports[target]={'same_style_solver_version_controls':style_controls,
        'crossed_original_style_archived_versions_to_current_restoration':crossed,
        'selected_archived_saved_row_replays':archived_rows,
        'requested_and_effective_settings_identical_between_versions_within_style':True}
out={'utc':datetime.now(timezone.utc).isoformat(),'reports':reports,'current_control_sources':sources,
     'selected_native_evaluations':20,'isolated_versions_match_archived_CAMB_and_Cobaya':True,
     'original_Python_environment_or_native_binary_reconstructed':False,
     'old_likelihood_package_and_data_identity_certified':False,
     'posterior_quantile_sensitivity_or_uniform_solver_accuracy_certified':False,
     'numerical_claim_revision_adopted':False,'live_sampler_environment_modified':False,'paper_modified':False}
with (HERE/'comparison_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:{s:{n:v[n] for n in ['max_absolute_selected_total_chi2_change','mass_response_change']} for s,v in r['same_style_solver_version_controls'].items()} for k,r in reports.items()},indent=2))
print(json.dumps({k:r['selected_archived_saved_row_replays'] for k,r in reports.items()},indent=2))
