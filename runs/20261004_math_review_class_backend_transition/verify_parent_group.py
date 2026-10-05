"""Evaluate archived endpoints on each fresh guarded numerical target before launch."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
from io import BytesIO
import json
from pathlib import Path
import sys

import classy
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('group', choices=['quad_A', 'quad_B', 'medium_A', 'medium_B'])
args = parser.parse_args()
preparation = json.loads((HERE / 'preparation_receipt.json').read_text())
module = Path(importlib.import_module(classy.Class.__module__).__file__)
expected = '7a5d736220b3d236f3dc7c89944d025fe3e4c7cb4c8e4473ef807c898fc71539'
assert hashlib.sha256(module.read_bytes()).hexdigest() == expected
entries = [entry for entry in preparation['records'] if entry['cohort'] + '_' + entry['lens'] == args.group]
assert len(entries) == (3 if args.group == 'medium_A' else 4)
folder = HERE / 'parent_native_checks'
folder.mkdir(exist_ok=True)
summaries = []
for entry in entries:
    config_file = ROOT / entry['config']
    assert hashlib.sha256(config_file.read_bytes()).hexdigest() == entry['config_sha256']
    cfg = yaml.safe_load(config_file.read_text())
    cfg.pop('output', None)
    chain = ROOT / entry['archived_chain']
    raw = chain.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['archived_chain_sha256']
    header = raw.splitlines()[0].decode().lstrip('#').split()
    rows = np.atleast_2d(np.loadtxt(BytesIO(raw)))
    assert len(rows) == entry['archived_stored_rows']
    checks = []
    with get_model(cfg, stop_at_error=True) as model:
        assert type(model.theory['classy'].classy) is classy.Class
        assert list(model.parameterization.sampled_params()) == list(entry['fixed_initial_point'])
        actual_args = dict(model.theory['classy'].extra_args)
        assert len(model.likelihood) == 6 and actual_args['l_max_scalars'] == 4095
        assert all(actual_args[name] == value for name, value in cfg['theory']['classy']['extra_args'].items())
        for index in [0, len(rows)-1]:
            values = dict(zip(header, rows[index]))
            point = {name: float(values[name]) for name in model.parameterization.sampled_params()}
            fresh = model.logposterior(point, cached=False)
            native = {'minuslogpost': -float(fresh.logpost),
                      'minuslogprior': -float(sum(fresh.logpriors)),
                      'chi2': -2 * float(sum(fresh.loglikes))}
            native.update({f'chi2__{name}': -2 * float(value)
                           for name, value in zip(model.likelihood, fresh.loglikes)})
            assert all(np.isfinite(value) for value in native.values())
            differences = {name: float(value - values[name]) for name, value in native.items()}
            assert abs(differences['minuslogprior']) <= 1e-12
            checks.append({'row_index': int(index), 'point': point, 'fresh_native': native,
                           'fresh_minus_original': differences,
                           'matches_original_at_atol_1e7_rtol_1e10': all(
                               np.isclose(value, values[name], atol=1e-7, rtol=1e-10)
                               for name, value in native.items())})
    assert checks[-1]['point'] == entry['fixed_initial_point']
    result = {'utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'selected_original_endpoints_evaluated_on_fresh_guarded_target',
              'parent_seed': entry['seed'], 'replacement_seed': entry['replacement_seed'],
              'config_sha256': entry['config_sha256'], 'chain_sha256': entry['archived_chain_sha256'],
              'module': str(module), 'module_sha256': expected,
              'actual_initialized_native_extra_args': actual_args,
              'checks': checks, 'fresh_initial_point_finite_native_target_verified': True,
              'selected_original_rows_match_at_declared_tolerance': all(c['matches_original_at_atol_1e7_rtol_1e10'] for c in checks),
              'full_domain_original_backend_identity_asserted': False,
              'posterior_convergence_certified': False,
              'uniform_numerical_accuracy_certified': False}
    with (folder / f"seed{entry['replacement_seed']}.json").open('x') as handle:
        handle.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    summaries.append({'replacement_seed': entry['replacement_seed'],
                      'selected_rows_match_at_declared_tolerance': result['selected_original_rows_match_at_declared_tolerance'],
                      'all_components_exact': all(value == 0 for check in checks for value in check['fresh_minus_original'].values())})
    print(f"Parent {entry['seed']} endpoints evaluated; new seed {entry['replacement_seed']} ready.", flush=True)
with (HERE / f'{args.group}_parent_verification.json').open('x') as handle:
    handle.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'group': args.group,
                            'summaries': summaries, 'posterior_convergence_certified': False}, indent=2) + '\n')
