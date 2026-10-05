import Mathlib

namespace TruncGaussProof

/-- Positive values mean that the second upper quantile is smaller. -/
def tighteningReadout (qA qB : ℝ) : ℝ := qA - qB

/-- Actual coordinate error bounds add under subtraction. These hypotheses are
not supplied by MCSE estimates, and no independence premise is required. -/
theorem tighteningReadout_error_le (trueA trueB estimateA estimateB εA εB : ℝ)
    (hA : |estimateA - trueA| ≤ εA) (hB : |estimateB - trueB| ≤ εB) :
    |tighteningReadout estimateA estimateB - tighteningReadout trueA trueB| ≤ εA + εB := by
  calc
    |tighteningReadout estimateA estimateB - tighteningReadout trueA trueB| =
        |(estimateA - trueA) + -(estimateB - trueB)| := by
      congr 1
      unfold tighteningReadout
      ring
    _ ≤ |estimateA - trueA| + |-(estimateB - trueB)| := abs_add _ _
    _ = |estimateA - trueA| + |estimateB - trueB| := by rw [abs_neg]
    _ ≤ εA + εB := add_le_add hA hB

theorem tighteningReadout_interval (trueA trueB estimateA estimateB εA εB : ℝ)
    (hA : |estimateA - trueA| ≤ εA) (hB : |estimateB - trueB| ≤ εB) :
    tighteningReadout estimateA estimateB - (εA + εB) ≤ tighteningReadout trueA trueB ∧
      tighteningReadout trueA trueB ≤ tighteningReadout estimateA estimateB + (εA + εB) := by
  rcases abs_le.mp (tighteningReadout_error_le trueA trueB estimateA estimateB εA εB hA hB)
      with ⟨hl, hu⟩
  constructor <;> linarith

/-- The direction is certified only when the measured shift exceeds the supplied
sum of actual coordinate errors. -/
theorem tighteningReadout_pos_of_error_bound (trueA trueB estimateA estimateB εA εB : ℝ)
    (hA : |estimateA - trueA| ≤ εA) (hB : |estimateB - trueB| ≤ εB)
    (hmargin : εA + εB < tighteningReadout estimateA estimateB) :
    0 < tighteningReadout trueA trueB := by
  have h := (tighteningReadout_interval trueA trueB estimateA estimateB εA εB hA hB).1
  linarith

/-- The sum bound is attained with strictly positive coordinate endpoints.
It cannot generally be replaced by a smaller coordinate-error bound. -/
theorem tighteningReadout_error_bound_sharp (εA εB : ℝ) (hA : 0 ≤ εA) (hB : 0 ≤ εB) :
    ∃ trueA trueB estimateA estimateB : ℝ,
      0 < trueA ∧ 0 < trueB ∧ 0 < estimateA ∧ 0 < estimateB ∧
      |estimateA - trueA| = εA ∧ |estimateB - trueB| = εB ∧
      |tighteningReadout estimateA estimateB - tighteningReadout trueA trueB| = εA + εB := by
  refine ⟨1 + εB, 1 + εB, 1 + εB + εA, 1, by linarith, by linarith,
    by linarith, by norm_num, ?_, ?_, ?_⟩
  · have h : (1 + εB + εA) - (1 + εB) = εA := by ring
    rw [h, abs_of_nonneg hA]
  · have h : (1 : ℝ) - (1 + εB) = -εB := by ring
    rw [h, abs_neg, abs_of_nonneg hB]
  · have h : tighteningReadout (1 + εB + εA) 1 - tighteningReadout (1 + εB) (1 + εB) =
        εA + εB := by unfold tighteningReadout; ring
    rw [h, abs_of_nonneg (add_nonneg hA hB)]

theorem tighteningReadout_failure_subset {Ω : Type*} (estimateA estimateB : Ω → ℝ)
    (trueA trueB εA εB : ℝ) :
    {ω | εA + εB < |tighteningReadout (estimateA ω) (estimateB ω) -
        tighteningReadout trueA trueB|} ⊆
      {ω | εA < |estimateA ω - trueA|} ∪ {ω | εB < |estimateB ω - trueB|} := by
  intro ω h
  by_contra hnot
  simp only [Set.mem_union, Set.mem_setOf_eq, not_or, not_lt] at hnot
  exact (not_lt_of_ge
    (tighteningReadout_error_le trueA trueB (estimateA ω) (estimateB ω) εA εB hnot.1 hnot.2)) h

/-- Subadditivity holds for any measure. Under a probability law this is a bound
on the failure probability, without an independence assumption. -/
theorem tighteningReadout_failure_measure_le {Ω : Type*} [MeasurableSpace Ω]
    (μ : MeasureTheory.Measure Ω) (estimateA estimateB : Ω → ℝ) (trueA trueB εA εB : ℝ) :
    μ {ω | εA + εB < |tighteningReadout (estimateA ω) (estimateB ω) -
        tighteningReadout trueA trueB|} ≤
      μ {ω | εA < |estimateA ω - trueA|} + μ {ω | εB < |estimateB ω - trueB|} := by
  calc
    _ ≤ μ ({ω | εA < |estimateA ω - trueA|} ∪ {ω | εB < |estimateB ω - trueB|}) :=
      MeasureTheory.measure_mono
        (tighteningReadout_failure_subset estimateA estimateB trueA trueB εA εB)
    _ ≤ _ := MeasureTheory.measure_union_le _ _

/-- The marginal failure bounds remain supplied recognition inputs. This theorem
does not infer them from Monte Carlo diagnostics or physical solver checks. -/
theorem tighteningReadout_failure_risk_le {Ω : Type*} [MeasurableSpace Ω]
    (μ : MeasureTheory.Measure Ω) (estimateA estimateB : Ω → ℝ)
    (trueA trueB εA εB : ℝ) (αA αB : ℝ≥0∞)
    (hA : μ {ω | εA < |estimateA ω - trueA|} ≤ αA)
    (hB : μ {ω | εB < |estimateB ω - trueB|} ≤ αB) :
    μ {ω | εA + εB < |tighteningReadout (estimateA ω) (estimateB ω) -
        tighteningReadout trueA trueB|} ≤ αA + αB :=
  (tighteningReadout_failure_measure_le μ estimateA estimateB trueA trueB εA εB).trans
    (add_le_add hA hB)

theorem tighteningReadout_failure_measurable {Ω : Type*} [MeasurableSpace Ω]
    (estimateA estimateB : Ω → ℝ) (trueA trueB εA εB : ℝ)
    (hA : Measurable estimateA) (hB : Measurable estimateB) :
    MeasurableSet {ω | εA + εB < |tighteningReadout (estimateA ω) (estimateB ω) -
        tighteningReadout trueA trueB|} := by
  change MeasurableSet {ω | εA + εB < |(estimateA ω - estimateB ω) - (trueA - trueB)|}
  exact measurableSet_lt measurable_const (((hA.sub hB).sub measurable_const).abs)

end TruncGaussProof
