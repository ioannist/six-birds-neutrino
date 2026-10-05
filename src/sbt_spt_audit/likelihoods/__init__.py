"""Likelihood wrappers for external inference tools."""

from .desi_dr2_bao import DESIDR2BAOGaussian

__all__ = ["CandlCobayaLikelihood", "DESIDR2BAOGaussian"]


def __getattr__(name):
    # Numerical BAO utilities do not require the optional CMB inference stack.
    if name == "CandlCobayaLikelihood":
        from .candl_cobaya import CandlCobayaLikelihood
        return CandlCobayaLikelihood
    raise AttributeError(name)
