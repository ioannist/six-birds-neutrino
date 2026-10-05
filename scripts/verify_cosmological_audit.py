#!/usr/bin/env python3
"""Recompute exported cosmological endpoints with fresh theory and native likelihoods."""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from run_cosmological_audit import (Audit, get_model, write_json, get_bin_spec_types,
                                    localize_quadratic_difference, validate_transfer_domain)


def verify(run, directions=None):
    cfg = yaml.safe_load((run / 'resolved.yaml').read_text())
    stored = json.loads((run / 'metrics.json').read_text())
    endpoints = [('B_given_A', 'lensB'), ('A_given_B', 'lensA')]
    expected = {direction for direction, _ in endpoints}
    available = set(stored['directions'])
    if directions is None:
        if available != expected:
            raise ValueError('Both directions must be complete before verification.')
        directions = expected
    else:
        directions = tuple(directions)
        if not directions or len(set(directions)) != len(directions) or set(directions) - expected:
            raise ValueError('Select distinct known directions for partial verification.')
        if set(directions) - available:
            raise ValueError('All selected directions must be complete before verification.')
    verified = {}
    with get_model(cfg, stop_at_error=True) as model:
        audit = Audit(model, cfg, stored['completion_likelihoods'], run, 25, .02)
        for direction, lens in endpoints:
            if direction not in directions:
                continue
            original = stored['directions'][direction]
            source_lens = 'lensA' if lens == 'lensB' else 'lensB'
            source = original.get('source_candidate')
            if source is None:
                # Legacy bundles retain the initial source fit in the fits mapping.
                source = stored['fits'][source_lens]
            validate_transfer_domain(original, source, audit.names)
            cross, reference = original['cross_candidate'], original['reference_candidate']
            a, b = [audit.ledger(lens, c['point']) for c in (cross, reference)]
            delta = -2 * (a[0] - b[0])
            if not np.allclose([a[0], b[0], delta],
                               [cross['loglike'], reference['loglike'], original['joint_candidate_delta_chi2']],
                               rtol=1e-10, atol=1e-7):
                raise ValueError(f'{direction}: exported scalar endpoints do not reproduce.')
            adapter = model.likelihood[lens]
            grid, groups, _, ledger = localize_quadratic_difference(
                a[3], a[2], b[2], get_bin_spec_types(adapter._like_obj),
                adapter._like_obj.effective_ells, original['ell_edges'], best_cov=b[3])
            native_spt = -2 * (a[1][lens] - b[1][lens])
            for term in ('prior_penalty', 'covariance_normalization'):
                ledger['delta_' + term] = a[4][term] - b[4][term]
            ledger_delta = (ledger['deltaQ_full'] + ledger['delta_prior_penalty']
                            + ledger['delta_covariance_normalization'])
            if not np.isclose(native_spt, ledger_delta, rtol=1e-10, atol=1e-7):
                raise ValueError(f'{direction}: native SPT accounting does not reproduce.')
            for key, value in ledger.items():
                old = original['spt_ledger'][key]
                if isinstance(value, (int, float)):
                    if not np.isclose(value, old, atol=1e-7, rtol=1e-10):
                        raise ValueError(f'{direction}: stored ledger field {key} differs.')
                elif value != old:
                    raise ValueError(f'{direction}: stored ledger definition differs.')
            component_deltas = {k: -2 * (a[1][k] - b[1][k]) for k in audit.completion + [lens]}
            if not np.isclose(sum(component_deltas.values()), delta, atol=1e-7, rtol=1e-10):
                raise ValueError(f'{direction}: joint accounting does not reproduce.')
            for k, value in component_deltas.items():
                if not np.isclose(value, original['signed_component_delta_chi2'][k], atol=1e-7, rtol=1e-10):
                    raise ValueError(f'{direction}: stored component {k} differs.')
            for spec in grid:
                if not np.allclose(grid[spec], original['spt_deltaQ_by_spec_ell'][spec], atol=1e-7, rtol=1e-10):
                    raise ValueError(f'{direction}: stored localization differs.')
            for endpoint, path_key in [(a, 'train'), (b, 'reference')]:
                with np.load(run / f'{direction}_spectra.npz') as spectra:
                    for k, value in endpoint[5].items():
                        if not np.allclose(spectra[f'{path_key}_{k}'], value, atol=1e-7, rtol=1e-10):
                            raise ValueError(f'{direction}: exported spectra differ.')
            verified[direction] = {'joint_candidate_delta_chi2': delta,
                                   'signed_component_delta_chi2': component_deltas,
                                   'spt_native_reconstruction_error': ledger_delta - native_spt,
                                   'top_groups': groups, 'ledger': ledger,
                                   'fresh_endpoint_spectra_verified': True,
                                   'fixed_source_coordinates_verified': True,
                                   'candidate_reference_nesting_verified': True,
                                   'global_optimum_certified': False}
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--direction', action='append', choices=['B_given_A', 'A_given_B'],
                        help='Explicitly verify only selected completed directions; '
                             'omit to require both directions.')
    args = parser.parse_args()
    write_json(args.output, verify(args.audit_dir.resolve(), args.direction))
    print(f'Fresh cosmological endpoint verification: {args.output}')


if __name__ == '__main__':
    main()
