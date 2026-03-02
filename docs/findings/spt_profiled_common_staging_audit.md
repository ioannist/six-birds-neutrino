# SPT Profiled Common-Staging Audit (R3)

- Date (UTC): `2026-02-11`

- Baseline profiled run:
  - `runs/20260211_180902_502030_cross_audit_profiled_spt2018_vs_sptd1_full_shared_tsz_ksz`
- Common-staging profiled run:
  - `runs/20260211_181123_395086_cross_audit_profiled_spt2018_vs_sptd1_common_staging_shared_tsz_ksz`
- Profiled comparison run:
  - `runs/20260211_181258_958327_spt_profiled_common_staging_compare`

- `Δχ²_profiled` baseline vs staging:
  - `B|A: 859.6408443567618 -> 840.1861841752798` (reduction `2.2631149170255234%`)
  - `A|B: 369.5190096373908 -> 370.4559889438033` (reduction `-0.25356728124269606%`)

- Baseline `B|A` top 5 localization groups (`spec`, `ell`, `ΔQ`):
  - `TT`, `[2500, 3000]`, `504.57669600274073`
  - `TT`, `[2000, 2500]`, `142.13273330225636`
  - `TT`, `[1500, 2000]`, `98.16228535120045`
  - `TT`, `[1000, 1500]`, `65.6304542223719`
  - `TT`, `[750, 1000]`, `34.17236600056873`

- Localization staging-change verdict:
  - no qualitative shift; both baseline and common-staging remain dominated by high-ell TT groups.
