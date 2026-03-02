#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render paper LaTeX table fragments from canonical artifacts.")
    parser.add_argument(
        "--canonical",
        default="docs/findings/canonical_results.json",
        help="Path to canonical_results.json",
    )
    parser.add_argument(
        "--anchors",
        default="docs/anchors/2601.16277.yaml",
        help="Path to 2601.16277.yaml",
    )
    parser.add_argument("--outdir", default=None, help="Optional explicit run bundle output dir")
    return parser.parse_args()


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")


def _fmt3(value: float) -> str:
    return f"{float(value):.3f}"


def _fmt2(value: float) -> str:
    return f"{float(value):.2f}"


def _fmt_boundary(value: float) -> str:
    return f"{float(value):.3g}"


def _latex_row(cells: list[str]) -> str:
    return " & ".join(cells) + r" \\" 


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level JSON object")
    return data


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level YAML mapping")
    return data


def _render_tab_mnu_shift(canonical: dict[str, Any]) -> tuple[str, list[list[str]]]:
    shift = canonical["mnu_shift"]
    spt = shift["spt_only_plus_desi"]
    cmb = shift["cmb_plancksubset_plus_desi"]

    rows: list[list[str]] = [
        [
            "SPT-only + DESI DR2 BAO",
            "SPT2018",
            _fmt3(spt["run2018"]["mnu_median"]),
            _fmt3(spt["run2018"]["mnu_p95_upper"]),
            _fmt3(spt["run2018"]["mnu_mode"]),
            _fmt_boundary(spt["run2018"]["boundary_fraction"]),
        ],
        [
            "SPT-only + DESI DR2 BAO",
            "SPT D1",
            _fmt3(spt["runD1"]["mnu_median"]),
            _fmt3(spt["runD1"]["mnu_p95_upper"]),
            _fmt3(spt["runD1"]["mnu_mode"]),
            _fmt_boundary(spt["runD1"]["boundary_fraction"]),
        ],
        [
            "SPT-only + DESI DR2 BAO",
            "Shift (2018 - D1)",
            _fmt3(spt["shift"]["delta_median"]),
            _fmt3(spt["shift"]["delta_p95_upper"]),
            "---",
            "---",
        ],
        [
            "Planck-subset baseline + PR4 lensing + SPT + DESI DR2 BAO",
            "SPT2018 baseline",
            _fmt3(cmb["run2018"]["mnu_median"]),
            _fmt3(cmb["run2018"]["mnu_p95_upper"]),
            _fmt3(cmb["run2018"]["mnu_mode"]),
            _fmt_boundary(cmb["run2018"]["boundary_fraction"]),
        ],
        [
            "Planck-subset baseline + PR4 lensing + SPT + DESI DR2 BAO",
            "SPT D1 baseline",
            _fmt3(cmb["runD1"]["mnu_median"]),
            _fmt3(cmb["runD1"]["mnu_p95_upper"]),
            _fmt3(cmb["runD1"]["mnu_mode"]),
            _fmt_boundary(cmb["runD1"]["boundary_fraction"]),
        ],
        [
            "Planck-subset baseline + PR4 lensing + SPT + DESI DR2 BAO",
            "Shift (2018 - D1)",
            _fmt3(cmb["shift"]["delta_median"]),
            _fmt3(cmb["shift"]["delta_p95_upper"]),
            "---",
            "---",
        ],
    ]

    lines = [
        r"\begin{tabular}{p{0.33\linewidth} l r r r r}",
        r"\toprule",
        r"Setup & Lens & median [eV] & 95\% upper [eV] & mode [eV] & boundary frac \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(_latex_row(row))
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines) + "\n", rows


def _render_tab_audit_summary(canonical: dict[str, Any]) -> tuple[str, list[list[str]]]:
    unp = canonical["cross_audit"]["unprofiled_baseline_vs_staging"]
    pro = canonical["cross_audit"]["profiled_baseline_vs_staging"]

    rows: list[list[str]] = [
        [
            "Unprofiled",
            "D1|2018",
            _fmt2(unp["baseline"]["B_given_A"]),
            _fmt2(unp["staging"]["B_given_A"]),
            _fmt2(unp["reduction_pct"]["B_given_A"]),
        ],
        [
            "Unprofiled",
            "2018|D1",
            _fmt2(unp["baseline"]["A_given_B"]),
            _fmt2(unp["staging"]["A_given_B"]),
            _fmt2(unp["reduction_pct"]["A_given_B"]),
        ],
        [
            "Profiled",
            "D1|2018",
            _fmt2(pro["baseline"]["profiled_B_given_A"]),
            _fmt2(pro["staging"]["profiled_B_given_A"]),
            _fmt2(pro["reduction_pct"]["profiled_B_given_A"]),
        ],
        [
            "Profiled",
            "2018|D1",
            _fmt2(pro["baseline"]["profiled_A_given_B"]),
            _fmt2(pro["staging"]["profiled_A_given_B"]),
            _fmt2(pro["reduction_pct"]["profiled_A_given_B"]),
        ],
    ]

    lines = [
        r"\begin{tabular}{l l r r r}",
        r"\toprule",
        r"Audit & Direction & Baseline $\Delta\chi^2$ & Common-staging $\Delta\chi^2$ & Reduction (\%) \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(_latex_row(row))
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines) + "\n", rows


def _format_l_ranges(dataset: dict[str, Any]) -> str:
    ell = dataset["ell_ranges"]
    return (
        f"TT [$\\ell_{{\\min}}$,$\\ell_{{\\max}}$]=[{ell['TT'][0]},{ell['TT'][1]}]; "
        f"TE/EE [$\\ell_{{\\min}}$,$\\ell_{{\\max}}$]=[{ell['TE'][0]},{ell['TE'][1]}]"
    )


def _render_tab_baseline_defs(anchor: dict[str, Any]) -> tuple[str, list[list[str]]]:
    datasets = anchor["datasets"]
    cmb = datasets["CMB"]
    cmb_d1 = datasets["CMB-D1"]

    planck_subset = (
        r"TT $\ell<30$ (Commander); EE $\ell<30$ (SRoll2); "
        r"TT $30<\ell<756$ (Plik)."
    )

    rows: list[list[str]] = [
        [
            "CMB (SPT2018)",
            _format_l_ranges(cmb),
            planck_subset,
            "SPT lensing + Planck PR4 lensing",
        ],
        [
            "CMB-D1",
            _format_l_ranges(cmb_d1),
            planck_subset,
            "SPT lensing + Planck PR4 lensing",
        ],
    ]

    lines = [
        r"\begin{tabular}{l p{0.33\linewidth} p{0.34\linewidth} p{0.21\linewidth}}",
        r"\toprule",
        r"Baseline & SPT primary ($\ell$ ranges) & Planck PR3 primary subset & Lensing \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(_latex_row(row))
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines) + "\n", rows


def _write_env(outdir: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "print_env.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    (outdir / "env.txt").write_text(res.stdout, encoding="utf-8")


def _write_smoke_doc(outdir: Path) -> Path:
    smoke_path = outdir / "tables_smoke.tex"
    smoke_path.write_text(
        "\n".join(
            [
                r"\documentclass{article}",
                r"\usepackage[margin=1in]{geometry}",
                r"\usepackage{booktabs}",
                r"\begin{document}",
                r"\begin{table}[h]",
                r"\centering",
                r"\input{../../paper/tables/tab_mnu_shift.tex}",
                r"\caption{Smoke test: mnu shift}",
                r"\end{table}",
                r"\begin{table}[h]",
                r"\centering",
                r"\input{../../paper/tables/tab_audit_summary.tex}",
                r"\caption{Smoke test: audit summary}",
                r"\end{table}",
                r"\begin{table}[h]",
                r"\centering",
                r"\input{../../paper/tables/tab_baseline_defs.tex}",
                r"\caption{Smoke test: baseline definitions}",
                r"\end{table}",
                r"\end{document}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return smoke_path


def _run_smoke_compile(outdir: Path) -> None:
    latexmk = shutil.which("latexmk")
    if not latexmk:
        raise RuntimeError("latexmk not found; required for table smoke compilation")

    result = subprocess.run(
        [latexmk, "-pdf", "-interaction=nonstopmode", "tables_smoke.tex"],
        cwd=outdir,
        capture_output=True,
        text=True,
        check=False,
    )
    (outdir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (outdir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError("latexmk smoke compilation failed; see stdout.txt/stderr.txt")


def main() -> int:
    args = parse_args()
    canonical_path = Path(args.canonical).expanduser().resolve()
    anchors_path = Path(args.anchors).expanduser().resolve()

    canonical = _load_json(canonical_path)
    anchors = _load_yaml(anchors_path)

    paper_tables_dir = REPO_ROOT / "paper" / "tables"
    paper_tables_dir.mkdir(parents=True, exist_ok=True)

    tab_mnu_text, tab_mnu_rows = _render_tab_mnu_shift(canonical)
    tab_audit_text, tab_audit_rows = _render_tab_audit_summary(canonical)
    tab_base_text, tab_base_rows = _render_tab_baseline_defs(anchors)

    tab_mnu_path = paper_tables_dir / "tab_mnu_shift.tex"
    tab_audit_path = paper_tables_dir / "tab_audit_summary.tex"
    tab_base_path = paper_tables_dir / "tab_baseline_defs.tex"

    tab_mnu_path.write_text(tab_mnu_text, encoding="utf-8")
    tab_audit_path.write_text(tab_audit_text, encoding="utf-8")
    tab_base_path.write_text(tab_base_text, encoding="utf-8")

    run_outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else REPO_ROOT / "runs" / f"{_stamp()}_render_paper_tables"
    )
    run_outdir.mkdir(parents=True, exist_ok=False)

    _write_env(run_outdir)

    inputs = {
        "canonical_json": str(canonical_path),
        "anchors_yaml": str(anchors_path),
        "tables": {
            "tab_mnu_shift": str(tab_mnu_path),
            "tab_audit_summary": str(tab_audit_path),
            "tab_baseline_defs": str(tab_base_path),
        },
    }
    (run_outdir / "inputs.yaml").write_text(yaml.safe_dump(inputs, sort_keys=False), encoding="utf-8")

    metrics = {
        "rendered": {
            "tab_mnu_shift": {"rows": tab_mnu_rows},
            "tab_audit_summary": {"rows": tab_audit_rows},
            "tab_baseline_defs": {"rows": tab_base_rows},
        }
    }
    (run_outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    _write_smoke_doc(run_outdir)
    _run_smoke_compile(run_outdir)

    smoke_pdf = run_outdir / "tables_smoke.pdf"
    if not smoke_pdf.exists():
        raise RuntimeError("smoke compile did not produce tables_smoke.pdf")

    print(f"Rendered: {tab_mnu_path}")
    print(f"Rendered: {tab_audit_path}")
    print(f"Rendered: {tab_base_path}")
    print(f"Run bundle: {run_outdir}")
    print(f"Smoke PDF: {smoke_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
