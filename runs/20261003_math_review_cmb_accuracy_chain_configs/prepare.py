"""Prepare distinct-seed numerical posterior controls without changing physics."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from run_cosmological_audit import build_common_config

source_paths = {lens: ROOT / f'runs/20261003_math_review_cmb_accuracy_configs/{lens}.yaml'
                for lens in ['A', 'B']}
configs = {lens: yaml.safe_load(p.read_text()) for lens, p in source_paths.items()}
build_common_config(configs['A'], configs['B'])
manifest = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'independent_intermediate_CLASS_precision_posterior_controls',
    'posterior_convergence_verified': False,
    'numerical_accuracy_certified': False,
    'pool_with_default_precision_chains': False,
    'replicas_per_lens': 2,
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in source_paths.values()},
    'runs': [],
}
for lens, seeds in [('A', [601, 602]), ('B', [603, 604])]:
    source = configs[lens]
    fit_path = ROOT / f'runs/20261003_math_review_cosmological_cmb_desi_accuracy/lens{lens}_fit_0.json'
    fit = json.loads(fit_path.read_text())
    manifest['source_sha256'][str(fit_path.relative_to(ROOT))] = hashlib.sha256(fit_path.read_bytes()).hexdigest()
    proposal_source = ROOT / f'runs/20261003_math_review_cmb_proposal_{lens}/proposal.covmat'
    proposal = np.loadtxt(proposal_source)
    assert proposal.shape == (10, 10)
    assert np.all(np.isfinite(proposal))
    assert np.allclose(proposal, proposal.T, rtol=1e-12, atol=0)
    np.linalg.cholesky(proposal)
    proposal_copy = HERE / f'{lens}_proposal.covmat'
    if proposal_copy.exists():
        raise FileExistsError(proposal_copy)
    proposal_copy.write_bytes(proposal_source.read_bytes())
    manifest['source_sha256'][str(proposal_source.relative_to(ROOT))] = hashlib.sha256(proposal_source.read_bytes()).hexdigest()
    for seed in seeds:
        cfg = deepcopy(source)
        cfg['run_name'] = f'math_accuracy_{lens}_seed{seed}'
        for name, block in cfg['params'].items():
            if isinstance(block, dict) and 'prior' in block:
                value = fit['point'][name]
                assert np.isfinite(value) and block['prior']['min'] <= value <= block['prior']['max']
                block['ref'] = {'dist': 'norm', 'loc': value, 'scale': block['proposal']}
        cfg['sampler'] = {'sbt_spt_audit.samplers.FullPrecisionMCMC': {
            'seed': seed, 'max_samples': 20000, 'learn_proposal': True,
            'Rminus1_stop': .01, 'Rminus1_cl_stop': .05, 'Rminus1_cl_level': .95,
            'oversample_power': 0, 'oversample_thin': False,
            'covmat': str(proposal_copy), 'learn_every': '10d',
        }}
        cfg['notes'] = dict(cfg.get('notes', {}),
            numerical_control='Same physical model, priors, and likelihoods as default-precision restoration; seven intermediate CLASS precision settings. Do not pool with default-target chains.',
            warm_start_fit=str(fit_path),
            proposal_scope='Previously checked static response proposal; initialization only, not a posterior covariance claim.',
            output_precision='17 significant figures preserve binary64 sampled coordinates.',
            sampler_scope='Independent seed and integer holding times; termination is not a convergence certificate.')
        assert cfg['likelihood'] == source['likelihood']
        assert cfg['theory'] == source['theory']
        for name, block in source['params'].items():
            actual = deepcopy(cfg['params'][name])
            if isinstance(actual, dict):
                actual.pop('ref', None)
            expected = deepcopy(block)
            if isinstance(expected, dict):
                expected.pop('ref', None)
            assert actual == expected
        p = HERE / f'{lens}_seed{seed}.yaml'
        if p.exists():
            raise FileExistsError(p)
        p.write_text(yaml.safe_dump(cfg, sort_keys=False))
        manifest['runs'].append({'lens': lens, 'seed': seed, 'config': str(p),
                                 'config_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                                 'outdir': str(ROOT / f'runs/20261003_math_review_cmb_accuracy_chain_{lens}_seed{seed}')})
(HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Prepared {len(manifest["runs"])} independent controlled-precision chains.')
