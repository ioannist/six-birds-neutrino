"""Likelihood wrappers for external inference tools."""

from .candl_cobaya import CandlCobayaLikelihood
from .desi_dr2_bao import DESIDR2BAOGaussian

__all__ = ["CandlCobayaLikelihood", "DESIDR2BAOGaussian"]
