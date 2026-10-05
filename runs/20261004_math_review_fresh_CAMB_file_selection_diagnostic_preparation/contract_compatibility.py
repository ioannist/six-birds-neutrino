"""Permit only the reviewed reader update across otherwise identical contracts."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path


def require_compatible_previous(current, current_sha256, previous_sha256, root):
    if previous_sha256 == current_sha256:
        return
    record = current.get('compatible_predecessor_contracts', {}).get(previous_sha256)
    if record is None:
        raise ValueError('Unknown predecessor assessment contract.')
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    path = Path(root) / record['path']
    if sha(path) != previous_sha256:
        raise ValueError('Predecessor contract bytes do not match their recorded hash.')
    proof = Path(root) / record['validation_receipt']
    if sha(proof) != record['validation_receipt_sha256']:
        raise ValueError('Reader-update validation receipt hash mismatch.')
    evidence = json.loads(proof.read_text())
    if not evidence.get('all_requested_reports_identical', False):
        raise ValueError('Reader-update report replay is incomplete.')
    if evidence['latest_reports_count'] != 9 or len(evidence['records']) != 9:
        raise ValueError('All nine current cohort reports must be replayed.')
    if evidence['reader_source_sha256'] != current['diagnostic_source_sha256']['scripts/extract_mnu_limits.py']:
        raise ValueError('Reader-update validation does not describe the current reader.')
    # This transition is deliberately restricted to the checked chain-file selection repair.
    if record['allowed_reader_source_updates'] != ['scripts/extract_mnu_limits.py']:
        raise ValueError('Only the reviewed chain-reader source update is permitted.')
    previous = json.loads(path.read_text())
    previous.pop('compatible_predecessor_contracts', None)
    candidate = deepcopy(current)
    candidate.pop('compatible_predecessor_contracts', None)
    previous['diagnostic_source_sha256']['scripts/extract_mnu_limits.py'] = candidate['diagnostic_source_sha256']['scripts/extract_mnu_limits.py']
    if previous != candidate:
        raise ValueError('Predecessor target, native identity, sampling policy or gates differ.')
