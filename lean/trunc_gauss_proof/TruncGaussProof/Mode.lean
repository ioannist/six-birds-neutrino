import TruncGaussProof.TruncGauss

namespace TruncGaussProof

/-- The constrained optimizer for every real mean. -/
noncomputable def mode (μ : ℝ) : ℝ := max 0 μ

theorem mode_nonneg (μ : ℝ) : 0 ≤ mode μ := le_max_left _ _

theorem squared_distance_min (μ x : ℝ) (hx : 0 ≤ x) :
    (mode μ - μ) ^ 2 ≤ (x - μ) ^ 2 := by
  unfold mode
  by_cases hμ : μ ≤ 0
  · rw [max_eq_left hμ]
    nlinarith [sq_nonneg x]
  · rw [max_eq_right (le_of_not_ge hμ)]
    simpa using sq_nonneg (x - μ)

theorem squared_distance_eq_iff (μ x : ℝ) (hx : 0 ≤ x) :
    (x - μ) ^ 2 = (mode μ - μ) ^ 2 ↔ x = mode μ := by
  constructor
  · intro h
    unfold mode at *
    by_cases hμ : μ ≤ 0
    · rw [max_eq_left hμ] at *
      nlinarith [sq_nonneg x]
    · rw [max_eq_right (le_of_not_ge hμ)] at *
      nlinarith [sq_nonneg (x - μ)]
  · intro h
    rw [h]

theorem unnorm_le_at_mode (μ σ x : ℝ) (hσ : 0 < σ) (hx : 0 ≤ x) :
    unnorm μ σ x ≤ unnorm μ σ (mode μ) := by
  apply Real.exp_le_exp.mpr
  have hden : 0 ≤ 2 * σ ^ 2 := by positivity
  have h := div_le_div_of_nonneg_right (squared_distance_min μ x hx) hden
  exact neg_le_neg h

theorem unnorm_eq_at_mode_iff (μ σ x : ℝ) (hσ : 0 < σ) (hx : 0 ≤ x) :
    unnorm μ σ x = unnorm μ σ (mode μ) ↔ x = mode μ := by
  unfold unnorm
  rw [Real.exp_injective.eq_iff, neg_inj]
  have hden : 2 * σ ^ 2 ≠ 0 := by positivity
  rw [div_left_inj' hden]
  exact squared_distance_eq_iff μ x hx

/-- Positive normalization preserves the unique constrained mode. This theorem
does not assert that an arbitrary supplied constant normalizes the integral. -/
theorem scaled_unnorm_unique_mode (c μ σ : ℝ) (hc : 0 < c) (hσ : 0 < σ) :
    (∀ x : ℝ, 0 ≤ x → c * unnorm μ σ x ≤ c * unnorm μ σ (mode μ)) ∧
    (∀ x : ℝ, 0 ≤ x →
      (c * unnorm μ σ x = c * unnorm μ σ (mode μ) ↔ x = mode μ)) := by
  constructor
  · intro x hx
    exact mul_le_mul_of_nonneg_left (unnorm_le_at_mode μ σ x hσ hx) (le_of_lt hc)
  · intro x hx
    rw [mul_right_inj' (ne_of_gt hc)]
    exact unnorm_eq_at_mode_iff μ σ x hσ hx

/-- Precision-weighted mean. Gaussian precisions are a = 1/σ₁², b = 1/σ₂². -/
noncomputable def combinedMean (a b μ₁ μ₂ : ℝ) : ℝ :=
  (a * μ₁ + b * μ₂) / (a + b)

theorem combine_completed_square (a b μ₁ μ₂ x : ℝ) (ha : 0 < a) (hb : 0 < b) :
    a * (x - μ₁) ^ 2 + b * (x - μ₂) ^ 2 =
      (a + b) * (x - combinedMean a b μ₁ μ₂) ^ 2 +
      (a * b / (a + b)) * (μ₁ - μ₂) ^ 2 := by
  unfold combinedMean
  have hab : a + b ≠ 0 := ne_of_gt (add_pos ha hb)
  field_simp
  ring

theorem combinedMean_nonneg (a b μ₁ μ₂ : ℝ) (ha : 0 < a) (hb : 0 < b)
    (hμ₁ : 0 ≤ μ₁) (hμ₂ : 0 ≤ μ₂) :
    0 ≤ combinedMean a b μ₁ μ₂ := by
  unfold combinedMean
  positivity

theorem combinedMean_nonpos_iff (a b μ₁ μ₂ : ℝ) (ha : 0 < a) (hb : 0 < b) :
    combinedMean a b μ₁ μ₂ ≤ 0 ↔ a * μ₁ + b * μ₂ ≤ 0 := by
  unfold combinedMean
  rw [div_le_iff₀ (add_pos ha hb)]
  simp

/-- Tightening both constraints by a common precision factor does not move the
mean, so cannot by itself move the mode across the physical gate. -/
theorem combinedMean_common_scale (a b μ₁ μ₂ t : ℝ) (ht : t ≠ 0) :
    combinedMean (t * a) (t * b) μ₁ μ₂ = combinedMean a b μ₁ μ₂ := by
  unfold combinedMean
  rw [show t * a * μ₁ + t * b * μ₂ = t * (a * μ₁ + b * μ₂) by ring,
      show t * a + t * b = t * (a + b) by ring]
  exact mul_div_mul_left _ _ ht

end TruncGaussProof
