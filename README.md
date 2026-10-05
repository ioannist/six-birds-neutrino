# A Six Birds' Eye View of Neutrino Mass

This repository contains the **neutrino mass inference audit** for the paper:

> **Six Birds for Neutrino Mass: Lens-Swap Stability and Packaging Audits**
>
> Version 2 (5 October 2026), Zenodo: https://doi.org/10.5281/zenodo.23161613
>
> Version 1 (2 March 2026), Research Square: https://doi.org/10.21203/rs.3.rs-9009357/v1

This paper applies Six Birds Theory (SBT) to diagnose a published anomaly: swapping the SPT-3G 2018 TT/TE/EE likelihood for the SPT-3G D1 (2019--2020) release has been reported (arXiv:2601.16277) to tighten the inferred neutrino mass upper bound and push the posterior toward the physical boundary. The repository treats this as a packaging stability problem using directional cross-lens audits, exact full-covariance localization, support-cut and other controls, and a formally verified boundary-mode analysis. This is the cosmological-neutrino companion to *Six Birds: Foundations of Emergence Calculus*.

## What this repository provides

The neutrino mass audit implements:

- **m_nu sampling and diagnostics**: Cobaya MCMC configurations, archived chains and a multi-chain campaign with pre-declared convergence gates; none qualified, so no tightening magnitude or direction is claimed (see the paper and `docs/findings/math_review.md`)
- **Cross-lens audits**: directional Delta-chi2 statistics measuring how well lens A's fit predicts lens B, with exact signed full-covariance localization of the SPT quadratic part by spectrum and multipole
- **Support-cut control**: removes D1's extra multipole coverage (binning, window functions and resolution are not matched, and D1 lacks the 2018 TE/EE modes at 300 <= ell < 400), plus optical-depth-prior and Boltzmann-precision controls
- **Boundary-mode analysis**: two-constraint Gaussian model under the gate m_nu >= 0; a boundary mode needs a nonpositive combined mean, which tension between constraints that both prefer positive masses cannot produce
- **Lean formal proofs**: 97 audited declarations (Lean 4 + Mathlib) covering the gated mode, normalization, CDF and quantiles, boundary probability under tightening, finite upper gate, readout error bounds and covariance accounting
- **Cobaya pipeline**: reproducible inference configurations for SPT-only, Planck subset, and CMB+DESI combinations
- **DESI DR2 BAO likelihood**: vendored Gaussian BAO data from CobayaSampler/bao_data v2.6, with per-subset likelihoods (ALL, LRG, ELG, QSO, BGS, Lya)
- **Paper-ready artifacts**: timestamped run bundles with chains, summaries, comparison plots, and rendered table fragments

## Scope and limitations

The paper is explicit about what it does and does not establish:

- No converged m_nu posterior on a qualified numerical target is available; the Version 1 tightening magnitudes are withdrawn as unsupported
- Audit values are numerical candidates, not certified global optima or calibrated significances; localization depends on baseline and direction
- Cross-lens audits are directional diagnostics, not causal attributions of the shift
- The boundary-mode analysis assumes Gaussian, independent constraints and a constant prior on the gate; it is not a claim about the true underlying cosmology
- LSS audits are not included; the focus is on CMB likelihood-release stability

## Install

```bash
pip install -e ".[dev]"
```

## Test

```bash
python -m pytest
```

## Run experiments

```bash
make toy           # Truncated Gaussian boundary-mode demo
make audit         # Toy MAP + cross-audit pipeline
make mnu_smoke     # Quick m_nu chains (SPT-only)
make mnu_full      # Full CMB+DESI chains (requires Planck assets)
```

## Build paper

```bash
make paper
```

## External data dependencies

- **SPT-3G likelihoods**: CANDL (installed via cobaya_packages)
- **Planck products**: PR3 low-ell TT/EE, PR3 high-ell TT (Plik-lite), PR4 lensing
- **DESI DR2 BAO**: vendored in `data/desi_dr2_bao/`
- **Boltzmann solvers**: CLASS or CAMB (via Cobaya)
