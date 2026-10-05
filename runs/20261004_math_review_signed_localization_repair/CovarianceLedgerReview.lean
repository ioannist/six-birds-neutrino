import TruncGaussProof

open TruncGaussProof
open scoped BigOperators Matrix

private def P : Matrix (Fin 2) (Fin 2) ℝ := !![1, -2; -2, 5]
private def r : Fin 2 → ℝ := ![1, 1]

-- Positive definiteness does not make each allocated coordinate positive.
private theorem P_posDef : P.PosDef := by
  apply Matrix.PosDef.of_dotProduct_mulVec_pos
  · change Pᴴ = P
    ext i j
    fin_cases i <;> fin_cases j <;> norm_num [P, Matrix.conjTranspose]
  · intro x hx
    simp only [dotProduct, Matrix.mulVec, Fin.sum_univ_two]
    simp [P]
    by_cases h1 : x 1 = 0
    · have h0 : x 0 ≠ 0 := by
        intro h0
        apply hx
        ext i
        fin_cases i <;> simp [h0, h1]
      simpa [h1] using h0
    · have hsq := sq_pos_of_ne_zero h1
      nlinarith [sq_nonneg (x 0 - 2 * x 1)]

example : P.PosDef ∧ P⁻¹.PosDef := ⟨P_posDef, P_posDef.inv⟩

example : coordinateAllocation P r 0 = -1 := by
  norm_num [coordinateAllocation, P, r, Matrix.mulVec, dotProduct, Fin.sum_univ_two]

example : coordinateAllocation P r 1 = 3 := by
  norm_num [coordinateAllocation, P, r, Matrix.mulVec, dotProduct, Fin.sum_univ_two]

example : residualQuadratic P r = 2 := by
  norm_num [residualQuadratic, P, r, Matrix.mulVec, dotProduct, Fin.sum_univ_two]

-- Discarding the signed remainder changes the displayed statistic.
private def label : Fin 2 → Option Unit := ![some (), none]

example : groupedQuadraticDifference label (some ()) P P r 0 = -1 := by
  norm_num [groupedQuadraticDifference, label, coordinateAllocation, P, r,
    Matrix.mulVec, dotProduct, Finset.sum_filter, Fin.sum_univ_two, Fin.sum_univ_succ]
  simp

example : groupedQuadraticDifference label none P P r 0 = 3 := by
  norm_num [groupedQuadraticDifference, label, coordinateAllocation, P, r,
    Matrix.mulVec, dotProduct, Finset.sum_filter, Fin.sum_univ_two, Fin.sum_univ_succ]
  simp

-- Empty index sets are allowed; they give a zero total without a fake positive mode.
example : residualQuadratic (0 : Matrix (Fin 0) (Fin 0) ℝ) 0 = 0 := by
  simp [residualQuadratic, dotProduct]

-- Different endpoint precision matrices are within the grouping theorem's scope.
example : groupedQuadraticDifference (fun _ : Fin 1 => ()) ()
    (1 : Matrix (Fin 1) (Fin 1) ℝ) (fun _ _ => 2)
    (fun _ => 1) (fun _ => 1) = -1 := by
  norm_num [groupedQuadraticDifference, coordinateAllocation, Matrix.mulVec, dotProduct]
