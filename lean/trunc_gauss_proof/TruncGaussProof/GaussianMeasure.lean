import TruncGaussProof.GaussianNormalization

namespace TruncGaussProof

open MeasureTheory

/-- The probability law built from the integral-normalized gated density.
Normalization as a probability measure is established below for positive sigma. -/
noncomputable def truncatedGaussianLaw (μ σ : ℝ) : Measure ℝ :=
  volume.withDensity (fun x => ENNReal.ofReal (truncatedDensity μ σ x))

/-- This is an actual probability law, with total mass derived from the
Lebesgue integral of the constructed density rather than assumed. -/
theorem truncatedGaussianLaw_isProbability (μ σ : ℝ) (hσ : 0 < σ) :
    IsProbabilityMeasure (truncatedGaussianLaw μ σ) := by
  constructor
  rw [truncatedGaussianLaw, withDensity_apply _ MeasurableSet.univ, Measure.restrict_univ]
  rw [← ofReal_integral_eq_lintegral_ofReal (truncatedDensity_integrable μ σ hσ)
    (Filter.Eventually.of_forall (fun x => truncatedDensity_nonneg μ σ x hσ))]
  rw [truncatedDensity_integral_eq_one μ σ hσ]
  simp

/-- The constructed law is absolutely continuous; a boundary density mode
does not introduce a singular mass. -/
theorem truncatedGaussianLaw_absolutelyContinuous (μ σ : ℝ) :
    truncatedGaussianLaw μ σ ≪ volume := by
  exact withDensity_absolutelyContinuous _ _

/-- Every negative coordinate lies outside the physical support. -/
theorem truncatedGaussianLaw_negative_halfline (μ σ : ℝ) :
    truncatedGaussianLaw μ σ (Set.Iio 0) = 0 := by
  rw [truncatedGaussianLaw, withDensity_apply _ measurableSet_Iio]
  apply lintegral_eq_zero_of_ae_eq_zero
  filter_upwards [ae_restrict_mem measurableSet_Iio] with x hx
  have hxlt : x < (0 : ℝ) := hx
  have hxnot : x ∉ Set.Ici (0 : ℝ) := by
    simpa only [Set.mem_Ici] using (not_le.mpr hxlt)
  simp [truncatedDensity, Set.indicator_of_notMem hxnot]

/-- A singleton, including the boundary point zero, has zero probability mass.
This states no claim about mass in a positive-width interval near the gate. -/
theorem truncatedGaussianLaw_singleton (μ σ x : ℝ) :
    truncatedGaussianLaw μ σ {x} = 0 := by
  exact truncatedGaussianLaw_absolutelyContinuous μ σ (measure_singleton x)

/-- Every positive-width interval next to the physical gate has positive
probability, even though the boundary singleton itself has zero mass. -/
theorem truncatedGaussianLaw_boundary_interval_pos (μ σ ε : ℝ)
    (hσ : 0 < σ) (hε : 0 < ε) :
    0 < truncatedGaussianLaw μ σ (Set.Ioc 0 ε) := by
  have hp : ∀ x : ℝ, 0 ≤ x → 0 < truncatedDensity μ σ x := by
    intro x hx
    rw [truncatedDensity, Set.indicator_of_mem (show x ∈ Set.Ici (0 : ℝ) from hx)]
    exact mul_pos (inv_pos.mpr (truncatedNormalizer_pos μ σ hσ)) (Real.exp_pos _)
  have hs : Function.support (truncatedDensity μ σ) ∩ Set.Ioc 0 ε = Set.Ioc 0 ε := by
    ext x
    constructor
    · exact fun hx => hx.2
    · intro hx
      exact ⟨ne_of_gt (hp x (le_of_lt hx.1)), hx⟩
  have hi : 0 < ∫ x in Set.Ioc 0 ε, truncatedDensity μ σ x := by
    apply (setIntegral_pos_iff_support_of_nonneg_ae
      (Filter.Eventually.of_forall (fun x => truncatedDensity_nonneg μ σ x hσ))
      (truncatedDensity_integrable μ σ hσ).integrableOn).mpr
    rw [hs, Real.volume_Ioc]
    simpa using ENNReal.ofReal_pos.mpr hε
  rw [truncatedGaussianLaw, withDensity_apply _ measurableSet_Ioc]
  rw [← ofReal_integral_eq_lintegral_ofReal (truncatedDensity_integrable μ σ hσ).integrableOn
    (Filter.Eventually.of_forall (fun x => truncatedDensity_nonneg μ σ x hσ))]
  exact ENNReal.ofReal_pos.mpr hi

end TruncGaussProof
