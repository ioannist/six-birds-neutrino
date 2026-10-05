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
  rw [restrict_withDensity measurableSet_Ici]

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

/-- Exact probability of a positive-side interval under the constructed law. -/
theorem truncatedGaussianLaw_Ioc_cdf (μ σ a b : ℝ) (hσ : 0 < σ)
    (ha : 0 ≤ a) (hab : a ≤ b) :
    (truncatedGaussianLaw μ σ).real (Set.Ioc a b) =
      (standardNormalCDF ((b - μ) / σ) - standardNormalCDF ((a - μ) / σ)) /
        standardNormalCDF (μ / σ) := by
  letI : IsProbabilityMeasure (gaussianOffsetLaw (-μ) σ) := by
    dsimp [gaussianOffsetLaw]
    infer_instance
  rw [truncatedGaussianLaw_real_apply μ σ hσ _ measurableSet_Ioc]
  have hset : Set.Ioc a b ∩ Set.Ici (0 : ℝ) = Set.Ioc a b := by
    apply Set.inter_eq_left.mpr
    intro x hx
    exact le_trans ha (le_of_lt hx.1)
  rw [hset, ← Set.Iic_diff_Iic]
  rw [measureReal_diff (Set.Iic_subset_Iic.mpr hab) measurableSet_Iic]
  rw [gaussianOffsetLaw_Iic_cdf (-μ) σ b hσ,
    gaussianOffsetLaw_Iic_cdf (-μ) σ a hσ]
  simp only [sub_eq_add_neg]

/-- The CDF of the constructed law on its physical half-line, with the
normalizing denominator derived from the actual Gaussian gate probability. -/
theorem truncatedGaussianLaw_cdf_of_nonneg (μ σ x : ℝ) (hσ : 0 < σ)
    (hx : 0 ≤ x) :
    cdf (truncatedGaussianLaw μ σ) x =
      (standardNormalCDF ((x - μ) / σ) - standardNormalCDF (-μ / σ)) /
        standardNormalCDF (μ / σ) := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hz : (truncatedGaussianLaw μ σ).real (Set.Iic 0) = 0 := by
    have hn := measure_union_le (Set.Iio (0 : ℝ)) ({0} : Set ℝ)
      (μ := truncatedGaussianLaw μ σ)
    rw [Set.Iio_union_right, truncatedGaussianLaw_negative_halfline,
      truncatedGaussianLaw_singleton, zero_add] at hn
    have he : truncatedGaussianLaw μ σ (Set.Iic 0) = 0 := le_antisymm hn (zero_le _)
    simp [Measure.real, he]
  have hi : (truncatedGaussianLaw μ σ).real (Set.Ioc 0 x) =
      (truncatedGaussianLaw μ σ).real (Set.Iic x) := by
    rw [← Set.Iic_diff_Iic,
      measureReal_diff (Set.Iic_subset_Iic.mpr hx) measurableSet_Iic, hz, sub_zero]
  rw [cdf_eq_real, ← hi, truncatedGaussianLaw_Ioc_cdf μ σ 0 x hσ (le_refl _) hx]
  simp

/-- Every nonpositive threshold has CDF zero, including the boundary itself. -/
theorem truncatedGaussianLaw_cdf_of_nonpos (μ σ x : ℝ) (hσ : 0 < σ)
    (hx : x ≤ 0) : cdf (truncatedGaussianLaw μ σ) x = 0 := by
  have hz := truncatedGaussianLaw_cdf_of_nonneg μ σ 0 hσ (le_refl _)
  simp only [zero_sub, sub_self, zero_div] at hz
  have hu := monotone_cdf (truncatedGaussianLaw μ σ) hx
  have hl := cdf_nonneg (truncatedGaussianLaw μ σ) x
  rw [hz] at hu
  exact le_antisymm hu hl

/-- The exact CDF is strictly increasing on the physical half-line even
when the density mode lies at its boundary. -/
theorem truncatedGaussianLaw_cdf_strictMonoOn (μ σ : ℝ) (hσ : 0 < σ) :
    StrictMonoOn (cdf (truncatedGaussianLaw μ σ)) (Set.Ici 0) := by
  have hp : 0 < standardNormalCDF (μ / σ) := by
    have hn := truncatedNormalizer_pos μ σ hσ
    rw [truncatedNormalizer_eq_cdf μ σ hσ] at hn
    have hc : 0 < σ * Real.sqrt (2 * Real.pi) := by positivity
    nlinarith
  intro x hx y hy hxy
  rw [truncatedGaussianLaw_cdf_of_nonneg μ σ x hσ hx,
    truncatedGaussianLaw_cdf_of_nonneg μ σ y hσ hy]
  apply (div_lt_div_iff_of_pos_right hp).mpr
  apply sub_lt_sub_right
  apply standardNormalCDF_strictMono
  exact (div_lt_div_iff_of_pos_right hσ).mpr (sub_lt_sub_right hxy μ)

end TruncGaussProof
