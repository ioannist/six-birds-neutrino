import TruncGaussProof

open TruncGaussProof MeasureTheory ProbabilityTheory

-- The offset CDF is standardized with the correct mean sign and scale.
example : (gaussianOffsetLaw 2 3).real (Set.Iic 4) = standardNormalCDF 2 := by
  convert gaussianOffsetLaw_Iic_cdf 2 3 4 (by norm_num) using 1; norm_num

example : (gaussianOffsetLaw 2 3).real (standardDeviationBoundaryEvent 1 2 1) =
    standardNormalCDF (-1) := by
  convert standardDeviationBoundaryGaussianProbability_cdf 1 2 1 2 3
    (by norm_num) (by norm_num) (by norm_num) using 1; norm_num

-- Exact strictness for both mean signs; all remaining parameters are fixed.
example : (gaussianOffsetLaw 0 1).real (standardDeviationBoundaryEvent 1 1 1) <
    (gaussianOffsetLaw 0 1).real (standardDeviationBoundaryEvent 1 (1/2) 1) := by
  exact standardDeviationBoundaryGaussianProbability_strictAnti 1 1 0 1
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)

example : (gaussianOffsetLaw 0 1).real (standardDeviationBoundaryEvent 1 (1/2) (-1)) <
    (gaussianOffsetLaw 0 1).real (standardDeviationBoundaryEvent 1 1 (-1)) := by
  exact standardDeviationBoundaryGaussianProbability_strictMono 1 (-1) 0 1
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)

example : (gaussianOffsetLaw 2 3).real (standardDeviationBoundaryEvent 1 2 0) =
    standardNormalCDF (2/3) := by
  exact standardDeviationBoundaryGaussianProbability_zero 1 2 2 3
    (by norm_num) (by norm_num) (by norm_num)

-- Zero scale is an atom, and the positive-scale CDF formula cannot be extended to it.
example : (gaussianOffsetLaw 0 0).real (standardDeviationBoundaryEvent 1 1 0) = 1 := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 1 0 (by norm_num) (by norm_num)]
  simp [gaussianOffsetLaw, Measure.real, gaussianReal_zero_var]

example : standardNormalCDF 0 < 1 := by
  exact lt_of_lt_of_le (standardNormalCDF_strictMono (show (0 : ℝ) < 1 by norm_num))
    (cdf_le_one (gaussianReal 0 1) 1)

-- A negative multiplier gives the same variance, but reverses the preimage inequality.
example : standardNormalCDF (-1) < (gaussianOffsetLaw 0 (-1)).real (Set.Iic 1) := by
  have h : gaussianOffsetLaw 0 (-1) = gaussianOffsetLaw 0 1 := by
    norm_num [gaussianOffsetLaw]
  rw [h, gaussianOffsetLaw_Iic_cdf 0 1 1 (by norm_num)]
  norm_num
  exact standardNormalCDF_strictMono (by norm_num)

-- Atomic offset measures retain the earlier non-strict law and need not be strict.
example : (Measure.dirac (0 : ℝ)).real (standardDeviationBoundaryEvent 1 1 1) =
    (Measure.dirac (0 : ℝ)).real (standardDeviationBoundaryEvent 1 (1/2) 1) := by
  rw [standardDeviationBoundaryEvent_eq_Iic 1 1 1 (by norm_num) (by norm_num),
    standardDeviationBoundaryEvent_eq_Iic 1 (1/2) 1 (by norm_num) (by norm_num)]
  norm_num [Measure.real]
