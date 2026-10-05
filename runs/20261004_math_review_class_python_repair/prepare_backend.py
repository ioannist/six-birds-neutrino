"""Prepare a separate pinned CLASS package with finite numerical-Jacobian guards."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
original_package = Path('/tmp/neutrino-math-review-venv/lib/python3.12/site-packages/classy')
overlay = Path('/mnt/8tb/six-birds-ml/tmp/neutrino_class_finite_jacobian_20261004/python_backend')
assert not overlay.exists()
package = overlay / 'classy'
shutil.copytree(original_package, package,
                ignore=shutil.ignore_patterns('__pycache__', '*.so', 'build', 'libclass.a'))
source_path = package / 'tools/evolver_ndf15.c'
original = source_path.read_text()
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == 'eaa907b6a785a2d29f194ba19e1a28f0c5f9938e59770695bd543aaecc4f1604'
primary_marker = '    for(i=1;i<=neq;i++) nj_ws->ydel_Fdel[i][j] = nj_ws->ffdel[i];'
secondary_marker = '          nj_ws->yydel[j] = y[j];'
assert original.count(primary_marker) == original.count(secondary_marker) == 1
primary = '''    /* A finite-difference trial can cross a frozen-species cutoff.
       Retry an ungrouped column in the other direction without changing
       the physical derivative function or replacing nonfinite values. */
    {
      int nonfinite_trial = 0;
      for (i=1;i<=neq;i++) if (!isfinite(nj_ws->ffdel[i])) nonfinite_trial = 1;
      if (nonfinite_trial && !(jac->use_sparse && jac->repeated_pattern >= jac->trust_sparse)) {
        nj_ws->del[j] = -nj_ws->del[j];
        for (i=1;i<=neq;i++) nj_ws->yydel[i] = y[i];
        nj_ws->yydel[j] += nj_ws->del[j];
        class_call((*derivs)(t,nj_ws->yydel+1,nj_ws->ffdel+1,
                   parameters_and_workspace_for_derivs,error_message),error_message,error_message);
        *nfe += 1;
      }
      for (i=1;i<=neq;i++) {
        class_test(!isfinite(nj_ws->ffdel[i]),error_message,
                   "Nonfinite numerical-Jacobian trial after permitted direction retry at t=%g, column/group=%d",t,j);
      }
    }
'''
secondary = '''          /* The roundoff-control increment needs the same protection. */
          {
            int nonfinite_trial = 0;
            for (i=1;i<=neq;i++) if (!isfinite(nj_ws->ffdel[i])) nonfinite_trial = 1;
            if (nonfinite_trial) {
              del2 = -del2;
              nj_ws->yydel[j] = y[j] + del2;
              class_call((*derivs)(t,nj_ws->yydel+1,nj_ws->ffdel+1,
                         parameters_and_workspace_for_derivs,error_message),error_message,error_message);
              *nfe += 1;
            }
            for (i=1;i<=neq;i++) {
              class_test(!isfinite(nj_ws->ffdel[i]),error_message,
                         "Both refined numerical-Jacobian directions give nonfinite derivatives at t=%g, column=%d",t,j);
            }
          }
'''
modified = original.replace(primary_marker, primary + primary_marker).replace(secondary_marker, secondary + secondary_marker)
base_marker = '    nj_ws->yscale[j] = MAX(fabs(y[j]),thresh);'
assert modified.count(base_marker) == 1
modified = modified.replace(base_marker, '''    class_test(!isfinite(y[j]) || !isfinite(fval[j]),error_message,
               "Nonfinite base state or derivative in numerical Jacobian at t=%g, coordinate=%d",t,j);
''' + base_marker)
division = '        dFdy[i][j] = Fdiff_new/nj_ws->del[j];'
assert modified.count(division) == 1
modified = modified.replace(division, division + '''
        class_test(!isfinite(dFdy[i][j]),error_message,
                   "Nonfinite dense numerical Jacobian at t=%g, row=%d, column=%d",t,i,j);
''')
refinement = '            nj_ws->tmp[i] = Fdiff_new/del2;'
assert modified.count(refinement) == 1
modified = modified.replace(refinement, refinement + '''
            class_test(!isfinite(nj_ws->tmp[i]),error_message,
                       "Nonfinite refined numerical Jacobian at t=%g, row=%d, column=%d",t,i,j);
''')
source_path.write_text(modified)
patch_directory = ROOT / 'patches'
patch_directory.mkdir(exist_ok=True)
patch_path = patch_directory / 'class-3.4.0-finite-jacobian.patch'
patch_path.write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True), modified.splitlines(keepends=True),
                                                fromfile='a/tools/evolver_ndf15.c', tofile='b/tools/evolver_ndf15.c')))
metadata = {'base_class_version': '3.4.0', 'base_classy_distribution_version': '3.4.0.1',
            'original_source_sha256': hashlib.sha256(original.encode()).hexdigest(),
            'patched_source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
            'patch_sha256': hashlib.sha256(patch_path.read_bytes()).hexdigest(),
            'scope': 'finite_difference_direction_retry_and_explicit_nonfinite_errors',
            'physical_derivative_formulas_changed': False,
            'uniform_numerical_accuracy_certified': False}
(patch_directory / 'class-3.4.0-finite-jacobian.json').write_text(json.dumps(metadata, indent=2) + '\n')
manifest = dict(metadata, utc=datetime.now(timezone.utc).isoformat(), overlay=str(overlay),
                package=str(package), original_package=str(original_package),
                active_inference_library_modified=False, build_parallel_jobs=2)
(HERE / 'preparation_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(overlay)
