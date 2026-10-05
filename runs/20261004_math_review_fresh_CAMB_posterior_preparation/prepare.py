"""Freeze proposals and five explicit numerical targets, with four starts each."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, indent=2, allow_nan=False)+'\n')

selection_path = ROOT/'runs/20261004_math_review_SPT_effective_CAMB_settings/selection_receipt.json'
selection = json.loads(selection_path.read_text())
proposals = {}
for lens, seed, receipt in [
    ('A',401,'runs/20261004_math_review_spt_sample_cap_completion/completion_receipt.json'),
    ('B',404,'runs/20261004_math_review_spt_internal_completion_B404/completion_receipt.json')]:
    completion = json.loads((ROOT/receipt).read_text())
    source = ROOT/f'runs/20261003_math_review_chain_{lens}_seed{seed}/chains/math_restoration_{lens}_seed{seed}.covmat'
    if 'records' in completion:
        record = next(r for r in completion['records'] if r['seed']==seed)
        witnesses = [r for r in record['files'] if Path(r['path']).name==source.name]
        assert record['exit_code']==0
    else:
        witnesses = [r for r in completion['files'] if r.get('source') == str(source.relative_to(ROOT))]
        assert completion['managed_exit_code']==0
    assert len(witnesses) == 1 and witnesses[0]['sha256'] == sha(source)
    state = json.loads((ROOT/'runs/20261003_math_review_validation/review_state.json').read_text())
    chain = next(e for e in state['restoration_chains'] if e['seed'] == seed)
    assert not Path('/proc',str(chain['pid'])).exists()
    names = source.read_text().splitlines()[0].lstrip('#').split()
    assert names == ['omegabh2','omegach2','H0','logA','ns','tau','mnu']
    matrix = np.loadtxt(source)
    assert matrix.shape == (7,7) and np.isfinite(matrix).all()
    # The archived decimal covariance has roundoff asymmetry below 3e-20.
    assert np.max(np.abs(matrix-matrix.T)) < 1e-18
    np.linalg.cholesky(matrix)
    destination = HERE/f'proposal_{lens}.covmat'
    with destination.open('xb') as f:
        f.write(source.read_bytes())
    proposals[lens] = {'source':str(source.relative_to(ROOT)), 'path':str(destination.relative_to(ROOT)),
        'sha256':sha(destination),'completion_receipt':receipt,'completion_receipt_sha256':sha(ROOT/receipt),
        'sampled_parameters':names,'maximum_asymmetry':float(np.max(np.abs(matrix-matrix.T))),
        'role':'fixed proposal heuristic only; no posterior or precision evidence'}

groups = [('old_A3200','A','1.6.5','original_style',1701),
          ('old_B4095','B','1.6.5','original_style',1705),
          ('current_A4095','A','2.0.4','restoration_style',1801),
          ('current_B4095','B','2.0.4','restoration_style',1805),
          ('current_A3200','A','2.0.4','original_style',1901)]
entries = []
implementation = {str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'scripts/run_cobaya.py',
    ROOT/'src/sbt_spt_audit/boltzmann.py',ROOT/'src/sbt_spt_audit/samplers.py', HERE/'launch_chain.py']}
for group,lens,version,style,start in groups:
    control = ROOT/('runs/20261004_math_review_SPT_archived_solver_version_control' if version=='1.6.5'
                    else 'runs/20261004_math_review_SPT_effective_CAMB_settings')
    receipt = control/lens/'evaluation_receipt.json'
    evaluated = json.loads(receipt.read_text())
    runtime = evaluated['runtime']
    base = yaml.safe_load((control/lens/style/'input.yaml').read_text())
    for seed,label in zip(range(start,start+4),['original_median','original_p95','restoration_median','restoration_p95']):
        point = selection['records'][lens]['points'][label]
        assert point == evaluated['records'][style]['evaluations'][label]['point']
        folder = HERE/f'seed{seed}'; folder.mkdir()
        cfg = deepcopy(base); cfg.pop('debug',None)
        cfg['run_name'] = f'fresh_CAMB_{group}_seed{seed}'
        theory = cfg['theory']['camb']
        theory.update({'class':'sbt_spt_audit.boltzmann.FreshCAMB','path':'global','version':version})
        theory['extra_args']['lmax'] = 3200 if group.endswith('3200') else 4095
        for name,value in point.items():
            cfg['params'][name]['ref'] = value
            assert cfg['params'][name]['prior']['min'] <= value <= cfg['params'][name]['prior']['max']
        cfg['sampler'] = {'mcmc':{'seed':seed,'max_samples':20000,'learn_proposal':True,
            'Rminus1_stop':.01,'Rminus1_cl_stop':.05,'Rminus1_cl_level':.95,
            'oversample_power':0,'oversample_thin':False,'covmat':str(ROOT/proposals[lens]['path'])}}
        cfg['notes'] = {'math_review':'Fresh transfers; distinct solver/cutoff target; current Python and data; no historical identity or posterior certification.',
            'camb_backend':{'module_sha256':runtime['CAMB_module_sha256'],'solver_version':version},
            'initial_point_label':label,'numerical_target':group,
            'proposal_role':'heuristic only; no source samples pooled','mass_prior':'uniform[0,5] eV, unchanged'}
        path=folder/'input.yaml'
        with path.open('x') as f: f.write(yaml.safe_dump(cfg,sort_keys=False))
        run_dir = f'runs/20261004_math_review_fresh_CAMB_{group}_seed{seed}'
        assert not (ROOT/run_dir).exists()
        e = {'seed':seed,'lens':lens,'group':group,'kind':'spt_desi_fresh_CAMB',
            'style':style,'solver_version':version,'Cobaya_version':runtime['versions']['cobaya'],
            'config':str(path.relative_to(ROOT)),'config_sha256':sha(path),'run_dir':run_dir,
            'initial_point':point,'initial_point_label':label,'control':str(receipt.relative_to(ROOT)),
            'control_sha256':sha(receipt),'selection_sha256':sha(selection_path),
            'module':runtime['CAMB_module'],'module_sha256':runtime['CAMB_module_sha256'],
            'wrapper':runtime['Cobaya_CAMB_wrapper'],'wrapper_sha256':runtime['Cobaya_CAMB_wrapper_sha256'],
            'proposal':proposals[lens],'implementation_sha256':implementation,
            'launch_receipt':str((folder/'launch_receipt.json').relative_to(ROOT))}
        write(folder/'preparation_receipt.json',e);entries.append(e)
write(HERE/'preparation_receipt.json',{'utc':datetime.now(timezone.utc).isoformat(),'entries':entries,
    'proposal_heuristics':proposals,'targets':groups,'cohorts_pooled':False,'posterior_certified':False,
    'comparison_scope':'Old and current A3200/B4095; current A4095/B4095. Reused B cohort makes paired differences dependent.',
    'original_historical_whole_environment_reconstructed':False,'paper_modified':False})
print('Prepared 20 configurations for five separate targets; preflight required.')
