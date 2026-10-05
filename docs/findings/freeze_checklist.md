# Freeze Checklist

The bundles below are the historical frozen snapshot. The 2026-10-03
[mathematics review](math_review.md) repairs covariance accounting, profiling
domains, and chain diagnostics. Original localization and convergence diagnostics
are superseded; these chains do not verify stable posterior limits. Use the
review's fresh artifacts and verification receipts when continuing the work.

## Canonical run bundle IDs (frozen snapshot)

- Toy / mechanism:
  - `runs/20260211_103448_toy_trunc_gauss`

- Baseline and common-staging (unprofiled/localized):
  - `runs/20260211_153956_456493_cross_audit_spt2018_map_vs_sptd1_map_full`
  - `runs/20260211_154004_970944_cross_audit_spt2018_map_vs_sptd1_map_common_staging`
  - `runs/20260211_154016_522463_spt_common_staging_compare`

- Profiled completion + common-staging comparison:
  - `runs/20260211_180902_502030_cross_audit_profiled_spt2018_vs_sptd1_full_shared_tsz_ksz`
  - `runs/20260211_181123_395086_cross_audit_profiled_spt2018_vs_sptd1_common_staging_shared_tsz_ksz`
  - `runs/20260211_181258_958327_spt_profiled_common_staging_compare`

- Template rewrite (optional supporting artifact):
  - `runs/20260211_130040_037128_template_rewrite_toy_lensA_vs_toy_lensB`

- candl/SPT discovery:
  - `runs/20260211_145616_816546_candl_spt_discovery`

- SPT-only smoke (N1 reference runs):
  - `runs/20260211_205158_771012_cobaya_spt2018_lcdm_mnu`
  - `runs/20260211_210608_852426_cobaya_sptd1_lcdm_mnu`

- SPT-only + DESI (N3):
  - `runs/20260212_060311_662922_cobaya_spt2018_desi_lcdm_mnu`
  - `runs/20260212_072014_910159_cobaya_sptd1_desi_lcdm_mnu`
  - `runs/20260212_080120_648405_mnu_shift_spt_only_desi`

- CMB baseline + DESI (N5 headline):
  - `runs/20260212_093719_342126_eval_cmb_plancksubset_desi`
  - `runs/20260212_093731_416464_cobaya_cmb_spt2018_plancksubset_desi_mnu`
  - `runs/20260212_100807_462875_cobaya_cmb_sptd1_plancksubset_desi_mnu`
  - `runs/20260212_111357_576743_mnu_shift_cmb_plancksubset_desi`
  - `runs/20260212_105410_338944_cobaya_cmb_spt2018_plancksubset_desi_mnu_seed1_short`

## Regeneration commands

- Freeze sanity one-command harness:
  - `make freeze_check`

- Toy mechanism:
  - `python scripts/toy_truncated_gaussian.py`

- Toy audit pipeline:
  - `make audit`

- Profiled baseline (shared macro params):
  - `python scripts/run_cross_audit_profiled.py --runA runs/20260211_150211_501395_spt2018_map --runB runs/20260211_150212_741064_sptd1_map --shared_params TT_tSZ_Amp,TT_kSZ_Amp --profile_set TT_cal_beta --maxiter 300`

- Profiled common-staging (shared macro params):
  - `python scripts/run_cross_audit_profiled.py --runA runs/20260211_150211_501395_spt2018_map --runB runs/20260211_153950_855685_sptd1_map_common_staging --shared_params TT_tSZ_Amp,TT_kSZ_Amp --profile_set TT_cal_beta --maxiter 300`

- Profiled baseline vs staging compare:
  - `python scripts/compare_cross_audits.py --baseline <baseline_profiled_bundle> --staging <staging_profiled_bundle>`

- Neutrino smoke (SPT-only):
  - `make mnu_smoke`

- Neutrino full baseline+DESI:
  - `make mnu_full`
  - `make mnu_full MNU_FULL_FAST=1`
  - `make mnu_full PLANCK_ASSETS_DIR=/path/to/cobaya_packages`
  - Planck assets expected under `external/cobaya_packages` unless `PLANCK_ASSETS_DIR` is overridden.

## Determinism note

- Run bundles are timestamped; regenerated directory names will differ.
- Canonical IDs above correspond to the frozen snapshot date and are the citation anchors for current internal notes.
