"""Add diagnostic-only LU input logging to a separate executable."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
stage = sys.argv[1] if len(sys.argv) > 1 else 'lu'
assert stage in ('lu', 'jacobian', 'helium')
suffix = '' if stage == 'lu' else '_' + stage
manifest = json.loads((HERE / 'build_manifest.json').read_text())
package = Path(manifest['scratch_package'])
scratch = package.parent
source = package / 'tools/evolver_ndf15.c'
original = source.read_text()
marker = '    /*Dense LU decomposition: */'
assert original.count(marker) == 1
diagnostic = '''    /* Diagnostic only: retain all original arithmetic and error checks. */
    for (i=1;i<=neq;i++) {
      for (j=1;j<=neq;j++) {
        if (!isfinite(jac->LU[i][j])) {
          fprintf(stderr, "NONFINITE_LU_INPUT neq=%d i=%d j=%d hinvGak=%.17g dfdy=%.17g LU=%.17g\\n",
                  neq,i,j,hinvGak,jac->dfdy[i][j],jac->LU[i][j]);
        }
      }
    }
'''
modified = original.replace(marker, diagnostic + marker)
if stage in ('jacobian', 'helium'):
    division = '        dFdy[i][j] = Fdiff_new/nj_ws->del[j];'
    assert modified.count(division) == 1
    modified = modified.replace(division, division + '''
        if (!isfinite(dFdy[i][j])) {
          fprintf(stderr, "NONFINITE_JACOBIAN t=%.17g neq=%d i=%d j=%d y_j=%.17g increment=%.17g f_base=%.17g f_perturbed=%.17g difference=%.17g derivative=%.17g\\n",
                  t,neq,i,j,y[j],nj_ws->del[j],fval[i],nj_ws->ydel_Fdel[i][j],Fdiff_new,dFdy[i][j]);
        }
''')
probe_source = HERE / ('evolver_ndf15_diagnostic' + suffix + '.c')
probe_source.write_text(modified)
obj = scratch / ('evolver_ndf15_diagnostic' + suffix + '.o')
binary = scratch / ('class_lu_diagnostic' + suffix)
compile_command = ['gcc', '-O3', '-pthread', '-g', '-fPIC',
                   '-D__CLASSDIR__="' + str(package) + '"', '-DHYREC',
                   '-I' + str(package / 'include'), '-c', str(probe_source), '-o', str(obj)]
objects = sorted((package / 'build').glob('*.o')) + sorted((package / 'build').glob('*.opp'))
assert sum(x.name == 'evolver_ndf15.o' for x in objects) == 1
objects = [obj if x.name == 'evolver_ndf15.o' else x for x in objects]
compile_commands = [compile_command]
if stage == 'helium':
    wrapper_source = package / 'external/HyRec2020/wrap_hyrec.c'
    wrapper = wrapper_source.read_text()
    wrapper_marker = '    *dx_He_dz = -1./(1.+z)* rec_helium_dxHeIIdlna(phy->data, z, 1.-x_H, xHeII, Hz) / phy->data->cosmo->fHe;'
    assert wrapper.count(wrapper_marker) == 1
    wrapper_probe = HERE / 'wrap_hyrec_helium_diagnostic.c'
    wrapper_probe.write_text(wrapper.replace(wrapper_marker, wrapper_marker + '''
    if (!isfinite(*dx_He_dz)) {
      fprintf(stderr, "NONFINITE_HELIUM_RATE z=%.17g x_He=%.17g fHe=%.17g xHeII=%.17g limit=%.17g H=%.17g Tmat=%.17g Trad=%.17g rate=%.17g\\n",
              z,x_He,phy->data->cosmo->fHe,xHeII,phy->xHeII_limit,Hz,Tmat,Trad,*dx_He_dz);
    }
'''))
    wrapper_obj = scratch / 'wrap_hyrec_helium_diagnostic.o'
    compile_commands.append(['gcc', '-O3', '-pthread', '-g', '-fPIC',
                             '-D__CLASSDIR__="' + str(package) + '"', '-DHYREC',
                             '-I' + str(package / 'include'),
                             '-I' + str(package / 'external/HyRec2020'),
                             '-I' + str(package / 'external/RecfastCLASS'),
                             '-I' + str(package / 'external/heating'),
                             '-c', str(wrapper_probe), '-o', str(wrapper_obj)])
    assert sum(x.name == 'wrap_hyrec.o' for x in objects) == 1
    objects = [wrapper_obj if x.name == 'wrap_hyrec.o' else x for x in objects]
link_command = ['g++', '--std=c++11', '-fpermissive', '-Wno-write-strings', '-O3', '-pthread',
                '-g', '-fPIC', '-o', str(binary)] + [str(x) for x in objects] + ['-lm']
with (HERE / ('lu_probe' + suffix + '_build_stdout.txt')).open('w') as output:
    for command in compile_commands + [link_command]:
        subprocess.run(command, check=True, stdout=output, stderr=subprocess.STDOUT)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'original_source_sha256': sha(source),
           'probe_source_sha256': sha(probe_source), 'probe_binary': str(binary),
           'probe_binary_sha256': sha(binary), 'compile_command': compile_command,
           'link_command': link_command, 'original_diagnostic_binary_unchanged': True,
           'original_diagnostic_binary_sha256': sha(package / 'class'),
           'active_inference_backend_changed': False}
receipt['compile_commands'] = compile_commands
if stage == 'helium':
    receipt['wrapper_original_source_sha256'] = sha(wrapper_source)
    receipt['wrapper_probe_source_sha256'] = sha(wrapper_probe)
(HERE / ('lu_probe' + suffix + '_build_receipt.json')).write_text(json.dumps(receipt, indent=2) + '\n')
print(binary)
