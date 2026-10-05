import TruncGaussProof.Tightening

namespace TruncGaussProof

open MeasureTheory ProbabilityTheory

/-- The standard normal CDF is tied to Mathlib's actual probability measure. -/
noncomputable def standardNormalCDF (x : ℝ) : ℝ := cdf (gaussianReal 0 1) x

/-- Gaussian offset law with mean `-d` and variance `s²`. -/
noncomputable def gaussianOffsetLaw (d s : ℝ) : Measure ℝ :=
  gaussianReal (-d) ⟨s ^ 2, sq_nonneg s⟩

/-- Strictness is derived from positive Gaussian density on every nonempty
interval, and is not asserted for arbitrary offset measures. -/
theorem standardNormalCDF_strictMono : StrictMono standardNormalCDF := by
  intro a b hab
  have hs : Function.support (gaussianPDFReal 0 1) = Set.univ := by
    ext x
    simp [Function.mem_support, ne_of_gt (gaussianPDFReal_pos 0 1 x (by norm_num))]
  have hp : 0 < ∫ x in Set.Ioc a b, gaussianPDFReal 0 1 x := by
    apply (setIntegral_pos_iff_support_of_nonneg_ae
      (Filter.Eventually.of_forall (gaussianPDFReal_nonneg 0 1))
      (integrable_gaussianPDFReal 0 1).integrableOn).mpr
    change 0 < volume (Function.support (gaussianPDFReal 0 1) ∩ Set.Ioc a b)
    simp [hs, Real.volume_Ioc, sub_pos.mpr hab]
  have hm : 0 < gaussianReal 0 1 (Set.Ioc a b) := by
    rw [gaussianReal_apply_eq_integral 0 (by norm_num)]
    exact ENNReal.ofReal_pos.mpr hp
  rw [← measure_cdf (gaussianReal 0 1), StieltjesFunction.measure_Ioc] at hm
  exact sub_pos.mp (ENNReal.ofReal_pos.mp hm)

/-- Derive the offset distribution from the standard normal law. This transport
identity is valid even at zero scale; standardization below needs positive scale. -/
theorem gaussianOffsetLaw_eq_map (d s : ℝ) :
    gaussianOffsetLaw d s = (gaussianReal 0 1).map (fun z => s * z - d) := by
  have hf : (fun z : ℝ => s * z - d) = (fun z : ℝ => z - d) ∘ (fun z => s * z) := rfl
  rw [hf, ← Measure.map_map (by fun_prop) (by fun_prop),
    gaussianReal_map_const_mul, gaussianReal_map_sub_const]
  simp [gaussianOffsetLaw]

/-- The actual probability of a lower half-line, standardized with positive
offset standard deviation. -/
theorem gaussianOffsetLaw_Iic_cdf (d s t : ℝ) (hs : 0 < s) :
    (gaussianOffsetLaw d s).real (Set.Iic t) = standardNormalCDF ((t + d) / s) := by
  have hset : (fun z : ℝ => s * z - d) ⁻¹' Set.Iic t = Set.Iic ((t + d) / s) := by
    ext z
    simp only [Set.mem_preimage, Set.mem_Iic]
    rw [le_div_iff₀ hs]
    constructor <;> intro h <;> nlinarith
  rw [gaussianOffsetLaw_eq_map, standardNormalCDF, cdf_eq_real]
  unfold Measure.real
  rw [Measure.map_apply (by fun_prop) measurableSet_Iic, hset]

/-- The analytic sweep formula returns to actual boundary maximization of the
two standard-deviation kernels and to a derived Gaussian offset distribution. -/
theorem standardDeviationBoundaryGaussianProbability_cdf (σ₁ σ₂ μ d s : ℝ)
    (hσ₁ : 0 < σ₁) (hσ₂ : 0 < σ₂) (hs : 0 < s) :
    (gaussianOffsetLaw d s).real (standardDeviationBoundaryEvent σ₁ σ₂ μ) =
      standardNormalCDF ((d - μ * (1 + σ₂ ^ 2 / σ₁ ^ 2)) / s) := by
  rw [standardDeviationBoundaryEvent_eq_Iic σ₁ σ₂ μ hσ₁ hσ₂,
    gaussianOffsetLaw_Iic_cdf d s _ hs]
  congr 1
  ring

/-- With fixed positive first width and offset noise, the exact Gaussian-law
probability strictly increases when the second width is reduced and `μ>0`. -/
theorem standardDeviationBoundaryGaussianProbability_strictAnti (σ₁ μ d s : ℝ)
    (hσ₁ : 0 < σ₁) (hμ : 0 < μ) (hs : 0 < s) :
    StrictAntiOn (fun σ₂ : ℝ =>
      (gaussianOffsetLaw d s).real (standardDeviationBoundaryEvent σ₁ σ₂ μ))
      (Set.Ioi 0) := by
  intro σ₂ hσ₂ σ₂' hσ₂' hlt
  dsimp only
  rw [standardDeviationBoundaryGaussianProbability_cdf σ₁ σ₂ μ d s hσ₁ hσ₂ hs,
    standardDeviationBoundaryGaussianProbability_cdf σ₁ σ₂' μ d s hσ₁ hσ₂' hs]
  apply standardNormalCDF_strictMono
  apply (div_lt_div_iff_of_pos_right hs).mpr
  have hsq : σ₂ ^ 2 < σ₂' ^ 2 := by
    nlinarith [mul_pos (sub_pos.mpr hlt) (add_pos hσ₂ hσ₂')]
  have hratio := (div_lt_div_iff_of_pos_right (sq_pos_of_pos hσ₁)).mpr hsq
  nlinarith [mul_pos hμ (sub_pos.mpr hratio)]

/-- The exact strict direction reverses for a negative fixed first mean. -/
theorem standardDeviationBoundaryGaussianProbability_strictMono (σ₁ μ d s : ℝ)
    (hσ₁ : 0 < σ₁) (hμ : μ < 0) (hs : 0 < s) :
    StrictMonoOn (fun σ₂ : ℝ =>
      (gaussianOffsetLaw d s).real (standardDeviationBoundaryEvent σ₁ σ₂ μ))
      (Set.Ioi 0) := by
  intro σ₂ hσ₂ σ₂' hσ₂' hlt
  dsimp only
  rw [standardDeviationBoundaryGaussianProbability_cdf σ₁ σ₂ μ d s hσ₁ hσ₂ hs,
    standardDeviationBoundaryGaussianProbability_cdf σ₁ σ₂' μ d s hσ₁ hσ₂' hs]
  apply standardNormalCDF_strictMono
  apply (div_lt_div_iff_of_pos_right hs).mpr
  have hsq : σ₂ ^ 2 < σ₂' ^ 2 := by
    nlinarith [mul_pos (sub_pos.mpr hlt) (add_pos hσ₂ hσ₂')]
  have hratio := (div_lt_div_iff_of_pos_right (sq_pos_of_pos hσ₁)).mpr hsq
  nlinarith [mul_pos (neg_pos.mpr hμ) (sub_pos.mpr hratio)]

theorem standardDeviationBoundaryGaussianProbability_zero (σ₁ σ₂ d s : ℝ)
    (hσ₁ : 0 < σ₁) (hσ₂ : 0 < σ₂) (hs : 0 < s) :
    (gaussianOffsetLaw d s).real (standardDeviationBoundaryEvent σ₁ σ₂ 0) =
      standardNormalCDF (d / s) := by
  simpa using standardDeviationBoundaryGaussianProbability_cdf σ₁ σ₂ 0 d s hσ₁ hσ₂ hs

end TruncGaussProof
