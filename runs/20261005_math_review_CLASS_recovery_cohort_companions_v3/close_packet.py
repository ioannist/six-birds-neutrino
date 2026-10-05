"""Close reviewed fresh preparation without activating additional samplers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
utc = lambda: datetime.now(timezone.utc).isoformat()
read = lambda p: json.loads(Path(p).read_text())


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


controls = read(HERE / 'preflight_execution_receipt.json')
review = read(HERE / 'preparation_self_review_receipt.json')
preparation = read(HERE / 'preparation_receipt.json')
assert len(controls['records']) == 6 and all(r['actual_terminal_exit_code'] == 0 for r in controls['records'])
assert review['six_fresh_companions_reconstructed'] and review['samplers_launched'] == 0
assert review['preparation_sha256'] == sha(HERE / 'preparation_receipt.json')
assert all(not (ROOT / e['run_dir']).exists() for e in preparation['entries'])
write(HERE / 'execution_receipt.json', {'utc': utc(), 'managed_session': 24620,
    'actual_terminal_exit_code': 0, 'preparation_self_review_direct_exit_code': 0,
    'all_native_control_workers_terminal': True, 'samplers_launched': 0,
    'native_preflight_records': controls['records']})
initial = ROOT / 'runs/20261005_math_review_CLASS_recovery_cohort_companions'
write(initial / 'execution_receipt.json', {'utc': utc(),
    'semantic_review_refused_preparation': True, 'native_control_workers_started': 0,
    'all_verification_workers_terminal': True, 'samplers_launched': 0})
state_path = ROOT / 'runs/20261003_math_review_validation/review_state.json'
s = read(state_path)
rel = str(HERE.relative_to(ROOT))
s['CLASS_recovery_cohort_companion_preparation'] = {
    'root': rel, 'cohorts': preparation['cohorts'], 'entries': preparation['entries'],
    'six_selected_native_starts_finite': True,
    'preparation_self_review': rel + '/preparation_self_review_receipt.json',
    'historical_source_scope_audit': rel + '/historical_source_scope_audit.json',
    'samplers_launched': 0, 'activation_and_first_saved_row_verification_pending': True,
    'new_cohort_diagnostic_workflow_pending': True,
    'posterior_qualified': False, 'independence_or_stationarity_proved': False}
s['native_failure_next_repair_obligation'] = (
    'Activate the six reviewed fresh CLASS companions, verify owned native runtime identities '
    'and first saved rows, then prepare separate fixed-gate diagnostics for the two declared '
    'four-start recovery cohorts. Preserve all original terminal and surviving registrations. '
    'Assess each sigma_time_v3 cap5/cap20 target when its fixed history gate is reached. '
    'Uniform physical accuracy, prior stability and both material main-claim discussions remain open.')
with state_path.open('w') as f:
    json.dump(s, f, indent=2, allow_nan=False)
    f.write('\n')
with (ROOT / 'docs/findings/math_review.md').open('a') as f:
    f.write('''

Six fresh CLASS companion configurations now define two separate four-start
recovery designs: medium_A seeds2201/2301/2302/2303 and quad_A seeds2202/2304/2305/2306.
The six new starts are the fixed original references of surviving seeds
1401/1402/1406 and1302/1303/1304 respectively. Only those initialization values
are reused. Every start is strictly inside its original prior, all four starts
per group are distinct, and each new companion preserves its existing recovery
anchor's declared likelihoods, priors, native settings and sampler profile.
The shared learned covariance per group is a finite positive-definite fixed
proposal heuristic. New RNG seeds and output prefixes are mandatory.

All six surviving original launch receipts bind source hashes that differ from
the current public launcher, MCMC, metrics and BAO implementation. The old
receipts do not bind every likelihood adapter source file. These differences
do not prove target change; they leave uniform historical/current numerical
target identity unproved. Original histories remain separately registered and
are not pooled with fresh recovery histories. Both fresh cohorts retain the
first-history gate1000 and later growth6/5, with actual diagnostic workflow
construction still pending.

The first design packet is preserved after semantic self-review refuses its
claim of conditional independence: different fixed seeds and starts do not
supply an independence theorem for random streams. A fresh v2 packet correctly
states distinct declared seeds/starts without proving probabilistic independence.
All six actual v2 native attempts then exit1 before model evaluation because
the runner omitted the private backend PYTHONPATH. The real public launcher
guard rejects the unguarded installed module; these complete failed attempts
remain preserved. A fresh v3 runner derives its backend search path from the
declared module and runs at most two native controls concurrently.

All six v3 native starts are finite, with finite provider arrays and individual
native log-likelihood components. Every actual launcher guard is exercised and
rejects a deliberately wrong native contract. Distinct self-review reconstructs
all six configurations, proposal/source bindings, four-start designs, native
proofs and preserved corrections. No additional sampler is activated at packet
closure. Activation, first saved-row replay and separate convergence assessments
are the next obligations; independence, stationarity and uniform solver accuracy
remain unproved. The paper and canonical results are unchanged.
''')
print('Six reviewed fresh companions recorded; activation and diagnostic qualification remain pending.')
