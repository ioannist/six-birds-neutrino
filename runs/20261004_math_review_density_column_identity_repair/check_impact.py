"""Exercise the added validation path on valid frozen and historical bundles."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import compare_mnu_posteriors as comparison
import extract_mnu_limits as extractor
import getdist.mcsamples as backend

state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
runs = []
for lens in ['A', 'B']:
    bundle = ROOT / state['latest_SPT_' + lens + '_diagnostic_bundle']
    runs += sorted(bundle.glob('chain_' + lens + '_seed*'))
for cohort, bundle in state['guarded_CLASS_latest_diagnostic_bundle_by_cohort'].items():
    runs += sorted((ROOT / bundle / cohort).glob('seed*'))
runs += [ROOT / f'runs/20261004_math_review_guarded_grid12_trial_B_seed{seed}/first_saved_rows'
         for seed in [1501, 1502, 1503, 1504]]
assert len(runs) == 32
entries = [(str(run.relative_to(ROOT)), extractor._resolve_prefix_from_run_dir(run)) for run in runs]
for name in ['spt2018_desi', 'sptd1_desi', 'cmb2018_desi', 'cmbd1_desi', 'cmb2018_seed1']:
    source = ROOT / f'runs/20261003_math_review_chain_diagnostics/{name}.json'
    entries.append((str(source.relative_to(ROOT)), Path(json.loads(source.read_text())['chains_prefix'])))

# A sentinel verifies the actual comparison function reaches GetDist unchanged
# after validation. This is not a recomputation of all 37 smoothed densities.
sentinel = object()
calls = []
def downstream(prefix, *, settings):
    calls.append((prefix, settings))
    return SimpleNamespace(get1DDensityGridData=lambda name: sentinel if name == 'mnu' else None)
backend.loadMCSamples = downstream
records = []
for label, prefix in entries:
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in prefix.parent.glob(prefix.name + '.*.txt')}
    assert comparison._load_density(prefix, .2) is sentinel
    assert calls[-1] == (str(prefix), {'ignore_rows': .2})
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == sha for p, sha in before.items())
    records.append({'input': label, 'prefix': str(prefix), 'mass_validation_accepted': True,
                    'GetDist_arguments_unchanged': True, 'chain_files_unchanged': True,
                    'sources': [{'path': str(p.relative_to(ROOT)), 'sha256': sha} for p, sha in before.items()]})
out = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'validation_path_and_downstream_argument_compatibility',
       'valid_bundle_count': len(records), 'records': records,
       'all_smoothed_density_grids_recomputed': False, 'native_targets_or_diagnostics_changed': False}
with (HERE / 'impact_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2) + '\n')
print('37 valid mass bundles reach the unchanged GetDist call after validation; chain bytes unchanged.')
