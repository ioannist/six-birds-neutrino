import TruncGaussProof

open TruncGaussProof MeasureTheory ProbabilityTheory

example : (gaussianOffsetLaw 0 1).real (Set.Ici 0) = standardNormalCDF 0 := by
  simpa using gaussian_physicalGate_probability 0 1 (by norm_num)

example : truncatedNormalizer (-2) 3 = 3 * Real.sqrt (2 * Real.pi) * standardNormalCDF (-2/3) := by
  exact truncatedNormalizer_eq_cdf (-2) 3 (by norm_num)

example : gaussianPDFReal (-2) ⟨(3 : ℝ)^2, sq_nonneg 3⟩ 0 =
    (3 * Real.sqrt (2 * Real.pi))⁻¹ * Real.exp (-(2/9)) := by
  rw [gaussianPDFReal_eq_scaled_unnorm (-2) 3 0 (by norm_num)]
  norm_num [unnorm]

example (μ : ℝ) : truncatedDensity μ 3 (-1) = 0 := by
  simp [truncatedDensity]

example (μ : ℝ) : 0 < truncatedDensity μ 3 0 := by
  simp only [truncatedDensity, Set.indicator_of_mem (show (0 : ℝ) ∈ Set.Ici 0 by simp)]
  exact mul_pos (inv_pos.mpr (truncatedNormalizer_pos μ 3 (by norm_num))) (Real.exp_pos _)

-- The kernel is unchanged at negative sigma, while a signed scale is not a normalizer.
example : 0 < truncatedNormalizer 0 (-1) := by
  have h : truncatedNormalizer 0 (-1) = truncatedNormalizer 0 1 := by
    unfold truncatedNormalizer
    congr 1
    ext x
    norm_num [unnorm]
  rw [h]
  exact truncatedNormalizer_pos 0 1 (by norm_num)

-- A zero-width totalized Bochner integral does not yield a normalized density.
example : (∫ x, truncatedDensity 0 0 x) = 0 := by
  have hn : truncatedNormalizer 0 0 = 0 := by
    simp [truncatedNormalizer, unnorm, Measure.real, Real.volume_Ici]
  simp [truncatedDensity, hn]

-- The positive-sigma physical-gate CDF bridge cannot be extended to a zero-variance atom.
example : (gaussianOffsetLaw 0 0).real (Set.Ici 0) = 1 := by
  simp [gaussianOffsetLaw, Measure.real, gaussianReal_zero_var]

example : standardNormalCDF 0 < 1 := by
  exact lt_of_lt_of_le (standardNormalCDF_strictMono (show (0 : ℝ) < 1 by norm_num))
    (cdf_le_one (gaussianReal 0 1) 1)
