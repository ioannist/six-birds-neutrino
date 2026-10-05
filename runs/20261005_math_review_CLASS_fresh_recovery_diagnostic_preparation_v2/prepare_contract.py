"""Bind two fresh four-start CLASS targets only after all eight first-row proofs exist."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path

import classy
import yaml
wrapper = importlib.import_module('cobaya.theories.classy.classy')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
source = ROOT / 'runs/20261005_math_review_sigma_time_v3_diagnostic_preparation/assessment_contract.json'
contract = json.loads(source.read_text())
contract.update(utc=datetime.now(timezone.utc).isoformat(), groups={}, compatible_predecessor_contracts={},
                scope='Two separate fresh CLASS four-start recovery targets. Selected native rows and unchanged ten-parameter gates; no posterior, independence or uniform physical theorem.')
contract.pop('reused_B_pair_comparisons_independent', None)
entries = {e['seed']: e for key in ['guarded_CLASS_fresh_recovery_trials', 'CLASS_recovery_companion_posterior_chains']
           for e in state[key]}
module = Path(importlib.import_module(classy.Class.__module__).__file__).resolve()
for group, cohort in state['fresh_CLASS_recovery_cohorts'].items():
    records = []
    for seed in cohort['seeds']:
        entry = deepcopy(entries[seed])
        proof_path = ROOT / entry['first_saved_row_receipt']
        proof = json.loads(proof_path.read_text())
        assert sha(proof_path) == entry['first_saved_row_receipt_sha256']
        assert proof['native_row_verified'] and proof['module_sha256'] == sha(module) == entry['module_sha256']
        assert max(map(abs, proof['native_check']['fresh_minus_recorded'].values())) == 0.0
        assert str(module) == entry['module']
        cfg = yaml.safe_load((ROOT / entry['config']).read_text())
        assert cfg['notes']['classy_backend']['module_sha256'] == entry['module_sha256']
        entry.update(group=group, solver_version=None, loaded_CLASS_version=classy.__version__,
                     Cobaya_version=importlib.metadata.version('cobaya'),
                     wrapper=str(Path(wrapper.__file__).resolve()), wrapper_sha256=sha(wrapper.__file__))
        records.append(entry)
    assert len(records) == 4
    contract['groups'][group] = records
with (HERE / 'assessment_contract.json').open('x') as f:
    json.dump(contract, f, indent=2, allow_nan=False)
    f.write('\n')
with (HERE / 'contract_preparation_receipt.json').open('x') as f:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'source_contract': str(source.relative_to(ROOT)),
        'source_contract_sha256': sha(source), 'new_contract_sha256': sha(HERE / 'assessment_contract.json'),
        'all_eight_first_saved_rows_native_verified': True,
        'holding_and_acceptance_thresholds_preserved': True,
        'historical_predecessor_compatibility_inherited': False,
        'CLASS_version_scope': 'Loaded replay module version is separate from absent launch-version metadata.',
        'posterior_qualified': False}, f, indent=2, allow_nan=False)
    f.write('\n')
print('Two separate CLASS contracts bound to all eight exact first-row native proofs.')
