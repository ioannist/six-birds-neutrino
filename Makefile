SHELL := /bin/bash

PLANCK_ASSETS_DIR ?= external/cobaya_packages
MNU_FULL_FAST ?= 0
PYTHON ?= python3

.PHONY: math_check
math_check:
	$(PYTHON) -m pytest -q
	cd lean/trunc_gauss_proof && lake build
	cd lean/trunc_gauss_proof && lake env lean AuditAxioms.lean

.PHONY: help env toy audit validate tables paper paper-clean paper_check arxiv_bundle researchsquare_bundle mnu_smoke mnu_full freeze_check

help:
	@echo "Available targets:"
	@echo "  make env   - Run environment check and save to runs/<timestamp>_env_check/env.txt"
	@echo "  make toy   - Run toy truncated Gaussian script into runs/<timestamp>_toy_trunc_gauss"
	@echo "  make audit - Run toy MAP + cross-audit pipeline (or skip with clear message if deps missing)"
	@echo "  make validate - Validate anchor YAML files"
	@echo "  make tables - Render paper table fragments from canonical artifacts"
	@echo "  make paper - Check LaTeX stack and build paper/main.tex with latexmk when available"
	@echo "  make paper-clean - Clean LaTeX build artifacts under paper/ when latexmk is available"
	@echo "  make paper_check - Run paper consistency checks, then build the paper"
	@echo "  make arxiv_bundle - Build a self-contained paper/arxiv_bundle package"
	@echo "  make researchsquare_bundle - Build self-contained ResearchSquare source zip under paper/build/"
	@echo "  make mnu_smoke - Run SPT-only mnu Cobaya smoke chains (2018 + D1) and compare posteriors"
	@echo "  make mnu_full  - Run CMB baseline+DESI mnu chains if Planck assets exist, else skip cleanly"
	@echo "  make freeze_check - Run pytest + anchor validation + env + toy + audit + optional Lean build"

env:
	@ts=$$(python -c "import datetime; print(datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f'))"); \
	out="runs/$${ts}_env_check"; \
	mkdir -p "$$out"; \
	echo "Writing env check to $$out/env.txt"; \
	python scripts/print_env.py | tee "$$out/env.txt"

toy:
	@ts=$$(python -c "import datetime; print(datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f'))"); \
	out="runs/$${ts}_toy_trunc_gauss"; \
	echo "Running toy truncated Gaussian into $$out"; \
	python scripts/toy_truncated_gaussian.py --outdir "$$out" --seed 0

audit:
	@python -c "import numpy, scipy, yaml, matplotlib" >/dev/null 2>&1 || { \
		echo "Audit skipped: missing python deps (numpy/scipy/yaml/matplotlib)."; \
		exit 0; \
	}; \
	ts=$$(python -c "import datetime; print(datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f'))"); \
	base="runs/$${ts}_audit"; \
	outA="$$base/toy_lensA"; \
	outB="$$base/toy_lensB"; \
	outX="$$base/cross_audit_toy_lensA_vs_toy_lensB"; \
	mkdir -p "$$base"; \
	python scripts/run_map.py --config configs/toy_lensA.yaml --outdir "$$outA"; \
	python scripts/run_map.py --config configs/toy_lensB.yaml --outdir "$$outB"; \
	python scripts/run_cross_audit.py --runA "$$outA" --runB "$$outB" --outdir "$$outX"; \
	echo "Audit outputs:"; \
	echo "  $$outA"; \
	echo "  $$outB"; \
	echo "  $$outX"

validate:
	@python scripts/validate_anchors.py

tables:
	@python scripts/render_paper_tables.py

paper:
	@set -euo pipefail; \
	python scripts/check_latex_stack.py; \
	bash scripts/build_paper.sh

paper-clean:
	@set -euo pipefail; \
	if command -v latexmk >/dev/null 2>&1; then \
		echo "Cleaning paper build artifacts with latexmk -C..."; \
		( cd paper && latexmk -C ); \
	else \
		echo "latexmk not found; paper-clean is a no-op."; \
	fi

paper_check:
	@python scripts/check_paper_consistency.py
	@$(MAKE) paper

arxiv_bundle:
	@python scripts/make_arxiv_bundle.py --clean

researchsquare_bundle:
	@bash scripts/make_researchsquare_source_zip.sh

mnu_smoke:
	@set -euo pipefail; \
	ts=$$(python -c "import datetime; print(datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f'))"); \
	base="runs/$${ts}_mnu_smoke"; \
	outA="$$base/spt2018"; \
	outB="$$base/sptd1"; \
	outC="$$base/compare"; \
	mkdir -p "$$base"; \
	python scripts/run_cobaya.py --config configs/neutrino/spt2018_lcdm_mnu.yaml --outdir "$$outA"; \
	python scripts/run_cobaya.py --config configs/neutrino/sptd1_lcdm_mnu.yaml --outdir "$$outB"; \
	python scripts/compare_mnu_posteriors.py --run2018 "$$outA" --runD1 "$$outB" --outdir "$$outC" \
		--title "SPT-only: mnu posterior overlay" \
		--label2018 "SPT2018 (SPT-only)" \
		--labelD1 "SPT D1 (SPT-only)"; \
	echo "mnu_smoke outputs: $$base"

mnu_full:
	@set -euo pipefail; \
	planck_root="$(PLANCK_ASSETS_DIR)"; \
	if [ ! -d "$$planck_root/data/planck_2018_pliklite_native" ] || [ ! -d "$$planck_root/code/planck_PR4_lensing" ]; then \
		echo "mnu_full skipped: Planck/PR4 assets not found under $$planck_root. Run N4 install first."; \
		exit 0; \
	fi; \
	ts=$$(python -c "import datetime; print(datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f'))"); \
	base="runs/$${ts}_mnu_full"; \
	outE="$$base/eval"; \
	outA="$$base/cmb2018"; \
	outB="$$base/cmbd1"; \
	outC="$$base/compare"; \
	mkdir -p "$$base"; \
	python scripts/eval_cmb_plancksubset_desi.py \
		--config configs/neutrino/cmb_spt2018_plancksubset_desi_mnu.yaml \
		--config configs/neutrino/cmb_sptd1_plancksubset_desi_mnu.yaml \
		--outdir "$$outE" \
		--packages_path "$$planck_root"; \
	max_opts=(); \
	if [ "$(MNU_FULL_FAST)" = "1" ]; then \
		max_opts=(--max_samples_override 120); \
	fi; \
	python scripts/run_cobaya.py --config configs/neutrino/cmb_spt2018_plancksubset_desi_mnu.yaml \
		--outdir "$$outA" --packages_path "$$planck_root" "$${max_opts[@]}"; \
	python scripts/run_cobaya.py --config configs/neutrino/cmb_sptd1_plancksubset_desi_mnu.yaml \
		--outdir "$$outB" --packages_path "$$planck_root" "$${max_opts[@]}"; \
	python scripts/compare_mnu_posteriors.py --run2018 "$$outA" --runD1 "$$outB" --outdir "$$outC" \
		--title "CMB baseline + DESI DR2: mnu posterior overlay" \
		--label2018 "SPT2018 + Planck subset + DESI" \
		--labelD1 "SPT D1 + Planck subset + DESI"; \
	echo "mnu_full outputs: $$base"

freeze_check:
	@set -euo pipefail; \
	before=$$(mktemp); \
	after=$$(mktemp); \
	find runs -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort > "$$before" || true; \
	echo "[freeze_check] 1/5 pytest"; \
	python -m pytest; \
	echo "[freeze_check] 2/5 anchor validate"; \
	$(MAKE) validate; \
	echo "[freeze_check] 3/5 env + toy"; \
	$(MAKE) env; \
	$(MAKE) toy; \
	echo "[freeze_check] 4/5 audit"; \
	$(MAKE) audit; \
	echo "[freeze_check] 5/5 lean build (best effort)"; \
	if command -v lake >/dev/null 2>&1 && [ -d "lean/trunc_gauss_proof" ]; then \
		( cd lean/trunc_gauss_proof && lake build ); \
	else \
		echo "Lean build skipped: lake or lean/trunc_gauss_proof not available."; \
	fi; \
	find runs -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort > "$$after" || true; \
	echo "freeze_check OK"; \
	echo "New run dirs:"; \
	comm -13 "$$before" "$$after" || true; \
	rm -f "$$before" "$$after"
