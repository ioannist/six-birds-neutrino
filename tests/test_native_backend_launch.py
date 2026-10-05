"""A declared native target must be enforced before creating sampler output."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
import yaml

pytest.importorskip('cobaya')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_cobaya as launcher


@pytest.fixture
def native_target(tmp_path, monkeypatch):
    native = tmp_path / 'camblib.so'
    native.write_bytes(b'controlled native build identity')
    sha = hashlib.sha256(native.read_bytes()).hexdigest()
    module = SimpleNamespace(__version__='1.6.5',
                             baseconfig=SimpleNamespace(camblib=SimpleNamespace(_name=str(native))))
    def load(name):
        assert name == 'camb'
        return module
    monkeypatch.setattr(launcher.importlib, 'import_module', load)
    config = {'theory': {'camb': {'version': '1.6.5'}},
              'notes': {'camb_backend': {'module_sha256': sha, 'solver_version': '1.6.5'}}}
    return config, module, native


def test_matching_camb_build_records_actual_import(native_target):
    config, _, native = native_target
    result = launcher._validate_native_backend(config)
    assert result == {'solver': 'camb', 'module': str(native.resolve()),
                      'module_sha256': hashlib.sha256(native.read_bytes()).hexdigest(),
                      'solver_version': '1.6.5'}


@pytest.mark.parametrize('defect', ['hash', 'version', 'theory_version', 'path',
                                  'missing_hash', 'missing_version', 'two_solvers',
                                  'two_contracts', 'wrong_solver', 'malformed_contract'])
def test_camb_contract_rejects_mismatches_before_output(native_target, tmp_path, monkeypatch, defect):
    original, module, native = native_target
    config = deepcopy(original)
    if defect == 'hash':
        native.write_bytes(b'different native build')
    elif defect == 'version':
        module.__version__ = '2.0.4'
    elif defect == 'theory_version':
        config['theory']['camb']['version'] = '2.0.4'
    elif defect == 'path':
        config['theory']['camb']['path'] = '/another/camb'
    elif defect.startswith('missing_'):
        config['notes']['camb_backend'].pop('module_sha256' if defect == 'missing_hash' else 'solver_version')
    elif defect == 'two_solvers':
        config['theory']['classy'] = {}
    elif defect == 'two_contracts':
        config['notes']['classy_backend'] = {}
    elif defect == 'wrong_solver':
        config['theory'] = {'classy': {}}
    else:
        config['notes']['camb_backend'] = 'invalid'
    source = tmp_path / 'input.yaml'
    source.write_text(yaml.safe_dump(config))
    output = tmp_path / 'new_run'
    monkeypatch.setattr(launcher, 'parse_args', lambda: SimpleNamespace(config=str(source), outdir=str(output)))
    assert launcher.main() == 2
    assert not output.exists()


def test_no_contract_preserves_ordinary_launch_configuration(monkeypatch):
    def forbidden(name):
        raise AssertionError('An undeclared contract must not import a solver')
    monkeypatch.setattr(launcher.importlib, 'import_module', forbidden)
    assert launcher._validate_native_backend({'theory': {'camb': {}}}) is None


def test_class_dispatch_preserves_existing_guard(monkeypatch):
    config = {'theory': {'classy': {}}, 'notes': {'classy_backend': {}}}
    witness = {'module': '/verified/classy.so', 'module_sha256': 'a'*64}
    def existing_guard(received):
        assert received is config
        return witness
    monkeypatch.setattr(launcher, '_validate_classy_backend', existing_guard)
    assert launcher._validate_native_backend(config) == {**witness, 'solver': 'classy'}


def test_custom_camb_adapter_is_rejected_before_output(native_target,tmp_path,monkeypatch):
    config,_,_=native_target
    config['theory']['camb']['class']='other.CustomCAMB'
    source=tmp_path/'custom.yaml';source.write_text(yaml.safe_dump(config))
    output=tmp_path/'custom_run'
    monkeypatch.setattr(launcher,'parse_args',lambda:SimpleNamespace(config=str(source),outdir=str(output)))
    assert launcher.main()==2
    assert not output.exists()


def test_launcher_records_fresh_adapter_before_sampling(native_target,tmp_path,monkeypatch):
    config,_,_=native_target
    config.update(params={'x':{'prior':{'min':0.,'max':1.}}},
                  sampler={'mcmc':{'max_samples':2,'learn_proposal':False}})
    source=tmp_path/'source.yaml';source.write_text(yaml.safe_dump(config))
    original=source.read_bytes()
    output=tmp_path/'recorded_run'
    monkeypatch.setattr(launcher,'parse_args',lambda:SimpleNamespace(
        config=str(source),outdir=str(output),seed=17,packages_path=str(tmp_path),max_samples_override=None))
    monkeypatch.setattr(launcher,'_run_env',lambda path:(path/'env.txt').write_text('controlled launch fixture'))
    seen=[]
    def capture(resolved,**kwargs):
        seen.append(deepcopy(resolved))
        raise RuntimeError('Controlled stop after recording; no native sampler invoked')
    monkeypatch.setattr(launcher,'cobaya_run',capture)
    assert launcher.main()==1
    saved=yaml.safe_load((output/'resolved.yaml').read_text())
    assert saved==seen[0]
    assert saved['theory']['camb']['class']=='sbt_spt_audit.boltzmann.FreshCAMB'
    assert saved['theory']['camb']['version']=='1.6.5'
    assert saved['params']==config['params']
    assert saved['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']=={
        'max_samples':2,'learn_proposal':False,'seed':17}
    assert (output/'input.yaml').read_bytes()==original==source.read_bytes()
