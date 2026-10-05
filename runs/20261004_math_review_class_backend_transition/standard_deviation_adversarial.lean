import TruncGaussProof

open TruncGaussProof

-- A positive first mean gives an offset admitted only after tightening.
example : (-3 / 2 : ℝ) ∉ standardDeviationBoundaryEvent 1 1 1 := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 1 1 (by norm_num) (by norm_num)]
  norm_num

example : (-3 / 2 : ℝ) ∈ standardDeviationBoundaryEvent 1 (1 / 2) 1 := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 (1 / 2) 1 (by norm_num) (by norm_num)]
  norm_num

-- A negative first mean reverses that direction.
example : (3 / 2 : ℝ) ∈ standardDeviationBoundaryEvent 1 1 (-1) := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 1 (-1) (by norm_num) (by norm_num)]
  norm_num

example : (3 / 2 : ℝ) ∉ standardDeviationBoundaryEvent 1 (1 / 2) (-1) := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 (1 / 2) (-1) (by norm_num) (by norm_num)]
  norm_num

-- At zero mean the closed boundary includes exactly zero and all smaller offsets.
example : standardDeviationBoundaryEvent 1 (1 / 2) 0 = Set.Iic 0 := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 (1 / 2) 0 (by norm_num) (by norm_num)]
  norm_num

-- A point mass at 10 would give zero probability at both deviations, so the
-- exported law cannot be strengthened to strictness for every offset measure.
example : (10 : ℝ) ∉ standardDeviationBoundaryEvent 1 1 1 := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 1 1 (by norm_num) (by norm_num)]
  norm_num

example : (10 : ℝ) ∉ standardDeviationBoundaryEvent 1 (1 / 2) 1 := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 (1 / 2) 1 (by norm_num) (by norm_num)]
  norm_num
