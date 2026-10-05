"""Actual sampler output must preserve the in-memory floating point witness."""
import numpy as np
import pytest
pytest.importorskip('cobaya')
from cobaya.run import run
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_cobaya import _configure_chain_output, _inject_seed, _inject_max_samples_override


def test_mcmc_text_round_trips_sampled_parameters_and_likelihoods(tmp_path):
    info = {'params': {'x': {'prior': {'min': -10., 'max': 10.},
                            'ref': .12345678901234567, 'proposal': .1}},
            'likelihood': {'gaussian': {'external': lambda x: -x*x/2}},
            'sampler': {'mcmc': {
                                'seed': 17, 'max_samples': 8, 'learn_proposal': False,
                                'measure_speeds': False}},
            'output': str(tmp_path/'precise')}
    _inject_seed(info, 17)
    _inject_max_samples_override(info, 8)
    _configure_chain_output(info)
    _, sampler = run(info, no_mpi=True)
    memory = sampler.collection.data.to_numpy(dtype=np.float64)
    disk = np.atleast_2d(np.loadtxt(tmp_path/'precise.1.txt'))
    assert disk.shape == memory.shape
    assert np.array_equal(disk, memory)
    before = (tmp_path/'precise.1.txt').read_bytes()
    info['resume'] = True
    info['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC'].update(max_samples=16)
    info['sampler']['sbt_spt_audit.samplers.FullPrecisionMCMC']['seed'] = 918273
    _, continued = run(info, no_mpi=True)
    assert continued.seed == 918273
    assert (tmp_path/'precise.1.txt').read_bytes().startswith(before)
    assert np.array_equal(np.atleast_2d(np.loadtxt(tmp_path/'precise.1.txt')),
                          continued.collection.data.to_numpy(dtype=np.float64))
