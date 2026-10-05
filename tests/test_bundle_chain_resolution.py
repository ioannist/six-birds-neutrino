"""Bundle summaries must use their saved data despite stale output paths."""
from pathlib import Path
import sys

import numpy as np
import pytest
import yaml

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from extract_mnu_limits import _load_chains_raw, _resolve_prefix_from_run_dir


def write_chain(prefix, masses):
    prefix.parent.mkdir(parents=True,exist_ok=True)
    np.savetxt(str(prefix)+'.1.txt',np.column_stack([np.ones(len(masses)),np.zeros(len(masses)),masses]),
               header='weight minuslogpost mnu')


def test_frozen_bundle_reads_its_rows_while_original_live_output_exists(tmp_path):
    active=tmp_path/'active'/'chains'/'sample';write_chain(active,[.1,.2,.3])
    frozen=tmp_path/'frozen';local=frozen/'chains'/'sample';write_chain(local,[.9])
    (frozen/'resolved.yaml').write_text(yaml.safe_dump({'output':str(active)}))
    prefix=_resolve_prefix_from_run_dir(frozen)
    values,weights=_load_chains_raw(prefix,'mnu',0)[0]
    assert prefix==local
    assert values.tolist()==[.9] and weights.tolist()==[1.]
    # Appending to the active chain must not alter the frozen readout.
    write_chain(active,[.1,.2,.3,.4])
    assert _load_chains_raw(_resolve_prefix_from_run_dir(frozen),'mnu',0)[0][0].tolist()==[.9]


def test_bundle_without_local_advertised_chain_refuses_external_output(tmp_path):
    active=tmp_path/'active'/'chains'/'sample';write_chain(active,[.1,.2])
    bundle=tmp_path/'bundle';bundle.mkdir()
    (bundle/'resolved.yaml').write_text(yaml.safe_dump({'output':str(active)}))
    with pytest.raises(FileNotFoundError,match='inside.*bundle'):
        _resolve_prefix_from_run_dir(bundle)


def test_metadata_selects_matching_local_prefix_instead_of_another_chain(tmp_path):
    run=tmp_path/'run';first=run/'chains'/'first';second=run/'chains'/'second'
    write_chain(first,[.1]);write_chain(second,[.2])
    (run/'resolved.yaml').write_text(yaml.safe_dump({'output':'chains/second'}))
    assert _resolve_prefix_from_run_dir(run)==second
    (run/'resolved.yaml').write_text(yaml.safe_dump({'output':'chains/missing'}))
    with pytest.raises(FileNotFoundError,match='inside.*bundle'):
        _resolve_prefix_from_run_dir(run)


def test_no_output_metadata_refuses_multiple_local_prefixes(tmp_path):
    run=tmp_path/'run';write_chain(run/'chains'/'first',[.1]);write_chain(run/'chains'/'second',[.2])
    with pytest.raises(ValueError,match='Ambiguous'):
        _resolve_prefix_from_run_dir(run)


def test_local_nested_prefix_and_single_text_chain_are_supported(tmp_path):
    run=tmp_path/'run';prefix=run/'saved'/'nested'/'sample';prefix.parent.mkdir(parents=True)
    np.savetxt(str(prefix)+'.txt',[[1.,0.,.2]],header='weight minuslogpost mnu')
    (run/'resolved.yaml').write_text(yaml.safe_dump({'output':'saved/nested/sample'}))
    assert _resolve_prefix_from_run_dir(run)==prefix


def test_two_local_copies_of_stale_prefix_require_an_explicit_choice(tmp_path):
    run=tmp_path/'run';write_chain(run/'chains'/'sample',[.1]);write_chain(run/'sample',[.2])
    (run/'resolved.yaml').write_text(yaml.safe_dump({'output':str(tmp_path/'elsewhere'/'sample')}))
    with pytest.raises(ValueError,match='Ambiguous'):
        _resolve_prefix_from_run_dir(run)


def test_diagnostic_report_uses_frozen_data_and_local_provenance(tmp_path, monkeypatch):
    pytest.importorskip('arviz')
    import diagnose_cobaya_chains
    command=['diagnose']
    for seed in [41,42]:
        active=tmp_path/f'active{seed}'/'chains'/'sample';write_chain(active,np.linspace(.1,.4,800))
        frozen=tmp_path/f'frozen{seed}';local=frozen/'chains'/'sample';write_chain(local,np.linspace(.1,.2,32))
        cfg={'output':str(active),'theory':{},'likelihood':{},'params':{'mnu':{'prior':{'min':0.,'max':5.}}},
             'sampler':{'mcmc':{'seed':seed}}}
        (frozen/'resolved.yaml').write_text(yaml.safe_dump(cfg))
        command+=['--run-dir',str(frozen)]
    output=tmp_path/'diagnostics.json';command+=['--burnin-frac','0','--output',str(output)]
    monkeypatch.setattr(sys,'argv',command)
    assert diagnose_cobaya_chains.main()==0
    import json
    result=json.loads(output.read_text())
    assert result['diagnostics']['mnu']['draws_per_chain']==32
    assert result['prefixes']==[str(tmp_path/f'frozen{seed}'/'chains'/'sample') for seed in [41,42]]
