#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER_DIR="$ROOT_DIR/paper"
BUILD_DIR="$PAPER_DIR/build"
STAGE_DIR="$BUILD_DIR/researchsquare_source_staging"
ZIP_PATH="$BUILD_DIR/researchsquare_source_upload.zip"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/sections" "$STAGE_DIR/tables" "$STAGE_DIR/figures" "$STAGE_DIR/includes"

# Ensure .bbl exists (submission portals often do not run BibTeX).
if ! [[ -f "$BUILD_DIR/main.bbl" ]]; then
  echo "[make_researchsquare_source_zip] main.bbl missing; compiling to generate it..." >&2
  (cd "$PAPER_DIR" && pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$BUILD_DIR" main.tex)
  (cd "$BUILD_DIR" && bibtex main)
  (cd "$PAPER_DIR" && pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$BUILD_DIR" main.tex)
fi

if ! [[ -f "$BUILD_DIR/main.bbl" ]]; then
  echo "[make_researchsquare_source_zip] ERROR: main.bbl not generated." >&2
  exit 3
fi

# Copy core sources.
cp "$PAPER_DIR/main.tex" "$STAGE_DIR/main.tex"
cp "$PAPER_DIR/references.bib" "$STAGE_DIR/references.bib"
cp "$BUILD_DIR/main.bbl" "$STAGE_DIR/main.bbl"

# Copy section and table inputs.
cp "$PAPER_DIR/sections/"*.tex "$STAGE_DIR/sections/"
cp "$PAPER_DIR/tables/"*.tex "$STAGE_DIR/tables/"
if compgen -G "$PAPER_DIR/includes/*.tex" > /dev/null; then
  cp "$PAPER_DIR/includes/"*.tex "$STAGE_DIR/includes/"
fi

# Copy figures used by manuscript.
for ext in png jpg jpeg pdf; do
  if compgen -G "$PAPER_DIR/figures/*.$ext" > /dev/null; then
    cp "$PAPER_DIR/figures/"*.$ext "$STAGE_DIR/figures/"
  fi
done

# Reject external path usage in source graph.
if rg -n '\\\\(input|includegraphics)\{(\.\./|/)' "$STAGE_DIR/main.tex" "$STAGE_DIR/sections/"*.tex >/dev/null 2>&1; then
  echo "[make_researchsquare_source_zip] ERROR: external paths detected in TeX sources." >&2
  exit 4
fi

# Remove transient LaTeX artifacts from staging if present.
find "$STAGE_DIR" -type f \( -name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.toc" -o -name "*.fdb_latexmk" -o -name "*.fls" \) -delete

rm -f "$ZIP_PATH"
(cd "$STAGE_DIR" && zip -r "$ZIP_PATH" . >/dev/null)

echo "[make_researchsquare_source_zip] Wrote $ZIP_PATH"
