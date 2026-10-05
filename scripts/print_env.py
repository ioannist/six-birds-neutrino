#!/usr/bin/env python3
import importlib.metadata as md
import platform
import sys
import os


def package_version(dist_name: str) -> str:
    try:
        return md.version(dist_name)
    except md.PackageNotFoundError:
        return "not installed"


def main() -> None:
    print(f"python: {sys.version}")
    print(f"platform: {platform.platform()}")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        print(f"{name}: {os.environ.get(name, 'unset')}")

    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("matplotlib", "matplotlib"),
        ("pandas", "pandas"),
        ("yaml", "PyYAML"),
        ("pytest", "pytest"),
        ("cobaya", "cobaya"),
        ("candl-like", "candl-like"),
        ("candl-data", "candl-data"),
        ("spt-candl-data", "spt-candl-data"),
        ("camb", "camb"),
        ("classy", "classy"),
        ("pybobyqa", "Py-BOBYQA"),
        ("arviz", "arviz"),
        ("arviz-stats", "arviz-stats"),
    ]

    for label, dist_name in packages:
        print(f"{label}: {package_version(dist_name)}")


if __name__ == "__main__":
    main()
