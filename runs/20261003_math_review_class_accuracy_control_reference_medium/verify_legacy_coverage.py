"""Verify requested coverage for legacy records lacking explicit coverage metadata.

Initializes saved models; it does not calculate new spectra or native likelihoods.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cobaya.model import get_model

current_baseline = yaml.safe_load((HERE / 'baseline.yaml').read_text())
records = {}
for name in ['reference', 'medium']:
    directory = ROOT / ('runs/20261003_math_review_class_accuracy_control_' + name)
    metrics_path = directory / 'metrics.json'
    metrics = json.loads(metrics_path.read_text())
    baseline = yaml.safe_load((directory / 'baseline.yaml').read_text())
    assert baseline == current_baseline
    expected_selected = deepcopy(baseline)
    expected_selected['theory']['classy'].setdefault('extra_args', {}).update(metrics['precision_settings_source']['settings'])
    phases = {}
    for phase in ['baseline', 'selected_reference_settings']:
        path = directory / (phase + '.yaml')
        cfg = yaml.safe_load(path.read_text())
        assert cfg == (baseline if phase == 'baseline' else expected_selected)
        with get_model(cfg, stop_at_error=True) as model:
            requested = model.theory['classy'].requested()['Cl']
            coverage = {spec: int(requested[spec]) for spec in ['tt', 'ee']}
            assert coverage == {'tt': 4095, 'ee': 4095}
        phases[phase] = {'configuration_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'requested_spectrum_ell_max': coverage}
    records[name] = {'metrics_sha256': hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
                     'baseline_matches_completed_control': True,
                     'selected_config_differs_only_by_declared_settings': True,
                     'phases': phases}
receipt = {'scope': 'initialized_legacy_saved_model_requirements', 'records': records,
           'completed_control_baseline_sha256': hashlib.sha256((HERE / 'baseline.yaml').read_bytes()).hexdigest(),
           'new_theory_or_likelihood_evaluations': False,
           'interval_error_certified': False, 'posterior_accuracy_certified': False}
(HERE / 'legacy_coverage_verification.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('Legacy saved configurations request matching TT/EE coverage through ell 4095.', flush=True)
