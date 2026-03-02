#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import importlib
import importlib.metadata as md
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


@dataclass
class PackageStatus:
    package: str
    import_name: str
    import_ok: bool
    version: str
    notes: str
    module: Any | None = None


PACKAGE_SPECS: list[tuple[str, str]] = [
    ("cobaya", "cobaya"),
    ("candl", "candl"),
    ("classy", "classy"),
    ("camb", "camb"),
    ("getdist", "getdist"),
]


def short_error(exc: Exception, max_len: int = 120) -> str:
    txt = f"{type(exc).__name__}: {exc}"
    if len(txt) > max_len:
        return txt[: max_len - 3] + "..."
    return txt


def detect_version(dist_name: str, module: Any | None) -> str:
    try:
        return md.version(dist_name)
    except Exception:
        pass
    if module is not None:
        for attr in ("__version__", "VERSION", "version"):
            value = getattr(module, attr, None)
            if isinstance(value, str) and value.strip():
                return value
    return "unknown"


def check_one(package: str, import_name: str) -> PackageStatus:
    try:
        module = importlib.import_module(import_name)
    except Exception as exc:  # noqa: BLE001
        return PackageStatus(
            package=package,
            import_name=import_name,
            import_ok=False,
            version="NA",
            notes=short_error(exc),
            module=None,
        )
    return PackageStatus(
        package=package,
        import_name=import_name,
        import_ok=True,
        version=detect_version(package, module),
        notes="",
        module=module,
    )


def check_stack() -> list[PackageStatus]:
    return [check_one(package, import_name) for package, import_name in PACKAGE_SPECS]


def print_matrix(title: str, statuses: list[PackageStatus]) -> None:
    print(title)
    print(f"{'package':10} {'import_ok':10} {'version':14} notes")
    for st in statuses:
        print(f"{st.package:10} {str(st.import_ok):10} {st.version:14} {st.notes}")
    print()


def pip_install(package: str) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pip", "install", package]
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    text = (res.stderr or res.stdout or "").strip().splitlines()
    first_line = text[0] if text else ""
    if len(first_line) > 160:
        first_line = first_line[:157] + "..."
    return (res.returncode == 0), first_line


def maybe_attempt_install(statuses: list[PackageStatus]) -> list[str]:
    notes: list[str] = []
    missing = {st.package for st in statuses if not st.import_ok}

    # Step 1: numpy/scipy preflight installs (only if missing)
    for base_pkg in ("numpy", "scipy"):
        ok = check_one(base_pkg, base_pkg).import_ok
        if ok:
            notes.append(f"{base_pkg}: already present, skipped")
        else:
            success, msg = pip_install(base_pkg)
            outcome = "installed" if success else "failed"
            notes.append(f"{base_pkg}: {outcome} ({msg})")

    install_order = ["cobaya", "getdist", "camb", "classy", "candl"]
    for pkg in install_order:
        if pkg not in missing:
            notes.append(f"{pkg}: already present, skipped")
            continue
        success, msg = pip_install(pkg)
        outcome = "installed" if success else "failed"
        notes.append(f"{pkg}: {outcome} ({msg})")
    return notes


def run_classy_sanity() -> str:
    try:
        from classy import Class
    except Exception as exc:  # noqa: BLE001
        return f"classy sanity skipped: {short_error(exc)}"

    cosmo = Class()
    try:
        cosmo.set(
            {
                "output": "tCl",
                "h": 0.67,
                "omega_b": 0.0224,
                "omega_cdm": 0.12,
                "A_s": 2.1e-9,
                "n_s": 0.965,
                "tau_reio": 0.054,
            }
        )
        cosmo.compute()
        omega_m = cosmo.Omega_m()
        h = cosmo.h()
        return f"classy sanity: ok (Omega_m={omega_m:.6f}, h={h:.6f})"
    except Exception as exc:  # noqa: BLE001
        return f"classy sanity: failed ({short_error(exc)})"
    finally:
        try:
            cosmo.struct_cleanup()
            cosmo.empty()
        except Exception:
            pass


def run_camb_sanity() -> str:
    try:
        import camb
    except Exception as exc:  # noqa: BLE001
        return f"camb sanity skipped: {short_error(exc)}"

    try:
        pars = camb.CAMBparams()
        pars.set_cosmology(H0=67.0, ombh2=0.0224, omch2=0.12, mnu=0.06, tau=0.054)
        pars.InitPower.set_params(As=2.1e-9, ns=0.965)
        results = camb.get_results(pars)
        derived = results.get_derived_params()
        omegam = derived.get("omegam", "unknown")
        return f"camb sanity: ok (H0={pars.H0}, omegam={omegam})"
    except Exception as exc:  # noqa: BLE001
        return f"camb sanity: failed ({short_error(exc)})"


def candl_asset_probe(module: Any | None) -> str:
    if module is None:
        return "candl probe skipped: candl not importable"

    details: list[str] = []
    env_vars = ["CANDL_DATA", "CANDL_DATA_DIR", "CANDL_PATH", "COBAYA_PACKAGES_PATH"]
    found_env = []
    for key in env_vars:
        raw = os.environ.get(key, "")
        if raw:
            value: Path = Path(raw).expanduser()
            found_env.append((key, str(value), value.exists()))
    if found_env:
        for key, p, exists in found_env:
            details.append(f"{key}={p} (exists={exists})")
    else:
        details.append("no candl-related env vars set")

    try:
        pkg_dir = Path(module.__file__).resolve().parent
        spt_like = []
        for pattern in ("*spt*", "*SPT*"):
            spt_like.extend(pkg_dir.rglob(pattern))
        spt_like = [p for p in spt_like if p.is_file() or p.is_dir()]
        if spt_like:
            preview = ", ".join(str(p.relative_to(pkg_dir)) for p in spt_like[:5])
            details.append(f"candl package has SPT-like paths ({len(spt_like)} found): {preview}")
        else:
            details.append(
                "candl installed but no obvious local SPT likelihood assets detected in package path; "
                "external data requirements likely but exact bundle unknown"
            )
    except Exception as exc:  # noqa: BLE001
        details.append(f"candl package scan failed: {short_error(exc)}")

    return " | ".join(details)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check cosmology stack availability.")
    parser.add_argument(
        "--attempt_install",
        action="store_true",
        help="Attempt pip install for missing packages.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print(f"timestamp_utc: {datetime.now(timezone.utc).isoformat()}")
    print()

    statuses = check_stack()
    print_matrix("Availability Matrix (pre-install)", statuses)

    if args.attempt_install:
        print("Install attempts:")
        for line in maybe_attempt_install(statuses):
            print(f"- {line}")
        print()
        statuses = check_stack()
        print_matrix("Availability Matrix (post-install)", statuses)

    st_by_pkg = {st.package: st for st in statuses}

    if st_by_pkg.get("classy") and st_by_pkg["classy"].import_ok:
        print(run_classy_sanity())
    elif st_by_pkg.get("camb") and st_by_pkg["camb"].import_ok:
        print(run_camb_sanity())
    else:
        print("No CLASS/CAMB sanity compute run: neither classy nor camb importable.")

    print(candl_asset_probe(st_by_pkg.get("candl").module if st_by_pkg.get("candl") else None))

    # Diagnostic tool: always exit 0 by design.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
