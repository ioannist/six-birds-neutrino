#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER_DIR="$ROOT_DIR/paper"
BUILD_DIR="$PAPER_DIR/build"

mkdir -p "$BUILD_DIR"

run_latexmk() {
  (cd "$PAPER_DIR" && latexmk -pdf -interaction=nonstopmode -halt-on-error \
    -outdir="$BUILD_DIR" "main.tex")
}

run_pdflatex() {
  (cd "$PAPER_DIR" && pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory "$BUILD_DIR" "main.tex")
  (cd "$BUILD_DIR" && bibtex main || true)
  (cd "$PAPER_DIR" && pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory "$BUILD_DIR" "main.tex")
  (cd "$PAPER_DIR" && pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory "$BUILD_DIR" "main.tex")
}

if command -v latexmk >/dev/null 2>&1; then
  run_latexmk
elif command -v pdflatex >/dev/null 2>&1; then
  run_pdflatex
else
  echo "[build_paper] ERROR: no LaTeX engine available (need latexmk or pdflatex)." >&2
  exit 2
fi

# Normalize output name for submission workflows.
if [[ -f "$BUILD_DIR/main.pdf" ]]; then
  cp -f "$BUILD_DIR/main.pdf" "$BUILD_DIR/sixbirds_neutrino_researchsquare.pdf"
elif [[ -f "$PAPER_DIR/main.pdf" ]]; then
  cp -f "$PAPER_DIR/main.pdf" "$BUILD_DIR/sixbirds_neutrino_researchsquare.pdf"
fi

if [[ ! -f "$BUILD_DIR/sixbirds_neutrino_researchsquare.pdf" ]]; then
  echo "[build_paper] ERROR: expected PDF was not produced." >&2
  exit 3
fi

# Write metadata sidecar from manuscript fields.
ROOT_DIR="$ROOT_DIR" python - <<'PY'
import json
import os
import re
from pathlib import Path

root = Path(os.environ["ROOT_DIR"]).resolve()
main_tex = (root / "paper" / "main.tex").read_text(encoding="utf-8")
abstract_tex = (root / "paper" / "sections" / "abstract.tex").read_text(encoding="utf-8")

title_m = re.search(r"\\title\{(.*?)\}", main_tex, re.S)
if not title_m:
    raise SystemExit("[build_paper] ERROR: could not extract title from paper/main.tex")
title = " ".join(title_m.group(1).split())

keywords_m = re.search(r"\\textbf\{keywords:\}\s*([^\n]+)", main_tex, re.IGNORECASE)
if not keywords_m:
    raise SystemExit("[build_paper] ERROR: could not extract keywords line from paper/main.tex")
keywords = [k.strip() for k in keywords_m.group(1).split(";") if k.strip()]

abstract_lines = []
for line in abstract_tex.splitlines():
    s = line.strip()
    if not s:
        continue
    if s.startswith("%"):
        continue
    if s.startswith("\\label"):
        continue
    abstract_lines.append(s)
abstract = " ".join(abstract_lines)

meta = {
    "researchsquare_metadata": {
        "title": title,
        "abstract_tex": abstract,
        "keywords": keywords,
        "authors": [
            {
                "first_name": "Ioannis",
                "last_name": "Tsiokos",
                "email": "ioannis@automorph.io",
                "orcid": "0009-0009-7659-5964",
                "corresponding": True,
                "affiliation": "Automorph Inc., 1207 Delaware Ave #4131, Wilmington, DE 19806, USA",
            }
        ],
    }
}

out = root / "paper" / "build" / "metadata.json"
out.write_text(json.dumps(meta, indent=2), encoding="utf-8")
PY

# Build ResearchSquare source bundle (LaTeX + assets + bbl).
bash "$ROOT_DIR/scripts/make_researchsquare_source_zip.sh"

echo "[build_paper] Wrote $BUILD_DIR/sixbirds_neutrino_researchsquare.pdf"
