#!/usr/bin/env python3
from __future__ import annotations

from sbt_spt_audit.metrics import (
    blockwise_delta_chi2_from_loglike_blocks,
    delta_chi2_from_loglike,
)


def main() -> None:
    delta = delta_chi2_from_loglike(loglike_test_at_train=-10.0, loglike_test_at_test=-5.0)
    print(f"delta_chi2 example: {delta:.3f}")

    block_result = blockwise_delta_chi2_from_loglike_blocks(
        {"sn": -4.0, "bao": -8.0},
        {"sn": -3.0, "bao": -6.0},
    )
    print(f"blockwise total: {block_result['total']:.3f}")
    print(f"blockwise by_block: {block_result['by_block']}")


if __name__ == "__main__":
    main()
