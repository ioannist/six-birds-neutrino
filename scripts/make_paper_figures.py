#!/usr/bin/env python3
"""Render manuscript figures and table fragments from verified run bundles.

Every plotted or tabulated audit number is read from a run bundle produced by the
mathematical review; nothing is transcribed by hand. Toy-model curves use the
repaired analytic helpers in ``scripts/toy_truncated_gaussian.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from toy_truncated_gaussian import (  # noqa: E402
    boundary_mode_probability,
    combine_gaussians,
    truncated_gaussian_pdf,
)

RUNS = ROOT / "runs"

# Reference palette (light mode); categorical slots in fixed order.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
DIVERGING = LinearSegmentedColormap.from_list(
    "blue_gray_red", ["#184f95", "#6da7ec", "#f0efec", "#ef8f8e", "#b52a2a"]
)

plt.rcParams.update(
    {
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "font.size": 9,
        "axes.edgecolor": INK2,
        "axes.labelcolor": INK,
        "axes.linewidth": 0.6,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "legend.frameon": False,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    }
)

LENS_LABEL = {"B_given_A": r"D1 | 2018", "A_given_B": r"2018 | D1"}


def _load(run: str) -> dict:
    return json.loads((RUNS / run / "metrics.json").read_text(encoding="utf-8"))


def _cosmo(run: str) -> dict:
    d = _load(run)["directions"]
    return {k: d[k] for k in ("B_given_A", "A_given_B")}


def _profiled(run: str) -> dict:
    d = _load(run)
    return {k: d[k]["delta_chi2_profiled"] for k in ("B_given_A", "A_given_B")}


def _style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ---------------------------------------------------------------- figure: toy
def fig_toy(out: Path) -> dict:
    mu1, s1, mu2, s2 = 0.05, 0.02, -0.02, 0.01
    mu_star, sd_star = combine_gaussians(mu1, s1, mu2, s2)
    x = np.linspace(-0.05, 0.06, 1200)
    unconstrained = np.exp(-0.5 * ((x - mu_star) / sd_star) ** 2) / (sd_star * np.sqrt(2 * np.pi))
    xp = x[x >= 0]
    gated = truncated_gaussian_pdf(xp, mu_star, sd_star)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.5), gridspec_kw={"wspace": 0.32})
    ax1.axvspan(x[0], 0, color="#f0efec", lw=0)
    ax1.plot(x, unconstrained, color=INK2, lw=1.4, ls=(0, (4, 2)), label="ungated product")
    ax1.plot(xp, gated, color=BLUE, lw=2.0, label=r"gated at $m\geq 0$")
    ax1.axvline(mu_star, color=INK2, lw=0.6, ls=":")
    ax1.text(mu_star, 4, r"$\mu_\star$ ", ha="right", va="bottom", color=INK2)
    ax1.text(-0.048, 4, "excluded\n($m<0$)", ha="left", va="bottom", color=INK2, fontsize=7.5)
    ax1.set_xlabel(r"$m$ [eV]")
    ax1.set_ylabel("density")
    ax1.set_xlim(x[0], x[-1])
    ax1.set_ylim(bottom=0)
    ax1.legend(loc="upper right", fontsize=8, handlelength=2.2, bbox_to_anchor=(1.0, 0.9))
    ax1.set_title(r"(a) combined constraint, then gate", fontsize=9, loc="left", color=INK)
    _style(ax1)

    widths = np.geomspace(0.002, 0.05, 200)
    s1b, d, s = 0.02, 0.0, 0.03
    curves = [(0.02, BLUE, r"$\mu_1=+0.02$"), (0.0, INK2, r"$\mu_1=0$"), (-0.02, ORANGE, r"$\mu_1=-0.02$")]
    for m1, color, label in curves:
        p = boundary_mode_probability(m1, s1b, d, s, widths)
        ax2.plot(widths, p, color=color, lw=2.0, label=label)
    ax2.set_xscale("log")
    ticks = [0.002, 0.005, 0.01, 0.02, 0.05]
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f"{t:g}" for t in ticks])
    ax2.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax2.invert_xaxis()
    ax2.set_xlabel(r"$\sigma_2$ [eV]   (tighter $\rightarrow$)")
    ax2.set_ylabel(r"$P(\mathrm{gated\ mode}=0)$")
    ax2.set_ylim(0, 1.02)
    ax2.legend(loc="center left", fontsize=8, handlelength=1.8, bbox_to_anchor=(0.0, 0.62))
    ax2.set_title("(b) tightening the second constraint", fontsize=9, loc="left", color=INK)
    ax2.grid(axis="y", color=GRID, lw=0.5)
    _style(ax2)

    fig.savefig(out)
    plt.close(fig)
    return {
        "panel_a": {"mu1": mu1, "sigma1": s1, "mu2": mu2, "sigma2": s2,
                    "mu_star": float(mu_star), "sd_star": float(sd_star)},
        "panel_b": {"sigma1": s1b, "d": d, "s": s, "mu1_values": [c[0] for c in curves],
                    "sigma2_range": [float(widths[0]), float(widths[-1])]},
    }


# ------------------------------------------------------- figure: audit totals
AUDIT_ROWS = [
    # (group, label, kind, run)
    ("SPT only, fixed spectra", "nuisance-profiled", "profiled", "20261003_math_review_profiled_multistart"),
    ("SPT only, fixed spectra", "+ support cut", "profiled", "20261003_math_review_profiled_staging_multistart"),
    ("SPT + DESI", "baseline", "cosmo", "20261003_math_review_cosmological_spt_desi"),
    ("SPT + DESI", "+ support cut", "cosmo", "20261003_math_review_cosmological_spt_desi_staging"),
    ("Full CMB + DESI", "baseline (multistart)", "cosmo", "20261003_math_review_cosmological_cmb_desi"),
    ("Full CMB + DESI", "baseline (warm start)", "cosmo", "20261003_math_review_cosmological_cmb_desi_warm"),
    ("Full CMB + DESI", "+ support cut", "cosmo", "20261003_math_review_cosmological_cmb_desi_staging"),
    ("Full CMB + DESI", r"$-$ SPT $\tau$ prior", "cosmo", "20261003_math_review_cosmological_cmb_desi_tau_control"),
    ("Full CMB + DESI", "+ CLASS precision", "cosmo", "20261003_math_review_cosmological_cmb_desi_accuracy"),
]


def audit_values() -> list[dict]:
    rows = []
    for group, label, kind, run in AUDIT_ROWS:
        if kind == "profiled":
            vals = _profiled(run)
        else:
            vals = {k: v["joint_candidate_delta_chi2"] for k, v in _cosmo(run).items()}
        rows.append({"group": group, "label": label, "run": run, **vals})
    return rows


def fig_audit(out: Path, rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    y = []
    pos = 0.0
    last_group = None
    ticks, ticklabels, headers = [], [], []
    for r in rows:
        if r["group"] != last_group:
            if last_group is not None:
                pos += 0.4
            headers.append((pos, r["group"]))
            pos += 0.9
        ticks.append(pos)
        ticklabels.append(r["label"])
        y.append(pos)
        last_group = r["group"]
        pos += 1.0
    y = np.array(y)
    ba = np.array([r["B_given_A"] for r in rows])
    ab = np.array([r["A_given_B"] for r in rows])
    for yi, a, b in zip(y, ba, ab):
        ax.plot([b, a], [yi, yi], color=GRID, lw=1.6, zorder=1)
    ax.scatter(ba, y, s=34, color=BLUE, edgecolor="white", linewidth=1.0, zorder=3, label="D1 | 2018  (D1 tested at 2018 fit)")
    ax.scatter(ab, y, s=34, color=ORANGE, edgecolor="white", linewidth=1.0, zorder=3, label="2018 | D1  (2018 tested at D1 fit)")
    ax.set_xscale("log")
    ax.set_xlim(15, 1500)
    ax.set_yticks(ticks)
    ax.set_yticklabels(ticklabels, fontsize=8)
    ax.set_ylim(pos - 0.4, -0.6)
    for hpos, g in headers:
        ax.text(-0.02, hpos, g, transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=8.5, color=INK, fontweight="bold")
    for xi, yi in ((ba, y), (ab, y)):
        for v, yy in zip(xi, yi):
            ax.text(v, yy - 0.32, f"{v:.0f}" if v >= 100 else f"{v:.1f}", ha="center", va="bottom",
                    fontsize=6.5, color=INK2)
    ax.set_xlabel(r"directional mismatch $\Delta\chi^2$ (log scale)")
    ax.grid(axis="x", color=GRID, lw=0.5, which="both")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, fontsize=8, handletextpad=0.3)
    _style(ax)
    fig.savefig(out)
    plt.close(fig)


# ------------------------------------------------- figure: localization maps
def fig_localization(out: Path) -> dict:
    panels = [
        ("20261003_math_review_cosmological_spt_desi", "B_given_A", "SPT + DESI:  D1 | 2018"),
        ("20261003_math_review_cosmological_spt_desi", "A_given_B", "SPT + DESI:  2018 | D1"),
        ("20261003_math_review_cosmological_cmb_desi", "B_given_A", "Full CMB + DESI:  D1 | 2018"),
        ("20261003_math_review_cosmological_cmb_desi", "A_given_B", "Full CMB + DESI:  2018 | D1"),
    ]
    nb = 7  # bands up to ell = 4000; higher bands are empty for both lenses
    spectra = ["TT", "TE", "EE"]
    grids, info = [], {}
    for run, direction, title in panels:
        dd = _cosmo(run)[direction]
        edges = dd["ell_edges"][: nb + 1]
        grid = np.array([dd["spt_deltaQ_by_spec_ell"][s][:nb] for s in spectra])
        grids.append((grid, edges, title, dd))
        info[f"{run}:{direction}"] = {
            "unlocalized_deltaQ": dd["spt_ledger"]["unlocalized_deltaQ"],
            "deltaQ_full": dd["spt_ledger"]["deltaQ_full"],
        }

    fig, axes = plt.subplots(2, 2, figsize=(6.6, 3.9), gridspec_kw={"hspace": 0.62, "wspace": 0.12})
    for ax, (grid, edges, title, dd) in zip(axes.flat, grids):
        vmax = max(abs(grid.min()), abs(grid.max()))
        norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
        im = ax.imshow(grid, aspect="auto", cmap=DIVERGING, norm=norm)
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                v = grid[i, j]
                if abs(v) >= 0.12 * vmax:
                    ax.text(j, i, f"{v:.0f}" if abs(v) >= 100 else f"{v:.1f}", ha="center", va="center",
                            fontsize=6.5, color="white" if abs(v) > 0.6 * vmax else INK)
        ax.set_yticks(range(3))
        ax.set_yticklabels(spectra, fontsize=8)
        ax.set_xticks(range(nb))
        ax.set_xticklabels([f"{int(edges[j])}" for j in range(nb)], fontsize=7)
        ax.set_xlabel(r"band lower edge $\ell$", fontsize=8)
        ax.set_title(title + rf"   ($\Delta Q$ = {dd['spt_ledger']['deltaQ_full']:.1f})", fontsize=8.5,
                     loc="left", color=INK)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
        cb.ax.tick_params(labelsize=6.5, length=2)
        cb.outline.set_visible(False)
    for ax in axes[:, 1]:
        ax.set_yticklabels([])
    fig.savefig(out)
    plt.close(fig)
    return info


# ------------------------------------------------------------ figure: schema
def fig_schema(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 2.0))
    ax.set_xlim(0, 14.4)
    ax.set_ylim(0, 4.0)
    ax.axis("off")

    def box(xc, yc, w, h, text, fc, ec, fs=8):
        ax.add_patch(matplotlib.patches.FancyBboxPatch((xc - w / 2, yc - h / 2), w, h,
                     boxstyle="round,pad=0.02,rounding_size=0.15", fc=fc, ec=ec, lw=0.9))
        ax.text(xc, yc, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.35)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.9, shrinkA=1, shrinkB=1))

    box(1.2, 3.1, 2.2, 1.1, "train lens $A$\n(SPT 2018)", "#e8f0fb", BLUE)
    box(1.2, 0.9, 2.2, 1.1, "test lens $B$\n(SPT D1)", "#fdeee7", ORANGE)
    box(4.9, 3.1, 3.4, 1.1, "fit $A$ + completion\n" + r"$\rightarrow\ \hat\phi_A$", "#f7f7f5", INK2)
    box(4.9, 0.9, 3.4, 1.1, "fit $B$ + completion\n" + r"$\rightarrow\ \hat\theta_B$ (reference)", "#f7f7f5", INK2)
    box(9.15, 2.0, 3.2, 1.5, "evaluate $B$ at $\\hat\\phi_A$;\nre-fit free\n$B$ nuisances", "#f7f7f5", INK2)
    box(12.85, 2.0, 2.9, 2.0, r"$\Delta\chi^2_{B|A}$;" + "\nSPT quadratic\npart split by\nspectrum, $\\ell$", "#fbfbfa", INK)
    arrow(2.3, 3.1, 3.2, 3.1)
    arrow(2.3, 0.9, 3.2, 0.9)
    arrow(6.6, 3.0, 7.55, 2.35)
    arrow(6.6, 1.0, 7.55, 1.65)
    arrow(10.75, 2.0, 11.4, 2.0)
    fig.savefig(out)
    plt.close(fig)


# ---------------------------------------------------------------- tables
def write_audit_table(path: Path, rows: list[dict]) -> None:
    lines = [
        r"\begin{tabular}{@{}l l r r@{}}",
        r"\toprule",
        r"Audit scope & Variant & $\dchi_{\mathrm{D1}|2018}$ & $\dchi_{2018|\mathrm{D1}}$ \\",
        r"\midrule",
    ]
    last = None
    for r in rows:
        group = r["group"] if r["group"] != last else ""
        if last is not None and r["group"] != last:
            lines.append(r"\addlinespace")
        lines.append(f"{group} & {r['label']} & {r['B_given_A']:.2f} & {r['A_given_B']:.2f} \\\\")
        last = r["group"]
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_chain_table(path: Path) -> list[dict]:
    src = RUNS / "20261003_math_review_chain_diagnostics"
    rows = [
        ("spt2018_desi.json", "SPT 2018 + DESI"),
        ("sptd1_desi.json", "SPT D1 + DESI"),
        ("cmb2018_desi.json", "Full CMB (2018) + DESI"),
        ("cmbd1_desi.json", "Full CMB (D1) + DESI"),
    ]
    out = []
    lines = [
        r"\begin{tabular}{@{}l r r r r r@{}}",
        r"\toprule",
        r"Archived single chain & \multicolumn{3}{c}{empirical 95th percentile [eV]} & split $\hat R$ & ESS proxy \\",
        r"\cmidrule(lr){2-4}",
        r" & all & first half & second half & & \\",
        r"\midrule",
    ]
    for fname, label in rows:
        d = json.loads((src / fname).read_text(encoding="utf-8"))
        rec = {
            "label": label,
            "p95": d["mnu_p95_upper"],
            "p95_first_half": d["mnu_p95_upper_first_half"],
            "p95_second_half": d["mnu_p95_upper_second_half"],
            "rhat": d["mnu_split_rhat"],
            "ess": d["mnu_ess"],
            "n_chains": d["n_chains"],
        }
        out.append(rec)
        lines.append(
            f"{label} & {rec['p95']:.3f} & {rec['p95_first_half']:.3f} & {rec['p95_second_half']:.3f}"
            f" & {rec['rhat']:.2f} & {rec['ess']:.1f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--figdir", default=str(ROOT / "paper" / "figures"))
    ap.add_argument("--tabdir", default=str(ROOT / "paper" / "tables"))
    args = ap.parse_args()
    figdir, tabdir = Path(args.figdir), Path(args.tabdir)
    figdir.mkdir(parents=True, exist_ok=True)
    tabdir.mkdir(parents=True, exist_ok=True)

    record = {"toy": fig_toy(figdir / "fig_toy_boundary.pdf")}
    rows = audit_values()
    fig_audit(figdir / "fig_audit_totals.pdf", rows)
    record["audit_rows"] = rows
    record["localization"] = fig_localization(figdir / "fig_localization.pdf")
    fig_schema(figdir / "fig_audit_schema.pdf")
    write_audit_table(tabdir / "tab_audit_summary.tex", rows)
    record["chains"] = write_chain_table(tabdir / "tab_archived_chains.tex")
    (figdir / "figure_sources.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
