import TruncGaussProof.GaussianMeasure

namespace TruncGaussProof

open MeasureTheory ProbabilityTheory

/-- The constructed density law is the actual Gaussian restricted to the
physical gate and rescaled by its derived gate probability. -/
theorem truncatedGaussianLaw_eq_smul_restrict (μ σ : ℝ) (hσ : 0 < σ) :
    truncatedGaussianLaw μ σ =
      ENNReal.ofReal ((standardNormalCDF (μ / σ))⁻¹) •
        (gaussianOffsetLaw (-μ) σ).restrict (Set.Ici 0) := by
  have hv : (⟨σ ^ 2, sq_nonneg σ⟩ : NNReal) ≠ 0 := by
    intro h
    have : σ ^ 2 = 0 := congrArg (fun v : NNReal => (v : ℝ)) h
    nlinarith
  have hp : 0 < standardNormalCDF (μ / σ) := by
    have hn := truncatedNormalizer_pos μ σ hσ
    rw [truncatedNormalizer_eq_cdf μ σ hσ] at hn
    have hc : 0 < σ * Real.sqrt (2 * Real.pi) := by positivity
    nlinarith
  have hf : (fun x => ENNReal.ofReal (truncatedDensity μ σ x)) =
      ENNReal.ofReal ((standardNormalCDF (μ / σ))⁻¹) •
        (Set.Ici (0 : ℝ)).indicator (gaussianPDF μ ⟨σ ^ 2, sq_nonneg σ⟩) := by
    ext x
    rw [truncatedDensity_eq_gaussianPDF_div_cdf μ σ hσ]
    by_cases hx : x ∈ Set.Ici (0 : ℝ)
    · simp only [Set.indicator_of_mem hx, Pi.smul_apply, smul_eq_mul,
        gaussianPDF, div_eq_mul_inv]
      rw [ENNReal.ofReal_mul (gaussianPDFReal_nonneg μ _ x)]
      rw [mul_comm]
    · simp [Set.indicator_of_notMem hx]
  rw [truncatedGaussianLaw, hf, withDensity_smul' _ _ ENNReal.ofReal_ne_top,
    withDensity_indicator measurableSet_Ici]
  simp only [gaussianOffsetLaw, neg_neg, gaussianReal_of_var_ne_zero _ hv]

/-- Read out the conditional probability on any measurable set from the
constructed density law; the normalizing denominator is not a premise. -/
theorem truncatedGaussianLaw_real_apply (μ σ : ℝ) (hσ : 0 < σ)
    (s : Set ℝ) (hs : MeasurableSet s) :
    (truncatedGaussianLaw μ σ).real s =
      (gaussianOffsetLaw (-μ) σ).real (s ∩ Set.Ici 0) /
        standardNormalCDF (μ / σ) := by
  have hp : 0 < standardNormalCDF (μ / σ) := by
    have hn := truncatedNormalizer_pos μ σ hσ
    rw [truncatedNormalizer_eq_cdf μ σ hσ] at hn
    have hc : 0 < σ * Real.sqrt (2 * Real.pi) := by positivity
    nlinarith
  rw [truncatedGaussianLaw_eq_smul_restrict μ σ hσ,
    measureReal_ennreal_smul_apply, measureReal_restrict_apply hs,
    ENNReal.toReal_ofReal (le_of_lt (inv_pos.mpr hp))]
  simp [div_eq_mul_inv, mul_comm]

end TruncGaussProof
