"""Build an isolated dense-Jacobian finite-difference repair candidate."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
build = json.loads((HERE / 'lu_probe_helium_build_receipt.json').read_text())
scratch = Path(build['probe_binary']).parent
source = (HERE / 'evolver_ndf15_diagnostic_helium.c').read_text()
primary_marker = '    for(i=1;i<=neq;i++) nj_ws->ydel_Fdel[i][j] = nj_ws->ffdel[i];'
secondary_marker = '          nj_ws->yydel[j] = y[j];'
assert source.count(primary_marker) == source.count(secondary_marker) == 1
primary = '''    /* Candidate repair: retry a nonfinite dense finite difference inward. */
    {
      int nonfinite_trial = 0;
      for (i=1;i<=neq;i++) if (!isfinite(nj_ws->ffdel[i])) nonfinite_trial = 1;
      if (nonfinite_trial && !(jac->use_sparse && jac->repeated_pattern >= jac->trust_sparse)) {
        fprintf(stderr, "RETRY_NONFINITE_PRIMARY t=%.17g column=%d original_increment=%.17g\\n",t,j,nj_ws->del[j]);
        nj_ws->del[j] = -nj_ws->del[j];
        for (i=1;i<=neq;i++) nj_ws->yydel[i] = y[i];
        nj_ws->yydel[j] += nj_ws->del[j];
        class_call((*derivs)(t,nj_ws->yydel+1,nj_ws->ffdel+1,
                   parameters_and_workspace_for_derivs,error_message),error_message,error_message);
        *nfe += 1;
        for (i=1;i<=neq;i++) {
          class_test(!isfinite(nj_ws->ffdel[i]),error_message,
                     "Both dense finite-difference directions give nonfinite derivatives at t=%g, column=%d",t,j);
        }
      }
    }
'''
secondary = '''          /* The larger roundoff-control increment needs the same finite check. */
          {
            int nonfinite_trial = 0;
            for (i=1;i<=neq;i++) if (!isfinite(nj_ws->ffdel[i])) nonfinite_trial = 1;
            if (nonfinite_trial) {
              fprintf(stderr, "RETRY_NONFINITE_SECONDARY t=%.17g column=%d original_increment=%.17g\\n",t,j,del2);
              del2 = -del2;
              nj_ws->yydel[j] = y[j] + del2;
              class_call((*derivs)(t,nj_ws->yydel+1,nj_ws->ffdel+1,
                         parameters_and_workspace_for_derivs,error_message),error_message,error_message);
              *nfe += 1;
              for (i=1;i<=neq;i++) {
                class_test(!isfinite(nj_ws->ffdel[i]),error_message,
                           "Both refined finite-difference directions give nonfinite derivatives at t=%g, column=%d",t,j);
              }
            }
          }
'''
source = source.replace(primary_marker, primary + primary_marker).replace(secondary_marker, secondary + secondary_marker)
path = HERE / 'evolver_ndf15_finite_retry.c'
path.write_text(source)
obj = scratch / 'evolver_ndf15_finite_retry.o'
binary = scratch / 'class_ndf_finite_retry'
compile_command = [str(path) if x == str(HERE / 'evolver_ndf15_diagnostic_helium.c')
                   else str(obj) if x == str(scratch / 'evolver_ndf15_diagnostic_helium.o') else x
                   for x in build['compile_commands'][0]]
link_command = [str(binary) if x == build['probe_binary']
                else str(obj) if x == str(scratch / 'evolver_ndf15_diagnostic_helium.o') else x
                for x in build['link_command']]
with (HERE / 'finite_retry_build_stdout.txt').open('w') as output:
    for command in [compile_command, link_command]:
        subprocess.run(command, check=True, stdout=output, stderr=subprocess.STDOUT)
sha = lambda value: hashlib.sha256(value.read_bytes()).hexdigest()
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': sha(path),
           'binary': str(binary), 'binary_sha256': sha(binary),
           'compile_command': compile_command, 'link_command': link_command,
           'scope': 'candidate_dense_numerical_Jacobian_repair_separate_executable',
           'physical_derivative_function_changed': False, 'active_inference_backend_changed': False,
           'uniform_numerical_accuracy_certified': False}
(HERE / 'finite_retry_build_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(binary)
