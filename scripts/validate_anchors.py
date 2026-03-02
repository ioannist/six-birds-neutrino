#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
ANCHORS_DIR = REPO_ROOT / "docs" / "anchors"

ANCHOR_FILES = {
    "2601": ANCHORS_DIR / "2601.16277.yaml",
    "dark_energy": ANCHORS_DIR / "six_birds_dark_energy.yaml",
    "foundations": ANCHORS_DIR / "six_birds_foundations.yaml",
    "neutrino_recipe": ANCHORS_DIR / "neutrino_recipe_2601.16277.yaml",
}

REQUIRED_TOP_LEVEL_BY_FILE = {
    "2601": {
        "claims",
        "definitions",
        "datasets",
        "tables_figures",
        "do_not_claim_novelty",
        "citations_local",
    },
    "dark_energy": {
        "claims",
        "definitions",
        "datasets",
        "tables_figures",
        "do_not_claim_novelty",
        "citations_local",
    },
    "foundations": {
        "claims",
        "definitions",
        "datasets",
        "tables_figures",
        "do_not_claim_novelty",
        "citations_local",
    },
    "neutrino_recipe": {
        "model",
        "parameters",
        "priors",
        "datasets",
        "table_combos",
        "implementation_notes",
        "found_configs",
        "citations_local",
    },
}


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping.")
    return data


def ensure_required_keys(path: Path, data: dict, required: set[str], errors: list[str]) -> None:
    missing = required - set(data.keys())
    if missing:
        errors.append(f"{path}: missing top-level keys: {sorted(missing)}")


def validate_2601(path: Path, data: dict, errors: list[str]) -> None:
    datasets = data.get("datasets")
    if not isinstance(datasets, dict):
        errors.append(f"{path}: datasets must be a mapping.")
        return

    for baseline in ("CMB", "CMB-D1"):
        if baseline not in datasets:
            errors.append(f"{path}: datasets.{baseline} is required.")
            continue
        item = datasets.get(baseline)
        if not isinstance(item, dict):
            errors.append(f"{path}: datasets.{baseline} must be a mapping.")
            continue
        ell = item.get("ell_ranges")
        if not isinstance(ell, dict):
            errors.append(f"{path}: datasets.{baseline}.ell_ranges must be a mapping.")
        else:
            for mode in ("TT", "TE", "EE"):
                if mode not in ell:
                    errors.append(f"{path}: datasets.{baseline}.ell_ranges.{mode} is required.")

    tables = data.get("tables_figures")
    if not isinstance(tables, dict):
        errors.append(f"{path}: tables_figures must be a mapping.")
        return

    for tab in ("tab:3", "tab:3a"):
        if tab not in tables:
            errors.append(f"{path}: tables_figures.{tab} is required.")
            continue
        tab_item = tables.get(tab)
        if not isinstance(tab_item, dict):
            errors.append(f"{path}: tables_figures.{tab} must be a mapping.")
            continue
        smnu = tab_item.get("sum_mnu_95_upper_eV")
        if not isinstance(smnu, dict) or not smnu:
            errors.append(
                f"{path}: tables_figures.{tab}.sum_mnu_95_upper_eV must be a non-empty mapping."
            )


def validate_neutrino_recipe(path: Path, data: dict, errors: list[str]) -> None:
    priors = data.get("priors")
    if not isinstance(priors, dict):
        errors.append(f"{path}: priors must be a mapping.")
    elif "sum_mnu" not in priors:
        errors.append(f"{path}: priors.sum_mnu is required.")

    table_combos = data.get("table_combos")
    if not isinstance(table_combos, dict):
        errors.append(f"{path}: table_combos must be a mapping.")
        return

    for tab in ("tab:3", "tab:3a"):
        if tab not in table_combos:
            errors.append(f"{path}: table_combos.{tab} is required.")
            continue
        tab_item = table_combos.get(tab)
        if not isinstance(tab_item, dict):
            errors.append(f"{path}: table_combos.{tab} must be a mapping.")
            continue
        columns = tab_item.get("columns")
        if not isinstance(columns, list) or not columns:
            errors.append(f"{path}: table_combos.{tab}.columns must be a non-empty list.")


def main() -> int:
    errors: list[str] = []
    loaded: dict[str, dict] = {}

    for key, path in ANCHOR_FILES.items():
        if not path.exists():
            errors.append(f"Missing required file: {path}")
            continue
        try:
            data = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: failed to load YAML ({exc})")
            continue
        loaded[key] = data
        required = REQUIRED_TOP_LEVEL_BY_FILE[key]
        ensure_required_keys(path, data, required, errors)

    if "2601" in loaded:
        validate_2601(ANCHOR_FILES["2601"], loaded["2601"], errors)
    if "neutrino_recipe" in loaded:
        validate_neutrino_recipe(
            ANCHOR_FILES["neutrino_recipe"], loaded["neutrino_recipe"], errors
        )

    if errors:
        print("Anchor validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Anchor validation passed.")
    for _, path in ANCHOR_FILES.items():
        print(f"- {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
