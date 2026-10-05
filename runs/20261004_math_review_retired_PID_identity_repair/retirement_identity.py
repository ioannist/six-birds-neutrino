"""Observe absence of a recorded process identity without signaling a PID."""
from pathlib import Path


def observe_retired_identity(pid, expected_start_ticks, proc_root=Path('/proc')):
    if type(pid) is not int or pid <= 0:
        raise ValueError('A positive integer PID is required.')
    if type(expected_start_ticks) is not int or expected_start_ticks <= 0:
        raise ValueError('Recorded positive process-start ticks are required.')
    record = {'pid': pid, 'expected_start_ticks': expected_start_ticks}
    try:
        raw = (Path(proc_root) / str(pid) / 'stat').read_text()
    except (FileNotFoundError, ProcessLookupError):
        return {**record, 'status': 'PID_not_present', 'original_identity_absent': True}
    fields = raw.rsplit(')', 1)[1].split()
    if int(raw.split(' ', 1)[0]) != pid:
        raise ValueError('Observed stat PID differs from the requested PID.')
    observed_ticks = int(fields[19])
    if observed_ticks <= 0:
        raise ValueError('Observed process-start ticks must be positive.')
    same = observed_ticks == expected_start_ticks
    return {**record, 'observed_start_ticks': observed_ticks,
            'observed_state': fields[0],
            'observed_process_name': raw[raw.find('(') + 1:raw.rfind(')')],
            'status': 'original_process_identity_present' if same else 'PID_reused_by_different_identity',
            'original_identity_absent': not same}
