- Ticket: N5 (CMB baseline + DESI DR2 BAO production-chain attempt)
- Comparison bundle: `runs/20260212_111357_576743_mnu_shift_cmb_plancksubset_desi`
- Production run (SPT2018 baseline): `runs/20260212_093731_416464_cobaya_cmb_spt2018_plancksubset_desi_mnu`
- Production run (SPT D1 baseline): `runs/20260212_100807_462875_cobaya_cmb_sptd1_plancksubset_desi_mnu`

- 2018 baseline + DESI: `mnu_median=0.06777`, `mnu_p95_upper=0.07981`, `mnu_mode=0.07470`, `boundary_fraction=0.0`
- D1 baseline + DESI: `mnu_median=0.05434`, `mnu_p95_upper=0.06765`, `mnu_mode=0.05443`, `boundary_fraction=0.0`
- Shift: `delta_p95_upper = p95_2018 - p95_D1 = 0.01216 eV` (D1 is tighter)

- Stability diagnostics (main chains):
- 2018: `n_samples_used=480`, `split_rhat=0.9981`, `p95_half_diff=0.00414 eV`, `ESS~10.41`
- D1: `n_samples_used=480`, `split_rhat=0.9994`, `p95_half_diff=0.00000 eV`, `ESS~9.10`

- Mild longer-chain check used Option B (second seed short rerun):
- Seed-1 rerun: `runs/20260212_105410_338944_cobaya_cmb_spt2018_plancksubset_desi_mnu_seed1_short`
- `|p95_main - p95_seed1| = 0.00945 eV` (passes <= 0.02 eV criterion)

- Comparison to anchored 2601.16277 table values (`tab:3`, `tab:3a`):
- Anchored `+DESI` p95 values are `0.110 eV` (2018) and `0.069 eV` (D1).
- Our D1 value (`0.06765`) is close to anchor, while our 2018 value (`0.07981`) is tighter than anchor.
- Net effect: directionality matches (D1 tighter), but our shift magnitude is smaller than anchored table shift.

- Plausible causes of deviation:
- We sample only a minimal nuisance subset (`A_planck`, `TT_tSZ_Amp`, `TT_kSZ_Amp`) rather than the full nuisance set used in the paper pipeline.
- Likelihood/data version differences can shift the 2018 posterior width more strongly than D1.
- Planck low-ell EE implementation choice (`EE_sroll2`) may induce small shifts.
- `mnu` upper prior in paper is unspecified; we use `[0,5] eV` by replication choice (likely subdominant here, but documented).
