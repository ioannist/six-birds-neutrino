"""Compare fixed medium proposals with a frozen, unconverged quad pilot."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import numpy as np
from scipy.linalg import solve_triangular
import yaml

from sbt_spt_audit.metrics import covariance_solve

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PILOT = ROOT / 'runs/20261004_math_review_guarded_CLASS_first_diagnostics'
proof_path = PILOT / 'completion_verification.json'
proof = json.loads(proof_path.read_text())
for item in proof['files']:
    assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
assert not (HERE / 'scout_receipt.json').exists()
pilot_records, proposal_records, files = {}, [], []
for lens in ['A', 'B']:
    paths = sorted((PILOT / ('quad_' + lens)).glob('seed*/chains/*.1.txt'))
    assert len(paths) == 4
    config = yaml.safe_load((paths[0].parents[1] / 'resolved.yaml').read_text())
    names = [n for n, p in config['params'].items() if isinstance(p, dict) and 'prior' in p]
    values, weights = [], []
    for path in paths:
        header = path.read_text().splitlines()[0].lstrip('#').split()
        data = np.atleast_2d(np.loadtxt(path))
        data = data[int(.2 * len(data)):]
        weights.append(data[:, 0])
        values.append(data[:, [header.index(n) for n in names]])
    x, w = np.concatenate(values), np.concatenate(weights)
    assert np.all(np.isfinite(x)) and np.all(w > 0) and np.all(w == np.floor(w))
    mean = np.average(x, axis=0, weights=w)
    centered = x - mean
    covariance = (centered.T * (w / w.sum())) @ centered
    covariance_solve(covariance, np.zeros(len(names)))
    target = HERE / ('pilot_' + lens + '.covmat')
    np.savetxt(target, covariance, header=' '.join(names), fmt='%.17e')
    pilot_records[lens] = {'parameters': names, 'stored_rows_after_burn': len(x),
                           'represented_steps_after_burn': int(w.sum()),
                           'weighted_mean': dict(zip(names, map(float, mean))),
                           'covariance_file': str(target.relative_to(ROOT)),
                           'finite_SPD': True, 'posterior_covariance_certified': False,
                           'prior_diagnostic_pass': proof['cohort_mass_diagnostics']['quad_' + lens]['all_parameter_gates_pass']}
for entry in state['guarded_medium_posterior_chains'] + state['guarded_solver_posterior_trials']:
    source = ROOT / entry['run_dir']
    cfg = yaml.safe_load((source / 'resolved.yaml').read_text())
    options = cfg['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']
    prefix = Path(cfg['output'])
    folder = HERE / f"seed{entry['seed']}"
    folder.mkdir()
    for path, name in [(prefix.with_suffix('.covmat'), 'current.covmat'),
                       (source / 'resolved.yaml', 'resolved.yaml'),
                       (source / 'runtime_state.json', 'runtime_state.json'),
                       (source / 'stdout.txt', 'stdout_prefix.txt')]:
        raw = path.read_bytes()
        if name == 'stdout_prefix.txt': raw = raw[:raw.rfind(b'\n') + 1]
        destination = folder / name
        destination.write_bytes(raw)
        files.append({'source': str(path), 'snapshot': str(destination.relative_to(ROOT)),
                      'sha256': hashlib.sha256(raw).hexdigest()})
    native = json.loads((folder / 'runtime_state.json').read_text())
    assert native['pid'] == entry['pid'] and native['seed'] == entry['seed']
    assert native['module_sha256'] == entry['native_module_sha256']
    proc = Path('/proc', str(entry['pid']))
    assert str(Path(native['module']).resolve()) in (proc / 'maps').read_text()
    cmd = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
    assert str(entry['seed']) in cmd or entry['seed'] == 1201 and 'launch_guarded_trial.py' in cmd
    names = (folder / 'current.covmat').read_text().splitlines()[0].lstrip('#').split()
    current = np.atleast_2d(np.loadtxt(folder / 'current.covmat'))
    covariance_solve(current, np.zeros(len(names)))
    pilot = pilot_records[entry['lens']]
    order = [pilot['parameters'].index(n) for n in names]
    c = np.loadtxt(ROOT / pilot['covariance_file'])[np.ix_(order, order)]
    l = np.linalg.cholesky(current)
    first = solve_triangular(l, c, lower=True)
    whitened = solve_triangular(l, first.T, lower=True).T
    whitened = (whitened + whitened.T) * .5
    eigenvalues = np.linalg.eigvalsh(whitened)
    assert np.all(np.isfinite(eigenvalues)) and np.all(eigenvalues > 0)
    log = (folder / 'stdout_prefix.txt').read_text()
    checks = re.findall(r'Convergence of means: R-1 = ([\d.eE+-]+) after (\d+) accepted steps', log)
    initial = np.loadtxt(options['covmat'])
    proposal_records.append({'seed': entry['seed'], 'lens': entry['lens'], 'live': True,
                             'proposal_updates': log.count('Updated covariance matrix of proposal pdf.'),
                             'current_equals_initial': np.allclose(current, initial, rtol=5e-15, atol=1e-20),
                             'last_internal_Rminus1': float(checks[-1][0]) if checks else None,
                             'pilot_covariance_in_current_proposal_basis_eigenvalues': eigenvalues.tolist(),
                             'pilot_to_current_marginal_sigma_ratios': dict(zip(names, map(float, np.sqrt(np.diag(c) / np.diag(current))))),
                             'same_posterior_target_claimed_between_precision_levels': False})
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'proposal_scout_from_frozen_unconverged_quad_pilot_with_live_medium_proposals',
           'pilot_verification': str(proof_path.relative_to(ROOT)),
           'pilot_verification_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
           'pilot_records': pilot_records, 'medium_proposal_comparisons': proposal_records,
           'files_individually_frozen_not_atomic_sampler_states': True,
           'sampler_rules_or_likelihood_targets_changed': False,
           'pilot_covariance_is_an_initialization_candidate_not_a_posterior_estimate': True,
           'precision_targets_pooled_for_posterior_inference': False,
           'efficiency_improvement_or_convergence_certified': False,
           'files': files + [{'source': str(p), 'snapshot': str(p.relative_to(ROOT)),
                            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in [HERE / 'pilot_A.covmat', HERE / 'pilot_B.covmat', Path(__file__)]]}
with (HERE / 'scout_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps([{k: r[k] for k in ['seed', 'proposal_updates', 'current_equals_initial',
                                    'pilot_covariance_in_current_proposal_basis_eigenvalues']}
                  for r in proposal_records], indent=2))
