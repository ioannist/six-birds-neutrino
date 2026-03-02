- Scope: N4 Planck-subset baseline installation + sanity status for neutrino baselines.
- Asset root: `external/cobaya_packages` (kept out of snapshot payloads).

- Install/listing bundles:
- `runs/20260212_090307_577773_planck_install`
- `runs/20260212_090307_579916_planck_like_list`

- Sanity bundles:
- `runs/20260212_090336_697069_planck_subset_sanity_cmb_baseline_spt2018_plancksubset_mnu`
- `runs/20260212_090337_966579_planck_subset_sanity_cmb_baseline_sptd1_plancksubset_mnu`

- Planck subset used in baseline configs:
- `planck_2018_lowl.TT` with effective range `l=2..29`.
- `planck_2018_lowl.EE_sroll2` with effective range `l=2..29`.
- `planck_2018_highl_plik.TT_lite_native` with native TT-only cut via `dataset_params.bins_for_L_range: [30, 756]`.
- `planckpr4lensing.PlanckPR4Lensing` loaded from `python_path: external/cobaya_packages/code/planck_PR4_lensing` with `lmax=2500`.

- Explicit exclusions:
- No Planck high-ell TE/EE likelihood components are included in these baseline configs.

- Sanity finite totals (reference points):
- SPT2018 baseline config total loglike: `-1559.195202608062`.
- SPTD1 baseline config total loglike: `-937.4853924494219`.

- Operational note:
- The TT upper-cut path is native (`bins_for_L_range`) rather than a custom wrapper.
