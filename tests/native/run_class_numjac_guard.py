"""Compile and exercise the real CLASS numjac implementation in a supplied build."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--class-dir', type=Path, required=True)
    args = parser.parse_args()
    package = args.class_dir.resolve()
    source = Path(__file__).with_name('class_numjac_guard.c')
    with tempfile.TemporaryDirectory(prefix='sbt-class-numjac-') as directory:
        obj = Path(directory) / 'guard.o'
        exe = Path(directory) / 'guard'
        subprocess.run(['gcc', '-std=c11', '-O2', '-I' + str(package / 'include'),
                        '-c', str(source), '-o', str(obj)], check=True)
        subprocess.run(['g++', '-pthread', str(obj), str(package / 'libclass.a'),
                        '-lm', '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
