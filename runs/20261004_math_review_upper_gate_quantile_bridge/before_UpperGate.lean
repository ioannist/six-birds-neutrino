import TruncGaussProof.GaussianQuantile
import Mathlib.Probability.ConditionalProbability

namespace TruncGaussProof

open MeasureTheory ProbabilityTheory

/-- Actual conditioning at a finite upper gate. The underlying law, including
any lower physical gate, is retained rather than replaced by a CDF surrogate. -/
noncomputable def upperConditionedLaw (ν : Measure ℝ) (U : ℝ) : Measure ℝ :=
  ProbabilityTheory.cond ν (Set.Iic U)

/-- The omitted tail is an actual event probability, including when there is
an atom at the upper gate: only mass strictly above the gate is omitted. -/
theorem upperGate_tail_probability (ν : Measure ℝ) [IsProbabilityMeasure ν] (U : ℝ) :
    ν.real (Set.Ioi U) = 1 - cdf ν U := by
  rw [← Set.compl_Iic, probReal_compl_eq_one_sub measurableSet_Iic, cdf_eq_real]

/-- A positive retained CDF supplies the nonzero normalization of the actual
restricted measure; probability normalization is not an assumed field. -/
theorem upperConditionedLaw_isProbability (ν : Measure ℝ) [IsProbabilityMeasure ν]
    (U : ℝ) (hU : 0 < cdf ν U) : IsProbabilityMeasure (upperConditionedLaw ν U) := by
  apply cond_isProbabilityMeasure
  apply (measureReal_ne_zero_iff).mp
  rw [← cdf_eq_real]
  exact ne_of_gt hU

/-- Exact CDF of the conditioned measure, valid with atoms as well as densities. -/
theorem upperConditionedLaw_cdf (ν : Measure ℝ) [IsProbabilityMeasure ν]
    (U x : ℝ) (hU : 0 < cdf ν U) :
    cdf (upperConditionedLaw ν U) x = cdf ν (min x U) / cdf ν U := by
  letI := upperConditionedLaw_isProbability ν U hU
  rw [cdf_eq_real, upperConditionedLaw, ProbabilityTheory.cond,
    measureReal_ennreal_smul_apply, measureReal_restrict_apply measurableSet_Iic,
    ENNReal.toReal_inv, Set.Iic_inter_Iic]
  change (ν.real (Set.Iic U))⁻¹ * ν.real (Set.Iic (min x U)) = _
  rw [← cdf_eq_real, ← cdf_eq_real]
  ring

/-- Conditioning can only raise the CDF and changes it by at most the omitted
tail probability. This is a probability-scale bound, not a coordinate error. -/
theorem upperConditionedLaw_cdf_error (ν : Measure ℝ) [IsProbabilityMeasure ν]
    (U x : ℝ) (hU : 0 < cdf ν U) :
    0 ≤ cdf (upperConditionedLaw ν U) x - cdf ν x ∧
      cdf (upperConditionedLaw ν U) x - cdf ν x ≤ 1 - cdf ν U := by
  have hF := cdf_nonneg ν x
  have hFU := cdf_le_one ν U
  rw [upperConditionedLaw_cdf ν U x hU]
  by_cases hx : x ≤ U
  · rw [min_eq_left hx]
    have hle := monotone_cdf ν hx
    constructor
    · apply sub_nonneg.mpr
      apply (le_div_iff₀ hU).mpr
      nlinarith
    · have hprod : 0 ≤ (cdf ν U - cdf ν x) * (1 - cdf ν U) :=
        mul_nonneg (sub_nonneg.mpr hle) (sub_nonneg.mpr hFU)
      apply (sub_le_iff_le_add).mpr
      apply (div_le_iff₀ hU).mpr
      nlinarith
  · rw [min_eq_right (le_of_not_ge hx), div_self (ne_of_gt hU)]
    constructor
    · exact sub_nonneg.mpr (cdf_le_one ν x)
    · have hle := monotone_cdf ν (le_of_not_ge hx)
      linarith

/-- The CDF-error bound is attained at the upper gate. -/
theorem upperConditionedLaw_cdf_error_at_gate (ν : Measure ℝ) [IsProbabilityMeasure ν]
    (U : ℝ) (hU : 0 < cdf ν U) :
    cdf (upperConditionedLaw ν U) U - cdf ν U = 1 - cdf ν U := by
  rw [upperConditionedLaw_cdf ν U U hU, min_self, div_self (ne_of_gt hU)]

/-- An interior coordinate's probability level is rescaled by the actual
retained mass; no inverse-CDF formula or numerical approximation is assumed. -/
theorem upperConditionedLaw_quantile_level (ν : Measure ℝ) [IsProbabilityMeasure ν]
    (U x q : ℝ) (hU : 0 < cdf ν U) (hx : x ≤ U) :
    cdf (upperConditionedLaw ν U) x = q ↔ cdf ν x = q * cdf ν U := by
  rw [upperConditionedLaw_cdf ν U x hU, min_eq_left hx]
  exact div_eq_iff (ne_of_gt hU)

/-- A positive-width gated Gaussian retains positive mass below every
positive finite upper gate. -/
theorem truncatedGaussianLaw_cdf_pos_at_upperGate (μ σ U : ℝ)
    (hσ : 0 < σ) (hU : 0 < U) : 0 < cdf (truncatedGaussianLaw μ σ) U := by
  have h := truncatedGaussianLaw_cdf_strictMonoOn μ σ hσ
    (show 0 ∈ Set.Ici (0 : ℝ) by change (0 : ℝ) ≤ 0; exact le_refl _)
    (show U ∈ Set.Ici (0 : ℝ) from le_of_lt hU) hU
  rw [truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _)] at h
  exact h

/-- The Gaussian with both lower physical and finite upper gates is a
probability measure, with both normalization steps derived. -/
theorem upperConditionedGaussian_isProbability (μ σ U : ℝ)
    (hσ : 0 < σ) (hU : 0 < U) :
    IsProbabilityMeasure (upperConditionedLaw (truncatedGaussianLaw μ σ) U) := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  exact upperConditionedLaw_isProbability _ U
    (truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU)

/-- Every interior probability level has one positive quantile strictly
below the finite upper gate, under the actual conditioned Gaussian law. -/
theorem upperConditionedGaussian_existsUnique_quantile (μ σ U q : ℝ)
    (hσ : 0 < σ) (hU : 0 < U) (hq0 : 0 < q) (hq1 : q < 1) :
    ∃! x : ℝ, 0 < x ∧ x < U ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) x = q := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hFU := truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU
  have hF1 := truncatedGaussianLaw_cdf_lt_one μ σ U hσ
  have hp0 : 0 < q * cdf (truncatedGaussianLaw μ σ) U := mul_pos hq0 hFU
  have hpU : q * cdf (truncatedGaussianLaw μ σ) U <
      cdf (truncatedGaussianLaw μ σ) U := by nlinarith
  obtain ⟨x, hx, huniq⟩ := truncatedGaussianLaw_existsUnique_quantile μ σ
    (q * cdf (truncatedGaussianLaw μ σ) U) hσ hp0 (lt_trans hpU hF1)
  have hxU : x < U := by
    by_contra h
    have hle := monotone_cdf (truncatedGaussianLaw μ σ) (le_of_not_gt h)
    rw [hx.2] at hle
    linarith
  refine ⟨x, ⟨hx.1, hxU, ?_⟩, ?_⟩
  · exact (upperConditionedLaw_quantile_level _ U x q hFU (le_of_lt hxU)).mpr hx.2
  · intro y hy
    apply huniq y
    exact ⟨hy.1, (upperConditionedLaw_quantile_level _ U y q hFU (le_of_lt hy.2.1)).mp hy.2.2⟩

end TruncGaussProof
