#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.metadata as md
import pkgutil
from typing import Any


KEYWORDS = ("spt", "spt3g", "d1", "2018", "2019", "2020", "tne", "ttteee")


def import_optional(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def module_version(name: str, mod: Any | None) -> str:
    try:
        return md.version(name)
    except Exception:
        pass
    if mod is not None:
        v = getattr(mod, "__version__", None)
        if isinstance(v, str) and v:
            return v
    return "unknown"


def module_walk_hits(mod: Any) -> list[str]:
    hits: list[str] = []
    mod_name = mod.__name__
    if not hasattr(mod, "__path__"):
        return hits
    for pkg in pkgutil.walk_packages(mod.__path__, mod_name + "."):
        low = pkg.name.lower()
        if any(k in low for k in KEYWORDS):
            hits.append(pkg.name)
    return sorted(set(hits))


def flatten_shortcuts(lib_name: str, shortcuts: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for group, payload in shortcuts.items():
        if isinstance(payload, dict):
            for variant, target in payload.items():
                rows.append(
                    {
                        "library": lib_name,
                        "group": group,
                        "variant": variant,
                        "id": target,
                        "expr": f"{lib_name}.{target}",
                    }
                )
        elif isinstance(payload, str):
            rows.append(
                {
                    "library": lib_name,
                    "group": group,
                    "variant": "index",
                    "id": payload,
                    "expr": f"{lib_name}.{payload}",
                }
            )
    return rows


def pick_best(rows: list[dict[str, str]]) -> tuple[str | None, str | None]:
    spt2018 = None
    sptd1 = None
    for row in rows:
        group = row["group"]
        variant = row["variant"]
        expr = row["expr"]
        if group == "SPT-3G 2018 TT/TE/EE" and variant == "multifreq":
            spt2018 = expr
            break
    if spt2018 is None:
        for row in rows:
            if row["group"] == "SPT-3G 2018 TT/TE/EE":
                spt2018 = row["expr"]
                break
    for row in rows:
        group = row["group"]
        variant = row["variant"]
        expr = row["expr"]
        if group == "SPT-3G D1 TnE" and variant == "multifreq":
            sptd1 = expr
            break
    if sptd1 is None:
        for row in rows:
            if row["group"] == "SPT-3G D1 TnE":
                sptd1 = row["expr"]
                break
    return spt2018, sptd1


def print_shortcuts(lib_name: str, mod: Any) -> list[dict[str, str]]:
    print(f"{lib_name} version={module_version(lib_name, mod)} path={getattr(mod, '__file__', 'unknown')}")
    if hasattr(mod, "print_all_shortcuts"):
        print(f"\n{lib_name}.print_all_shortcuts():")
        mod.print_all_shortcuts()
    rows: list[dict[str, str]] = []
    shortcuts = getattr(mod, "shortcuts", None)
    if isinstance(shortcuts, dict):
        rows = flatten_shortcuts(lib_name, shortcuts)
    print()
    return rows


def main() -> int:
    candl, candl_err = import_optional("candl")
    candl_data, candl_data_err = import_optional("candl_data")
    spt_data, spt_data_err = import_optional("spt_candl_data")

    if candl is None:
        print(f"candl import failed: {candl_err}")
        return 0

    print(f"candl version={module_version('candl', candl)} path={candl.__file__}")
    print()

    print("Module walk keyword hits")
    for mod in [candl, candl_data, spt_data]:
        if mod is None:
            continue
        hits = module_walk_hits(mod)
        print(f"- {mod.__name__}: {len(hits)} hit(s)")
        for item in hits[:20]:
            print(f"  - {item}")
    print()

    rows: list[dict[str, str]] = []
    if candl_data is not None:
        rows.extend(print_shortcuts("candl_data", candl_data))
    else:
        print(f"candl_data import failed: {candl_data_err}\n")
    if spt_data is not None:
        rows.extend(print_shortcuts("spt_candl_data", spt_data))
    else:
        print(f"spt_candl_data import failed: {spt_data_err}\n")

    print("SPT-focused shortcut rows")
    spt_rows = [r for r in rows if "spt" in r["group"].lower()]
    for row in spt_rows:
        print(
            f"- group={row['group']} variant={row['variant']} "
            f"id={row['id']} expr={row['expr']}"
        )
    print()

    spt2018, sptd1 = pick_best(rows)
    print("Best guess likelihood IDs")
    print(f"- SPT2018: {spt2018 or 'not found'}")
    print(f"- SPT D1: {sptd1 or 'not found'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
