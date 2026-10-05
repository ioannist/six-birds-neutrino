import TruncGaussProof.Mode

namespace TruncGaussProof

open MeasureTheory

theorem unnorm_integrable (μ σ : ℝ) (hσ : 0 < σ) :
    Integrable (unnorm μ σ) := by
  have h := (integrable_exp_neg_mul_sq (b := (2 * σ ^ 2)⁻¹) (by positivity)).comp_sub_right μ
  convert h using 1
  ext x
  unfold unnorm
  congr 1
  rw [div_eq_mul_inv]
  ring

/-- The actual Lebesgue integral on the physical half-line, not a supplied
normalization parameter or an assumed CDF formula. -/
noncomputable def truncatedNormalizer (μ σ : ℝ) : ℝ :=
  ∫ x in Set.Ici (0 : ℝ), unnorm μ σ x

theorem truncatedNormalizer_pos (μ σ : ℝ) (hσ : 0 < σ) :
    0 < truncatedNormalizer μ σ := by
  unfold truncatedNormalizer
  have hs : Function.support (unnorm μ σ) = Set.univ := by
    ext x
    simp [Function.mem_support, unnorm, Real.exp_ne_zero]
  apply (setIntegral_pos_iff_support_of_nonneg_ae
    (Filter.Eventually.of_forall (fun x => (Real.exp_pos _).le))
    (unnorm_integrable μ σ hσ).integrableOn).mpr
  change 0 < volume (Function.support (unnorm μ σ) ∩ Set.Ici (0 : ℝ))
  simp [hs, Real.volume_Ici]

/-- A density on all real coordinates, zero outside the physical gate. -/
noncomputable def truncatedDensity (μ σ : ℝ) : ℝ → ℝ :=
  (Set.Ici (0 : ℝ)).indicator (fun x => (truncatedNormalizer μ σ)⁻¹ * unnorm μ σ x)

theorem truncatedDensity_nonneg (μ σ x : ℝ) (hσ : 0 < σ) :
    0 ≤ truncatedDensity μ σ x := by
  unfold truncatedDensity
  by_cases hx : 0 ≤ x
  · rw [Set.indicator_of_mem (show x ∈ Set.Ici (0 : ℝ) from hx)]
    exact mul_nonneg (le_of_lt (inv_pos.mpr (truncatedNormalizer_pos μ σ hσ)))
      (Real.exp_pos _).le
  · simp [hx]

theorem truncatedDensity_integrable (μ σ : ℝ) (hσ : 0 < σ) :
    Integrable (truncatedDensity μ σ) := by
  exact ((unnorm_integrable μ σ hσ).const_mul (truncatedNormalizer μ σ)⁻¹).indicator
    measurableSet_Ici

theorem truncatedDensity_integral_eq_one (μ σ : ℝ) (hσ : 0 < σ) :
    ∫ x, truncatedDensity μ σ x = 1 := by
  rw [truncatedDensity, integral_indicator measurableSet_Ici, integral_const_mul]
  change (truncatedNormalizer μ σ)⁻¹ * truncatedNormalizer μ σ = 1
  exact inv_mul_cancel₀ (ne_of_gt (truncatedNormalizer_pos μ σ hσ))

/-- The normalized density has the exact unique gated mode, with its positive
normalizer derived from the integral rather than assumed. -/
theorem truncatedDensity_unique_mode (μ σ : ℝ) (hσ : 0 < σ) :
    (∀ x : ℝ, 0 ≤ x → truncatedDensity μ σ x ≤ truncatedDensity μ σ (mode μ)) ∧
    (∀ x : ℝ, 0 ≤ x →
      (truncatedDensity μ σ x = truncatedDensity μ σ (mode μ) ↔ x = mode μ)) := by
  have h := scaled_unnorm_unique_mode (truncatedNormalizer μ σ)⁻¹ μ σ
    (inv_pos.mpr (truncatedNormalizer_pos μ σ hσ)) hσ
  have hg : ∀ x : ℝ, 0 ≤ x → truncatedDensity μ σ x =
      (truncatedNormalizer μ σ)⁻¹ * unnorm μ σ x := by
    intro x hx
    simp [truncatedDensity, hx]
  constructor
  · intro x hx
    rw [hg x hx, hg (mode μ) (mode_nonneg μ)]
    exact h.1 x hx
  · intro x hx
    rw [hg x hx, hg (mode μ) (mode_nonneg μ)]
    exact h.2 x hx

end TruncGaussProof
