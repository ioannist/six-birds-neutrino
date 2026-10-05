"""Cobaya MCMC with round-trip-safe chain serialization and readback.

The collection's text precision changes. Proposals, acceptance, priors,
likelihoods, and stopping rules remain those of the installed Cobaya MCMC.
"""
import numpy as np
from cobaya.samplers.mcmc.mcmc import MCMC


class FullPrecisionMCMC(MCMC):
    # Upstream checkpoints do not retain RNG state. A resumed segment must be
    # able to select a fresh seed instead of replaying the original stream.
    _at_resume_prefer_new = MCMC._at_resume_prefer_new + ['seed']

    def initialize(self):
        super().initialize()
        # Cobaya 3.6.2 hard-codes eight significant figures in SampleCollection.
        # Configure before the first sampler step or appended output. Existing
        # historical files are never rewritten by this class.
        collection = self.collection
        if not hasattr(collection, '_numpy_fmts'):
            raise ValueError('Full precision requires a supported Cobaya collection.')
        collection.n_float = 17
        collection._numpy_fmts = [f'%{collection._width_col(n)}.17g'
                                  for n in collection.data.columns]
        if collection.n_last_out:
            # Cobaya's pandas reader does not request round-trip conversion.
            # Restore recorded binary64 values before extending a precise file.
            disk = np.atleast_2d(np.loadtxt(collection.file_name))
            if disk.shape != collection.data.shape or not np.all(np.isfinite(disk)):
                raise ValueError('Cannot restore a finite precise collection.')
            collection.data.loc[:, :] = disk
            last = collection.data.iloc[-1]
            point = {n: float(last[n]) for n in collection.sampled_params}
            self.current_point.add(np.asarray(list(point.values()), dtype=np.float64),
                                   self.model.logposterior(point, cached=False))
