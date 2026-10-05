#!/usr/bin/env python3
"""Verify exported profile endpoints against full native Gaussian accounting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from run_cross_audit_profiled import (
    _load_run, _make_lens_context, _localize_profiled_direction,
)
from sbt_spt_audit.candl_support import evaluate_loglike_from_base


def verify(audit_dir: Path):
    metrics = json.loads((audit_dir / "metrics.json").read_text())
    inputs = yaml.safe_load((audit_dir / "inputs.yaml").read_text())
    result = {}
    for direction, test_run in [("B_given_A", inputs["runB"]), ("A_given_B", inputs["runA"])]:
        ctx = _make_lens_context(*_load_run(Path(test_run)))
        stored = metrics[direction]
        train = stored["profiled_params_at_train"]
        best = stored["profiled_params_at_reference"]
        grid, groups, spectra, ledger = _localize_profiled_direction(ctx, train, best)
        native = -2.0 * (
            evaluate_loglike_from_base(ctx.like_obj, ctx.base_params, train)
            - evaluate_loglike_from_base(ctx.like_obj, ctx.base_params, best))
        reconstructed = (ledger["deltaQ_heatmap"] + ledger["unlocalized_deltaQ"]
                         + ledger["delta_prior_penalty"] + ledger["delta_covariance_normalization"])
        if not np.isclose(native, stored["delta_chi2_profiled"], rtol=1e-10, atol=1e-7):
            raise ValueError(f"{direction}: stored endpoints do not reproduce stored likelihood difference.")
        if not np.isclose(native, reconstructed, rtol=1e-10, atol=1e-7):
            raise ValueError(f"{direction}: independent accounting does not reconstruct native likelihood difference.")
        result[direction] = {"native_delta_chi2": native,
                             "reconstructed_delta_chi2": reconstructed,
                             "accounting": ledger, "top_groups": groups,
                             "deltaQ_by_spec_ell": grid, "spectra": spectra}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit_dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.audit_dir.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Verified both directions and native accounting: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
