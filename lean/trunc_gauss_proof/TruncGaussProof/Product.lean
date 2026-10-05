import TruncGaussProof.Mode

namespace TruncGaussProof

/-- Product of two unnormalized Gaussian factors with precision parameters.
A posterior interpretation additionally requires a constant prior on x ≥ 0. -/
noncomputable def gaussianProduct (a b μ₁ μ₂ x : ℝ) : ℝ :=
  Real.exp (-(a * (x - μ₁) ^ 2 / 2)) * Real.exp (-(b * (x - μ₂) ^ 2 / 2))

/-- Bridge from positive standard deviations to precision parameters. -/
theorem gaussianProduct_inverse_variance (μ₁ μ₂ σ₁ σ₂ x : ℝ)
    (hσ₁ : 0 < σ₁) (hσ₂ : 0 < σ₂) :
    gaussianProduct (1 / σ₁ ^ 2) (1 / σ₂ ^ 2) μ₁ μ₂ x =
      unnorm μ₁ σ₁ x * unnorm μ₂ σ₂ x := by
  unfold gaussianProduct unnorm
  congr 1 <;> congr 1 <;> field_simp

/-- The product is a Gaussian kernel times a strictly positive x-independent
factor. No integral-normalization claim is made here. -/
theorem gaussianProduct_completed_square (a b μ₁ μ₂ x : ℝ)
    (ha : 0 < a) (hb : 0 < b) :
    gaussianProduct a b μ₁ μ₂ x =
      Real.exp (-(a * b / (a + b) * (μ₁ - μ₂) ^ 2 / 2)) *
      Real.exp (-((a + b) * (x - combinedMean a b μ₁ μ₂) ^ 2 / 2)) := by
  unfold gaussianProduct
  rw [← Real.exp_add, ← Real.exp_add]
  congr 1
  have h := combine_completed_square a b μ₁ μ₂ x ha hb
  linarith

/-- Exact unique maximizer of the two-factor product on the physical gate. -/
theorem gaussianProduct_unique_mode (a b μ₁ μ₂ : ℝ) (ha : 0 < a) (hb : 0 < b) :
    (∀ x : ℝ, 0 ≤ x →
      gaussianProduct a b μ₁ μ₂ x ≤
      gaussianProduct a b μ₁ μ₂ (mode (combinedMean a b μ₁ μ₂))) ∧
    (∀ x : ℝ, 0 ≤ x →
      (gaussianProduct a b μ₁ μ₂ x =
       gaussianProduct a b μ₁ μ₂ (mode (combinedMean a b μ₁ μ₂)) ↔
       x = mode (combinedMean a b μ₁ μ₂))) := by
  constructor
  · intro x hx
    rw [gaussianProduct_completed_square a b μ₁ μ₂ x ha hb,
        gaussianProduct_completed_square a b μ₁ μ₂ (mode (combinedMean a b μ₁ μ₂)) ha hb]
    apply mul_le_mul_of_nonneg_left _ (le_of_lt (Real.exp_pos _))
    apply Real.exp_le_exp.mpr
    have h := mul_le_mul_of_nonneg_left
      (squared_distance_min (combinedMean a b μ₁ μ₂) x hx) (le_of_lt (add_pos ha hb))
    linarith
  · intro x hx
    rw [gaussianProduct_completed_square a b μ₁ μ₂ x ha hb,
        gaussianProduct_completed_square a b μ₁ μ₂ (mode (combinedMean a b μ₁ μ₂)) ha hb,
        mul_right_inj' (Real.exp_ne_zero _), Real.exp_injective.eq_iff, neg_inj,
        div_left_inj' (by norm_num : (2 : ℝ) ≠ 0),
        mul_right_inj' (ne_of_gt (add_pos ha hb))]
    exact squared_distance_eq_iff (combinedMean a b μ₁ μ₂) x hx

/-- Exact return to the original standard-deviation Gaussian factors. -/
theorem unnorm_product_unique_mode (μ₁ μ₂ σ₁ σ₂ : ℝ)
    (hσ₁ : 0 < σ₁) (hσ₂ : 0 < σ₂) :
    let m := mode (combinedMean (1 / σ₁ ^ 2) (1 / σ₂ ^ 2) μ₁ μ₂)
    (∀ x : ℝ, 0 ≤ x → unnorm μ₁ σ₁ x * unnorm μ₂ σ₂ x ≤
      unnorm μ₁ σ₁ m * unnorm μ₂ σ₂ m) ∧
    (∀ x : ℝ, 0 ≤ x →
      (unnorm μ₁ σ₁ x * unnorm μ₂ σ₂ x = unnorm μ₁ σ₁ m * unnorm μ₂ σ₂ m ↔ x = m)) := by
  have ha : 0 < 1 / σ₁ ^ 2 := by positivity
  have hb : 0 < 1 / σ₂ ^ 2 := by positivity
  simpa only [gaussianProduct_inverse_variance μ₁ μ₂ σ₁ σ₂ _ hσ₁ hσ₂] using
    gaussianProduct_unique_mode (1 / σ₁ ^ 2) (1 / σ₂ ^ 2) μ₁ μ₂ ha hb

/-- The product has its unique maximum at the boundary precisely when its
precision-weighted numerator is nonpositive. -/
theorem gaussianProduct_boundary_max_iff (a b μ₁ μ₂ : ℝ) (ha : 0 < a) (hb : 0 < b) :
    (∀ x : ℝ, 0 ≤ x → gaussianProduct a b μ₁ μ₂ x ≤ gaussianProduct a b μ₁ μ₂ 0) ↔
    a * μ₁ + b * μ₂ ≤ 0 := by
  constructor
  · intro hmax
    have hmode := gaussianProduct_unique_mode a b μ₁ μ₂ ha hb
    have heq : gaussianProduct a b μ₁ μ₂ 0 =
        gaussianProduct a b μ₁ μ₂ (mode (combinedMean a b μ₁ μ₂)) :=
      le_antisymm (hmode.1 0 le_rfl) (hmax _ (mode_nonneg _))
    have hzero := (hmode.2 0 le_rfl).mp heq
    have hmean : combinedMean a b μ₁ μ₂ ≤ 0 := by
      have hle : combinedMean a b μ₁ μ₂ ≤ mode (combinedMean a b μ₁ μ₂) := le_max_right _ _
      rw [← hzero] at hle
      exact hle
    exact (combinedMean_nonpos_iff a b μ₁ μ₂ ha hb).mp hmean
  · intro hnum x hx
    have hmean := (combinedMean_nonpos_iff a b μ₁ μ₂ ha hb).mpr hnum
    have hzero : mode (combinedMean a b μ₁ μ₂) = 0 := max_eq_left hmean
    have h := (gaussianProduct_unique_mode a b μ₁ μ₂ ha hb).1 x hx
    rwa [hzero] at h

/-- The exact deterministic gate behind the stochastic offset sweep. -/
theorem combinedMean_offset_gate (a b μ ε : ℝ) (ha : 0 < a) (hb : 0 < b) :
    combinedMean a b μ (μ + ε) ≤ 0 ↔ ε ≤ -((a + b) * μ) / b := by
  rw [combinedMean_nonpos_iff a b μ (μ + ε) ha hb, le_div_iff₀ hb]
  constructor <;> intro h <;> nlinarith

end TruncGaussProof
