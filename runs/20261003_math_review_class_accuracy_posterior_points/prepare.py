"""Select four declared archived CMB coordinates for numerical sensitivity tests."""
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
sys.path.insert(0, str(ROOT / 'src'))
from sbt_spt_audit.mcmc import weighted_quantile

baseline_source = ROOT / 'runs/20261003_math_review_class_accuracy_control_reference/baseline.yaml'
medium_source = ROOT / 'runs/20261003_math_review_class_accuracy_control_medium/precision_settings.json'
reference_source = ROOT / 'runs/20261003_math_review_class_accuracy_control_reference/precision_settings.json'
baseline = yaml.safe_load(baseline_source.read_text())
medium = json.loads(medium_source.read_text())
cfg = deepcopy(baseline)
cfg['theory']['classy']['extra_args'].update(medium['settings'])
names = [k for k, v in cfg['params'].items() if isinstance(v, dict) and 'prior' in v]
points, selections = {}, []
for lens, seed in [('A', 503), ('B', 507)]:
    source = ROOT / f'runs/20261003_math_review_chain_snapshots_fifth/cmb_chain_{lens}_seed{seed}/chains/math_restoration_{lens}_seed{seed}.1.txt'
    header = source.read_text().splitlines()[0].lstrip('#').split()
    rows = np.atleast_2d(np.loadtxt(source))
    discarded = int(len(rows) * .2)
    used = rows[discarded:]
    values = used[:, header.index('mnu_sample')]
    weights = used[:, header.index('weight')]
    assert np.all(weights == np.floor(weights)) and np.all(weights > 0)
    for probability in [.5, .95]:
        mass = weighted_quantile(values, weights, probability)
        index = int(np.flatnonzero(values == mass)[0]) + discarded
        label = f'chain_{lens}_q{int(probability * 100)}'
        point = {n: float(rows[index, header.index(n)]) for n in names}
        assert all(np.isfinite(v) and cfg['params'][n]['prior']['min'] <= v <= cfg['params'][n]['prior']['max']
                   for n, v in point.items())
        points[label] = point
        selections.append({'label': label, 'source_chain': str(source.relative_to(ROOT)),
                           'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                           'stored_row_zero_based': index,
                           'discarded_stored_prefix_rows': discarded,
                           'selection_probability': probability, 'selected_mass': mass,
                           'scope': 'coordinate_from_unconverged_snapshot_not_a_posterior_bound'})
paths = [baseline_source, medium_source, reference_source]
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'two_declared_precise_CMB_chain_files_four_coordinates_only',
    'selection_rule': 'first remaining stored row exactly matching holding-time weighted empirical mass quantile after discarding 20% of stored rows',
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    'posterior_convergence_verified': False, 'posterior_accuracy_certified': False,
    'baseline_numerical_settings': medium['settings'],
    'selected_reference_settings': json.loads(reference_source.read_text())['settings'],
    'selection': selections,
}
for name, content in [('input.yaml', yaml.safe_dump(cfg, sort_keys=False)),
                      ('default_input.yaml', baseline_source.read_text()),
                      ('precision_settings.json', reference_source.read_text()),
                      ('points.json', json.dumps(points, indent=2) + '\n'),
                      ('selection_receipt.json', json.dumps(receipt, indent=2) + '\n')]:
    p = HERE / name
    if p.exists():
        raise FileExistsError(p)
    p.write_text(content)
runner = HERE / 'runner_snapshot.py'
if runner.exists():
    raise FileExistsError(runner)
runner.write_bytes((ROOT / 'scripts/check_boltzmann_numerical_accuracy.py').read_bytes())
print(json.dumps(selections, indent=2))
