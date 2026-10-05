import TruncGaussProof.GaussianQuantile

open TruncGaussProof ProbabilityTheory MeasureTheory

-- A negative mean and a boundary density mode still give a positive p95.
example : ∃! x : ℝ, 0 < x ∧ cdf (truncatedGaussianLaw (-2) 3) x = 19/20 :=
  truncatedGaussianLaw_existsUnique_quantile (-2) 3 (19/20)
    (by norm_num) (by norm_num) (by norm_num)

-- The existence theorem also covers positive and exactly zero means.
example : ∃! x : ℝ, 0 < x ∧ cdf (truncatedGaussianLaw 2 3) x = 1/2 :=
  truncatedGaussianLaw_existsUnique_quantile 2 3 (1/2)
    (by norm_num) (by norm_num) (by norm_num)

example : ∃! x : ℝ, 0 < x ∧ cdf (truncatedGaussianLaw 0 1) x = 1/2 :=
  truncatedGaussianLaw_existsUnique_quantile 0 1 (1/2)
    (by norm_num) (by norm_num) (by norm_num)

-- Continuity at the gate is compatible with a boundary density mode.
example (μ σ : ℝ) (hσ : 0 < σ) :
    ContinuousAt (cdf (truncatedGaussianLaw μ σ)) 0 :=
  (truncatedGaussianLaw_cdf_continuous μ σ hσ).continuousAt

-- Probability level one cannot be reached at a finite coordinate.
example (μ σ : ℝ) (hσ : 0 < σ) :
    ¬ ∃ x : ℝ, cdf (truncatedGaussianLaw μ σ) x = 1 := by
  rintro ⟨x, hx⟩
  have h := truncatedGaussianLaw_cdf_lt_one μ σ x hσ
  rw [hx] at h
  exact lt_irrefl _ h

-- Probability level zero has no positive coordinate.
example (μ σ : ℝ) (hσ : 0 < σ) :
    ¬ ∃ x : ℝ, 0 < x ∧ cdf (truncatedGaussianLaw μ σ) x = 0 := by
  rintro ⟨x, hx, hzero⟩
  have h := truncatedGaussianLaw_cdf_strictMonoOn μ σ hσ
    (show (0 : ℝ) ∈ Set.Ici 0 by simp) (le_of_lt hx) hx
  rw [truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _), hzero] at h
  exact lt_irrefl _ h

-- Extending uniqueness to q=0 across the full real line would be false.
example (μ σ : ℝ) (hσ : 0 < σ) :
    cdf (truncatedGaussianLaw μ σ) (-1) = cdf (truncatedGaussianLaw μ σ) 0 ∧
      (-1 : ℝ) ≠ 0 := by
  rw [truncatedGaussianLaw_cdf_of_nonpos μ σ (-1) hσ (by norm_num),
    truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _)]
  norm_num

-- A CDF level below zero is impossible for any coordinate.
example (μ σ : ℝ) :
    ¬ ∃ x : ℝ, cdf (truncatedGaussianLaw μ σ) x = -1 := by
  rintro ⟨x, hx⟩
  have h := cdf_nonneg (truncatedGaussianLaw μ σ) x
  rw [hx] at h
  norm_num at h

-- Zero variance of an actual Gaussian gives a Dirac CDF, so interior
-- CDF levels need not be attained without the positive-width hypothesis.
example : ¬ ∃ x : ℝ, cdf (gaussianOffsetLaw 0 0) x = 19/20 := by
  rintro ⟨x, hx⟩
  by_cases h : 0 ≤ x
  · simp [gaussianOffsetLaw, gaussianReal_zero_var, cdf_eq_real, Measure.real, h] at hx
    norm_num at hx
  · simp [gaussianOffsetLaw, gaussianReal_zero_var, cdf_eq_real, Measure.real, h] at hx
    norm_num at hx
