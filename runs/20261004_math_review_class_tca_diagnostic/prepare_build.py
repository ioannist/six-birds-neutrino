"""Prepare an isolated native CLASS executable with startup-only diagnostics."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
source = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy')
scratch = Path('/mnt/8tb/six-birds-ml/tmp/neutrino_class_tca_diagnostic_20261004')
assert not scratch.exists()
package = scratch / 'classy'
shutil.copytree(source, package, ignore=shutil.ignore_patterns('__pycache__', '*.so'))
original_path = source / 'source/perturbations.c'
path = package / 'source/perturbations.c'
original = path.read_text()
marker = '  /** - if there are no approximation switches, just write final time and return */'
assert original.count(marker) == 1
diagnostic = '''  /* Diagnostic-only: quantities just evaluated at the actual initial time. */
  if ((_scalars_) && (ppw->approx[ppw->index_ap_tca] == (int)tca_off)) {
    fprintf(stderr,
            "TCA_INITIAL_DIAGNOSTIC k=%.17g tau=%.17g a=%.17g H=%.17g dkappa=%.17g ratio_h=%.17g ratio_k=%.17g start_h=%.17g start_k=%.17g trigger_h=%.17g trigger_k=%.17g\\n",
            k,tau_ini,ppw->pvecback[pba->index_bg_a],ppw->pvecback[pba->index_bg_H],
            ppw->pvecthermo[pth->index_th_dkappa],
            ppw->pvecback[pba->index_bg_a]*ppw->pvecback[pba->index_bg_H]/ppw->pvecthermo[pth->index_th_dkappa],
            k/ppw->pvecthermo[pth->index_th_dkappa],
            ppr->start_small_k_at_tau_c_over_tau_h,ppr->start_large_k_at_tau_h_over_tau_k,
            ppr->tight_coupling_trigger_tau_c_over_tau_h,ppr->tight_coupling_trigger_tau_c_over_tau_k);
  }

'''
modified = original.replace(marker, diagnostic + marker)
path.write_text(modified)
(HERE / 'diagnostic_insertion.txt').write_text(
    'Diagnostic insertion before the unique initial-switch footer:\n' + diagnostic.rstrip() + '\n')
arguments_path = ROOT / 'runs/20261004_math_review_class_tca_failure_seed505/failed_class_arguments.json'
arguments = json.loads(arguments_path.read_text())['translated_class_arguments']
lines = [f'{key} = {value}' for key, value in arguments.items()]
output_root = str(scratch / 'exact_failure_')
lines.append('root = ' + output_root)
input_path = HERE / 'exact_failure.ini'
input_path.write_text('\n'.join(lines) + '\n')
manifest = {'utc': datetime.now(timezone.utc).isoformat(),
            'scope': 'isolated_standalone_CLASS_startup_diagnostic_not_inference_backend',
            'original_package': str(source), 'scratch_package': str(package),
            'original_source_sha256': hashlib.sha256(original_path.read_bytes()).hexdigest(),
            'diagnostic_source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'exact_failed_arguments_sha256': hashlib.sha256(arguments_path.read_bytes()).hexdigest(),
            'input_ini_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
            'only_solver_source_change': 'fprintf after initial approximation selection; original error checks retained',
            'build_parallel_jobs': 2, 'active_inference_library_changed': False,
            'posterior_accuracy_certified': False}
(HERE / 'build_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(package)
