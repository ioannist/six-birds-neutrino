from __future__ import annotations

from typing import Protocol


class Likelihood(Protocol):
    """Minimal likelihood protocol for dataset-agnostic audit code.

    Implementations must provide ``loglike``.
    ``loglike_blocks`` is an optional richer interface used when block-level
    held-out diagnostics are available.
    """

    def loglike(self, theta: dict[str, float]) -> float:
        ...

    def loglike_blocks(self, theta: dict[str, float]) -> dict[str, float]:
        ...
