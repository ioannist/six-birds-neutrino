#!/usr/bin/env python3
"""Build a Gauss-Newton MCMC proposal, never a posterior covariance claim.

The target likelihood is unmodified. Covariance-derivative curvature and
nonlinear residual terms are deliberately absent from this proposal heuristic.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from cobaya.model import get_model
from sbt_spt_audit.boltzmann import configure_fresh_camb_transfers
from sbt_spt_audit.candl_support import compute_gaussian_residual_and_covariance
from sbt_spt_audit.likelihoods.desi_dr2_bao import compute_theory_vector
from sbt_spt_audit.metrics import covariance_solve
from run_cosmological_audit import SPT, write_json

BAO = 'sbt_spt_audit.likelihoods.desi_dr2_bao.DESIDR2BAOGaussian'
PLIK = 'planck_2018_highl_plik.TT_lite_native'
LENSING = 'planckpr4lensing.PlanckPR4Lensing'
LOW = {'planck_2018_lowl.TT', 'planck_2018_lowl.EE_sroll2'}


def gaussian_completion_residuals(model, inputs, native_loglikes):
    """Residuals in the exact coordinate order of native Gaussian completions.

    Every returned residual reconstructs that component's native -2 log L.
    Non-Gaussian low-l components are intentionally handled separately.
    """
    cls = model.provider.get_Cl(ell_factor=True)
    responses = {}
    if PLIK in model.likelihood:
        like = model.likelihood[PLIK]
        pred = []
        for key, bins in zip(('tt', 'te', 'ee'), like.used_bins):
            for i in bins:
                pred.append(np.dot(cls[key][like.blmin[i]:like.blmax[i] + 1],
                                   like.weights[like.blmin[i]:like.blmax[i] + 1]))
        residual = like.X_data - np.asarray(pred) / inputs[like.calibration_param] ** 2
        responses[PLIK] = (residual, like.cov)
    if LENSING in model.likelihood:
        like = model.likelihood[LENSING]
        if like.like_approx != 'gaussian' or not like.binned:
            raise ValueError('Lensing proposal bridge requires native binned Gaussian form.')
        pars = {n: inputs[n] for n in like.input_params}
        like.get_theory_map_cls(cls, pars)
        binned = like.get_binned_map_cls(like.map_cls)
        pieces = []
        for b in range(like.nbins_used):
            matrix = np.empty((like.nmaps, like.nmaps))
            like.elements_to_matrix(binned[b, :], matrix)
            if like.cl_noise is not None:
                matrix += like.noise_matrix[b]
            matrix -= like.bandpower_matrix[b]
            vector = np.empty(like.ncl)
            like.matrix_to_elements(matrix, vector)
            pieces.append(vector[like.cl_used_index])
        residual = np.concatenate(pieces)
        covariance_solve(like.covinv, np.ones(residual.size))
        responses[LENSING] = (residual, np.linalg.inv(like.covinv))
    for name, (residual, covariance) in responses.items():
        q = float(residual @ covariance_solve(covariance, residual))
        if not np.isclose(q, -2 * native_loglikes[name], atol=1e-7, rtol=1e-10):
            raise ValueError(f'Native Gaussian response bridge failed: {name}')
    return responses


def fisher_gram(jacobian, covariance):
    jac = np.asarray(jacobian, dtype=float)
    if jac.ndim != 2 or not np.all(np.isfinite(jac)):
        raise ValueError('Finite matrix of response derivatives required.')
    solved = np.column_stack([covariance_solve(covariance, col) for col in jac.T])
    gram = jac.T @ solved
    return (gram + gram.T) * .5


def regularized_proposal(fisher, scales, relative_floor=1e-6):
    f, scales = np.asarray(fisher, dtype=float), np.asarray(scales, dtype=float)
    if scales.ndim != 1 or not scales.size or f.shape != (scales.size, scales.size) or not np.all(np.isfinite(f)) or not np.all(np.isfinite(scales)) or np.any(scales <= 0):
        raise ValueError('Finite square Fisher matrix and positive scales required.')
    tolerance = 64 * np.finfo(float).eps * float(np.max(np.abs(f)))
    if not np.allclose(f, f.T, rtol=0, atol=tolerance):
        raise ValueError('Fisher matrix must be symmetric.')
    eigenvalues, vectors = np.linalg.eigh((f + f.T) * .5)
    if eigenvalues[-1] <= 0 or not 0 < relative_floor < 1:
        raise ValueError('At least one positive response direction and valid regularization required.')
    if eigenvalues[0] < -tolerance * scales.size:
        raise ValueError('Response Fisher matrix must be positive semidefinite.')
    floor = max(relative_floor * eigenvalues[-1], 1e-8)
    regularized = np.maximum(eigenvalues, floor)
    inverse_scaled = (vectors / regularized) @ vectors.T
    proposal = inverse_scaled * np.outer(scales, scales)
    covariance_solve(proposal, np.ones(scales.size))
    return proposal, {'fisher_eigenvalues_scaled': eigenvalues.tolist(),
                      'regularized_eigenvalues_scaled': regularized.tolist(),
                      'eigenvalue_floor': float(floor),
                      'n_regularized_directions': int(np.count_nonzero(eigenvalues < floor))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--outdir', type=Path, required=True)
    parser.add_argument('--step', type=float, default=.5, help='Central-difference step in proposal units')
    parser.add_argument('--relative-floor', type=float, default=1e-6)
    args = parser.parse_args()
    if not 0 < args.step <= 1:
        parser.error('Require 0 < step <= 1')
    cfg = yaml.safe_load(args.config.read_text())
    configure_fresh_camb_transfers(cfg)
    keys = set(cfg['likelihood'])
    if not {SPT, BAO} <= keys or keys - {SPT, BAO, PLIK, LENSING} - LOW:
        parser.error('Only SPT + DESI, optionally the declared Planck completion, is supported')
    out = args.outdir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'input.yaml').write_text(args.config.read_text())
    (out / 'resolved.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    started = time.monotonic()
    with get_model(cfg, packages_path=str(Path('external/cobaya_packages').resolve()), stop_at_error=True) as model:
        names = list(model.parameterization.sampled_params())
        scales = np.array([cfg['params'][n]['proposal'] for n in names])
        bounds = np.asarray(model.prior.bounds())
        point = {n: float(cfg['params'][n]['ref']['loc']) if isinstance(cfg['params'][n]['ref'], dict)
                    else float(cfg['params'][n]['ref']) for n in names}
        # Curvature can be estimated in the interior even when the mode lies
        # at a boundary. Moving this anchor changes only the proposal heuristic.
        for j, n in enumerate(names):
            margin = 1.01 * args.step * scales[j]
            if bounds[j, 1] - bounds[j, 0] <= 2 * margin:
                raise ValueError('Difference step does not fit inside the parameter domain.')
            point[n] = float(np.clip(point[n], bounds[j, 0] + margin, bounds[j, 1] - margin))
        spt, bao = model.likelihood[SPT], model.likelihood[BAO]

        def scalar_params(p):
            pars = deepcopy(spt._base_params)
            inputs = model.parameterization.to_input(p)
            pars.update({n: inputs[n] for n in spt.input_params})
            return pars

        def response(p):
            likes = model.loglikes(p, as_dict=True, return_derived=False, cached=True)
            if not all(np.isfinite(float(v)) for v in likes.values()):
                raise ValueError('Nonfinite response evaluation.')
            inputs = model.parameterization.to_input(p)
            pars = spt.current_candl_params({n: inputs[n] for n in spt.input_params})
            bandpowers = np.asarray(spt._like_obj.bin_model_specs(spt._like_obj.get_model_specs(pars)))
            distances = compute_theory_vector(bao._dataset.points, float(model.provider.get_param('rdrag')),
                model.provider.get_angular_diameter_distance,
                lambda z: model.provider.get_Hubble(z, units='km/s/Mpc'))
            completion = gaussian_completion_residuals(model, inputs, likes) if PLIK in keys or LENSING in keys else {}
            return bandpowers, distances, pars, completion, likes

        center = response(point)
        _, cmb_cov = compute_gaussian_residual_and_covariance(spt._like_obj, center[2])
        jac_cmb, jac_bao = [], []
        extra_jac = {k: [] for k in center[3]}
        raw_low_curvature = {k: np.zeros(len(names)) for k in keys & LOW}
        for j, n in enumerate(names):
            plus, minus = dict(point), dict(point)
            plus[n] += args.step * scales[j]
            minus[n] -= args.step * scales[j]
            a, b = response(plus), response(minus)
            jac_cmb.append((a[0] - b[0]) / (2 * args.step))
            jac_bao.append((a[1] - b[1]) / (2 * args.step))
            for k in extra_jac:
                extra_jac[k].append((a[3][k][0] - b[3][k][0]) / (2 * args.step))
            for k in raw_low_curvature:
                raw_low_curvature[k][j] = -(a[4][k] + b[4][k] - 2 * center[4][k]) / args.step ** 2
            print(f'Response derivative {j + 1}/{len(names)}: {n}', flush=True)
        f_cmb = fisher_gram(np.column_stack(jac_cmb), cmb_cov)
        f_bao = fisher_gram(np.column_stack(jac_bao), bao._dataset.cov)
        extra_fisher = {k: fisher_gram(np.column_stack(j), center[3][k][1]) for k, j in extra_jac.items()}
        # This is a proposal approximation, not a replacement likelihood.
        # Positive diagonal low-l curvature supplements the Gaussian responses;
        # non-Gaussian cross curvature and negative diagonal curvature are omitted.
        low_diagonal = sum((np.maximum(v, 0) for v in raw_low_curvature.values()), np.zeros(len(names)))
        f_prior = np.zeros_like(f_cmb)
        for prior in spt._like_obj.priors:
            def prior_coordinates(p):
                pars = scalar_params(p)
                x = np.asarray([pars[n] for n in prior.par_names], dtype=float)
                if prior.multiplicative_par:
                    if np.any(x <= 0):
                        raise ValueError('Multiplicative prior coordinates must be positive.')
                    x = np.log(x)
                return x
            jac = []
            for j, n in enumerate(names):
                plus, minus = dict(point), dict(point)
                plus[n] += args.step * scales[j]
                minus[n] -= args.step * scales[j]
                jac.append((prior_coordinates(plus) - prior_coordinates(minus)) / (2 * args.step))
            f_prior += fisher_gram(np.column_stack(jac), prior.prior_covariance)
        fisher = f_cmb + f_bao + f_prior + sum(extra_fisher.values(), np.zeros_like(f_cmb)) + np.diag(low_diagonal)
        cov, regularization = regularized_proposal(fisher, scales, args.relative_floor)
        np.savetxt(out / 'proposal.covmat', cov, header=' '.join(names))
        np.savez_compressed(out / 'response_matrices.npz', fisher_cmb=f_cmb, fisher_bao=f_bao,
                           fisher_native_priors=f_prior, scales=scales,
                           jac_cmb=np.column_stack(jac_cmb), jac_bao=np.column_stack(jac_bao),
                           fisher_gaussian_completion=sum(extra_fisher.values(), np.zeros_like(f_cmb)),
                           fisher_positive_lowell_diagonal=np.diag(low_diagonal))
        write_json(out / 'metrics.json', {'scope': 'regularized_Gauss_Newton_MCMC_proposal_only',
                    'posterior_covariance_certified': False, 'parameter_names': names,
                    'anchor': point, 'step_in_proposal_units': args.step,
                    'source_config': str(args.config.resolve()),
                    'source_config_sha256': hashlib.sha256(args.config.read_bytes()).hexdigest(),
                    'native_gaussian_completion_bridges_verified': list(extra_fisher),
                    'lowell_diagonal_curvature_scaled': {k: v.tolist() for k, v in raw_low_curvature.items()},
                    'elapsed_seconds': time.monotonic() - started, **regularization})
    print(f'Proposal bundle: {out}')


if __name__ == '__main__':
    main()
