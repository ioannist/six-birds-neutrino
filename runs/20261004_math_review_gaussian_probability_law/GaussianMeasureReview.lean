import TruncGaussProof.GaussianMeasure

open MeasureTheory TruncGaussProof

-- Total mass is derived for every mean and positive standard deviation.
example (μ σ : ℝ) (hσ : 0 < σ) : truncatedGaussianLaw μ σ Set.univ = 1 := by
  exact (truncatedGaussianLaw_isProbability μ σ hσ).measure_univ

-- The actual law is supported on the physical half-line.
example (μ σ : ℝ) : (truncatedGaussianLaw μ σ).real (Set.Iio 0) = 0 := by
  simp [Measure.real, truncatedGaussianLaw_negative_halfline]

-- A positive density at the boundary still gives zero singleton probability.
example (μ σ : ℝ) (hσ : 0 < σ) : 0 < truncatedDensity μ σ 0 := by
  simp only [truncatedDensity, Set.indicator_of_mem (show (0 : ℝ) ∈ Set.Ici 0 by simp)]
  exact mul_pos (inv_pos.mpr (truncatedNormalizer_pos μ σ hσ)) (Real.exp_pos _)

example (μ σ : ℝ) : (truncatedGaussianLaw μ σ).real {0} = 0 := by
  simp [Measure.real, truncatedGaussianLaw_singleton]

-- For a negative mean the boundary is a density mode, not an atom.
example (μ σ : ℝ) (hμ : μ ≤ 0) (hσ : 0 < σ) :
    (∀ x : ℝ, 0 ≤ x → truncatedDensity μ σ x ≤ truncatedDensity μ σ 0) ∧
      truncatedGaussianLaw μ σ {0} = 0 := by
  constructor
  · simpa [mode, max_eq_left hμ] using (truncatedDensity_unique_mode μ σ hσ).1
  · exact truncatedGaussianLaw_singleton μ σ 0

-- Positive-width boundary mass is not replaced by the singleton readout.
example (μ σ ε : ℝ) (hσ : 0 < σ) (hε : 0 < ε) :
    ¬truncatedGaussianLaw μ σ (Set.Ioc 0 ε) = 0 := by
  exact ne_of_gt (truncatedGaussianLaw_boundary_interval_pos μ σ ε hσ hε)

-- Extending the probability statement to sigma=0 would be false: the
-- integral-derived density uses the totalized undefined integral zero.
example : ¬IsProbabilityMeasure (truncatedGaussianLaw 0 0) := by
  have hn : truncatedNormalizer 0 0 = 0 := by
    simp [truncatedNormalizer, unnorm, Measure.real, Real.volume_Ici]
  have hz : truncatedGaussianLaw 0 0 = 0 := by
    simp [truncatedGaussianLaw, truncatedDensity, hn]
  intro h
  have hmass := h.measure_univ
  simp [hz] at hmass

-- An actual zero-variance Gaussian is a Dirac atom and is outside the
-- positive-width density construction.
example : (ProbabilityTheory.gaussianReal 0 0) {0} = 1 := by
  simp [ProbabilityTheory.gaussianReal_zero_var]

-- The no-atom statement is specific to an absolutely continuous law.
example (x : ℝ) : Measure.dirac x {x} ≠ 0 := by simp

-- Frequency of a boundary mode over random constraint offsets is a different
-- probability space from posterior mass exactly at zero.
example :
    0 < (gaussianOffsetLaw 0 1).real (standardDeviationBoundaryEvent 1 1 0) ∧
      truncatedGaussianLaw 0 1 {0} = 0 := by
  constructor
  · rw [standardDeviationBoundaryGaussianProbability_zero 1 1 0 1
      (by norm_num) (by norm_num) (by norm_num)]
    simp only [zero_div]
    have hn := truncatedNormalizer_pos 0 1 (by norm_num)
    rw [truncatedNormalizer_eq_cdf 0 1 (by norm_num)] at hn
    simp only [one_mul, zero_div] at hn
    by_contra h
    have hnonpos : standardNormalCDF 0 ≤ 0 := le_of_not_gt h
    have hprod := mul_nonpos_of_nonneg_of_nonpos (Real.sqrt_nonneg (2 * Real.pi)) hnonpos
    exact (not_lt_of_ge hprod) hn
  · exact truncatedGaussianLaw_singleton 0 1 0
