"""Build the copied package's Python extension without running upstream make -j."""
import json
from pathlib import Path
import subprocess

from Cython.Build import cythonize
import numpy as np
from setuptools import Extension, setup

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / 'preparation_manifest.json').read_text())
package = Path(manifest['package'])
assert (package / 'libclass.a').exists()
runtime = Path(subprocess.check_output(['gcc', '-print-libgcc-file-name'], text=True).strip()).parent
extension = Extension(
    'classy._classy', [str(package / 'python/classy.pyx')],
    include_dirs=[np.get_include(), str(package / 'include'),
                  str(package / 'external/heating'), str(package / 'external/RecfastCLASS'),
                  str(package / 'external/HyRec2020')],
    libraries=['class', 'mvec', 'm'], library_dirs=[str(package), str(runtime)],
    language='c++', extra_compile_args=['-std=c++11', '-pthread'], extra_link_args=['-pthread'],
)
setup(name='sbt-classy-repaired-backend', version='3.4.0.1', packages=[],
      ext_modules=cythonize([extension], compiler_directives={'language_level': 3}, quiet=True))
