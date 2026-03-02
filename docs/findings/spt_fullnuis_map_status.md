# SPT Full-Nuisance MAP Status (R1)

- Date (UTC): `2026-02-11`

- Parameter inspection run:
  - `runs/20260211_163316_521109_candl_param_inspect`
  - defaults cover all required parameters for both lenses (`missing = []`).

- Full-nuisance MAP run bundles:
  - SPT2018: `runs/20260211_165648_324427_spt2018_map_fullnuis`
  - SPTD1: `runs/20260211_165655_916918_sptd1_map_fullnuis`

- Free-parameter counts:
  - SPT2018: `n_params_free = 35` (total `41`, fixed `6`)
  - SPTD1: `n_params_free = 43` (total `44`, fixed `1`)

- Objective improvement:
  - SPT2018: `chi2_init = 2672.3212858987968` → `chi2_best = 2672.3212858987968` (Δ=0)
  - SPTD1: `chi2_init = 1380.550904843325` → `chi2_best = 1380.550904843325` (Δ=0)

- Bound hits:
  - SPT2018: none
  - SPTD1: none

- Optimizer convergence:
  - SPT2018: `success=true`, message `CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL`
  - SPTD1: `success=true`, message `CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL`

- Determinism check:
  - Re-run SPT2018: `runs/20260211_165703_243471_spt2018_map_fullnuis`
  - `Δchi2_best = 0.0` vs first run (within `1e-6`).
