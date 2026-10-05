#!/usr/bin/env python3
"""Prepare/build a pinned opt-in CAMB policy in a new private directory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile

POLICY_PATH = Path(__file__).resolve().parents[1] / 'native_policies/camb204_sigma_refinement_v1.json'
FFLAGS = '-O0 -g -fbacktrace -fbounds-check -MMD -cpp -ffree-line-length-none -fmax-errors=4 -fopenmp'
PROFILES = {
    'audit': FFLAGS,
    'optimized': '-O3 -fno-unsafe-math-optimizations -ffp-contract=off -MMD -cpp -ffree-line-length-none -fmax-errors=4 -fopenmp',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_policy(original: bytes, policy: dict) -> bytes:
    if sha(original) != policy['original_source_sha256']:
        name = PurePosixPath(policy['source_file']).stem
        raise ValueError(f'Original {name} source differs from the pinned CAMB release.')
    patched = original
    for change in policy['changes']:
        before, after = change['before'].encode(), change['after'].encode()
        if patched.count(before) != 1:
            raise ValueError('Patch context is ambiguous or missing.')
        patched = patched.replace(before, after, 1)
    if sha(patched) != policy['patched_source_sha256']:
        raise ValueError('Patched source differs from the reviewed candidate.')
    return patched


def prepare(archive: Path, destination: Path, policy_path: Path | None = None) -> tuple[Path, dict]:
    policy_path = policy_path if policy_path is not None else POLICY_PATH
    policy_bytes = policy_path.read_bytes()
    policy = json.loads(policy_bytes)
    # Check provenance and patch before creating any output.
    raw = archive.read_bytes()
    if sha(raw) != policy['archive_sha256']:
        raise ValueError('Archive SHA256 differs from the pinned CAMB 2.0.4 sdist.')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Destination already exists; choose a fresh private directory.')
    source_files = []
    with tarfile.open(fileobj=BytesIO(raw)) as tar:
        members = tar.getmembers()
        names = set()
        for member in members:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or not path.parts
                    or path.parts[0] != policy['source_root']
                    or not (member.isfile() or member.isdir()) or member.name in names):
                raise ValueError('Archive has an unsupported member or path.')
            names.add(member.name)
        source_policies = policy.get('sources', [policy])
        if not source_policies:
            raise ValueError('Policy has no source changes.')
        patches = {}
        for source_policy in source_policies:
            relative = PurePosixPath(source_policy['source_file'])
            if relative.is_absolute() or '..' in relative.parts or not relative.parts:
                raise ValueError('Policy has an unsupported source path.')
            target = policy['source_root'] + '/' + str(relative)
            if target in patches:
                raise ValueError('Policy has duplicate source changes.')
            member = tar.getmember(target)
            if not member.isfile():
                raise ValueError('Policy source must be an archive file.')
            original = tar.extractfile(member).read()
            patches[target] = apply_policy(original, source_policy)
        destination.mkdir(parents=True, exist_ok=False)
        for member in members:
            path = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            data = tar.extractfile(member).read()
            with path.open('xb') as f:
                f.write(patches.get(member.name, data))
            source_files.append({'path': member.name, 'original_sha256': sha(data),
                                 'prepared_sha256': sha(path.read_bytes())})
    source = destination / policy['source_root']
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'policy_id': policy['policy_id'],
               'solver_version': policy['solver_version'], 'policy_sha256': sha(policy_bytes),
               'policy_path': str(policy_path.resolve()),
               'archive': str(archive.resolve()), 'archive_sha256': sha(raw),
               'source_root': str(source.resolve()), 'files': source_files,
               'scope': policy['scope'], 'production_adopted': False}
    with (destination / 'source_preparation.json').open('x') as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
        f.write('\n')
    return source, receipt


def build(source: Path, destination: Path, compiler_directory: Path | None, profile: str = 'audit') -> int:
    if profile not in PROFILES:
        raise ValueError('Unknown build profile.')
    preparation = json.loads((destination / 'source_preparation.json').read_text())
    if sha(Path(preparation['policy_path']).read_bytes()) != preparation['policy_sha256']:
        raise ValueError('Policy changed since source preparation.')
    for entry in preparation['files']:
        if sha((destination / entry['path']).read_bytes()) != entry['prepared_sha256']:
            raise ValueError('Prepared source changed before the build.')
    env = os.environ.copy()
    if compiler_directory is not None:
        env['PATH'] = str(compiler_directory.resolve()) + os.pathsep + env.get('PATH', '')
    compiler = shutil.which('gfortran', path=env.get('PATH'))
    if compiler is None:
        raise ValueError('gfortran is unavailable; use --compiler-directory or --prepare-only.')
    version = subprocess.check_output([compiler, '--version'], env=env, text=True)
    command = ['make', '-j2', 'python', 'COMPILER=gfortran', 'CLUSTER_SAFE=1', f'FFLAGS={PROFILES[profile]}']
    with (destination / 'build_stdout.txt').open('xb') as out, (destination / 'build_stderr.txt').open('xb') as err:
        result = subprocess.run(command, cwd=source / 'fortran', env=env, stdout=out, stderr=err)
    module = source / 'camb/camblib.so'
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'policy_id': preparation['policy_id'],
               'policy_sha256': preparation['policy_sha256'], 'build_profile': profile,
               'source_preparation_sha256': sha((destination / 'source_preparation.json').read_bytes()),
               'command': command, 'compiler': compiler, 'compiler_sha256': sha(Path(compiler).read_bytes()),
               'compiler_version': version, 'LD_LIBRARY_PATH': env.get('LD_LIBRARY_PATH', ''),
               'exit_code': result.returncode,
               'module': str(module.resolve()) if module.exists() else None,
               'module_sha256': sha(module.read_bytes()) if module.exists() else None,
               'production_adopted': False, 'posterior_or_uniform_accuracy_certified': False}
    with (destination / 'build_receipt.json').open('x') as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
        f.write('\n')
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--compiler-directory', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--policy', choices=['v1', 'v2', 'v3'], default='v1')
    parser.add_argument('--build-profile', choices=sorted(PROFILES), default='audit')
    args = parser.parse_args()
    destination = args.destination.expanduser()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Destination already exists; choose a fresh private directory.')
    destination = destination.resolve()
    policy_path = {
        'v1': POLICY_PATH,
        'v2': POLICY_PATH.with_name('camb204_sigma_refinement_v2.json'),
        'v3': POLICY_PATH.with_name('camb204_sigma_time_v3.json'),
    }[args.policy]
    source, _ = prepare(args.archive.expanduser(), destination, policy_path)
    if args.prepare_only:
        return 0
    return build(source, destination, args.compiler_directory, args.build_profile)


if __name__ == '__main__':
    raise SystemExit(main())
