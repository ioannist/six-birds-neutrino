# Cosmo Stack Install Attempt (T05 Preflight)

- Timestamp (UTC): `2026-02-11`
- Commands run:
  - `python scripts/check_cosmo_stack.py --attempt_install`
  - `python scripts/check_cosmo_stack.py`

## Pre-install matrix (from `--attempt_install` run)

```text
Availability Matrix (pre-install)
package    import_ok  version        notes
cobaya     False      NA             ModuleNotFoundError: No module named 'cobaya'
candl      False      NA             ModuleNotFoundError: No module named 'candl'
classy     False      NA             ModuleNotFoundError: No module named 'classy'
camb       False      NA             ModuleNotFoundError: No module named 'camb'
getdist    False      NA             ModuleNotFoundError: No module named 'getdist'
```

## Install attempt summary

```text
Install attempts:
- numpy: already present, skipped
- scipy: already present, skipped
- cobaya: installed (Defaulting to user installation because normal site-packages is not writeable)
- getdist: installed (Defaulting to user installation because normal site-packages is not writeable)
- camb: installed (Defaulting to user installation because normal site-packages is not writeable)
- classy: installed (Defaulting to user installation because normal site-packages is not writeable)
- candl: installed (Defaulting to user installation because normal site-packages is not writeable)
```

## Post-install matrix (from `--attempt_install` run)

```text
Availability Matrix (post-install)
package    import_ok  version        notes
cobaya     True       3.6.1
candl      True       0.0.7
classy     True       3.3.4.0
camb       True       1.6.5
getdist    True       1.7.5
```

## Final matrix (fresh second run)

```text
Availability Matrix (pre-install)
package    import_ok  version        notes
cobaya     True       3.6.1
candl      True       0.0.7
classy     True       3.3.4.0
camb       True       1.6.5
getdist    True       1.7.5
```

## Pip error highlights

- No package install failed in this run, so there are no pip error excerpts to report.

## Immediate implication for T05

- Stack importability gate is satisfied.
- Proceeded to candl SPT likelihood discovery and smoke probing; results recorded in:
  - `docs/findings/candl_spt_probe.md`
  - `runs/20260211_112049_candl_spt_probe/`
