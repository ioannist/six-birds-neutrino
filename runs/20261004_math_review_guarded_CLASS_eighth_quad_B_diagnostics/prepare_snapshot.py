"""Freeze only the growth-qualified guarded CLASS quadrature B cohort."""
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
state = json.loads((ROOT / 'runs/20261003_math_review_validation/review_state.json').read_text())
groups = {
 'quad_B': [e for e in state['guarded_quadrature_posterior_chains'] if e['lens']=='B'],
}
assert not (HERE / 'snapshot_receipt.json').exists()
previous_path=HERE.parent/'20261004_math_review_guarded_CLASS_seventh_quad_B_diagnostics/snapshot_receipt.json'
previous=json.loads(previous_path.read_text())
old_files={f['source']:f for f in previous['files']}
prior_processes={p['seed']:p for p in previous['runtime_observations']}
# Cache complete prefixes so the growth gate applies to the exact frozen bytes.
raw_cache={};growth_lengths={}
for group, entries in groups.items():
    lengths=[]
    for entry in entries:
        path=next((ROOT/entry['run_dir']/'chains').glob('*.1.txt'))
        raw=path.read_bytes();complete=raw[:raw.rfind(b'\n')+1]
        rows=np.atleast_2d(np.loadtxt(BytesIO(complete)))
        lengths.append(int(rows[int(.2*len(rows)):,0].sum()))
        earlier=old_files[str(path.relative_to(ROOT))]
        prefix=(ROOT/earlier['snapshot']).read_bytes()
        assert hashlib.sha256(prefix).hexdigest()==earlier['sha256'] and complete.startswith(prefix)
        raw_cache[entry['seed']]=complete
    growth_lengths[group]=min(lengths)
if any(growth_lengths[g]<1.2*previous['draws_per_chain_by_cohort'][g] for g in groups):
    print('Growth gate not met for all cohorts; no snapshots written.',growth_lengths)
    sys.exit(3)

files, configurations, backends, observed, commands, lengths = [], [], [], [], {}, {}
for group, entries in groups.items():
    assert len(entries) == 4 and len({e['seed'] for e in entries}) == 4
    retained = []
    command = [sys.executable, str(ROOT / 'scripts/diagnose_cobaya_chains.py')]
    for entry in sorted(entries, key=lambda e: e['seed']):
        source = ROOT / entry['run_dir']
        destination = HERE / group / f"seed{entry['seed']}"
        assert not destination.exists()
        (destination / 'chains').mkdir(parents=True)
        proc = Path('/proc', str(entry['pid']))
        process_command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
        backend_identity = json.loads((source / 'runtime_state.json').read_text())
        assert backend_identity['seed'] == entry['seed'] and backend_identity['pid'] == entry['pid']
        if entry['seed'] == 1201:
            assert '20261004_math_review_class_python_repair/launch_guarded_trial.py' in process_command
        else:
            assert str(entry['seed']) in process_command
        proc_fields=(proc / 'stat').read_text().rsplit(')',1)[1].split()
        ticks = int(proc_fields[19])
        assert proc_fields[0]!='Z' and ticks==prior_processes[entry['seed']]['process_start_ticks']
        assert process_command==prior_processes[entry['seed']]['command']
        original = next((source / 'chains').glob('*.1.txt'))
        complete = raw_cache[entry['seed']]
        rows = np.atleast_2d(np.loadtxt(BytesIO(complete)))
        assert np.all(np.isfinite(rows)) and np.all(rows[:, 0] > 0)
        assert np.all(rows[:, 0] == np.floor(rows[:, 0]))
        n = int(rows[int(.2 * len(rows)):, 0].sum())
        assert n >= 8
        retained.append(n)
        target = destination / 'chains' / original.name
        target.write_bytes(complete)
        files.append({'group': group, 'seed': entry['seed'], 'source': str(original.relative_to(ROOT)),
                      'snapshot': str(target.relative_to(ROOT)), 'sha256': hashlib.sha256(complete).hexdigest(),
                      'snapshot_bytes': len(complete), 'stored_rows': len(rows), 'retained_represented_steps': n,
                      'trajectory_scope': 'guarded_fresh_uninterrupted_saved_prefix_no_parent_append'})
        for name in ['input.yaml', 'resolved.yaml', 'runtime_state.json']:
            data = (source / name).read_bytes()
            saved = data
            if name == 'resolved.yaml':
                cfg = yaml.safe_load(data)
                prefix = Path(cfg['output']).name
                assert original.name == prefix + '.1.txt'
                cfg['output'] = str(destination / 'chains' / prefix)
                saved = yaml.safe_dump(cfg, sort_keys=False).encode()
            path = destination / name
            path.write_bytes(saved)
            record = {'group': group, 'seed': entry['seed'], 'source': str((source / name).relative_to(ROOT)),
                      'snapshot': str(path.relative_to(ROOT)), 'source_sha256': hashlib.sha256(data).hexdigest(),
                      'snapshot_sha256': hashlib.sha256(saved).hexdigest()}
            if name == 'runtime_state.json':
                backend = json.loads(data)
                assert backend['module_sha256'] == entry['native_module_sha256']
                assert hashlib.sha256(Path(backend['module']).read_bytes()).hexdigest() == backend['module_sha256']
                assert str(Path(backend['module']).resolve()) in (proc / 'maps').read_text()
                record['native_module_sha256'] = backend['module_sha256']
                backends.append(record)
            else:
                configurations.append(record)
        observed.append({'group': group, 'seed': entry['seed'], 'pid': entry['pid'],
                         'process_start_ticks': ticks, 'command': process_command, 'live': True,
                         'source_runtime_status_is_historical_not_a_current_sampler_checkpoint': True})
        command += ['--run-dir', str(destination)]
    commands[group] = command + ['--burnin-frac', '.2', '--quantile-mcse-limit', '.001',
                                '--relative-quantile-mcse-limit', '.05', '--output',
                                str(HERE / (group + '_diagnostics.json'))]
    lengths[group] = min(retained)
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'eighth_guarded_CLASS_quad_B_cohort_diagnostics',
    'previous_snapshot_receipt':str(previous_path.relative_to(ROOT)),
    'previous_snapshot_receipt_sha256':hashlib.sha256(previous_path.read_bytes()).hexdigest(),
    'growth_fractions_by_cohort':{g:lengths[g]/previous['draws_per_chain_by_cohort'][g]-1 for g in groups},
    'grid12_trial_included':False, 'A_cohorts_reassessed':False, 'medium_B_reassessed':False,
    'files': files, 'configurations': configurations, 'native_backend_witnesses': backends,
    'runtime_observations': observed, 'draws_per_chain_by_cohort': lengths,
    'complete_lines_only': True, 'individually_frozen_not_atomic_sampler_checkpoint': True,
    'precision_cohorts_pooled': False, 'unmodified_backend_histories_included': False,
    'parent_histories_appended': False, 'diagnostic_gates_changed': False,
    'diagnostic_commands': commands,
    'diagnostic_script_sha256': hashlib.sha256((ROOT / 'scripts/diagnose_cobaya_chains.py').read_bytes()).hexdigest(),
    'diagnostic_dependency_sha256': {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['scripts/extract_mnu_limits.py','src/sbt_spt_audit/mcmc.py','src/sbt_spt_audit/mcmc_diagnostics.py']},
    'mathematical_convergence_or_uniform_accuracy_certified': False,
}
with (HERE / 'snapshot_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print(json.dumps(lengths, indent=2))
