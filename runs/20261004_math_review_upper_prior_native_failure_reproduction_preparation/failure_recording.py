"""Record an already-raised evaluation failure, then propagate that same exception."""
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import numpy as np


def call_and_record(original, model, values, outdir, *args, **kwargs):
    try:
        return original(model, values, *args, **kwargs)
    except Exception as original_error:
        trace = traceback.format_exc()
        outdir = Path(outdir)
        try:
            names = list(model.parameterization.sampled_params())
            sampled = ({name: float(values[name]) for name in names} if isinstance(values, dict)
                       else {name: float(value) for name, value in zip(names, values, strict=True)})
            out = {'utc': datetime.now(timezone.utc).isoformat(), 'sampled': sampled,
                   'exception_type': type(original_error).__name__, 'error': str(original_error),
                   'traceback': trace, 'evaluation_returned_posterior_rejection': False}
            try:
                spectra = model.provider.get_Cl(ell_factor=False, units='muK2')
                arrays = {str(k): np.asarray(v, dtype=float) for k, v in spectra.items()}
                out['spectra'] = {}
                for key, arr in arrays.items():
                    finite = arr[np.isfinite(arr)]
                    out['spectra'][key] = {'shape': list(arr.shape), 'ndim': arr.ndim,
                                           'all_finite': bool(np.all(np.isfinite(arr))),
                                           'nan_flat_indices': np.flatnonzero(np.isnan(arr)).tolist(),
                                           'inf_flat_indices': np.flatnonzero(np.isinf(arr)).tolist(),
                                           'finite_min': float(np.min(finite)) if finite.size else None,
                                           'finite_max': float(np.max(finite)) if finite.size else None}
                with (outdir / 'failed_provider_spectra.npz').open('xb') as f:
                    np.savez_compressed(f, **arrays)
            except Exception as spectrum_error:
                out['spectrum_capture_error'] = f'{type(spectrum_error).__name__}: {spectrum_error}'
            with (outdir / 'failed_proposal.json').open('x') as f:
                f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
        except Exception as recording_error:
            with (outdir / 'failure_recording_error.txt').open('x') as f:
                f.write(f'{type(recording_error).__name__}: {recording_error}\n')
        raise
