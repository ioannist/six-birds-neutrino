"""Reconstruct signed quadrature weights from native node dumps."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep = json.loads((HERE / 'instrumentation_preparation.json').read_text())
original, instrumented = Path(prep['original_source']), Path(prep['instrumented_source'])
assert sha(original) == prep['original_sha256']
assert sha(instrumented) == sha(HERE / 'instrumented_halofit.f90') == prep['instrumented_sha256']
text = instrumented.read_text()
for old, new in reversed(prep['changes']):
    assert text.count(new) == 1
    text = text.replace(new, old, 1)
assert text.encode() == original.read_bytes()
assert 'pfull = (p2h**a + p1h**a)**(1./a)' in original.read_text()
source_prep = json.loads((HERE / 'source_and_compiler_preparation.json').read_text())
scratch = Path(source_prep['scratch_source'])
instrumented_root = instrumented.parents[1]
for file in source_prep['unchanged_Fortran_files']:
    assert sha(scratch / file['path']) == file['sha256']
    if file['path'] != 'fortran/halofit.f90':
        assert sha(instrumented_root / file['path']) == file['sha256']

records = []
for seed, session in [(2003, 71113), (2004, 26425)]:
    stdout, stderr = HERE / f'seed{seed}_instrumented_stdout.txt', HERE / f'seed{seed}_instrumented_stderr.txt'
    text = stdout.read_text()
    assert str(instrumented_root / 'camb') in text
    assert stderr.read_text().strip() == 'ERROR STOP AUDIT before fractional power of negative halo component'
    bases = [line for line in text.splitlines() if line.strip().startswith('AUDIT_NEGATIVE_HALO_BASE ')]
    assert len(bases) == 1
    z, k, p1h, p2h, alpha = map(float, bases[0].split()[1:])
    assert z >= 0 and k > 0 and p1h < 0 and p2h > 0 and alpha == .5
    lines = [line for line in text.splitlines() if line.startswith('AUDIT_HALO_NODE ')]
    assert [int(line.split()[1]) for line in lines] == list(range(1, 257))
    nodes = np.array([[float(v) for v in line.split()[2:]] for line in lines])
    assert nodes.shape == (256, 4) and np.isfinite(nodes).all()
    mass, sigma, nu, weights = nodes.T
    assert (mass > 0).all() and (sigma > 0).all() and (nu > 0).all()
    assert (np.diff(mass) > 0).all() and (np.diff(nu) < 0).any()
    # These Fortran dl constants are initialized from default-real literals.
    a, p, bigA = [float(np.float32(v)) for v in [.707, .3, .21616]]
    widths = np.r_[nu[1]-nu[0], nu[2:]-nu[:-2], nu[-1]-nu[-2]]
    reconstructed = .5*bigA*(1+(a*nu*nu)**(-p))*np.exp(-a*nu*nu/2)*mass*widths
    assert np.array_equal(reconstructed, weights)
    assert np.array_equal(weights < 0, (widths < 0) & (reconstructed != 0))
    exact_sum = sum((Fraction(float(w)) for w in weights), Fraction(0))
    assert exact_sum < 0
    with (HERE / f'seed{seed}_halo_nodes.npz').open('xb') as f:
        np.savez_compressed(f, mass=mass, sigma=sigma, nu=nu, weights=weights)
    records.append({'seed': seed, 'managed_session': session, 'actual_terminal_exit_code': 1,
                    'termination_scope': 'intentional instrumentation stop before invalid fractional power',
                    'redshift': z, 'wavenumber_h_per_Mpc': k,
                    'negative_one_halo_component': p1h, 'positive_two_halo_component': p2h,
                    'fractional_exponent': alpha, 'halo_nodes': len(nodes),
                    'negative_weights': int((weights < 0).sum()), 'minimum_peak_height': float(nu.min()),
                    'minimum_adjacent_peak_height_difference': float(np.diff(nu).min()),
                    'all_quadrature_weights_reconstructed_binary64_exactly': True,
                    'sum_of_recorded_weights_exact_rational_sign': 'negative',
                    'sum_of_recorded_weights_float_readout': float(exact_sum),
                    'node_dump_sha256': sha(HERE / f'seed{seed}_halo_nodes.npz'),
                    'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr)})
module = instrumented_root / 'camb/camblib.so'
production = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/camb/camblib.so')
assert sha(production) == '306640a8948cd5246fc9b21e76525f6adebdff5ba3bc792a57d50bba67225ad5'
out = {'utc': datetime.now(timezone.utc).isoformat(), 'review_type': 'distinct_self_review_not_independent_agent',
       'records': records, 'instrumentation_changes_reversed_exactly': True,
       'other_Fortran_sources_unchanged': True, 'instrumented_module': str(module),
       'instrumented_module_sha256': sha(module), 'production_module_unchanged': True,
       'mechanism_witnessed': 'nonmonotone peak heights give signed negative quadrature weights; negative one-halo power is passed to exponent one half',
       'why_sigma_or_peak_height_table_is_nonmonotone_resolved': False,
       'target_preserving_solver_repair_proved': False,
       'original_unflushed_failure_proposals_known': False, 'posterior_qualified': False}
with (HERE / 'negative_halo_self_review_receipt.json').open('x') as f:
    f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print('Both negative one-halo fractional-power witnesses reviewed; 256 weights each reproduced exactly; numerical repair pending.')
