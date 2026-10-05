"""Prepare eight fresh quadrature-repaired posterior chains with fixed warm witnesses."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
assert not (HERE / 'manifest.json').exists()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
snapshot_root = ROOT / 'runs/20261003_math_review_chain_snapshots_ninth'
snapshot = json.loads((snapshot_root / 'snapshot_receipt.json').read_text())
snapshots = {entry['original_seed']: entry for entry in snapshot['files']}
shape_root = ROOT / 'runs/20261003_math_review_cmb_proposal_shape_check'
shape_inputs = json.loads((shape_root / 'inputs.json').read_text())
sampler_name = 'sbt_spt_audit.samplers.FullPrecisionMCMC'
records = []
for lens, original_seeds, first_seed, control_seed in [
        ('A', [501, 502, 503, 504], 1101, 601),
        ('B', [505, 506, 507, 508], 1105, 603)]:
    control_path = ROOT / f'runs/20261003_math_review_cmb_accuracy_chain_configs/{lens}_seed{control_seed}.yaml'
    control_bytes = control_path.read_bytes()
    control = yaml.safe_load(control_bytes)
    covariance_path = shape_root / f'{lens}_learned_default.covmat'
    covariance = covariance_path.read_bytes()
    assert hashlib.sha256(covariance).hexdigest() == shape_inputs['records'][covariance_path.name]['sha256']
    names = covariance.splitlines()[0].decode().removeprefix('#').split()
    matrix = np.loadtxt(BytesIO(covariance))
    assert np.all(np.isfinite(matrix))
    widths = np.sqrt(np.diag(matrix))
    assert np.max(np.abs(matrix - matrix.T) / np.outer(widths, widths)) < 1e-12
    np.linalg.cholesky((matrix + matrix.T) / 2)
    sampled = [name for name, options in control['params'].items()
               if isinstance(options, dict) and 'prior' in options]
    assert names == sampled and matrix.shape == (10, 10)
    copied_covariance = HERE / covariance_path.name
    copied_covariance.write_bytes(covariance)
    (HERE / f'{lens}_intermediate_source.yaml').write_bytes(control_bytes)
    for offset, original_seed in enumerate(original_seeds):
        seed = first_seed + offset
        parent = next(entry for entry in state['restoration_chains'] if entry['seed'] == original_seed)
        assert parent['lens'] == lens and parent['kind'] == 'cmb_desi'
        parent_config = yaml.safe_load((ROOT / parent['run_dir'] / 'resolved.yaml').read_text())
        evidence = snapshots[original_seed]
        parent_chain = ROOT / evidence['snapshot']
        raw = parent_chain.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == evidence['sha256']
        rows = np.atleast_2d(np.loadtxt(BytesIO(raw)))
        header = raw.splitlines()[0].decode().removeprefix('#').split()
        assert len(rows) == evidence['stored_rows']
        values = dict(zip(header, rows[-1]))
        config = deepcopy(control)
        config['run_name'] = f'math_quad_{lens}_seed{seed}'
        config['theory']['classy']['extra_args'] = {
            'N_ncdm': 3, 'N_ur': 0.00641, 'l_max_scalars': 4095, 'tol_ncdm_bg': 1e-8}
        assert config['likelihood'] == parent_config['likelihood']
        for name, block in config['params'].items():
            reference_block = deepcopy(parent_config['params'][name])
            actual = deepcopy(block)
            if isinstance(actual, dict):
                actual.pop('ref', None)
            if isinstance(reference_block, dict):
                reference_block.pop('ref', None)
            assert actual == reference_block, (original_seed, name)
            if name in sampled:
                value = float(values[name])
                assert np.isfinite(value) and block['prior']['min'] <= value <= block['prior']['max']
                block['ref'] = value
        for key in ['N_ncdm', 'N_ur', 'l_max_scalars']:
            assert config['theory']['classy']['extra_args'][key] == parent_config['theory']['classy']['extra_args'][key]
        options = config['sampler'][sampler_name]
        options['seed'] = seed
        options['covmat'] = str(copied_covariance)
        assert options['Rminus1_stop'] == .01 and options['Rminus1_cl_stop'] == .05
        assert options['Rminus1_cl_level'] == .95 and options['max_samples'] == 20000
        assert options['oversample_power'] == 0 and options['oversample_thin'] is False
        config['notes'] = dict(config.get('notes', {}),
            numerical_control='Common ell_max4095 and tol_ncdm_bg1e-8 only; distinct numerical target from both legacy default and seven-setting intermediate chains. Do not pool across targets.',
            warm_start_fit='Fixed last saved row of the declared immutable ninth snapshot; used only as initialization, not as a new-target posterior draw.',
            proposal_scope='Archived unconverged default-target learned covariance; proposal initialization only, not a posterior covariance certificate.',
            initialization_scope='Each replica has a distinct parent family and fresh RNG seed. Initialization reuses old-target points; no independence or convergence certificate follows from that reuse.')
        path = HERE / f'{lens}_seed{seed}.yaml'
        serialized = yaml.safe_dump(config, sort_keys=False).encode()
        path.write_bytes(serialized)
        warm_point = {name: float(values[name]) for name in sampled}
        records.append({'lens': lens, 'seed': seed, 'parent_family_seed': original_seed,
                        'parent_active_segment_seed': evidence['active_segment_seed'],
                        'parent_snapshot': str(parent_chain.relative_to(ROOT)),
                        'parent_snapshot_sha256': evidence['sha256'], 'parent_row_index': len(rows) - 1,
                        'fixed_initial_point': warm_point,
                        'config': str(path.relative_to(ROOT)),
                        'config_sha256': hashlib.sha256(serialized).hexdigest(),
                        'outdir': f'runs/20261004_math_review_cmb_quad_chain_{lens}_seed{seed}',
                        'omp_threads': 4, 'covariance_sha256': hashlib.sha256(covariance).hexdigest(),
                        'unchanged_likelihoods_and_physical_priors_verified': True,
                        'stopping_and_integer_holding_settings_verified': True})
assert len({entry['seed'] for entry in records}) == 8
manifest = {'utc': datetime.now(timezone.utc).isoformat(),
            'scope': 'fresh_quadrature_repaired_common_grid_posterior_cohort',
            'replicas_per_lens': 4, 'omp_threads_per_process': 4, 'total_omp_threads': 32,
            'numerical_settings': {'l_max_scalars': 4095, 'tol_ncdm_bg': 1e-8},
            'pool_with_legacy_or_intermediate_targets': False,
            'old_prefixes_appended_to_new_chains': False,
            'posterior_convergence_verified': False, 'posterior_accuracy_certified': False,
            'runs': records}
(HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
print('Prepared eight fresh quadrature-repaired configs; physical priors and likelihoods match parents.')
