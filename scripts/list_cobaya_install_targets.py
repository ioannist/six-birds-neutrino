#!/usr/bin/env python3
from __future__ import annotations

import importlib
import pkgutil


def main() -> int:
    import cobaya.likelihoods as likelihoods

    targets: set[str] = set()

    # Built-in likelihood module targets.
    for mod in pkgutil.walk_packages(likelihoods.__path__, likelihoods.__name__ + "."):
        name = mod.name
        low = name.lower()
        if "planck" in low or "clik" in low:
            short = name.replace("cobaya.likelihoods.", "")
            targets.add(short)

    # Additional known external Planck candidate package targets.
    targets.update(
        {
            "planckpr4lensing",
            "planckpr4lensing.PlanckPR4Lensing",
            "planckpr4lensing.PlanckPR4LensingMarged",
        }
    )

    # Detect if external package is importable.
    try:
        pr4 = importlib.import_module("planckpr4lensing")
        print(f"planckpr4lensing_importable=True version={getattr(pr4, '__version__', 'unknown')}")
    except Exception as exc:  # noqa: BLE001
        print(f"planckpr4lensing_importable=False error={type(exc).__name__}: {exc}")

    print("install_targets_planck_clik:")
    for target in sorted(targets):
        print(f"- {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
