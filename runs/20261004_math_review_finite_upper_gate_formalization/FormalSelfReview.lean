import TruncGaussProof

open MeasureTheory ProbabilityTheory TruncGaussProof

-- Actual probability law for any real mean, positive width and positive cap.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    IsProbabilityMeasure (upperConditionedLaw (truncatedGaussianLaw μ σ) U) :=
  upperConditionedGaussian_isProbability μ σ U hσ hU

-- The quantitative tail is mass strictly beyond U, not mass at or beyond U.
example (ν : Measure ℝ) [IsProbabilityMeasure ν] (U : ℝ) :
    ν.real (Set.Ioi U) = 1 - cdf ν U := upperGate_tail_probability ν U

-- The generic statement remains valid for probability laws with atoms.
example (x : ℝ) :
    cdf (upperConditionedLaw (Measure.dirac (0 : ℝ)) 0) x =
      cdf (Measure.dirac (0 : ℝ)) x := by
  have hF : cdf (Measure.dirac (0 : ℝ)) 0 = 1 := by
    rw [cdf_eq_real]
    simp [Measure.real]
  have h := upperConditionedLaw_cdf_error (Measure.dirac (0 : ℝ)) 0 x
    (by rw [hF]; norm_num)
  rw [hF] at h
  linarith

-- This finite-prior example supplies quantile existence, not its numerical value.
example (μ σ : ℝ) (hσ : 0 < σ) :
    ∃! x : ℝ, 0 < x ∧ x < 5 ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) 5) x = (95 : ℝ) / 100 := by
  exact upperConditionedGaussian_existsUnique_quantile μ σ 5 ((95 : ℝ) / 100)
    hσ (by norm_num) (by norm_num) (by norm_num)

-- The retained-probability factor is derived for an actual capped Gaussian.
example (μ σ U x q : ℝ) (hσ : 0 < σ) (hU : 0 < U) (hx : x ≤ U) :
    cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) x = q ↔
      cdf (truncatedGaussianLaw μ σ) x = q * cdf (truncatedGaussianLaw μ σ) U := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  exact upperConditionedLaw_quantile_level _ U x q
    (truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU) hx

-- The CDF error bound is attained; it cannot be replaced by zero for every cap.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    0 < cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) U -
      cdf (truncatedGaussianLaw μ σ) U := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  rw [upperConditionedLaw_cdf_error_at_gate _ U
    (truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU)]
  exact sub_pos.mpr (truncatedGaussianLaw_cdf_lt_one μ σ U hσ)

-- At level one, U and U+1 both solve the CDF equation: global uniqueness fails.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) U = 1 ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) (U + 1) = 1 := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hFU := truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU
  constructor
  · rw [upperConditionedLaw_cdf _ U U hFU, min_self, div_self (ne_of_gt hFU)]
  · rw [upperConditionedLaw_cdf _ U (U+1) hFU,
      min_eq_right (show U ≤ U+1 by linarith), div_self (ne_of_gt hFU)]

-- At level zero, every negative threshold and the boundary give zero CDF.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) (-1) = 0 ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) 0 = 0 := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hFU := truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU
  constructor
  · rw [upperConditionedLaw_cdf _ U (-1) hFU,
      min_eq_left (show (-1:ℝ) ≤ U by linarith),
      truncatedGaussianLaw_cdf_of_nonpos μ σ (-1) hσ (by norm_num), zero_div]
  · rw [upperConditionedLaw_cdf _ U 0 hFU, min_eq_left (le_of_lt hU),
      truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _), zero_div]

-- A nonpositive cap retains no mass from a positive-width physical-gated law.
-- Totalized conditioning then gives the zero measure, not a probability law.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : U ≤ 0) :
    upperConditionedLaw (truncatedGaussianLaw μ σ) U = 0 := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hz : (truncatedGaussianLaw μ σ).real (Set.Iic U) = 0 := by
    rw [← cdf_eq_real]
    exact truncatedGaussianLaw_cdf_of_nonpos μ σ U hσ hU
  have hm : truncatedGaussianLaw μ σ (Set.Iic U) = 0 :=
    (measureReal_eq_zero_iff).mp hz
  exact cond_eq_zero_of_meas_eq_zero hm

-- The uniform error guarantee is only on probability levels. It supplies no
-- coordinate quantile bound without a modulus or local density information.
example (ν : Measure ℝ) [IsProbabilityMeasure ν] (U x : ℝ) (hU : 0 < cdf ν U) :
    |cdf (upperConditionedLaw ν U) x - cdf ν x| ≤ ν.real (Set.Ioi U) := by
  have h := upperConditionedLaw_cdf_error ν U x hU
  rw [abs_of_nonneg h.1, upperGate_tail_probability]
  exact h.2
