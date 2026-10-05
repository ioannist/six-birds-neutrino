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
  simp [truncatedDensity, Set.indicator_of_notMem (show x ∉ Set.Ici (0 : ℝ) by
    exact not_le.mpr hx)]

/-- A singleton, including the boundary point zero, has zero probability mass.
This states no claim about mass in a positive-width interval near the gate. -/
theorem truncatedGaussianLaw_singleton (μ σ x : ℝ) :
    truncatedGaussianLaw μ σ {x} = 0 := by
  exact truncatedGaussianLaw_absolutelyContinuous μ σ (measure_singleton x)

end TruncGaussProof
