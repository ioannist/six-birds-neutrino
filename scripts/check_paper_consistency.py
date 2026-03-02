#!/usr/bin/env python3
"""Validate paper self-consistency for figures, tables, citations, and paths."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
INPUT_RE = re.compile(r"\\input\{([^}]+)\}")
CITE_RE = re.compile(r"\\cite[a-zA-Z\*]*\{([^}]*)\}")
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")

IMAGE_EXTENSIONS = (".png", ".pdf", ".jpg", ".jpeg", ".eps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper_dir",
        default="paper",
        help="Path to paper root directory (default: paper).",
    )
    return parser.parse_args()


def resolve_reference(
    paper_dir: Path, rel_ref: str, is_graphic: bool
) -> tuple[bool, Path | None]:
    rel_ref = rel_ref.strip()
    candidate = paper_dir / rel_ref
    if candidate.exists():
        return True, candidate

    if is_graphic and candidate.suffix == "":
        for ext in IMAGE_EXTENSIONS:
            trial = candidate.with_suffix(ext)
            if trial.exists():
                return True, trial
    elif (not is_graphic) and candidate.suffix == "":
        trial = candidate.with_suffix(".tex")
        if trial.exists():
            return True, trial

    return False, None


def is_external_path(path_str: str) -> bool:
    path_str = path_str.strip()
    return path_str.startswith("../") or path_str.startswith("/")


def iter_tex_files(paper_dir: Path) -> list[Path]:
    tex_files: list[Path] = []
    exclude_arxiv_subtree = paper_dir.name != "arxiv_bundle"
    for tex_path in sorted(paper_dir.rglob("*.tex")):
        if exclude_arxiv_subtree and "arxiv_bundle" in tex_path.parts:
            continue
        tex_files.append(tex_path)
    return tex_files


def main() -> int:
    args = parse_args()
    paper_dir = Path(args.paper_dir).resolve()
    if not paper_dir.exists():
        print(f"ERROR: paper_dir does not exist: {paper_dir}")
        return 2

    bib_path = paper_dir / "references.bib"
    if not bib_path.exists():
        print(f"ERROR: Missing bibliography file: {bib_path}")
        return 2

    tex_files = iter_tex_files(paper_dir)

    figure_refs: list[tuple[Path, str]] = []
    table_inputs: list[tuple[Path, str]] = []
    citation_keys_used: set[str] = set()
    external_path_violations: list[tuple[Path, str, str]] = []

    for tex_file in tex_files:
        text = tex_file.read_text(encoding="utf-8")

        for match in INCLUDEGRAPHICS_RE.finditer(text):
            ref = match.group(1).strip()
            figure_refs.append((tex_file, ref))
            if is_external_path(ref):
                external_path_violations.append((tex_file, "includegraphics", ref))

        for match in INPUT_RE.finditer(text):
            ref = match.group(1).strip()
            if ref.startswith("tables/"):
                table_inputs.append((tex_file, ref))
            if is_external_path(ref):
                external_path_violations.append((tex_file, "input", ref))

        for match in CITE_RE.finditer(text):
            raw_keys = match.group(1).strip()
            if not raw_keys:
                continue
            for key in raw_keys.split(","):
                key = key.strip()
                if key:
                    citation_keys_used.add(key)

    missing_figures: list[tuple[Path, str]] = []
    for tex_file, ref in figure_refs:
        ok, _ = resolve_reference(paper_dir, ref, is_graphic=True)
        if not ok:
            missing_figures.append((tex_file, ref))

    missing_tables: list[tuple[Path, str]] = []
    for tex_file, ref in table_inputs:
        ok, _ = resolve_reference(paper_dir, ref, is_graphic=False)
        if not ok:
            missing_tables.append((tex_file, ref))

    bib_text = bib_path.read_text(encoding="utf-8")
    bib_keys_defined = set(BIB_KEY_RE.findall(bib_text))
    missing_citation_keys = sorted(citation_keys_used - bib_keys_defined)
    unused_bib_keys = sorted(bib_keys_defined - citation_keys_used)

    print(f"Scanned tex files: {len(tex_files)}")
    print(f"Figures referenced: {len(figure_refs)}, missing: {len(missing_figures)}")
    print(f"Table inputs found: {len(table_inputs)}, missing: {len(missing_tables)}")
    print(
        "Citation keys used: "
        f"{len(citation_keys_used)}, missing: {len(missing_citation_keys)}"
    )
    print(f"External path violations: {len(external_path_violations)}")
    print(f"Unused bib keys (info): {len(unused_bib_keys)}")

    if missing_figures:
        print("Missing figures:")
        for tex_file, ref in missing_figures:
            print(f"  - {tex_file.relative_to(paper_dir)} -> {ref}")

    if missing_tables:
        print("Missing table inputs:")
        for tex_file, ref in missing_tables:
            print(f"  - {tex_file.relative_to(paper_dir)} -> {ref}")

    if missing_citation_keys:
        print("Missing citation keys:")
        for key in missing_citation_keys:
            print(f"  - {key}")

    if external_path_violations:
        print("External-path violations:")
        for tex_file, cmd, ref in external_path_violations:
            print(f"  - {tex_file.relative_to(paper_dir)}: \\{cmd}{{{ref}}}")

    has_errors = bool(
        missing_figures
        or missing_tables
        or missing_citation_keys
        or external_path_violations
    )

    return 2 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
