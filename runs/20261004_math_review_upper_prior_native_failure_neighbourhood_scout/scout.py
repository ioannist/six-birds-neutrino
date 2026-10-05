"""Selected nearby prior-interior controls; stop on the first numerical exception."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model, Model
from failure_recording import call_and_record

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(HERE / 'failure_recording.py') == sha(ROOT / 'runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation/failure_recording.py')
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
entries = {e['seed']: e for e in state['upper_prior_posterior_chains'] if e['seed'] in [2003, 2004]}
points, cfg = [], None
for seed, e in entries.items():
    assert sha(e['module']) == e['module_sha256'] and sha(e['wrapper']) == e['wrapper_sha256']
    for path, digest in e['implementation_sha256'].items():
        assert sha(ROOT / path) == digest
    receipt = json.loads((ROOT / e['terminal_receipt']).read_text())
    assert sha(ROOT / e['terminal_receipt']) == e['terminal_receipt_sha256']
    chain = next(r for r in receipt['terminal_output_files'] if r['source'].endswith('.1.txt'))
    raw = (ROOT / chain['frozen']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == chain['sha256']
    header = raw.decode().splitlines()[0].lstrip('#').split()
    row = np.loadtxt(BytesIO(raw), ndmin=2)[-1]
    config = next(r for r in receipt['terminal_output_files'] if r['source'].endswith('/resolved.yaml'))
    assert sha(ROOT / config['frozen']) == config['sha256']
    this_cfg = yaml.safe_load((ROOT / config['frozen']).read_text())
    cfg = cfg or this_cfg
    sampled = [name for name, block in this_cfg['params'].items() if isinstance(block, dict) and 'prior' in block]
    base = {name: float(row[header.index(name)]) for name in sampled}
    points.append({'source_seed': seed, 'label': 'last_successful_saved_row', 'sampled': base})
    for cdm in [.0011, .002, .005]:
        point = dict(base, omegach2=cdm)
        points.append({'source_seed': seed, 'label': f'cold_dark_matter_density_{cdm}', 'sampled': point})
    for mass in [16., 19.]:
        point = dict(base, mnu=mass)
        points.append({'source_seed': seed, 'label': f'mass_{mass}', 'sampled': point})
for point in points:
    for name, value in point['sampled'].items():
        bounds = cfg['params'][name]['prior']
        assert bounds['min'] < value < bounds['max']
with (HERE / 'preparation_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'planned_selected_points': points,
                       'all_points_strictly_inside_declared_priors': True,
                       'scope': 'nearby numerical failure scouting; no exact failing-proposal or uniform support assertion',
                       'source_terminal_receipts': [e['terminal_receipt'] for e in entries.values()],
                       'source_module_sha256': entries[2003]['module_sha256'],
                       'recorder_sha256': sha(HERE / 'failure_recording.py'), 'scout_sha256': sha(__file__),
                       'posterior_qualified': False}, indent=2, allow_nan=False) + '\n')
model_cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params', 'packages_path', 'prior'] if k in cfg}
records = []
with get_model(model_cfg, stop_at_error=True) as model:
    for index, point in enumerate(points):
        folder = HERE / f'point{index:02d}'
        folder.mkdir(exist_ok=False)
        try:
            result = call_and_record(Model.logposterior, model, point['sampled'], folder, cached=False)
            record = {**point, 'index': index, 'status': 'finite_evaluation',
                      'logpost': float(result.logpost), 'logpriors': list(map(float, result.logpriors)),
                      'loglikes': list(map(float, result.loglikes))}
            assert np.isfinite([record['logpost'], *record['logpriors'], *record['loglikes']]).all()
            records.append(record)
            print(index, point['source_seed'], point['label'], 'finite', flush=True)
        except Exception as error:
            records.append({**point, 'index': index, 'status': 'numerical_exception',
                            'exception_type': type(error).__name__, 'error': str(error),
                            'failed_proposal_capture': str((folder / 'failed_proposal.json').relative_to(ROOT)),
                            'native_failure_is_posterior_rejection': False})
            print(index, point['source_seed'], point['label'], type(error).__name__, str(error), flush=True)
            break
with (HERE / 'scout_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
                       'planned_selected_points': len(points), 'tested_selected_points': len(records),
                       'stopped_on_first_exception': records[-1]['status'] == 'numerical_exception',
                       'scope': 'selected legal prior points; no complete original failed-transition reconstruction or uniform solver certificate',
                       'posterior_qualified': False}, indent=2, allow_nan=False) + '\n')
