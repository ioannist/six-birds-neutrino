# candl SPT Discovery + Smoke (F2)

- Date (UTC): `2026-02-11`
- Run bundle: `runs/20260211_145616_816546_candl_spt_discovery`

## Discovered shortcut IDs

- SPT2018 TT/TE/EE (multifreq): `candl_data.SPT3G_2018_TTTEEE_multifreq`
- SPT D1 TnE (multifreq): `spt_candl_data.SPT3G_D1_TnE_multifreq`

## Smoke-eval outcome

- `candl`, `candl_data`, `spt_candl_data`, `camb`, `classy`, and `cobaya` all import successfully.
- SPT2018 instantiation/eval succeeded with finite values:
  - `chi2 = 1528.8739637258693`
  - `loglike = -1336.1606429493984`
- SPT D1 instantiation/eval succeeded with finite values:
  - `chi2 = 1373.2802544894303`
  - `loglike = -690.2754524216625`

## Artifacts

- Discovery output (all shortcuts): `runs/20260211_145616_816546_candl_spt_discovery/list_stdout.txt`
- Smoke run console: `runs/20260211_145616_816546_candl_spt_discovery/stdout.txt`
- Machine-readable metrics: `runs/20260211_145616_816546_candl_spt_discovery/metrics.json`
