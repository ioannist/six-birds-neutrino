import TruncGaussProof.Product

namespace TruncGaussProof

/-- Offsets for which the two-factor constrained mode is at the boundary. -/
def offsetBoundaryEvent (a b μ : ℝ) : Set ℝ :=
  {ε | combinedMean a b μ (μ + ε) ≤ 0}

theorem product_boundary_iff_offset_event (a b μ ε : ℝ) (ha : 0 < a) (hb : 0 < b) :
    (∀ x : ℝ, 0 ≤ x → gaussianProduct a b μ (μ + ε) x ≤
      gaussianProduct a b μ (μ + ε) 0) ↔ ε ∈ offsetBoundaryEvent a b μ := by
  change (∀ x : ℝ, 0 ≤ x → gaussianProduct a b μ (μ + ε) x ≤
    gaussianProduct a b μ (μ + ε) 0) ↔ combinedMean a b μ (μ + ε) ≤ 0
  rw [gaussianProduct_boundary_max_iff a b μ (μ + ε) ha hb]
  exact (combinedMean_nonpos_iff a b μ (μ + ε) ha hb).symm

theorem offsetBoundaryEvent_eq_Iic (a b μ : ℝ) (ha : 0 < a) (hb : 0 < b) :
    offsetBoundaryEvent a b μ = Set.Iic (-((a + b) * μ) / b) := by
  ext ε
  exact combinedMean_offset_gate a b μ ε ha hb

theorem offsetBoundaryEvent_measurable (a b μ : ℝ) (ha : 0 < a) (hb : 0 < b) :
    MeasurableSet (offsetBoundaryEvent a b μ) := by
  rw [offsetBoundaryEvent_eq_Iic a b μ ha hb]
  exact measurableSet_Iic

theorem offsetThreshold_mono (a b₁ b₂ μ : ℝ) (ha : 0 < a)
    (hb₁ : 0 < b₁) (hb₂ : 0 < b₂) (hμ : 0 ≤ μ) (hb : b₁ ≤ b₂) :
    -((a + b₁) * μ) / b₁ ≤ -((a + b₂) * μ) / b₂ := by
  apply (div_le_div_iff₀ hb₁ hb₂).mpr
  have h := mul_nonneg (mul_nonneg (le_of_lt ha) hμ) (sub_nonneg.mpr hb)
  nlinarith

theorem offsetThreshold_antitone (a b₁ b₂ μ : ℝ) (ha : 0 < a)
    (hb₁ : 0 < b₁) (hb₂ : 0 < b₂) (hμ : μ ≤ 0) (hb : b₁ ≤ b₂) :
    -((a + b₂) * μ) / b₂ ≤ -((a + b₁) * μ) / b₁ := by
  apply (div_le_div_iff₀ hb₂ hb₁).mpr
  have h := mul_nonpos_of_nonpos_of_nonneg
    (mul_nonpos_of_nonneg_of_nonpos (le_of_lt ha) hμ) (sub_nonneg.mpr hb)
  nlinarith

theorem offsetBoundaryEvent_subset_of_nonneg (a b₁ b₂ μ : ℝ) (ha : 0 < a)
    (hb₁ : 0 < b₁) (hb₂ : 0 < b₂) (hμ : 0 ≤ μ) (hb : b₁ ≤ b₂) :
    offsetBoundaryEvent a b₁ μ ⊆ offsetBoundaryEvent a b₂ μ := by
  rw [offsetBoundaryEvent_eq_Iic a b₁ μ ha hb₁,
      offsetBoundaryEvent_eq_Iic a b₂ μ ha hb₂]
  exact Set.Iic_subset_Iic.mpr (offsetThreshold_mono a b₁ b₂ μ ha hb₁ hb₂ hμ hb)

theorem offsetBoundaryEvent_subset_of_nonpos (a b₁ b₂ μ : ℝ) (ha : 0 < a)
    (hb₁ : 0 < b₁) (hb₂ : 0 < b₂) (hμ : μ ≤ 0) (hb : b₁ ≤ b₂) :
    offsetBoundaryEvent a b₂ μ ⊆ offsetBoundaryEvent a b₁ μ := by
  rw [offsetBoundaryEvent_eq_Iic a b₁ μ ha hb₁,
      offsetBoundaryEvent_eq_Iic a b₂ μ ha hb₂]
  exact Set.Iic_subset_Iic.mpr (offsetThreshold_antitone a b₁ b₂ μ ha hb₁ hb₂ hμ hb)

theorem offsetBoundaryEvent_zero (a b : ℝ) (ha : 0 < a) (hb : 0 < b) :
    offsetBoundaryEvent a b 0 = Set.Iic 0 := by
  simpa using offsetBoundaryEvent_eq_Iic a b 0 ha hb

/-- One fixed offset measure throughout the precision change. For a probability
measure this is the non-strict boundary-probability law; no Gaussian CDF identity
or strictness for an arbitrary measure is asserted. -/
theorem offsetBoundaryMeasure_mono (ν : MeasureTheory.Measure ℝ) (a μ : ℝ)
    (ha : 0 < a) (hμ : 0 ≤ μ) :
    MonotoneOn (fun b : ℝ => ν (offsetBoundaryEvent a b μ)) (Set.Ioi 0) := by
  intro b₁ hb₁ b₂ hb₂ hb
  exact MeasureTheory.measure_mono
    (offsetBoundaryEvent_subset_of_nonneg a b₁ b₂ μ ha hb₁ hb₂ hμ hb)

theorem offsetBoundaryMeasure_antitone (ν : MeasureTheory.Measure ℝ) (a μ : ℝ)
    (ha : 0 < a) (hμ : μ ≤ 0) :
    AntitoneOn (fun b : ℝ => ν (offsetBoundaryEvent a b μ)) (Set.Ioi 0) := by
  intro b₁ hb₁ b₂ hb₂ hb
  exact MeasureTheory.measure_mono
    (offsetBoundaryEvent_subset_of_nonpos a b₁ b₂ μ ha hb₁ hb₂ hμ hb)

theorem offsetBoundaryEvent_common_scale (a b μ t : ℝ) (ht : 0 < t) :
    offsetBoundaryEvent (t * a) (t * b) μ = offsetBoundaryEvent a b μ := by
  ext ε
  change combinedMean (t * a) (t * b) μ (μ + ε) ≤ 0 ↔ combinedMean a b μ (μ + ε) ≤ 0
  rw [combinedMean_common_scale a b μ (μ + ε) t (ne_of_gt ht)]

/-- Boundary maximization stated directly for the standard-deviation kernels. -/
def standardDeviationBoundaryEvent (σ₁ σ₂ μ : ℝ) : Set ℝ :=
  {ε | ∀ x : ℝ, 0 ≤ x → unnorm μ σ₁ x * unnorm (μ + ε) σ₂ x ≤
    unnorm μ σ₁ 0 * unnorm (μ + ε) σ₂ 0}

theorem inverseVariance_antitone (σ₁ σ₂ : ℝ) (hσ₁ : 0 < σ₁)
    (hσ₂ : 0 < σ₂) (hσ : σ₁ ≤ σ₂) :
    1 / σ₂ ^ 2 ≤ 1 / σ₁ ^ 2 := by
  apply (div_le_div_iff₀ (sq_pos_of_pos hσ₂) (sq_pos_of_pos hσ₁)).mpr
  have h := mul_nonneg (sub_nonneg.mpr hσ) (le_of_lt (add_pos hσ₂ hσ₁))
  nlinarith

theorem standardDeviationBoundaryEvent_eq_precision_event (σ₁ σ₂ μ : ℝ)
    (hσ₁ : 0 < σ₁) (hσ₂ : 0 < σ₂) :
    standardDeviationBoundaryEvent σ₁ σ₂ μ =
      offsetBoundaryEvent (1 / σ₁ ^ 2) (1 / σ₂ ^ 2) μ := by
  ext ε
  change (∀ x : ℝ, 0 ≤ x → unnorm μ σ₁ x * unnorm (μ + ε) σ₂ x ≤
    unnorm μ σ₁ 0 * unnorm (μ + ε) σ₂ 0) ↔ _
  simp_rw [← gaussianProduct_inverse_variance μ (μ + ε) σ₁ σ₂ _ hσ₁ hσ₂]
  exact product_boundary_iff_offset_event _ _ μ ε (by positivity) (by positivity)

theorem standardDeviationBoundaryEvent_eq_Iic (σ₁ σ₂ μ : ℝ)
    (hσ₁ : 0 < σ₁) (hσ₂ : 0 < σ₂) :
    standardDeviationBoundaryEvent σ₁ σ₂ μ = Set.Iic (-μ * (1 + σ₂ ^ 2 / σ₁ ^ 2)) := by
  rw [standardDeviationBoundaryEvent_eq_precision_event σ₁ σ₂ μ hσ₁ hσ₂,
      offsetBoundaryEvent_eq_Iic _ _ μ (by positivity) (by positivity)]
  congr 1
  field_simp [ne_of_gt hσ₁, ne_of_gt hσ₂]
  <;> ring

theorem standardDeviationBoundaryEvent_measurable (σ₁ σ₂ μ : ℝ)
    (hσ₁ : 0 < σ₁) (hσ₂ : 0 < σ₂) :
    MeasurableSet (standardDeviationBoundaryEvent σ₁ σ₂ μ) := by
  rw [standardDeviationBoundaryEvent_eq_Iic σ₁ σ₂ μ hσ₁ hσ₂]
  exact measurableSet_Iic

/-- For one fixed offset law and nonnegative mean, reducing σ₂ cannot reduce
the boundary probability. The first standard deviation remains fixed. -/
theorem standardDeviationBoundaryMeasure_antitone (ν : MeasureTheory.Measure ℝ)
    (σ₁ μ : ℝ) (hσ₁ : 0 < σ₁) (hμ : 0 ≤ μ) :
    AntitoneOn (fun σ₂ : ℝ => ν (standardDeviationBoundaryEvent σ₁ σ₂ μ)) (Set.Ioi 0) := by
  intro σ₂ hσ₂ σ₂' hσ₂' hσ
  apply MeasureTheory.measure_mono
  rw [standardDeviationBoundaryEvent_eq_precision_event σ₁ σ₂' μ hσ₁ hσ₂',
      standardDeviationBoundaryEvent_eq_precision_event σ₁ σ₂ μ hσ₁ hσ₂]
  exact offsetBoundaryEvent_subset_of_nonneg _ _ _ μ (by positivity)
    (by positivity) (by positivity) hμ (inverseVariance_antitone σ₂ σ₂' hσ₂ hσ₂' hσ)

/-- With a nonpositive mean the standard-deviation direction reverses. -/
theorem standardDeviationBoundaryMeasure_mono (ν : MeasureTheory.Measure ℝ)
    (σ₁ μ : ℝ) (hσ₁ : 0 < σ₁) (hμ : μ ≤ 0) :
    MonotoneOn (fun σ₂ : ℝ => ν (standardDeviationBoundaryEvent σ₁ σ₂ μ)) (Set.Ioi 0) := by
  intro σ₂ hσ₂ σ₂' hσ₂' hσ
  apply MeasureTheory.measure_mono
  rw [standardDeviationBoundaryEvent_eq_precision_event σ₁ σ₂ μ hσ₁ hσ₂,
      standardDeviationBoundaryEvent_eq_precision_event σ₁ σ₂' μ hσ₁ hσ₂']
  exact offsetBoundaryEvent_subset_of_nonpos _ _ _ μ (by positivity)
    (by positivity) (by positivity) hμ (inverseVariance_antitone σ₂ σ₂' hσ₂ hσ₂' hσ)

end TruncGaussProof
