"""Adversarial recount of genuine prefixes, with control scope kept explicit."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
preparation = json.loads((HERE / 'control_preparation_receipt.json').read_text())
production_path = ROOT / preparation['source_contract']
assert sha(production_path) == preparation['source_contract_sha256']
production = json.loads(production_path.read_text())
control = json.loads((HERE / 'assessment_contract.json').read_text())
assert production['first_minimum_retained_represented_steps'] == 1000
assert control['first_minimum_retained_represented_steps'] == 8
restored = dict(control)
restored.pop('control_scope')
restored['first_minimum_retained_represented_steps'] = 1000
assert restored == production
assert sha(HERE / 'assessment_contract.json') == preparation['control_contract_sha256']
for record in preparation['copied_scripts']:
    assert sha(ROOT / record['source']) == sha(ROOT / record['control_copy']) == record['sha256']
for path, digest in production['diagnostic_source_sha256'].items():
    assert sha(ROOT / path) == digest

summaries = {}
total_checks = 0
max_native_error = 0.0
for group in ['current_A3200', 'old_A3200']:
    folder = HERE / group
    receipt = json.loads((folder / 'snapshot_receipt.json').read_text())
    native = json.loads((folder / 'native_rows_verification.json').read_text())
    report = json.loads((folder / 'diagnostics.json').read_text())
    reviewed = json.loads((folder / 'self_review_receipt.json').read_text())
    entries = {e['seed']: e for e in production['groups'][group]}
    assert len(receipt['families']) == 4
    assert {f['seed'] for f in receipt['families']} == set(entries)
    assert receipt['assessment_trigger'] == 8
    assert receipt['minimum_retained_represented_steps'] < 1000
    assert native['group'] == group and native['upstream_original_class_forced_fresh']
    assert native['atol'] == 1e-9 and native['rtol'] == 0
    assert native['module_sha256'] == entries[next(iter(entries))]['module_sha256']
    assert native['solver_version'] == entries[next(iter(entries))]['solver_version']
    assert len(native['records']) == 4
    native_by_seed = {r['seed']: r for r in native['records']}
    assert set(native_by_seed) == set(entries)
    assert report['seeds'] == sorted(entries) and report['burnin_fraction_of_stored_rows'] == .2
    assert not report['all_diagnostic_thresholds_pass']
    assert all(not d['mathematical_convergence_certificate'] for d in report['diagnostics'].values())
    populations = {n: [] for n in report['diagnostics']}
    retained_counts = []
    for family in receipt['families']:
        e = entries[family['seed']]
        path = Path(family['snapshot'])
        raw = path.read_bytes()
        assert sha(path) == family['snapshot_sha256']
        assert (ROOT / family['source']).read_bytes().startswith(raw)
        rows = np.loadtxt(BytesIO(raw), ndmin=2)
        header = raw.decode().splitlines()[0].lstrip('#').split()
        assert len(header) == len(set(header)) and rows.shape == (family['stored_rows'], len(header))
        weights = [Fraction(l.split()[0]) for l in raw.decode().splitlines()
                   if l.strip() and not l.startswith('#')]
        assert all(w > 0 and w.denominator == 1 for w in weights)
        cut = len(weights) // 5
        retained_counts.append(sum(int(w) for w in weights[cut:]))
        for name in populations:
            populations[name].extend(zip(rows[cut:, header.index(name)], map(int, weights[cut:])))
        checks = native_by_seed[family['seed']]
        assert checks['file_sha256'] == sha(path)
        assert [r['row_index'] for r in checks['checks']] == [0, (len(rows)-1)//2, len(rows)-1]
        required = {'minuslogpost', 'minuslogprior', 'chi2'} | {n for n in header if n.startswith('chi2__')}
        for check in checks['checks']:
            assert set(check['fresh_minus_recorded']) == required
            error = max(abs(v) for v in check['fresh_minus_recorded'].values())
            assert np.isfinite(error) and error <= 1e-9
            max_native_error = max(max_native_error, error)
            total_checks += 1
        cfg = yaml.safe_load((path.parent.parent / 'resolved.yaml').read_text())
        original = yaml.safe_load((ROOT / e['run_dir'] / 'resolved.yaml').read_text())
        original['output'] = str(path).removesuffix('.1.txt')
        assert cfg == original
        assert sha(path.parent.parent / 'input.yaml') == e['config_sha256']
        assert sha(path.parent.parent / 'solver_backend.json') == e['native_backend_receipt_sha256']
    assert min(retained_counts) == receipt['minimum_retained_represented_steps']
    assert retained_counts == reviewed['retained_represented_steps']
    limits = {}
    for name, population in populations.items():
        # Direct extended-precision weighted moments supply an independent
        # calculation of the relative precision target on all postburn data.
        values = np.array([v for v, _ in population], dtype=np.longdouble)
        weights = np.array([w for _, w in population], dtype=np.longdouble)
        mean = np.sum(values * weights) / np.sum(weights)
        sd = np.sqrt(np.sum(weights * (values - mean)**2) / np.sum(weights))
        expected = .001 if name == 'mnu' else float(np.longdouble('.05') * sd)
        d = report['diagnostics'][name]
        assert np.isclose(d['quantile_mcse_limit'], expected, rtol=2e-14, atol=0)
        assert d['draws_per_chain'] == min(retained_counts) and d['n_chains'] == 4
        assert not d['diagnostic_thresholds_pass']
        limits[name] = expected
    summaries[group] = {'retained_represented_steps': retained_counts,
                        'independently_recounted_precision_limits': limits,
                        'all_seven_parameter_gate_sets_fail': True,
                        'production_first_trigger_met': False,
                        'snapshot_and_native_and_diagnostic_path_exercised': True}

refusal = json.loads((HERE / 'wrong_environment_rejection.json').read_text())
assert refusal['expected_refusal'] and refusal['exit_code'] == 1
assert refusal['rejected_before_model_construction']
assert total_checks == 24
with (HERE / 'distinct_self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                       'reviewer': 'distinct_self_review_not_independent_agent',
                       'groups': summaries, 'selected_native_rows_checked': total_checks,
                       'maximum_absolute_native_component_error': max_native_error,
                       'wrong_native_environment_refused': True,
                       'production_first_history_trigger': 1000,
                       'production_contract_and_gate_settings_unchanged': True,
                       'first_production_assessments_remain_pending': True,
                       'posterior_qualification_or_uniform_accuracy_certified': False,
                       'self_review_script_sha256': sha(__file__)}, indent=2, allow_nan=False) + '\n')
print('Both full control paths verified; 24 native rows and all relative precision limits recounted.')
