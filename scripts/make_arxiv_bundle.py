#!/usr/bin/env python3
"""Create a self-contained arXiv bundle under paper/arxiv_bundle."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".pdf", ".jpg", ".jpeg", ".eps"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        default="paper/arxiv_bundle",
        help="Bundle output directory (default: paper/arxiv_bundle).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete output directory before copying files.",
    )
    return parser.parse_args()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    paper_dir = repo_root / "paper"
    outdir = (repo_root / args.outdir).resolve()

    if not paper_dir.exists():
        print(f"ERROR: paper directory not found: {paper_dir}")
        return 2

    if args.clean and outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    required_root_files = ["main.tex", "references.bib"]
    for name in required_root_files:
        src = paper_dir / name
        if not src.exists():
            print(f"ERROR: Missing required paper file: {src}")
            return 2
        copy_file(src, outdir / name)

    for tex_file in sorted((paper_dir / "sections").glob("*.tex")):
        copy_file(tex_file, outdir / "sections" / tex_file.name)

    for tex_file in sorted((paper_dir / "tables").glob("*.tex")):
        copy_file(tex_file, outdir / "tables" / tex_file.name)

    for tex_file in sorted((paper_dir / "includes").glob("*.tex")):
        copy_file(tex_file, outdir / "includes" / tex_file.name)

    copied_figures = 0
    for fig_file in sorted((paper_dir / "figures").glob("*")):
        if fig_file.is_file() and fig_file.suffix.lower() in IMAGE_EXTENSIONS:
            copy_file(fig_file, outdir / "figures" / fig_file.name)
            copied_figures += 1

    build_txt = outdir / "BUILD.txt"
    build_txt.write_text(
        "\n".join(
            [
                "Build instructions",
                "==================",
                "",
                "cd paper/arxiv_bundle",
                "pdflatex main.tex",
                "bibtex main",
                "pdflatex main.tex",
                "pdflatex main.tex",
                "",
                "If using latexmk:",
                "latexmk -pdf -interaction=nonstopmode main.tex",
                "",
            ]
        ),
        encoding="utf-8",
    )

    checker = repo_root / "scripts" / "check_paper_consistency.py"
    check_cmd = [sys.executable, str(checker), "--paper_dir", str(outdir)]
    check_proc = subprocess.run(check_cmd, capture_output=True, text=True)
    if check_proc.stdout:
        print(check_proc.stdout.strip())
    if check_proc.stderr:
        print(check_proc.stderr.strip(), file=sys.stderr)
    if check_proc.returncode != 0:
        print("ERROR: Bundle consistency check failed.")
        return check_proc.returncode

    print(f"Bundle created: {outdir}")
    print(f"Copied section files: {len(list((outdir / 'sections').glob('*.tex')))}")
    print(f"Copied table files: {len(list((outdir / 'tables').glob('*.tex')))}")
    print(f"Copied figure files: {copied_figures}")
    print(f"Wrote build instructions: {build_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
