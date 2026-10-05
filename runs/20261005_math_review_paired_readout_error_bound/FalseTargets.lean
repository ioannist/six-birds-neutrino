import TruncGaussProof

open TruncGaussProof

-- The actual sum-bound mechanism accepts the sharp, positive-endpoint example.
example : |tighteningReadout 3 1 - tighteningReadout 2 2| ≤ (1 : ℝ) + 1 := by
  exact tighteningReadout_error_le 2 2 3 1 1 1 (by norm_num) (by norm_num)

-- Maximum individual error is too small for the same example.
example : ¬ (|tighteningReadout 3 1 - tighteningReadout 2 2| ≤ max (1 : ℝ) 1) := by
  norm_num [tighteningReadout]

-- A quadrature bound also fails for deterministic coordinate errors. This does
-- not refute variance addition under its separate independence hypotheses.
example : ¬ (|tighteningReadout 3 1 - tighteningReadout 2 2| ≤
    Real.sqrt ((1 : ℝ) ^ 2 + 1 ^ 2)) := by
  intro h
  norm_num [tighteningReadout] at h
  have hs : (Real.sqrt (2 : ℝ)) ^ 2 = 2 := Real.sq_sqrt (by norm_num)
  have hn := Real.sqrt_nonneg (2 : ℝ)
  nlinarith

-- Equality between the measured shift and summed errors does not certify a
-- strictly positive true shift; the strict margin in the theorem is necessary.
example : ¬ (∀ trueA trueB estimateA estimateB εA εB : ℝ,
    |estimateA - trueA| ≤ εA → |estimateB - trueB| ≤ εB →
    εA + εB ≤ tighteningReadout estimateA estimateB →
    0 < tighteningReadout trueA trueB) := by
  intro h
  have bad := h 2 2 3 1 1 1 (by norm_num) (by norm_num)
    (by norm_num [tighteningReadout])
  norm_num [tighteningReadout] at bad
