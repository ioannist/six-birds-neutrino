# Cosmology Stack Status (T04)

- Timestamp (UTC): `2026-02-11T10:52:33Z`
- Command run: `python scripts/check_cosmo_stack.py`
- Install mode: `--attempt_install` was **not** used in this ticket run.

## Availability matrix (captured output)

```text
timestamp_utc: 2026-02-11T10:52:33.714772+00:00

Availability Matrix (pre-install)
package    import_ok  version        notes
cobaya     False      NA             ModuleNotFoundError: No module named 'cobaya'
candl      False      NA             ModuleNotFoundError: No module named 'candl'
classy     False      NA             ModuleNotFoundError: No module named 'classy'
camb       False      NA             ModuleNotFoundError: No module named 'camb'
getdist    False      NA             ModuleNotFoundError: No module named 'getdist'

No CLASS/CAMB sanity compute run: neither classy nor camb importable.
candl probe skipped: candl not importable
```

## Summary: available vs missing

- Available from target stack: none (`cobaya`, `candl`, `classy`, `camb`, `getdist` all missing).
- Missing components block both:
  - direct SPT likelihood work through `candl`
  - Boltzmann-theory-backed checks through `classy`/`camb`
  - Cobaya-driven audit chains and posterior handling via `getdist`

## Key blockers and implications for T05/T06

- Blocker 1: no cosmology inference framework (`cobaya`) or posterior tooling (`getdist`) available.
  - Implication: cannot run real MCMC-driven likelihood audits yet.
- Blocker 2: no Boltzmann solver python bindings (`classy`, `camb`) available.
  - Implication: cannot do CLASS/CAMB-backed cosmology predictions in this environment yet.
- Blocker 3: no `candl` package available.
  - Implication: cannot run SPT likelihood objects directly.
- External data requirements for SPT/Planck likelihood assets:
  - Status: **unknown in this run** because `candl` is not importable, so no package-level data-path discovery was possible.
  - Likely next step: after stack install, run `python scripts/check_cosmo_stack.py --attempt_install` and then re-run asset discovery to identify exact data directories/download prerequisites.
