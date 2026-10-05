import Mathlib

namespace TruncGaussProof

/-- Directional likelihood improvement. Nonnegativity needs an actual maximizer
over a domain containing the transferred point, not just optimizer success. -/
def directionalDelta {α : Type*} (logL : α → ℝ) (train best : α) : ℝ :=
  -2 * (logL train - logL best)

theorem directionalDelta_nonneg {α : Type*} (logL : α → ℝ) (train best : α)
    (hbest : logL train ≤ logL best) : 0 ≤ directionalDelta logL train best := by
  unfold directionalDelta
  linarith

/-- The additive identity is conditional on using actual additive block terms.
It does not justify separately inverting correlated covariance submatrices. -/
theorem directionalDelta_sum {α ι : Type*} (s : Finset ι)
    (blocks : ι → α → ℝ) (train best : α) :
    directionalDelta (fun x => s.sum (fun i => blocks i x)) train best =
      s.sum (fun i => directionalDelta (blocks i) train best) := by
  unfold directionalDelta
  simp_rw [mul_sub]
  rw [Finset.mul_sum, Finset.mul_sum, Finset.sum_sub_distrib]

end TruncGaussProof
