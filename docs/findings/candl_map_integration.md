# candl MAP Integration (F3)

- Date (UTC): `2026-02-11`
- Configs used:
  - `configs/spt2018_map.yaml`
  - `configs/sptd1_map.yaml`

## Produced MAP run bundles

- `runs/20260211_150211_501395_spt2018_map`
- `runs/20260211_150212_741064_sptd1_map`

## Finite best-fit results

- SPT2018:
  - `theta_hat.TT_tSZ_Amp = 2.6248863660540183`
  - `theta_hat.TT_kSZ_Amp = 10.0`
  - `chi2_best = 2553.9422834060497` (`objective = -2loglike`)
- SPT D1:
  - `theta_hat.TT_tSZ_Amp = 1.2826783466224576`
  - `theta_hat.TT_kSZ_Amp = 1.900633917618081`
  - `chi2_best = 1379.1195021133121` (`objective = -2loglike`)

## Cross-audit smoke on candl MAP outputs

- `python scripts/run_cross_audit.py --runA runs/20260211_150211_501395_spt2018_map --runB runs/20260211_150212_741064_sptd1_map`
- Run bundle: `runs/20260211_150225_677104_cross_audit_spt2018_map_vs_sptd1_map`
- Directional metrics:
  - `Δχ²_{B|A} = 2222.172359975601`
  - `Δχ²_{A|B} = 313.5678894802195`
