import TruncGaussProof.Normalization
import TruncGaussProof.GaussianSweep

namespace TruncGaussProof

open MeasureTheory ProbabilityTheory

/-- Reflection returns the actual probability of the physical gate to the
standard normal CDF, without assuming a tail identity. -/
theorem gaussian_physicalGate_probability (μ σ : ℝ) (hσ : 0 < σ) :
    (gaussianOffsetLaw (-μ) σ).real (Set.Ici 0) = standardNormalCDF (μ / σ) := by
  have hlaw : gaussianOffsetLaw (-μ) σ = (gaussianOffsetLaw μ σ).map (fun z => -z) := by
    simp [gaussianOffsetLaw, gaussianReal_map_neg]
  have hset : (fun z : ℝ => -z) ⁻¹' Set.Ici 0 = Set.Iic 0 := by
    ext z
    simp
  rw [hlaw]
  unfold Measure.real
  rw [Measure.map_apply (by fun_prop) measurableSet_Ici, hset]
  change (gaussianOffsetLaw μ σ).real (Set.Iic 0) = _
  simpa using gaussianOffsetLaw_Iic_cdf μ σ 0 hσ

/-- Identify the original kernel with the actual Gaussian probability density,
including the positive standard-deviation scale. -/
theorem gaussianPDFReal_eq_scaled_unnorm (μ σ x : ℝ) (hσ : 0 < σ) :
    gaussianPDFReal μ ⟨σ ^ 2, sq_nonneg σ⟩ x =
      (σ * Real.sqrt (2 * Real.pi))⁻¹ * unnorm μ σ x := by
  have hsqrt : Real.sqrt (2 * Real.pi * σ ^ 2) = σ * Real.sqrt (2 * Real.pi) := by
    rw [Real.sqrt_mul (by positivity), Real.sqrt_sq_eq_abs, abs_of_pos hσ]
    ring
  simp only [gaussianPDFReal, NNReal.coe_mk, hsqrt, unnorm]
  rw [neg_div]

/-- Closed CDF formula for the previously integral-derived normalizer. -/
theorem truncatedNormalizer_eq_cdf (μ σ : ℝ) (hσ : 0 < σ) :
    truncatedNormalizer μ σ = σ * Real.sqrt (2 * Real.pi) * standardNormalCDF (μ / σ) := by
  have hv : (⟨σ ^ 2, sq_nonneg σ⟩ : NNReal) ≠ 0 := by
    intro h
    have : σ ^ 2 = 0 := congrArg (fun v : NNReal => (v : ℝ)) h
    nlinarith
  have hi : 0 ≤ ∫ x in Set.Ici (0 : ℝ), gaussianPDFReal μ ⟨σ ^ 2, sq_nonneg σ⟩ x := by
    exact integral_nonneg (fun x => gaussianPDFReal_nonneg μ _ x)
  have hcdf : standardNormalCDF (μ / σ) =
      (σ * Real.sqrt (2 * Real.pi))⁻¹ * truncatedNormalizer μ σ := by
    rw [← gaussian_physicalGate_probability μ σ hσ]
    simp only [gaussianOffsetLaw, neg_neg, Measure.real]
    rw [gaussianReal_apply_eq_integral μ hv, ENNReal.toReal_ofReal hi]
    simp_rw [gaussianPDFReal_eq_scaled_unnorm μ σ _ hσ]
    rw [integral_const_mul]
    rfl
  have hn : σ * Real.sqrt (2 * Real.pi) ≠ 0 := ne_of_gt (by positivity)
  rw [hcdf]
  field_simp

/-- The exact density matches the usual gated Gaussian-PDF/CDF expression.
This is an identity of real functions, not a floating-point approximation bound. -/
theorem truncatedDensity_eq_gaussianPDF_div_cdf (μ σ : ℝ) (hσ : 0 < σ) :
    truncatedDensity μ σ = (Set.Ici (0 : ℝ)).indicator
      (fun x => gaussianPDFReal μ ⟨σ ^ 2, sq_nonneg σ⟩ x / standardNormalCDF (μ / σ)) := by
  ext x
  by_cases hx : x ∈ Set.Ici (0 : ℝ)
  · simp only [truncatedDensity, Set.indicator_of_mem hx,
      truncatedNormalizer_eq_cdf μ σ hσ, gaussianPDFReal_eq_scaled_unnorm μ σ x hσ]
    simp [div_eq_mul_inv, mul_inv_rev, mul_assoc, mul_comm, mul_left_comm]
  · simp [truncatedDensity, Set.indicator_of_notMem hx]

end TruncGaussProof
