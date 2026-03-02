# MAP Pipeline Status (T06)

- Timestamp (UTC): `2026-02-11`
- Script implemented: `scripts/run_map.py`
- Configs exercised:
  - `configs/toy_lensA.yaml`
  - `configs/toy_lensB.yaml`

## Run bundles

- `runs/20260211_115444_728228_toy_lensA`
- `runs/20260211_115444_750542_toy_lensB`
- `runs/20260211_115444_756751_toy_lensA` (repeat for determinism check)

## Fit outcomes

- Toy lens A (run #1): `theta_hat = {x1: 0.0, x2: -0.060000005239512155}`, `chi2_best = 4.000000000000002`.
- Toy lens B: `theta_hat = {x1: 0.049999994387755105, x2: 0.149999993877551}`, `chi2_best = 4.425239490016526e-15`.
- Toy lens A (run #2): `theta_hat = {x1: 0.0, x2: -0.060000005239512155}`, `chi2_best = 4.000000000000002`.

## Determinism check

- Compared `theta_hat` between toy lens A run #1 and run #2.
- Max absolute per-parameter difference: `0.0`.
- Verdict: deterministic (exact match in this environment).

## SPT placeholder configs

- Added blocked placeholders:
  - `configs/spt2018_lcdm.yaml`
  - `configs/sptd1_lcdm.yaml`
- Both are marked `enabled: false`, `status: blocked`, and reference the T05 blocker run:
  - `runs/20260211_112049_candl_spt_probe`.
