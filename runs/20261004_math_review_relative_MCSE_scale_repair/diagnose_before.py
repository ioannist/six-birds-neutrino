#!/usr/bin/env python3
"""Diagnose matched independent chain bundles without pooling their chronology."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys

import yaml
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from extract_mnu_limits import _resolve_prefix_from_run_dir, _load_chains_raw
from sbt_spt_audit.mcmc_diagnostics import rank_tail_diagnostics
from sbt_spt_audit.mcmc import mcmc_config_options, require_unit_temperature


def _native_backend_provenance(runs, configs):
    """Prevent pooling recorded distinct CLASS builds or verified/unknown builds.

    Legacy bundles without any build evidence retain their historical workflow,
    with the unverified target-identity assumption explicit in the report.
    A current installed module cannot establish the backend of an archived chain.
    """
    if 'classy' not in configs[0].get('theory', {}):
        return [], 'configuration_only_native_build_identity_not_recorded'
    records = []
    for run, cfg in zip(runs, configs):
        witnesses = []
        for name in ['solver_backend.json', 'runtime_state.json']:
            path = run / name
            if not path.exists():
                continue
            data = json.loads(path.read_text())
            if not isinstance(data, dict):
                raise ValueError('Native backend record must be a JSON object.')
            digest = data.get('module_sha256')
            if digest is None:
                continue
            if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
                raise ValueError('Native backend record requires a valid module SHA256.')
            witnesses.append({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                              'module_sha256': digest})
        hashes = {w['module_sha256'] for w in witnesses}
        if len(hashes) > 1:
            raise ValueError('Conflicting native backend records within one chain bundle.')
        digest = next(iter(hashes), None)
        notes = cfg.get('notes')
        requirement = notes.get('classy_backend') if isinstance(notes, dict) else None
        if requirement is not None:
            expected = requirement.get('module_sha256') if isinstance(requirement, dict) else None
            if digest is None or digest != expected:
                raise ValueError('Declared CLASS backend lacks matching recorded launch evidence.')
        records.append({'run': str(run), 'module_sha256': digest, 'witnesses': witnesses})
    hashes = {r['module_sha256'] for r in records}
    if len(hashes) > 1:
        raise ValueError('Bundles do not use the same recorded native backend; '
                         'different builds or recorded/unknown identities cannot be pooled.')
    scope = ('recorded_native_module_hash_agreement_not_uniform_solver_accuracy'
             if records[0]['module_sha256'] else 'unrecorded_native_builds_target_identity_assumed')
    return records, scope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, action='append', required=True)
    parser.add_argument('--param', action='append', help='Defaults to every sampled parameter')
    parser.add_argument('--burnin-frac', type=float, default=.2)
    parser.add_argument('--quantile-mcse-limit', type=float, default=.001,
                        help='Absolute limit for mass, or a sole explicitly requested parameter')
    parser.add_argument('--relative-quantile-mcse-limit', type=float, default=.05,
                        help='Other parameters: MCSE limit as a fraction of empirical posterior SD')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not np.isfinite(args.relative_quantile_mcse_limit) or args.relative_quantile_mcse_limit <= 0:
        parser.error('A positive finite relative MCSE limit is required')
    runs = [p.resolve() for p in args.run_dir]
    if len(set(runs)) != len(runs):
        parser.error('Duplicate run bundle would duplicate chain evidence.')
    configs = [yaml.safe_load((p / 'resolved.yaml').read_text()) for p in runs]
    for cfg in configs:
        require_unit_temperature(mcmc_config_options(cfg))
    signature = {k: configs[0].get(k) for k in ('likelihood', 'theory', 'prior')}
    priors = {n: c.get('prior') for n, c in configs[0]['params'].items() if isinstance(c, dict) and 'prior' in c}
    for cfg in configs[1:]:
        if signature != {k: cfg.get(k) for k in signature}:
            raise ValueError('Bundles do not use identical likelihoods, theory, and external priors.')
        other = {n: c.get('prior') for n, c in cfg['params'].items() if isinstance(c, dict) and 'prior' in c}
        if priors != other:
            raise ValueError('Bundles do not use identical sampled parameter priors.')
        # Derived mappings and fixed values are substantive too. Ref/proposal
        # may differ across starts, but the rest of parameterization must match.
        clean = lambda c: {n: {k: v for k, v in b.items() if k not in ('ref', 'proposal')}
                            if isinstance(b, dict) else b for n, b in c['params'].items()}
        if clean(cfg) != clean(configs[0]):
            raise ValueError('Bundles do not use identical fixed/derived parameterization.')
    backend_records, backend_scope = _native_backend_provenance(runs, configs)
    seeds = [mcmc_config_options(c).get('seed') for c in configs]
    if len(runs) > 1 and (None in seeds or len(set(seeds)) != len(seeds)):
        raise ValueError('Separate bundles require recorded distinct sampler seeds.')
    params = args.param or list(priors)
    prefixes = [_resolve_prefix_from_run_dir(r) for r in runs]
    if len(set(prefixes)) != len(prefixes):
        raise ValueError('Bundles resolve to duplicate chain prefixes.')
    diagnostics = {}
    for param in params:
        chains = [chain for prefix in prefixes for chain in _load_chains_raw(prefix, param, args.burnin_frac)]
        try:
            if param in ('mnu', 'mnu_sample') or (args.param and len(args.param) == 1):
                limit = args.quantile_mcse_limit
                precision_scope = 'absolute_parameter_units'
            else:
                values = np.concatenate([v for v, w in chains])
                weights = np.concatenate([w for v, w in chains])
                weights = weights / weights.max()
                mean = np.average(values, weights=weights)
                sd = np.sqrt(np.average((values - mean) ** 2, weights=weights))
                limit = args.relative_quantile_mcse_limit * sd
                precision_scope = 'fraction_of_empirical_posterior_standard_deviation'
            diagnostics[param] = rank_tail_diagnostics(chains, quantile_mcse_limit=limit)
            diagnostics[param]['precision_target_scope'] = precision_scope
        except ValueError as exc:
            diagnostics[param] = {'diagnostic_thresholds_pass': False, 'error': str(exc)}
    report = {'runs': [str(r) for r in runs], 'prefixes': [str(p) for p in prefixes],
              'seeds': seeds, 'burnin_fraction_of_stored_rows': args.burnin_frac,
              'diagnostics': diagnostics,
              'all_diagnostic_thresholds_pass': all(d['diagnostic_thresholds_pass'] for d in diagnostics.values()),
              'independence_scope': 'separate recorded seeds and chain files; initialization independence assumed',
              'native_backend_provenance': backend_records,
              'native_backend_identity_scope': backend_scope,
              'packages': {n: importlib.metadata.version(n) for n in ('arviz', 'arviz_stats', 'numpy', 'scipy')}}
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(f'Diagnostic thresholds pass: {report["all_diagnostic_thresholds_pass"]}; report: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
