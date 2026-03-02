# SPT Profiled Cross-Audit (R2)

- Date (UTC): `2026-02-11`
- Run bundle: `runs/20260211_173957_845376_cross_audit_profiled_spt2018_vs_sptd1`

- `Δχ²_unprofiled_B|A = 2223.2841745765645`
- `Δχ²_profiled_B|A = -0.0`
- `Δχ²_unprofiled_A|B = 580.869044229586`
- `Δχ²_profiled_A|B = -0.0`

- Reduction:
  - `B|A = 100.0%`
  - `A|B = 100.0%`

- Profile set:
  - requested: `TT_cal_beta`
  - used: `TT_cal_beta`
  - profiled nuisance count:
    - `B|A: 12`
    - `A|B: 12`

- Top 5 profiled localization groups (`B|A`):
  - `TT`, `[400, 750]`, `ΔQ = 0.0`
  - `TT`, `[750, 1000]`, `ΔQ = 0.0`
  - `TT`, `[1000, 1500]`, `ΔQ = 0.0`
  - `TT`, `[1500, 2000]`, `ΔQ = 0.0`
  - `TT`, `[2000, 2500]`, `ΔQ = 0.0`

- Caveat:
  - With the specific R2 input runs, shared cosmo-like intersection reduced to `["tau"]`, and both directions used test-lens defaults for that key (no tau in source `theta_hat` maps), so profiled-at-train-shared and profiled-best were identical.
