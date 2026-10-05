"""Provenance/refusal checks for the opt-in native numerical policy."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import tarfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_camb_sigma_policy as builder


@pytest.fixture
def release_fixture(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    policy = json.loads(builder.POLICY_PATH.read_text())
    candidate = root / 'runs/20261005_math_review_CAMB204_sigma_integration_candidate14/candidate_halofit.f90'
    original = candidate.read_bytes()
    for change in reversed(policy['changes']):
        original = original.replace(change['after'].encode(), change['before'].encode(), 1)
    assert hashlib.sha256(original).hexdigest() == policy['original_source_sha256']
    archive = tmp_path / 'fixture.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name, data in [('camb-2.0.4/fortran/halofit.f90', original),
                           ('camb-2.0.4/LICENCE.txt', b'fixture license')]:
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, BytesIO(data))
    # This synthetic container is for unit tests only; retain real halofit hashes.
    policy['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    policy_path = tmp_path / 'fixture_policy.json'
    policy_path.write_text(json.dumps(policy))
    monkeypatch.setattr(builder, 'POLICY_PATH', policy_path)
    return archive, policy, original, candidate.read_bytes()


def test_pinned_source_prepares_exact_reviewed_bytes(release_fixture, tmp_path):
    archive, policy, original, candidate = release_fixture
    destination = tmp_path / 'private'
    source, receipt = builder.prepare(archive, destination)
    assert (source / policy['source_file']).read_bytes() == candidate
    assert (source / 'LICENCE.txt').read_bytes() == b'fixture license'
    assert len(receipt['files']) == 2
    assert sum(f['original_sha256'] != f['prepared_sha256'] for f in receipt['files']) == 1
    assert builder.apply_policy(original, policy) == candidate


@pytest.mark.parametrize('change', ['integrand', 'already_patched'])
def test_changed_or_already_patched_native_source_refused(release_fixture, change):
    _, policy, original, candidate = release_fixture
    data = original.replace(b'sigma_integrand', b'other_integrand', 1) if change == 'integrand' else candidate
    with pytest.raises(ValueError, match='Original halofit'):
        builder.apply_policy(data, policy)


def test_archive_mismatch_refused_before_output(release_fixture, tmp_path):
    archive, _, _, _ = release_fixture
    archive.write_bytes(archive.read_bytes() + b'changed source archive')
    destination = tmp_path / 'private'
    with pytest.raises(ValueError, match='Archive SHA256'):
        builder.prepare(archive, destination)
    assert not destination.exists()


def test_existing_directory_and_receipts_never_overwritten(release_fixture, tmp_path):
    archive, _, _, _ = release_fixture
    destination = tmp_path / 'private'
    destination.mkdir()
    marker = destination / 'build_receipt.json'
    marker.write_bytes(b'preserved existing receipt')
    with pytest.raises(FileExistsError):
        builder.prepare(archive, destination)
    assert marker.read_bytes() == b'preserved existing receipt'


def test_patch_output_hash_guards_policy_changes(release_fixture):
    _, policy, original, _ = release_fixture
    policy['changes'][0]['after'] = policy['changes'][0]['after'].replace('1e-6', '1e-3')
    with pytest.raises(ValueError, match='reviewed candidate'):
        builder.apply_policy(original, policy)


def test_cli_refuses_dangling_destination_link(release_fixture, tmp_path, monkeypatch):
    archive, _, _, _ = release_fixture
    destination = tmp_path / 'existing_link'
    target = tmp_path / 'absent_target'
    destination.symlink_to(target)
    monkeypatch.setattr(sys, 'argv', ['builder', '--archive', str(archive),
                                    '--destination', str(destination), '--prepare-only'])
    with pytest.raises(FileExistsError):
        builder.main()
    assert destination.is_symlink() and not target.exists()


def test_explicit_v2_preparation_binds_selected_policy(release_fixture, tmp_path):
    archive, fixture_policy, original, _ = release_fixture
    root = Path(__file__).resolve().parents[1]
    selected = json.loads((root / 'native_policies/camb204_sigma_refinement_v2.json').read_text())
    selected['archive_sha256'] = fixture_policy['archive_sha256']
    policy_path = tmp_path / 'selected_v2.json'
    policy_path.write_text(json.dumps(selected))
    source, receipt = builder.prepare(archive, tmp_path / 'v2', policy_path)
    actual = (source / selected['source_file']).read_bytes()
    expected = root / 'runs/20261005_math_review_sigma_limit22_candidate/candidate_halofit.f90'
    assert actual == expected.read_bytes()
    assert receipt['policy_id'] == 'camb204_sigma_refinement_v2'
    assert receipt['policy_sha256'] == hashlib.sha256(policy_path.read_bytes()).hexdigest()
    assert receipt['policy_path'] == str(policy_path.resolve())


@pytest.mark.parametrize('defect', ['policy', 'source'])
def test_build_refuses_changed_preparation_before_compilation(release_fixture, tmp_path, defect):
    archive, _, _, _ = release_fixture
    destination = tmp_path / 'prepared'
    source, receipt = builder.prepare(archive, destination)
    if defect == 'policy':
        Path(receipt['policy_path']).write_text('{}')
    else:
        (source / 'fortran/halofit.f90').write_bytes(b'changed scientific source')
    with pytest.raises(ValueError, match='changed'):
        builder.build(source, destination, None, profile='optimized')
    assert not (destination / 'build_stdout.txt').exists()
    assert not (destination / 'build_receipt.json').exists()


def test_invalid_profile_refused_before_reading_or_building(tmp_path):
    with pytest.raises(ValueError, match='profile'):
        builder.build(tmp_path / 'missing_source', tmp_path / 'missing_output', None, 'fast-math')
    assert not list(tmp_path.iterdir())


@pytest.fixture
def combined_release_fixture(release_fixture, tmp_path):
    _, _, original_halofit, _ = release_fixture
    root = Path(__file__).resolve().parents[1]
    policy = json.loads((root / 'native_policies/camb204_sigma_time_v3.json').read_text())
    results_candidate = (root / 'runs/20261005_math_review_sigma_time_endpoint_candidate_v3/candidate_results.f90').read_bytes()
    original_results = results_candidate
    for change in reversed(policy['sources'][1]['changes']):
        original_results = original_results.replace(change['after'].encode(), change['before'].encode(), 1)
    assert hashlib.sha256(original_results).hexdigest() == policy['sources'][1]['original_source_sha256']
    archive = tmp_path / 'combined_fixture.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name, data in [('fortran/halofit.f90', original_halofit),
                           ('fortran/results.f90', original_results),
                           ('LICENCE.txt', b'fixture license')]:
            member = tarfile.TarInfo('camb-2.0.4/' + name)
            member.size = len(data)
            tar.addfile(member, BytesIO(data))
    policy['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    policy_path = tmp_path / 'combined_policy.json'
    policy_path.write_text(json.dumps(policy))
    return archive, policy_path, results_candidate


def test_combined_policy_prepares_both_reviewed_sources(combined_release_fixture, tmp_path):
    archive, policy_path, results_candidate = combined_release_fixture
    source, receipt = builder.prepare(archive, tmp_path / 'combined', policy_path)
    assert (source / 'fortran/results.f90').read_bytes() == results_candidate
    expected = Path(__file__).resolve().parents[1] / 'runs/20261005_math_review_sigma_limit22_candidate/candidate_halofit.f90'
    assert (source / 'fortran/halofit.f90').read_bytes() == expected.read_bytes()
    assert (source / 'LICENCE.txt').read_bytes() == b'fixture license'
    assert {f['path'] for f in receipt['files'] if f['original_sha256'] != f['prepared_sha256']} == {
        'camb-2.0.4/fortran/halofit.f90', 'camb-2.0.4/fortran/results.f90'}


@pytest.mark.parametrize('defect', ['second_source_hash', 'second_patch_hash', 'duplicate', 'empty', 'parent_path'])
def test_combined_policy_defects_refused_before_output(combined_release_fixture, tmp_path, defect):
    archive, policy_path, _ = combined_release_fixture
    policy = json.loads(policy_path.read_text())
    if defect == 'second_source_hash':
        policy['sources'][1]['original_source_sha256'] = '0' * 64
    elif defect == 'second_patch_hash':
        policy['sources'][1]['patched_source_sha256'] = '0' * 64
    elif defect == 'duplicate':
        policy['sources'].append(policy['sources'][0])
    elif defect == 'empty':
        policy['sources'] = []
    else:
        policy['sources'][1]['source_file'] = '../results.f90'
    policy_path.write_text(json.dumps(policy))
    destination = tmp_path / 'refused'
    with pytest.raises(ValueError):
        builder.prepare(archive, destination, policy_path)
    assert not destination.exists()


def test_combined_build_refuses_changed_second_source(combined_release_fixture, tmp_path):
    archive, policy_path, _ = combined_release_fixture
    destination = tmp_path / 'changed_results'
    source, _ = builder.prepare(archive, destination, policy_path)
    (source / 'fortran/results.f90').write_bytes(b'changed time integrator')
    with pytest.raises(ValueError, match='Prepared source changed'):
        builder.build(source, destination, None, 'optimized')
    assert not (destination / 'build_stdout.txt').exists()


def test_cli_selects_combined_policy_explicitly(combined_release_fixture, tmp_path, monkeypatch):
    archive, policy_path, results_candidate = combined_release_fixture
    selected_path = builder.POLICY_PATH.with_name('camb204_sigma_time_v3.json')
    selected_path.write_bytes(policy_path.read_bytes())
    destination = tmp_path / 'cli_combined'
    monkeypatch.setattr(sys, 'argv', ['builder', '--archive', str(archive),
                                    '--destination', str(destination), '--policy', 'v3', '--prepare-only'])
    assert builder.main() == 0
    preparation = json.loads((destination / 'source_preparation.json').read_text())
    assert preparation['policy_id'] == 'camb204_sigma_time_v3'
    assert preparation['policy_path'] == str(selected_path.resolve())
    assert (destination / 'camb-2.0.4/fortran/results.f90').read_bytes() == results_candidate
