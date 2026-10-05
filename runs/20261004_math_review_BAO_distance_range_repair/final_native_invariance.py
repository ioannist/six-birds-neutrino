"""Replay native first/last rows and compare ordinary BAO arithmetic exactly."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_chain_targets import compare_native_row
from sbt_spt_audit.likelihoods.desi_dr2_bao import compute_theory_vector
from cobaya.model import get_model
import camb

parser = argparse.ArgumentParser()
parser.add_argument('group', choices=['current_A3200', 'old_A3200'])
args = parser.parse_args()
contract = json.loads((ROOT / 'runs/20261004_math_review_fresh_CAMB_diagnostic_preparation/assessment_contract.json').read_text())
entry = contract['groups'][args.group][0]
module = Path(camb.baseconfig.camblib._name).resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert str(module) == entry['module'] and sha(module) == entry['module_sha256']
assert importlib.metadata.version('camb') == entry['solver_version']
assert importlib.metadata.version('cobaya') == entry['Cobaya_version']
legacy_spec = importlib.util.spec_from_file_location('bao_legacy_range_control', HERE / 'before_desi_dr2_bao.py')
legacy = importlib.util.module_from_spec(legacy_spec)
sys.modules[legacy_spec.name] = legacy
legacy_spec.loader.exec_module(legacy)

folder = ROOT / 'runs/20261004_math_review_fresh_CAMB_workflow_control' / args.group
receipt = json.loads((folder / 'snapshot_receipt.json').read_text())
family = next(f for f in receipt['families'] if f['seed'] == entry['seed'])
path = Path(family['snapshot'])
assert sha(path) == family['snapshot_sha256']
raw = path.read_bytes()
header = raw.decode().splitlines()[0].lstrip('#').split()
rows = np.loadtxt(BytesIO(raw), ndmin=2)
cfg = yaml.safe_load((path.parent.parent / 'resolved.yaml').read_text())
assert cfg['theory']['camb'].pop('class') == 'sbt_spt_audit.boltzmann.FreshCAMB'
cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
checks = []
with get_model(cfg, stop_at_error=True) as model:
    for index in [0, len(rows)-1]:
        native = compare_native_row(header, rows[index], model, atol=1e-9, rtol=0)
        bao = next(l for l in model.likelihood.values() if hasattr(l, '_dataset'))
        from sbt_spt_audit.likelihoods.desi_dr2_bao import _provider_rdrag
        kwargs = dict(points=bao._dataset.points, rd=_provider_rdrag(bao.provider),
                      angular_diameter_distance_fn=bao.provider.get_angular_diameter_distance,
                      hubble_fn=lambda z: bao.provider.get_Hubble(z, units='km/s/Mpc'))
        before = legacy.compute_theory_vector(**kwargs)
        after = compute_theory_vector(**kwargs)
        assert np.array_equal(before, after)
        checks.append({'row_index': index, 'native': native,
                       'BAO_predictions': after.tolist(), 'ordinary_BAO_before_after_exact': True})
with (HERE / (args.group + '_final_native_invariance.json')).open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'group': args.group,
                       'seed': entry['seed'], 'frozen_sha256': sha(path),
                       'module_sha256': sha(module), 'solver_version': entry['solver_version'],
                       'checks': checks, 'native_atol': 1e-9, 'native_rtol': 0,
                       'scope': 'selected native rows and ordinary observable invariance; no uniform accuracy certificate',
                       'production_source_sha256': sha(ROOT / 'src/sbt_spt_audit/likelihoods/desi_dr2_bao.py'),
                       'script_sha256': sha(__file__)}, indent=2, allow_nan=False) + '\n')
print(args.group, 'two selected native rows and ordinary BAO vectors verified.')
