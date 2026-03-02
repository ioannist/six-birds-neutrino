# Toy Truncated Gaussian: Boundary-Mode Lab Notes

Run bundle reference: `runs/20260211_103448_toy_trunc_gauss`

## Model setup

- Gaussian product combination:
  - `sigma_star^2 = (sigma1^-2 + sigma2^-2)^-1`
  - `mu_star = sigma_star^2 * (mu1*sigma1^-2 + mu2*sigma2^-2)`
- Physical truncation (`m >= 0`):
  - `p_trunc(m) = 0` for `m < 0`
  - `p_trunc(m) = N(m | mu_star, sigma_star^2) / Z` for `m >= 0`
  - `Z = 1 - Phi((0 - mu_star)/sigma_star)`
- Truncated mode rule: `mode = max(0, mu_star)`.
- Sweep mismatch model:
  - `mu2 = mu1 + epsilon`
  - `epsilon ~ N(-d, s^2)`
  - Defaults used: `mu1=0.05`, `sigma1=0.02`, `d=0.07`, `s=0.03`, `n_mc=20000`, `seed=0`.

## Quantitative outcomes

- Example case inputs: `mu2 = -0.02`, `sigma2 = 0.01`.
- Example combined posterior: `mu_star = -0.0060`, `sigma_star = 0.008944`.
- Example truncated mode: `mode = 0.0` (boundary mode).
- Sweep boundary fraction min: `0.0000` at `sigma2 = 0.035839`.
- Sweep boundary fraction max: `0.74275` at `sigma2 = 0.002235`.
- Net increase across sweep: `+0.74275` (well above the 0.20 criterion).
- Approximate 50% boundary crossing: `sigma2 ~= 0.01268` (linear interpolation between adjacent grid points).
- Boundary fraction trend is strongly increasing as `sigma2` tightens (decreases), consistent with the truncation+tension mechanism.

## Artifacts

- `runs/20260211_103448_toy_trunc_gauss/figures/figure_a_density_comparison.png`
- `runs/20260211_103448_toy_trunc_gauss/figures/figure_b_boundary_frequency_sweep.png`
