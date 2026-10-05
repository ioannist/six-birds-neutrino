#!/usr/bin/env python3
"""Compare fresh native likelihoods under declared Boltzmann precision settings.

This is a sampled numerical sensitivity control. It provides neither an interval
error bound nor a posterior convergence or precision certificate.
"""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import time

import numpy as np
import yaml
from run_cosmological_audit import get_model, write_json


def main(required_backend=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--points', type=Path, required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--outdir', type=Path, required=True)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    if len(cfg['theory']) != 1 or next(iter(cfg['theory'])) not in {'classy', 'camb'}:
        raise ValueError('A single CLASS or CAMB backend is required.')
    backend = next(iter(cfg['theory']))
    if required_backend is not None and backend != required_backend:
        raise ValueError(f'A single {required_backend} backend is required.')
    points = json.loads(args.points.read_text())
    settings = json.loads(args.settings.read_text())
    if backend == 'classy':
        import classy
        header = (Path(classy.__file__).parent / 'include' / 'precisions.h').read_text()
        allowed = set(re.findall(r'class_(?:precision|type)_parameter\(\s*(\w+)\s*,', header))
    else:
        # Restrict this control to CAMB's three documented accuracy boosts.
        # Physical theory parameters are never accepted as precision settings.
        allowed = {'AccuracyBoost', 'lAccuracyBoost', 'lSampleBoost'}
    if not settings['settings'] or set(settings['settings']) - allowed:
        raise ValueError('Only declared numerical precision parameters may be changed.')
    if not all(isinstance(v, (int, float)) and np.isfinite(v)
               for v in settings['settings'].values()):
        raise ValueError('Finite numeric precision settings required.')
    if backend == 'camb' and any(v <= 0 for v in settings['settings'].values()):
        raise ValueError('CAMB accuracy boosts must be positive.')
    args.outdir.mkdir(parents=True, exist_ok=True)
    output = args.outdir / 'metrics.json'
    if output.exists():
        raise ValueError('Completed precision results already exist.')
    runtime = {'status': 'running_no_numerical_accuracy_certificate', 'pid': os.getpid(),
               'omp_threads': os.environ.get('OMP_NUM_THREADS')}
    write_json(args.outdir / 'runtime_state.json', runtime)
    records, spectra = {}, {}
    for variant in ['baseline', 'selected_reference_settings']:
        one = deepcopy(cfg)
        if variant != 'baseline':
            one['theory'][backend].setdefault('extra_args', {}).update(settings['settings'])
        (args.outdir / (variant + '.yaml')).write_text(yaml.safe_dump(one, sort_keys=False))
        records[variant], spectra[variant] = {}, {}
        with get_model(one, stop_at_error=True) as model:
            names = set(model.parameterization.sampled_params())
            requested_cl = model.theory[backend].requested().get('Cl', {})
            coverage = {k: int(requested_cl[k]) for k in ['tt', 'ee']}
            if any(n < 2 for n in coverage.values()):
                raise ValueError('Requested TT/EE coverage through ell >= 2 required.')
            for label, point in points.items():
                if set(point) != names or not all(np.isfinite(v) for v in point.values()):
                    raise ValueError(f'{label}: complete finite sampled point required.')
                start = time.monotonic()
                likes = model.loglikes(point, as_dict=True, return_derived=False, cached=False)
                chi2 = {n: -2 * float(v) for n, v in likes.items()}
                if not all(np.isfinite(v) for v in chi2.values()):
                    raise ValueError('Nonfinite native likelihood.')
                cl = model.provider.get_Cl(ell_factor=False, units='muK2')
                if any(np.asarray(cl[k]).ndim != 1 or len(cl[k]) <= n
                       for k, n in coverage.items()):
                    raise ValueError('Spectra do not cover the likelihood requirements.')
                spectra[variant][label] = {
                    k: np.array(cl[k][:n + 1], copy=True) for k, n in coverage.items()}
                records[variant][label] = {'point': point, 'native_chi2': chi2,
                                           'spectrum_ell_max': coverage,
                                           'elapsed_seconds': time.monotonic() - start}
                write_json(args.outdir / 'progress.json', records)
                print(f'{variant}: {label} completed', flush=True)
    comparison = {}
    for label in points:
        base, refined = [records[v][label]['native_chi2'] for v in records]
        fractional = {}
        if records['baseline'][label]['spectrum_ell_max'] != records[
                'selected_reference_settings'][label]['spectrum_ell_max']:
            raise ValueError('Likelihood spectrum requirements differ between settings.')
        for spec in ['tt', 'ee']:
            a, b = [spectra[v][label][spec] for v in records]
            if a.shape != b.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
                raise ValueError('Finite spectra with matched coverage required.')
            use = np.arange(a.size) >= 2
            if np.any(a[use] <= 0):
                raise ValueError('Positive reference TT/EE spectra required.')
            fractional[spec] = float(np.max(np.abs((b[use] - a[use]) / a[use])))
        comparison[label] = {'native_chi2_change': {n: refined[n] - base[n] for n in base},
                             'max_fractional_spectrum_change': fractional}
    changes = {}
    point_pairs = [('initial_exact_slow', 'initial_rounded_slow')]
    point_pairs += [(label, label + suffix) for label in points
                    for suffix in ['_mass_minus', '_mass_plus']
                    if label + suffix in points]
    for variant, results in records.items():
        changes[variant] = {}
        for a, b in point_pairs:
            if a not in results or b not in results:
                continue
            changes[variant][b + '_minus_' + a] = {
                n: results[b]['native_chi2'][n] - results[a]['native_chi2'][n]
                for n in results[a]['native_chi2']}
    write_json(output, {'scope': 'selected_Boltzmann_precision_and_local_parameter_sensitivity',
        'backend': backend,
        'interval_error_certified': False, 'posterior_accuracy_certified': False,
        'precision_settings_source': settings, 'records': records,
        'refined_minus_baseline': comparison, 'within_setting_point_changes': changes})
    runtime['status'] = 'complete_sampled_sensitivity_control_not_error_certificate'
    write_json(args.outdir / 'runtime_state.json', runtime)
    print(f'Precision control complete: {output}', flush=True)


if __name__ == '__main__':
    main()
