"""CAMB evaluation with fresh native transfers and ordinary spectrum caching.

Selected controls show that a cached CAMB transfer result can produce different
spectra after another cosmology or model has been evaluated. Recalculating the
transfers preserves the forced-fresh numerical target. This adapter leaves
CAMB's parameters, requirements, native numerical settings and spectrum
calculation unchanged; its cost is an extra transfer calculation on fast moves.
"""
from collections.abc import MutableMapping
from cobaya.theories.camb.camb import CAMB, CambTransfers


class FreshCAMBTransfers(CambTransfers):
    """Never reuse a native transfer result, including after sampler resizing."""

    def check_cache_and_compute(self, params_values_dict, dependency_params=None,
                                want_derived=False, cached=True):
        return super().check_cache_and_compute(
            params_values_dict, dependency_params=dependency_params,
            want_derived=want_derived, cached=False,
        )


class FreshCAMB(CAMB):
    """Standard Cobaya CAMB theory with forced-fresh native transfer evaluation."""

    def get_helper_theories(self):
        self._camb_transfers = FreshCAMBTransfers(
            self, 'camb.transfers', {'stop_at_error': self.stop_at_error},
            timing=self.timer,
        )
        self._camb_transfers.requires = self._transfer_requires
        return {'camb.transfers': self._camb_transfers}


FRESH_CAMB_CLASS = 'sbt_spt_audit.boltzmann.FreshCAMB'


def configure_fresh_camb_transfers(config):
    """Record the effective CAMB adapter in a config before writing or using it.

    Custom theory classes require their own reviewed transfer handling; silently
    replacing them could alter the target. CLASS configurations are untouched.
    """
    theory = config.get('theory', {})
    if 'camb' not in theory:
        return
    options = theory['camb']
    if options is None:
        options = theory['camb'] = {}
    if not isinstance(options, MutableMapping):
        raise ValueError('Fresh CAMB evaluation requires a theory option mapping.')
    if options.get('external') is not None or options.get('class') not in (None, 'camb', FRESH_CAMB_CLASS):
        raise ValueError('Custom CAMB theory requires separately reviewed fresh-transfer handling.')
    options['class'] = FRESH_CAMB_CLASS
