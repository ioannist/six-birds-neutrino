# candl SPT Probe (T05)

- Timestamp (UTC): `2026-02-11`
- Discovery script: `python scripts/list_candl_likelihoods.py`
- Smoke script: `python scripts/smoke_eval_spt.py`
- Run bundle: `runs/20260211_112049_candl_spt_probe`

## Discovery result

- `candl` is importable, version `0.0.7`.
- Module walk (`pkgutil.walk_packages`) found **no** SPT-related modules.
- Source scan found **no** SPT-related strings (`SPT`, `spt3g`, `D1`, `2018`, `2019`, `2020`, `MUSE`).
- Best-guess IDs:
  - SPT2018: `not found`
  - SPT D1: `not found`

## Instantiation / smoke-eval result

- Stack availability in run:
  - `candl_importable=true`
  - `camb_importable=true`
  - `classy_importable=true`
  - `cobaya_importable=true`
- Likelihood evaluation:
  - SPT2018: skipped (no ID guess available)
  - SPT D1: skipped (no ID guess available)
- No finite `loglike(theta_ref)` values produced.

## Exact diagnostic message

- `"No SPT likelihood identifiers found inside candl installation."`

## Best-guess resolution

- The installed `candl` package appears to be a different package than the expected cosmology/SPT likelihood package (only `candl.nn` and `candl.tensor` modules present).
- Likely fixes:
  - install the correct candl source/distribution that includes SPT likelihood components, potentially from a specific Git repo/tag rather than PyPI default,
  - and/or obtain the expected SPT likelihood data bundle path/env configuration once the correct package is installed.
