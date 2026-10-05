from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np
from failure_recording import call_and_record

HERE = Path(__file__).resolve().parent
calls = []
sentinel = object()
def success(model, values, *args, **kwargs):
    calls.append((model, values, args, kwargs))
    return sentinel
values = object()
assert call_and_record(success, sentinel, values, HERE, 7, cached=True) is sentinel
assert calls == [(sentinel, values, (7,), {'cached': True})]
class Parameters:
    def sampled_params(self):
        return {'mnu': None}
class Provider:
    def get_Cl(self, **kwargs):
        assert kwargs == {'ell_factor': False, 'units': 'muK2'}
        return {'tt': np.array([0., np.nan, np.inf]), 'ee': np.ones(3)}
class Model:
    parameterization = Parameters()
    provider = Provider()
model = Model()
error = ValueError('finite-spectrum control failure')
def failure(model, values, *args, **kwargs):
    raise error
folder = HERE / 'failure_control'
folder.mkdir(exist_ok=False)
try:
    call_and_record(failure, model, [6.], folder)
except ValueError as observed:
    assert observed is error
else:
    raise AssertionError('Original exception was swallowed.')
record = json.loads((folder / 'failed_proposal.json').read_text())
assert record['sampled'] == {'mnu': 6.}
assert not record['evaluation_returned_posterior_rejection']
assert record['spectra']['tt']['nan_flat_indices'] == [1]
assert record['spectra']['tt']['inf_flat_indices'] == [2]
assert record['spectra']['tt']['shape'] == [3]
assert record['spectra']['ee']['all_finite']
with (HERE / 'controls_receipt.json').open('x') as f:
    f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'original_success_result_identity_preserved': True,
                       'original_argument_forwarding_exact': True, 'original_exception_identity_rethrown': True,
                       'failure_sampled_coordinates_recorded': True, 'nonfinite_spectrum_indices_recorded': True,
                       'failure_returned_as_posterior_rejection': False}, indent=2) + '\n')
print('Failure recording controls passed: original results, arguments, and exception identity preserved.')
