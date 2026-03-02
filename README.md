# A Six Birds' Eye View of Neutrino Mass

This repository contains the **neutrino mass inference audit** for the paper:

> **A Six Birds' Eye View of Neutrino Mass: Lens-Swap Stability and Packaging Audits**
>
> Archived at: TBD
>
> DOI: TBD

This paper applies Six Birds Theory (SBT) to diagnose a published anomaly: swapping the SPT-3G 2018 TT/TE/EE likelihood for the SPT-3G D1 (2019--2020) release materially shifts the inferred neutrino mass upper bound, sometimes pushing posteriors toward the physical boundary. The repository operationalizes this as a packaging stability problem using directional cross-lens audits, blockwise mismatch localization, common-staging controls, and a formal boundary-mode mechanism. This is the cosmological-neutrino companion to *Six Birds: Foundations of Emergence Calculus*.

## What this repository provides

The neutrino mass audit implements:

- **Replication of the m_nu shift**: quantified tightening when swapping SPT2018 to D1 under DESI DR2 BAO, with full Cobaya MCMC chains
- **Cross-lens audits**: directional Delta-chi2 held-out mismatch statistics measuring how well lens A predicts lens B, with blockwise decomposition by spectrum and multipole
- **Common-staging controls**: matching multipole support and resolution to isolate intrinsic mismatch from cut artifacts
- **Boundary-mode analysis**: toy truncated Gaussian mechanism showing how boundary modes arise from tension under physical gates (m_nu >= 0)
- **Lean formal proof**: mechanized antitone property of truncated Gaussian density on [0, infinity) when mean <= 0 (Lean 4 + Mathlib)
- **Cobaya pipeline**: reproducible inference configurations for SPT-only, Planck subset, and CMB+DESI combinations
- **DESI DR2 BAO likelihood**: vendored Gaussian BAO data from CobayaSampler/bao_data v2.6, with per-subset likelihoods (ALL, LRG, ELG, QSO, BGS, Lya)
- **Paper-ready artifacts**: timestamped run bundles with chains, summaries, comparison plots, and rendered table fragments

## Scope and limitations

The paper is explicit about what it does and does not establish:

- The m_nu shift replication uses a minimal nuisance subset; full nuisance matching may differ
- Cross-lens audits are directional diagnostics, not causal attributions of the shift
- The boundary-mode mechanism is a toy illustration of truncation under tension, not a claim about the true underlying cosmology
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
