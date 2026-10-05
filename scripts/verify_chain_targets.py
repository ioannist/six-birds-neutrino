#!/usr/bin/env python3
"""Re-evaluate selected immutable chain rows against fresh native likelihoods.

This checks recorded posterior accounting and sampled target consistency at
selected points. It does not certify every transition or posterior convergence.
Text output rounds parameters and likelihoods, so comparison tolerances are
explicit numerical controls, not rigorous interval error bounds.
"""
import argparse
from io import StringIO
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from cobaya.model import get_model
from extract_mnu_limits import _resolve_prefix_from_run_dir


def compare_native_row(header, row, model, atol=.002, rtol=1e-6):
    if len(header) != len(row) or not np.all(np.isfinite(row)):
        raise ValueError('Finite chain row matching its column header required.')
    values = dict(zip(header, row))
    point = {n: float(values[n]) for n in model.parameterization.sampled_params()}
    fresh = model.logposterior(point, cached=False)
    expected = {'minuslogpost': -float(fresh.logpost),
                'minuslogprior': -float(sum(fresh.logpriors)),
                'chi2': -2 * float(sum(fresh.loglikes))}
    expected.update({f'chi2__{n}': -2 * float(v)
                     for n, v in zip(model.likelihood, fresh.loglikes)})
    errors = {}
    for name, value in expected.items():
        if name not in values:
            raise ValueError(f'Missing recorded target component: {name}')
        if not np.isfinite(value) or not np.isclose(value, values[name], atol=atol, rtol=rtol):
            raise ValueError(f'Fresh native target differs for {name}: '
                             f'stored {values[name]}, fresh {value}')
        errors[name] = float(value - values[name])
    return {'point': point, 'fresh_minuslogpost': expected['minuslogpost'],
            'fresh_minus_recorded': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, action='append', required=True,
                        help='Use immutable snapshots while a sampler is still writing.')
    parser.add_argument('--rows-per-chain', type=int, default=3)
    parser.add_argument('--atol', type=float, default=.002)
    parser.add_argument('--rtol', type=float, default=1e-6)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.rows_per_chain < 2 or not np.isfinite(args.atol) or args.atol <= 0 or not np.isfinite(args.rtol) or args.rtol < 0:
        parser.error('At least two rows and finite nonnegative tolerances required, with atol > 0.')
    report = []
    for run in args.run_dir:
        cfg = yaml.safe_load((run / 'resolved.yaml').read_text())
        prefix = _resolve_prefix_from_run_dir(run)
        files = sorted(prefix.parent.glob(prefix.name + '.*.txt'))
        if not files:
            raise ValueError(f'No chain files for {run}')
        with get_model(cfg, stop_at_error=True) as model:
            for path in files:
                raw = path.read_bytes()
                text = raw.decode()
                header = text.splitlines()[0].lstrip('#').split()
                if len(set(header)) != len(header):
                    raise ValueError('Chain column names must be distinct.')
                rows = np.atleast_2d(np.loadtxt(StringIO(text)))
                if not rows.size or rows.shape[1] != len(header):
                    raise ValueError('No valid chain rows.')
                indices = np.unique(np.linspace(0, len(rows) - 1,
                                               min(len(rows), args.rows_per_chain), dtype=int))
                checks = [dict(row_index=int(i), **compare_native_row(
                    header, rows[i], model, args.atol, args.rtol)) for i in indices]
                report.append({'run': str(run.resolve()), 'file': str(path.resolve()),
                               'file_sha256': hashlib.sha256(raw).hexdigest(),
                               'total_stored_rows': len(rows), 'checks': checks})
                print(f'Fresh target verified: {run}, {len(checks)} rows', flush=True)
    args.output.write_text(json.dumps({'scope': 'selected_native_target_consistency_only',
        'atol': args.atol, 'rtol': args.rtol, 'tolerance_accounts_for_text_rounding': True,
        'interval_error_certified': False, 'posterior_convergence_certified': False,
        'chains': report}, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
