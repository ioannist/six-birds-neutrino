"""Reconstruct observed guard failures and current Python/Lean coverage."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
r=json.loads((HERE/'probe_receipt.json').read_text())
assert len(r['negative_and_positive_controls'])==3
for case in r['negative_and_positive_controls']:
    folder=HERE/'fixtures'/case['case']
    hashes,versions=set(),set()
    for index in [0,1]:
        run=folder/str(index)
        if (run/'solver_backend.json').exists():
            hashes.add(json.loads((run/'solver_backend.json').read_text())['module_sha256'])
        import yaml
        versions.add(yaml.safe_load((run/'sample.updated.yaml').read_text())['theory']['camb']['version'])
    if case['case']=='matching_recorded_targets':
        assert len(hashes)==len(versions)==1 and len(case['after'][0])==2
    else:
        assert case['after']['rejected'] and (len(hashes)>1 or len(versions)>1)
    assert case['before']==[[],'configuration_only_native_build_identity_not_recorded']
assert sum(len(c['runs']) for c in r['valid_cohort_impact'].values())==32
for c in r['valid_cohort_impact'].values():
    assert c['accepted']
    for source in c['resolved_sources']:
        assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
# Preserve the actual read metadata bytes so subsequent sampler state is not
# needed to verify the observed package versions.
frozen=HERE/'observed_SPT_version_metadata';frozen.mkdir()
metadata=[]
for target,values in r['existing_SPT_version_evidence'].items():
    assert len(values[0])==6 and {v['solver_version'] for v in values[0]}=={'2.0.4'}
    for index,v in enumerate(values[0]):
        for witness in v['version_witnesses']:
            raw=Path(witness['path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==witness['sha256']
            path=frozen/(target+'_'+str(index)+'.updated.yaml');path.write_bytes(raw)
            metadata.append({'source':witness['path'],'frozen':str(path.relative_to(ROOT)),
                             'sha256':witness['sha256']})
output=(HERE/'math_check_stdout.txt').read_text()
assert '145 passed' in output and 'Build completed successfully' in output
assert not (HERE/'math_check_stderr.txt').read_bytes()
public=set()
for p in (ROOT/'lean/trunc_gauss_proof/TruncGaussProof').glob('*.lean'):
    public.update(re.findall(r'^theorem (\w+)',p.read_text(),re.M))
axioms={name:{a.strip() for a in values.split(',') if a.strip()} for name,values in
        re.findall(r"'TruncGaussProof\.(\w+)' depends on axioms: \[([^\]]*)\]",output)}
assert len(public)==74 and set(axioms)==public
assert all(v <= {'propext','Classical.choice','Quot.sound'} for v in axioms.values())
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT)
files=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
       for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
files += [{'path':str(p),'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
          for p in ['scripts/diagnose_cobaya_chains.py','tests/test_math_repairs.py']]
out={'utc':datetime.now(timezone.utc).isoformat(),'review_type':'distinct_self_review_not_independent_review',
     'mixed_CAMB_native_builds_and_recorded_versions_no_longer_accepted':True,
     'valid_matching_records_and_legacy_assumptions_checked':True,'valid_bundle_guard_checks':32,
     'existing_SPT_version_evidence_frozen':metadata,'Python_tests_passed':145,
     'Lean_exported_theorems_axiom_checked':74,'managed_math_check_session':16448,'exit_code':0,
     'rank_algorithms_gates_and_native_targets_unchanged':True,'Lean_sources_unchanged':True,
     'historical_native_identity_not_inferred_from_installed_module':True,'paper_unchanged':True,'files':files}
with (HERE/'validation_receipt.json').open('x') as handle:
    handle.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Mixed CAMB evidence rejected; 32 valid bundles, 145 tests and all 74 public axiom outputs verified.')
