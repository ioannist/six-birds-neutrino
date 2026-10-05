"""Localize the saved-row discrepancy with small, explicit native histories."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'src'))
from cobaya.model import get_model
import camb

calls = [json.loads(s) for s in (HERE / 'sampler_trajectory_trace/posterior_calls.jsonl').read_text().splitlines()]
config = yaml.safe_load((HERE / 'sampler_trajectory_trace/input.yaml').read_text())
config = {k: config[k] for k in ['theory', 'likelihood', 'params', 'packages_path']}
assert importlib.metadata.version('camb') == '1.6.5'
cases = [('initial_then_target', [0, 35], False),
         ('earlier_fast_then_target', [0, 32, 35], False),
         ('slow_then_target', [0, 1, 35], False),
         ('late_window', [0, 32, 33, 34, 35], False),
         ('late_window_independent_copy', [0, 32, 33, 34, 35], True)]
records = []
for name, sequence, use_copy in cases:
    getter_calls = []
    with get_model(config, stop_at_error=True) as model:
        helper = model.theory['camb.transfers']
        original = helper.get_CAMB_transfers
        def observe_getter():
            params, results = original()
            getter_calls.append({'state_params': dict(helper.current_state['params']),
                                 'As_before_spectra': float(results.Params.InitPower.As),
                                 'ns_before_spectra': float(results.Params.InitPower.ns),
                                 'has_scalar_time_sources': bool(results.HasScalarTimeSources)})
            return (params.copy(), results.copy()) if use_copy else (params, results)
        helper.get_CAMB_transfers = observe_getter
        values = []
        for index in sequence:
            posterior = model.logposterior(calls[index]['point'], cached=True)
            values.append({'call': index, 'loglikes': [float(v) for v in posterior.loglikes],
                           'getter_call_count': len(getter_calls),
                           'transfer_state_params': dict(helper.current_state['params'])})
        cached = values[-1]['loglikes']
        fresh = [float(v) for v in model.logposterior(calls[35]['point'], cached=False).loglikes]
        record = {'case': name, 'sequence': sequence, 'independent_copy': use_copy,
                  'values': values, 'getter_calls': getter_calls,
                  'fresh_target_loglikes': fresh,
                  'cached_minus_fresh_chi2': [-2 * (a-b) for a,b in zip(cached,fresh)],
                  'helper_non_linear_sources': helper.non_linear_sources}
        records.append(record)
        print(name, record['cached_minus_fresh_chi2'], 'getter calls', len(getter_calls), flush=True)
native = Path(camb.baseconfig.camblib._name).resolve()
receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
           'native_path': str(native), 'native_sha256': hashlib.sha256(native.read_bytes()).hexdigest(),
           'scope': 'selected history-localization controls, no inference or production changes'}
with (HERE / 'reduced_histories_receipt.json').open('x') as handle:
    handle.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
