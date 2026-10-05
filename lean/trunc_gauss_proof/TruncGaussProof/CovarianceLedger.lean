import Mathlib

namespace TruncGaussProof

open scoped BigOperators Matrix

variable {ι γ : Type*} [Fintype ι]

/-- The full residual quadratic form, using one precision matrix at this endpoint. -/
def residualQuadratic (P : Matrix ι ι ℝ) (r : ι → ℝ) : ℝ :=
  r ⬝ᵥ (P *ᵥ r)

/-- A signed allocation of the full quadratic form, including its cross terms. -/
def coordinateAllocation (P : Matrix ι ι ℝ) (r : ι → ℝ) (i : ι) : ℝ :=
  r i * (P *ᵥ r) i

/-- This bridge is definitional; it supplies no positivity of individual allocations. -/
theorem coordinateAllocation_sum (P : Matrix ι ι ℝ) (r : ι → ℝ) :
    ∑ i, coordinateAllocation P r i = residualQuadratic P r := by
  rfl

/-- A positive definite covariance makes its actual linear solve unique. -/
theorem covariance_solve_eq_inverse [DecidableEq ι] (C : Matrix ι ι ℝ) (hC : C.PosDef)
    (r u : ι → ℝ) (hsolve : C *ᵥ u = r) : u = C⁻¹ *ᵥ r := by
  have hdet : IsUnit C.det := (Matrix.isUnit_iff_isUnit_det C).mp hC.isUnit
  calc
    u = (1 : Matrix ι ι ℝ) *ᵥ u := (Matrix.one_mulVec u).symm
    _ = (C⁻¹ * C) *ᵥ u := by rw [C.nonsing_inv_mul hdet]
    _ = C⁻¹ *ᵥ (C *ᵥ u) := (Matrix.mulVec_mulVec u C⁻¹ C).symm
    _ = C⁻¹ *ᵥ r := by rw [hsolve]

/-- The global inverse-covariance quadratic form is nonnegative. -/
theorem residualQuadratic_inverse_nonneg [DecidableEq ι] (C : Matrix ι ι ℝ) (hC : C.PosDef)
    (r : ι → ℝ) : 0 ≤ residualQuadratic C⁻¹ r := by
  by_cases hr : r = 0
  · simp [residualQuadratic, hr]
  · have hpos := hC.inv.dotProduct_mulVec_pos hr
    simpa [residualQuadratic] using le_of_lt hpos

/-- This is the exact-real bridge for a covariance solve, rather than an
assumption that a supplied matrix is the inverse. -/
theorem covariance_solve_allocation_sum [DecidableEq ι]
    (C : Matrix ι ι ℝ) (hC : C.PosDef) (r u : ι → ℝ) (hsolve : C *ᵥ u = r) :
    ∑ i, r i * u i = residualQuadratic C⁻¹ r := by
  rw [covariance_solve_eq_inverse C hC r u hsolve]
  rfl

/-- Each group sums full-precision coordinate differences. The endpoint precision
matrices may differ; no covariance submatrix is independently inverted. -/
def groupedQuadraticDifference [DecidableEq γ] (label : ι → γ) (g : γ)
    (P_train P_best : Matrix ι ι ℝ) (r_train r_best : ι → ℝ) : ℝ :=
  ∑ i ∈ Finset.univ.filter (fun i => label i = g),
    (coordinateAllocation P_train r_train i - coordinateAllocation P_best r_best i)

/-- An exhaustive finite grouping preserves the full difference, without a sign
assumption or an assumption that endpoint covariances coincide. -/
theorem groupedQuadraticDifference_sum [Fintype γ] [DecidableEq γ]
    (label : ι → γ) (P_train P_best : Matrix ι ι ℝ) (r_train r_best : ι → ℝ) :
    ∑ g, groupedQuadraticDifference label g P_train P_best r_train r_best =
      residualQuadratic P_train r_train - residualQuadratic P_best r_best := by
  unfold groupedQuadraticDifference
  rw [Finset.sum_fiberwise, Finset.sum_sub_distrib]
  rw [coordinateAllocation_sum, coordinateAllocation_sum]

/-- `none` retains bins outside the displayed groups. Discarding it in general
does not preserve the full statistic. -/
theorem groupedQuadraticDifference_with_remainder [Fintype γ] [DecidableEq γ]
    (label : ι → Option γ) (P_train P_best : Matrix ι ι ℝ)
    (r_train r_best : ι → ℝ) :
    (∑ g : γ, groupedQuadraticDifference label (some g) P_train P_best r_train r_best) +
      groupedQuadraticDifference label none P_train P_best r_train r_best =
      residualQuadratic P_train r_train - residualQuadratic P_best r_best := by
  have h := groupedQuadraticDifference_sum label P_train P_best r_train r_best
  rw [Fintype.sum_option] at h
  linarith

end TruncGaussProof
