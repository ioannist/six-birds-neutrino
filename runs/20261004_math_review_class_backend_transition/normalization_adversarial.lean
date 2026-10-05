import TruncGaussProof

open TruncGaussProof MeasureTheory

-- Both signs of the mean give an actually normalized density.
example : ∫ x, truncatedDensity (-2) 1 x = 1 :=
  truncatedDensity_integral_eq_one (-2) 1 (by norm_num)

example : ∫ x, truncatedDensity 3 1 x = 1 :=
  truncatedDensity_integral_eq_one 3 1 (by norm_num)

-- The explicit density is zero outside the physical gate and positive on it.
example : truncatedDensity (-2) 1 (-1) = 0 := by
  simp [truncatedDensity]

example : 0 < truncatedDensity (-2) 1 0 := by
  have h := inv_pos.mpr (truncatedNormalizer_pos (-2) 1 (by norm_num))
  have he : 0 < unnorm (-2) 1 0 := Real.exp_pos _
  simpa [truncatedDensity] using mul_pos h he

-- The negative-mean normalized density has its unique gated maximum at zero.
example : ∀ x : ℝ, 0 ≤ x →
    (truncatedDensity (-2) 1 x = truncatedDensity (-2) 1 0 ↔ x = 0) := by
  simpa [mode] using (truncatedDensity_unique_mode (-2) 1 (by norm_num)).2

-- Zero deviation is deliberately excluded. Real division by zero makes the
-- kernel constant one, whose Bochner integral on the infinite half-line is the
-- undefined-integral default zero, not a positive normalization constant.
example : truncatedNormalizer 1 0 = 0 := by
  simp [truncatedNormalizer, unnorm, Measure.real, Real.volume_Ici]

example : ∫ x, truncatedDensity 1 0 x = 0 := by
  have h : truncatedNormalizer 1 0 = 0 := by simp [truncatedNormalizer, unnorm, Measure.real, Real.volume_Ici]
  simp [truncatedDensity, h]
