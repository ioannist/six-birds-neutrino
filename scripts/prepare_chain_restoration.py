#!/usr/bin/env python3
"""Prepare independently seeded replacement chains with a matched backend lmax.

Only starting distributions and sampler settings change; target priors, spectra
models, nuisance defaults, and completion components are inherited explicitly.
No sampling or posterior certification occurs in this preparation step.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import yaml
from run_cosmological_audit import SPT, build_common_config, write_json
from sbt_spt_audit.candl_support import load_test_vector


def window_lmax(expr):
    vector = load_test_vector(expr)
    path = Path(vector.dataset_path)
    dataset = yaml.safe_load(path.read_text())
    folder = path.parent / dataset['window_functions_folder']
    files = sorted(folder.glob('*.txt'))
    if not files:
        raise ValueError(f'No text window functions: {folder}')
    maximum = 0
    for p in files:
        ell = np.loadtxt(p, usecols=0)
        if ell.ndim != 1 or not np.all(np.isfinite(ell)) or not np.all(np.diff(ell) == 1):
            raise ValueError(f'Invalid window multipole support: {p}')
        if ell[-1] != int(ell[-1]):
            raise ValueError('Noninteger maximum multipole.')
        maximum = max(maximum, int(ell[-1]))
    return maximum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configA', type=Path, required=True)
    parser.add_argument('--configB', type=Path, required=True)
    parser.add_argument('--fitA', type=Path, required=True)
    parser.add_argument('--fitB', type=Path, required=True)
    parser.add_argument('--outdir', type=Path, required=True)
    parser.add_argument('--replicas', type=int, default=4)
    parser.add_argument('--first-seed', type=int, default=301)
    parser.add_argument('--max-samples', type=int, default=20000, help='Per replica; stopping early still requires independent diagnostics')
    args = parser.parse_args()
    if args.replicas < 2 or args.max_samples < 1000:
        parser.error('At least two replicas and 1000 samples are required')
    configs = [yaml.safe_load(p.read_text()) for p in (args.configA, args.configB)]
    build_common_config(*configs)  # Match the substantive completion before writing.
    fits = [json.loads(p.read_text()) for p in (args.fitA, args.fitB)]
    shared_lmax = max(window_lmax(c['likelihood'][SPT]['dataset_expr']) for c in configs)
    args.outdir.mkdir(parents=True, exist_ok=False)
    manifest = {'scope': 'new_posterior_chains_not_certified_converged',
                'shared_backend_lmax': shared_lmax, 'runs': [],
                'starting_fits': [str(p.resolve()) for p in (args.fitA, args.fitB)],
                'starting_fit_snapshots': fits,
                'fit_scope': 'numerical_candidate_used_only_to_initialize_sampler',
                'sampler_weights': 'integer_holding_times_no_oversampling_thinning'}
    for lens, cfg, fit in zip(('A', 'B'), configs, fits):
        backend = next(iter(cfg['theory']))
        if len(cfg['theory']) != 1 or backend not in ('camb', 'classy'):
            raise ValueError('Only one explicit CAMB or CLASS backend is supported.')
        settings = cfg['theory'][backend].setdefault('extra_args', {})
        key = 'lmax' if backend == 'camb' else 'l_max_scalars'
        settings[key] = max(shared_lmax, int(settings.get(key, 0)))
        for name, block in cfg['params'].items():
            if isinstance(block, dict) and 'prior' in block:
                value = float(fit['point'][name])
                prior = block['prior']
                if not np.isfinite(value) or not prior['min'] <= value <= prior['max']:
                    raise ValueError(f'Warm start outside {name} prior.')
                block['ref'] = {'dist': 'norm', 'loc': value, 'scale': float(block['proposal'])}
        for replica in range(args.replicas):
            seed = args.first_seed + replica + (0 if lens == 'A' else args.replicas)
            one = deepcopy(cfg)
            one['run_name'] = f'math_restoration_{lens}_seed{seed}'
            one['sampler'] = {'mcmc': {'seed': seed, 'max_samples': args.max_samples,
                              'learn_proposal': True, 'Rminus1_stop': .01,
                              'Rminus1_cl_stop': .05, 'Rminus1_cl_level': .95,
                              'oversample_power': 0, 'oversample_thin': False}}
            one['notes'] = dict(one.get('notes', {}),
                math_review='Fresh independently seeded chain; native termination and sample cap do not certify posterior precision.',
                matched_theory_lmax=shared_lmax,
                warm_start_fit=str((args.fitA if lens == 'A' else args.fitB).resolve()))
            path = args.outdir / f'{lens}_seed{seed}.yaml'
            path.write_text(yaml.safe_dump(one, sort_keys=False))
            manifest['runs'].append({'lens': lens, 'seed': seed, 'config': str(path.resolve())})
    write_json(args.outdir / 'manifest.json', manifest)
    print(f'Prepared {len(manifest["runs"])} independent chain configs: {args.outdir}')


if __name__ == '__main__':
    main()
