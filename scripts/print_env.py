#!/usr/bin/env python3
import importlib.metadata as md
import platform
import sys


def package_version(dist_name: str) -> str:
    try:
        return md.version(dist_name)
    except md.PackageNotFoundError:
        return "not installed"


def main() -> None:
    print(f"python: {sys.version}")
    print(f"platform: {platform.platform()}")

    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("matplotlib", "matplotlib"),
        ("pandas", "pandas"),
        ("yaml", "PyYAML"),
        ("pytest", "pytest"),
    ]

    for label, dist_name in packages:
        print(f"{label}: {package_version(dist_name)}")


if __name__ == "__main__":
    main()
