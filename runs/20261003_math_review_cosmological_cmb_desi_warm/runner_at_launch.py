#!/usr/bin/env python3
"""Candidate cosmological transfer audit with one common Boltzmann calculation.

Fits maximize each SPT lens plus the identical configured completion likelihoods,
subject to the identical sampled-parameter box. SPT component differences are
signed contributions, not differences from SPT-alone maxima. No global optimum
or posterior convergence is certified by this runner.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model
import pybobyqa
from sbt_spt_audit.candl_support import (
    compute_gaussian_residual_and_covariance, gaussian_native_adjustment,
    get_bin_spec_types,
)
from sbt_spt_audit.localization import localize_quadratic_difference

SPT = 'sbt_spt_audit.likelihoods.candl_cobaya.CandlCobayaLikelihood'
COSMO = {'omegabh2', 'omegach2', 'H0', 'logA', 'ns', 'tau', 'mnu', 'mnu_sample'}


def build_common_config(a, b, cuts=None):
    """Reject unmatched completion, parameterization, or backend settings."""
    for key in ('params', 'theory', 'prior'):
        if a.get(key) != b.get(key):
            raise ValueError(f'Configurations differ in {key}; no matched completion.')
    completion_a = {k: v for k, v in a['likelihood'].items() if k != SPT}
    completion_b = {k: v for k, v in b['likelihood'].items() if k != SPT}
    if completion_a != completion_b:
        raise ValueError('Configurations differ in completion likelihoods.')
    cfg = {k: deepcopy(a[k]) for k in ('params', 'theory', 'prior') if k in a}
    cfg['likelihood'] = deepcopy(completion_a)
    for name, original in [('lensA', a), ('lensB', b)]:
        block = deepcopy(original['likelihood'][SPT])
        block['class'] = SPT
        # The adapter declares all supported scalar inputs, including tau.
        block.pop('input_params', None)
        if cuts is not None:
            block['ell_cuts'] = deepcopy(cuts)
        cfg['likelihood'][name] = block
    return cfg, list(completion_a)


def write_json(path, payload):
    # Refuse NaN/Infinity receipts: a failed evaluation is not evidence.
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')


def chain_start(run, names):
    """Archived best stored posterior point is only an optimization start."""
    candidates = []
    for path in sorted((run / 'chains').glob('*.txt')):
        header = path.open().readline().lstrip('#').split()
        if 'minuslogpost' not in header or not set(names) <= set(header):
            continue
        values = np.atleast_2d(np.loadtxt(path))
        if values.shape[1] != len(header) or not np.all(np.isfinite(values)):
            raise ValueError(f'Invalid chain rows: {path}')
        i = np.argmin(values[:, header.index('minuslogpost')])
        candidates.append((values[i, header.index('minuslogpost')],
                           {n: float(values[i, header.index(n)]) for n in names}, str(path)))
    if not candidates:
        raise ValueError(f'No compatible stored point in {run}')
    _, point, origin = min(candidates, key=lambda x: x[0])
    return point, origin


class Audit:
    def __init__(self, model, cfg, completion, out, maxfun, rhoend):
        self.model, self.cfg, self.completion, self.out = model, cfg, completion, out
        self.names = list(model.parameterization.sampled_params())
        self.bounds = np.asarray(model.prior.bounds(), dtype=float)
        if not np.all(np.isfinite(self.bounds)):
            raise ValueError('This runner requires finite hard bounds.')
        self.scales = {n: float(cfg['params'][n]['proposal']) for n in self.names}
        if any(not np.isfinite(v) or v <= 0 for v in self.scales.values()):
            raise ValueError('Finite positive parameter scales are required.')
        self.maxfun, self.rhoend = maxfun, rhoend
        self.evaluations = 0

    def evaluate(self, point, lens, cached=True):
        x = np.asarray([point[n] for n in self.names])
        if not np.all(np.isfinite(x)) or np.any(x < self.bounds[:, 0]) or np.any(x > self.bounds[:, 1]):
            raise ValueError('Evaluation outside declared common parameter domain.')
        likes = self.model.loglikes(point, as_dict=True, return_derived=False, cached=cached)
        components = {k: float(v) for k, v in likes.items()}
        total = float(sum(components[k] for k in self.completion + [lens]))
        self.evaluations += 1
        if not np.isfinite(total):
            raise ValueError('Nonfinite objective inside sampled parameter domain.')
        return total, components

    def fit(self, lens, initial, free, label):
        baseline, _ = self.evaluate(initial, lens)
        if not free:
            return {'point': dict(initial), 'loglike': baseline, 'success': True,
                    'scope': 'evaluation_no_free_parameters', 'free': [], 'n_evals': 1}
        ix = [self.names.index(n) for n in free]
        origin = np.asarray([initial[n] for n in free])
        scales = np.asarray([self.scales[n] for n in free])
        lower = (self.bounds[ix, 0] - origin) / scales
        upper = (self.bounds[ix, 1] - origin) / scales
        best = {'point': dict(initial), 'loglike': baseline}
        calls = 0
        started = time.monotonic()

        def objective(x):
            nonlocal calls
            point = dict(initial)
            point.update(zip(free, (origin + scales * x).tolist()))
            # Bound projection handles only floating point overshoot.
            for n, j in zip(free, ix):
                point[n] = float(np.clip(point[n], *self.bounds[j]))
            value, _ = self.evaluate(point, lens)
            calls += 1
            if value > best['loglike']:
                best.update(point=point, loglike=value)
            if calls % 25 == 0:
                print(f'{label}: evaluations={calls} best_loglike={best["loglike"]:.8f}', flush=True)
                write_json(self.out / f'{label}_progress.json', best)
            return -value

        result = pybobyqa.solve(objective, np.zeros(len(free)), bounds=(lower, upper),
                                rhobeg=1., rhoend=self.rhoend, maxfun=self.maxfun,
                                do_logging=False)
        best.update(success=bool(result.flag == result.EXIT_SUCCESS),
                    flag=int(result.flag), message=str(result.msg), free=free,
                    n_evals=calls, elapsed_seconds=time.monotonic() - started,
                    scope='bounded_numerical_candidate_not_global_certificate')
        write_json(self.out / f'{label}.json', best)
        print(f'{label}: {best["message"]}; best_loglike={best["loglike"]:.8f}', flush=True)
        return best

    def ledger(self, lens, point):
        total, components = self.evaluate(point, lens, cached=False)
        adapter = self.model.likelihood[lens]
        inputs = self.model.parameterization.to_input(point)
        pars = adapter.current_candl_params({n: inputs[n] for n in adapter.input_params})
        residual, covariance = compute_gaussian_residual_and_covariance(adapter._like_obj, pars)
        adjustment = gaussian_native_adjustment(adapter._like_obj, pars, {}, residual, covariance)
        native = float(adapter._like_obj.log_like(pars))
        if not np.isclose(native, components[lens], atol=1e-7, rtol=1e-10):
            raise ValueError('Cobaya/candl endpoint likelihood bridge failed.')
        return total, components, residual, covariance, adjustment, pars['Dl']

    def direction(self, lens, source, target, label):
        shared = [n for n in self.names if n in COSMO]
        nuisance = [n for n in self.names if n not in shared]
        initial = dict(target['point'])
        initial.update({n: source['point'][n] for n in shared})
        cross = self.fit(lens, initial, nuisance, label + '_profile')
        # The reference frees a superset, initialized at the cross candidate.
        # Keep the better of the own-fit and this new candidate, preserving nesting
        # without pretending a heuristic optimizer has certified a supremum.
        refreshed = self.fit(lens, cross['point'], self.names, label + '_reference')
        reference = max([target, refreshed, cross], key=lambda r: r['loglike'])
        train = self.ledger(lens, cross['point'])
        best = self.ledger(lens, reference['point'])
        for endpoint, candidate in [(train, cross), (best, reference)]:
            if not np.isclose(endpoint[0], candidate['loglike'], atol=1e-7, rtol=1e-10):
                raise ValueError('Uncached endpoint differs from stored optimizer likelihood.')
        delta = -2 * (train[0] - best[0])
        adapter = self.model.likelihood[lens]
        edges = [400., 800., 1200., 1600., 2000., 2500., 3000., 4000., 5000., 6000.]
        grid, groups, spectra, accounting = localize_quadratic_difference(
            train[3], train[2], best[2], get_bin_spec_types(adapter._like_obj),
            adapter._like_obj.effective_ells, edges, best_cov=best[3])
        for key in ('prior_penalty', 'covariance_normalization'):
            accounting['delta_' + key] = train[4][key] - best[4][key]
        sp_delta = -2 * (train[1][lens] - best[1][lens])
        reconstructed = (accounting['deltaQ_full'] + accounting['delta_prior_penalty']
                         + accounting['delta_covariance_normalization'])
        if not np.isclose(reconstructed, sp_delta, atol=1e-7, rtol=1e-10):
            raise ValueError('SPT component accounting bridge failed.')
        component_deltas = {k: -2 * (train[1][k] - best[1][k]) for k in self.completion + [lens]}
        if not np.isclose(sum(component_deltas.values()), delta, atol=1e-7, rtol=1e-10):
            raise ValueError('Joint component accounting bridge failed.')
        np.savez_compressed(self.out / f'{label}_spectra.npz',
                           **{f'train_{k}': np.asarray(v) for k, v in train[5].items()},
                           **{f'reference_{k}': np.asarray(v) for k, v in best[5].items()})
        return {'scope': 'SPT_plus_configured_completion_candidate_transfer',
                'shared_parameters': shared, 'profiled_parameters': nuisance,
                'cross_candidate': cross, 'reference_candidate': reference,
                'joint_candidate_delta_chi2': delta,
                'signed_component_delta_chi2': component_deltas,
                'spt_ledger': accounting, 'spt_accounting_error': reconstructed - sp_delta,
                'spt_deltaQ_by_spec_ell': grid, 'top_groups': groups,
                'spectra': spectra, 'ell_edges': edges,
                'optimization_success': cross['success'] and refreshed['success'] and target['success'],
                'global_optimum_certified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configA', type=Path, required=True)
    parser.add_argument('--configB', type=Path, required=True)
    parser.add_argument('--start-runA', type=Path)
    parser.add_argument('--start-runB', type=Path)
    parser.add_argument('--start-fitA', type=Path, help='JSON candidate with a point mapping; warm start only')
    parser.add_argument('--start-fitB', type=Path, help='JSON candidate with a point mapping; warm start only')
    parser.add_argument('--no-ref-start', action='store_true', help='Use an explicit warm start instead of a second reference-point start')
    parser.add_argument('--outdir', type=Path, required=True)
    parser.add_argument('--packages-path', type=Path, default=ROOT / 'external/cobaya_packages')
    parser.add_argument('--maxfun', type=int, default=500)
    parser.add_argument('--rhoend', type=float, default=0.02, help='Tolerance in proposal-scaled coordinates')
    staging = parser.add_mutually_exclusive_group()
    staging.add_argument('--common-cuts', action='store_true', help='Symmetric TT[750,3000], TE/EE[400,3000] support cuts')
    staging.add_argument('--d1-support-cut', action='store_true', help='Original one-sided D1 TT[750,3000], TE/EE[300,3000] support control')
    args = parser.parse_args()
    if args.maxfun < 25 or not 0 < args.rhoend < 1:
        parser.error('maxfun >= 25 and 0 < rhoend < 1 are required')
    out = args.outdir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    a, b = [yaml.safe_load(p.read_text()) for p in (args.configA, args.configB)]
    cuts = {'TT': [750., 3000.], 'TE': [400., 3000.], 'EE': [400., 3000.]} if args.common_cuts else None
    cfg, completion = build_common_config(a, b, cuts)
    if args.d1_support_cut:
        cfg['likelihood']['lensB']['ell_cuts'] = {'TT': [750., 3000.], 'TE': [300., 3000.], 'EE': [300., 3000.]}
    cfg['packages_path'] = str(args.packages_path.resolve())
    (out / 'resolved.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False))
    write_json(out / 'inputs.json', {'configA': str(args.configA.resolve()), 'configB': str(args.configB.resolve()),
               'sha256A': hashlib.sha256(args.configA.read_bytes()).hexdigest(),
               'sha256B': hashlib.sha256(args.configB.read_bytes()).hexdigest(),
               'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'working_tree_diff': subprocess.check_output(['git', 'diff'], cwd=ROOT, text=True),
               'arguments': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}})
    (out / 'env.txt').write_text(subprocess.check_output([sys.executable, str(ROOT / 'scripts/print_env.py')], text=True))
    with get_model(cfg, stop_at_error=True) as model:
        audit = Audit(model, cfg, completion, out, args.maxfun, args.rhoend)
        ref = {n: float(cfg['params'][n]['ref']) for n in audit.names}
        fits = {}
        for lens, run, fit in [('lensA', args.start_runA, args.start_fitA), ('lensB', args.start_runB, args.start_fitB)]:
            starts = [] if args.no_ref_start else [ref]
            if run:
                point, origin = chain_start(run, audit.names)
                starts.insert(0, point)
                write_json(out / f'{lens}_start_origin.json', {'origin': origin, 'use': 'warm_start_only'})
            if fit:
                candidate = json.loads(fit.read_text())
                point = {n: float(candidate['point'][n]) for n in audit.names}
                starts.insert(0, point)
                write_json(out / f'{lens}_fit_start_origin.json',
                           {'origin': str(fit.resolve()), 'sha256': hashlib.sha256(fit.read_bytes()).hexdigest(),
                            'point': point, 'use': 'warm_start_only'})
            if not starts:
                raise ValueError('--no-ref-start requires an explicit warm start for both lenses.')
            results = [audit.fit(lens, p, audit.names, f'{lens}_fit_{i}') for i, p in enumerate(starts)]
            fits[lens] = max(results, key=lambda r: r['loglike'])
        write_json(out / 'fits.json', fits)
        directions = {}
        for lens, source, label in [('lensB', 'lensA', 'B_given_A'), ('lensA', 'lensB', 'A_given_B')]:
            directions[label] = audit.direction(lens, fits[source], fits[lens], label)
            write_json(out / 'metrics.json', {'completion_likelihoods': completion, 'directions': directions,
                       'fit_objective': 'sum_native_loglikes_excluding_Cobaya_prior_with_hard_prior_bounds',
                       'same_theory_spectra_for_both_lenses': True,
                       'posterior_convergence_verified': False, 'fits': fits,
                       'lens_metadata': {n: asdict(model.likelihood[n]._like_meta) for n in fits}})
    print(f'Run bundle: {out}')
    return 0 if all(d['optimization_success'] for d in directions.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
