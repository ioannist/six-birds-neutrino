import TruncGaussProof.GaussianGatedCDF

open MeasureTheory ProbabilityTheory TruncGaussProof

-- Negative mean: both standardized endpoints have the correct positive sign.
example : (truncatedGaussianLaw (-2) 3).real (Set.Ioc 0 5) =
    (standardNormalCDF (7/3) - standardNormalCDF (2/3)) /
      standardNormalCDF (-2/3) := by
  convert truncatedGaussianLaw_Ioc_cdf (-2) 3 0 5 (by norm_num) (by norm_num)
    (by norm_num) using 1 <;> norm_num

-- Positive mean: the lower standardized endpoint reverses sign.
example : (truncatedGaussianLaw 2 3).real (Set.Ioc 0 5) =
    (standardNormalCDF 1 - standardNormalCDF (-2/3)) /
      standardNormalCDF (2/3) := by
  convert truncatedGaussianLaw_Ioc_cdf 2 3 0 5 (by norm_num) (by norm_num)
    (by norm_num) using 1 <;> norm_num

-- The conditional-measure equality concerns every measurable event.
example (μ σ : ℝ) (hσ : 0 < σ) (s : Set ℝ) (hs : MeasurableSet s) :
    (truncatedGaussianLaw μ σ).real s =
      (gaussianOffsetLaw (-μ) σ).real (s ∩ Set.Ici 0) /
        standardNormalCDF (μ / σ) :=
  truncatedGaussianLaw_real_apply μ σ hσ s hs

-- A boundary density mode has zero CDF at the boundary itself.
example (μ σ : ℝ) (hσ : 0 < σ) : cdf (truncatedGaussianLaw μ σ) 0 = 0 :=
  truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _)

-- Positive-width boundary fractions are positive even though that CDF is zero.
example (μ σ ε : ℝ) (hσ : 0 < σ) (hε : 0 < ε) :
    0 < cdf (truncatedGaussianLaw μ σ) ε := by
  have h := truncatedGaussianLaw_cdf_strictMonoOn μ σ hσ
    (show (0 : ℝ) ∈ Set.Ici 0 from le_refl _)
    (show ε ∈ Set.Ici 0 from le_of_lt hε) hε
  rwa [truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _)] at h

-- Any specified CDF value can have at most one nonnegative coordinate.
example (μ σ x y : ℝ) (hσ : 0 < σ) (hx : 0 ≤ x) (hy : 0 ≤ y)
    (hxy : cdf (truncatedGaussianLaw μ σ) x = cdf (truncatedGaussianLaw μ σ) y) :
    x = y := by
  exact (truncatedGaussianLaw_cdf_strictMonoOn μ σ hσ).injOn hx hy hxy

-- The nonnegative-threshold formula cannot be applied at a negative threshold:
-- its unguarded right side is strictly negative, while the actual CDF is zero.
example : cdf (truncatedGaussianLaw 0 1) (-1) = 0 ∧
    (standardNormalCDF (-1) - standardNormalCDF 0) / standardNormalCDF 0 < 0 := by
  constructor
  · exact truncatedGaussianLaw_cdf_of_nonpos 0 1 (-1) (by norm_num) (by norm_num)
  · have hn := truncatedNormalizer_pos 0 1 (by norm_num)
    rw [truncatedNormalizer_eq_cdf 0 1 (by norm_num)] at hn
    simp only [one_mul, zero_div] at hn
    have hp : 0 < standardNormalCDF 0 := by
      have hc : 0 < Real.sqrt (2 * Real.pi) := by positivity
      nlinarith
    exact div_neg_of_neg_of_pos (sub_neg.mpr (standardNormalCDF_strictMono (by norm_num))) hp

-- Reversed endpoints are excluded from the displayed CDF-difference statement.
example : (truncatedGaussianLaw 0 1).real (Set.Ioc 2 1) = 0 ∧
    standardNormalCDF 1 - standardNormalCDF 2 < 0 := by
  constructor
  · simp [Set.Ioc_eq_empty_of_le (show (1 : ℝ) ≤ 2 by norm_num)]
  · exact sub_neg.mpr (standardNormalCDF_strictMono (by norm_num))

-- A finite upper gate would change the law: this one assigns positive mass
-- beyond the arbitrary coordinate one.
example : 0 < (truncatedGaussianLaw 0 1).real (Set.Ioc 1 2) := by
  rw [truncatedGaussianLaw_Ioc_cdf 0 1 1 2 (by norm_num) (by norm_num) (by norm_num)]
  simp only [sub_zero, div_one, zero_div]
  have hn := truncatedNormalizer_pos 0 1 (by norm_num)
  rw [truncatedNormalizer_eq_cdf 0 1 (by norm_num)] at hn
  simp only [one_mul, zero_div] at hn
  have hp : 0 < standardNormalCDF 0 := by
    have hc : 0 < Real.sqrt (2 * Real.pi) := by positivity
    nlinarith
  exact div_pos (sub_pos.mpr (standardNormalCDF_strictMono (by norm_num))) hp

-- Sigma zero gives the totalized zero density law, while the actual Gaussian
-- with zero variance has an atom. The positive-width restriction is substantive.
example : truncatedGaussianLaw 0 0 {0} = 0 ∧ (gaussianOffsetLaw 0 0) {0} = 1 := by
  constructor
  · exact truncatedGaussianLaw_singleton 0 0 0
  · simp [gaussianOffsetLaw, gaussianReal_zero_var]
