"""Check ambiguity refusal and byte-identical numeric reads of valid histories."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
import extract_mnu_limits as repaired
from sbt_spt_audit.mcmc import weighted_quantile

spec = importlib.util.spec_from_file_location('column_identity_before', HERE / 'extract_mnu_limits_before.py')
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)
refusals = []
for case in ['duplicate_header', 'duplicate_paramnames', 'duplicate_extra_header']:
    prefix = HERE / case / 'sample'
    original = before._load_chains_raw(prefix, 'mnu', 0)
    assert original[0][0].tolist() == [.02, .03]
    try:
        repaired._load_chains_raw(prefix, 'mnu', 0)
    except ValueError as error:
        assert 'unique' in str(error)
        refusals.append({'case': case, 'error': str(error)})
    else:
        raise AssertionError('Ambiguous parameter identity still accepted')
runs = sorted((ROOT / 'runs/20261004_math_review_spt_chain_snapshots_twelfth_A').glob('chain_A_seed*'))
runs += sorted((ROOT / 'runs/20261004_math_review_spt_chain_snapshots_thirteenth_B').glob('chain_B_seed*'))
class_root = ROOT / 'runs/20261004_math_review_guarded_CLASS_second_diagnostics'
for cohort in ['quad_A', 'quad_B', 'medium_A', 'medium_B']:
    runs += sorted((class_root / cohort).glob('seed*'))
runs += [ROOT / f'runs/20261004_math_review_guarded_grid12_trial_B_seed{seed}/first_saved_rows'
         for seed in [1501, 1502, 1503, 1504]]
assert len(runs) == 32
entries = [(str(run.relative_to(ROOT)), repaired._resolve_prefix_from_run_dir(run),
            'mnu_sample' if 'CLASS_' in str(run) or 'grid12' in str(run) else 'mnu') for run in runs]
for name in ['spt2018_desi', 'sptd1_desi', 'cmb2018_desi', 'cmbd1_desi', 'cmb2018_seed1']:
    source = ROOT / f'runs/20261003_math_review_chain_diagnostics/{name}.json'
    data = json.loads(source.read_text())
    entries.append((str(source.relative_to(ROOT)), Path(data['chains_prefix']), data['param']))
records = []
for label, prefix, parameter in entries:
    old, new = [loader._load_chains_raw(prefix, parameter, .2) for loader in [before, repaired]]
    assert len(old) == len(new)
    for (v0, w0), (v1, w1) in zip(old, new):
        np.testing.assert_array_equal(v0, v1)
        np.testing.assert_array_equal(w0, w1)
    values = np.concatenate([v for v, w in new]); weights = np.concatenate([w for v, w in new])
    paths = sorted(prefix.parent.glob(prefix.name + '.*.txt'))
    records.append({'input': label, 'parameter': parameter, 'chains': len(new),
                    'postburn_stored_rows': len(values), 'complete_represented_steps': int(weights.sum()),
                    'median_eV': weighted_quantile(values, weights, .5), 'p95_eV': weighted_quantile(values, weights, .95),
                    'numeric_values_and_holding_weights_identical': True,
                    'source_files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                                     for p in paths]})
out = {'utc': datetime.now(timezone.utc).isoformat(),
       'scope': 'ambiguous_coordinate_refusal_and_valid_archive_snapshot_read_equivalence',
       'refusals': refusals, 'valid_history_checks': records, 'valid_history_count': len(records),
       'production_source_sha256': hashlib.sha256((ROOT / 'scripts/extract_mnu_limits.py').read_bytes()).hexdigest(),
       'before_source_sha256': hashlib.sha256((HERE / 'extract_mnu_limits_before.py').read_bytes()).hexdigest(),
       'uniform_numerical_accuracy_or_posterior_convergence_certified': False}
with (HERE / 'impact_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(f'{len(refusals)} ambiguous inputs rejected; {len(records)} valid historical/frozen mass reads unchanged.')
