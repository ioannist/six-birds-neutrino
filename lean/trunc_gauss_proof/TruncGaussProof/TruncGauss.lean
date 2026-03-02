import Mathlib

namespace TruncGaussProof

noncomputable def unnorm (μ σ x : ℝ) : ℝ :=
  Real.exp (-((x - μ) ^ 2 / (2 * σ ^ 2)))

theorem unnorm_antitoneOn_Ici (μ σ : ℝ) (hσ : 0 < σ) (hμ : μ ≤ 0) :
    AntitoneOn (fun x => unnorm μ σ x) (Set.Ici (0 : ℝ)) := by
  intro x hx y hy hxy
  unfold unnorm
  refine Real.exp_le_exp.mpr ?_
  have hx0 : 0 ≤ x := hx
  have hy0 : 0 ≤ y := hy
  have hxm_nonneg : 0 ≤ x - μ := by linarith
  have hym_nonneg : 0 ≤ y - μ := by linarith
  have hxm_le_hym : x - μ ≤ y - μ := sub_le_sub_right hxy μ
  have hsq : (x - μ) ^ 2 ≤ (y - μ) ^ 2 := by
    nlinarith [hxm_nonneg, hym_nonneg, hxm_le_hym]
  have hden : 0 < 2 * σ ^ 2 := by
    have hs2 : 0 < σ ^ 2 := sq_pos_of_pos hσ
    nlinarith
  have hfrac : (x - μ) ^ 2 / (2 * σ ^ 2) ≤ (y - μ) ^ 2 / (2 * σ ^ 2) := by
    exact div_le_div_of_nonneg_right hsq (le_of_lt hden)
  linarith

theorem unnorm_le_at_zero (μ σ : ℝ) (hσ : 0 < σ) (hμ : μ ≤ 0) :
    ∀ {x : ℝ}, 0 ≤ x → unnorm μ σ x ≤ unnorm μ σ 0 := by
  intro x hx
  have hant := unnorm_antitoneOn_Ici μ σ hσ hμ
  have h0 : (0 : ℝ) ∈ Set.Ici (0 : ℝ) := by simp
  have hxmem : x ∈ Set.Ici (0 : ℝ) := hx
  simpa using hant h0 hxmem hx

end TruncGaussProof
