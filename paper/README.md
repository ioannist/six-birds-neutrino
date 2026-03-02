# Paper Build

Primary workflow from repo root:

- `make paper`

This runs the paper build pipeline and writes:

- `paper/build/main.pdf`
- `paper/build/sixbirds_neutrino_researchsquare.pdf`
- `paper/build/metadata.json`
- `paper/build/researchsquare_source_upload.zip`

Manual compile fallback from inside `paper/`:

1. `pdflatex -interaction=nonstopmode -output-directory build main.tex`
2. `bibtex build/main`
3. `pdflatex -interaction=nonstopmode -output-directory build main.tex`
4. `pdflatex -interaction=nonstopmode -output-directory build main.tex`

ResearchSquare form content checklist:

- `paper/SUBMISSION_NOTES.md`
