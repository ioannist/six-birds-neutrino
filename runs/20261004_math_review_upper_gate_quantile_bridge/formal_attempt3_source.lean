import TruncGaussProof.UpperGate

open MeasureTheory ProbabilityTheory TruncGaussProof

-- Actual probability law for any real mean, positive width and positive cap.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    IsProbabilityMeasure (upperConditionedLaw (truncatedGaussianLaw μ σ) U) :=
  upperConditionedGaussian_isProbability μ σ U hσ hU

-- The quantitative tail is mass strictly beyond U, not mass at or beyond U.
example (ν : Measure ℝ) [IsProbabilityMeasure ν] (U : ℝ) :
    ν.real (Set.Ioi U) = 1 - cdf ν U := upperGate_tail_probability ν U

-- The generic statement remains valid for probability laws with atoms.
example (x : ℝ) :
    cdf (upperConditionedLaw (Measure.dirac (0 : ℝ)) 0) x =
      cdf (Measure.dirac (0 : ℝ)) x := by
  have hF : cdf (Measure.dirac (0 : ℝ)) 0 = 1 := by
    rw [cdf_eq_real]
    simp [Measure.real]
  have h := upperConditionedLaw_cdf_error (Measure.dirac (0 : ℝ)) 0 x
    (by rw [hF]; norm_num)
  rw [hF] at h
  linarith

-- This finite-prior example supplies quantile existence, not its numerical value.
example (μ σ : ℝ) (hσ : 0 < σ) :
    ∃! x : ℝ, 0 < x ∧ x < 5 ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) 5) x = (95 : ℝ) / 100 := by
  exact upperConditionedGaussian_existsUnique_quantile μ σ 5 ((95 : ℝ) / 100)
    hσ (by norm_num) (by norm_num) (by norm_num)

-- The retained-probability factor is derived for an actual capped Gaussian.
example (μ σ U x q : ℝ) (hσ : 0 < σ) (hU : 0 < U) (hx : x ≤ U) :
    cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) x = q ↔
      cdf (truncatedGaussianLaw μ σ) x = q * cdf (truncatedGaussianLaw μ σ) U := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  exact upperConditionedLaw_quantile_level _ U x q
    (truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU) hx

-- The CDF error bound is attained; it cannot be replaced by zero for every cap.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    0 < cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) U -
      cdf (truncatedGaussianLaw μ σ) U := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  rw [upperConditionedLaw_cdf_error_at_gate _ U
    (truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU)]
  exact sub_pos.mpr (truncatedGaussianLaw_cdf_lt_one μ σ U hσ)

-- At level one, U and U+1 both solve the CDF equation: global uniqueness fails.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) U = 1 ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) (U + 1) = 1 := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hFU := truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU
  constructor
  · rw [upperConditionedLaw_cdf _ U U hFU, min_self, div_self (ne_of_gt hFU)]
  · rw [upperConditionedLaw_cdf _ U (U+1) hFU,
      min_eq_right (show U ≤ U+1 by linarith), div_self (ne_of_gt hFU)]

-- At level zero, every negative threshold and the boundary give zero CDF.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) (-1) = 0 ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) 0 = 0 := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hFU := truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU
  constructor
  · rw [upperConditionedLaw_cdf _ U (-1) hFU,
      min_eq_left (show (-1:ℝ) ≤ U by linarith),
      truncatedGaussianLaw_cdf_of_nonpos μ σ (-1) hσ (by norm_num), zero_div]
  · rw [upperConditionedLaw_cdf _ U 0 hFU, min_eq_left (le_of_lt hU),
      truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _), zero_div]

-- A nonpositive cap retains no mass from a positive-width physical-gated law.
-- Totalized conditioning then gives the zero measure, not a probability law.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : U ≤ 0) :
    upperConditionedLaw (truncatedGaussianLaw μ σ) U = 0 := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hz : (truncatedGaussianLaw μ σ).real (Set.Iic U) = 0 := by
    rw [← cdf_eq_real]
    exact truncatedGaussianLaw_cdf_of_nonpos μ σ U hσ hU
  have hm : truncatedGaussianLaw μ σ (Set.Iic U) = 0 :=
    (measureReal_eq_zero_iff).mp hz
  exact cond_eq_zero_of_meas_eq_zero hm

-- The uniform error guarantee is only on probability levels. It supplies no
-- coordinate quantile bound without a modulus or local density information.
example (ν : Measure ℝ) [IsProbabilityMeasure ν] (U x : ℝ) (hU : 0 < cdf ν U) :
    |cdf (upperConditionedLaw ν U) x - cdf ν x| ≤ ν.real (Set.Ioi U) := by
  have h := upperConditionedLaw_cdf_error ν U x hU
  rw [abs_of_nonneg h.1, upperGate_tail_probability]
  exact h.2

-- The actual Gaussian quantiles exist and the finite-cap one is strictly lower.
example (μ σ U : ℝ) (hσ : 0 < σ) (hU : 0 < U) :
    ∃ x y : ℝ, 0 < x ∧ x < U ∧ x < y ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) x = (95 : ℝ) / 100 ∧
      cdf (truncatedGaussianLaw μ σ) y = (95 : ℝ) / 100 := by
  obtain ⟨x, hx, _⟩ := upperConditionedGaussian_existsUnique_quantile μ σ U
    ((95 : ℝ) / 100) hσ hU (by norm_num) (by norm_num)
  obtain ⟨y, hy, _⟩ := truncatedGaussianLaw_existsUnique_quantile μ σ
    ((95 : ℝ) / 100) hσ (by norm_num) (by norm_num)
  exact ⟨x, y, hx.1, hx.2.1,
    upperConditionedGaussian_quantile_lt_original μ σ U x y _ hσ hU
      (by norm_num) (by norm_num) hx.2.2 hy.2, hx.2.2, hy.2⟩

-- Both actual finite-cap quantiles are realizable and ordered, for any real mean.
example (μ σ U V : ℝ) (hσ : 0 < σ) (hU : 0 < U) (hUV : U < V) :
    ∃ x y : ℝ, x < y ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) x = (95 : ℝ) / 100 ∧
      cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) V) y = (95 : ℝ) / 100 := by
  obtain ⟨x, hx, _⟩ := upperConditionedGaussian_existsUnique_quantile μ σ U
    ((95 : ℝ) / 100) hσ hU (by norm_num) (by norm_num)
  obtain ⟨y, hy, _⟩ := upperConditionedGaussian_existsUnique_quantile μ σ V
    ((95 : ℝ) / 100) hσ (lt_trans hU hUV) (by norm_num) (by norm_num)
  exact ⟨x, y, upperConditionedGaussian_quantile_strictMono_gate μ σ U V x y _
    hσ hU hUV (by norm_num) (by norm_num) hx.2.2 hy.2.2, hx.2.2, hy.2.2⟩

-- The coordinate conclusion retains the supplied positive CDF-growth certificate.
example (μ σ U x y c : ℝ) (hσ : 0 < σ) (hU : 0 < U) (hc : 0 < c)
    (hx : cdf (upperConditionedLaw (truncatedGaussianLaw μ σ) U) x = (95 : ℝ) / 100)
    (hy : cdf (truncatedGaussianLaw μ σ) y = (95 : ℝ) / 100)
    (hgrowth : c * (y - x) ≤
      cdf (truncatedGaussianLaw μ σ) y - cdf (truncatedGaussianLaw μ σ) x) :
    0 < y - x ∧ y - x ≤ (95 : ℝ) / 100 *
      (1 - cdf (truncatedGaussianLaw μ σ) U) / c := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  exact upperConditionedLaw_quantile_displacement_le _ U x y _ c
    (truncatedGaussianLaw_cdf_pos_at_upperGate μ σ U hσ hU)
    (truncatedGaussianLaw_cdf_lt_one μ σ U hσ) (by norm_num) (by norm_num)
    hx hy hc hgrowth

-- Actual atomic witnesses make the scope boundaries concrete.
noncomputable def threeAtomLaw (L : ℝ) : Measure ℝ :=
  ENNReal.ofReal ((1 : ℝ) / 4) • Measure.dirac 0 +
    ENNReal.ofReal ((1 : ℝ) / 4) • Measure.dirac L +
      ENNReal.ofReal ((1 : ℝ) / 2) • Measure.dirac (2 * L)

instance threeAtom_probability (L : ℝ) : IsProbabilityMeasure (threeAtomLaw L) := by
  constructor
  simp only [threeAtomLaw, Measure.add_apply, Measure.smul_apply,
    Measure.dirac_apply_of_mem (Set.mem_univ _), mul_one]
  rw [← ENNReal.ofReal_add (by norm_num) (by norm_num),
    ← ENNReal.ofReal_add (by norm_num) (by norm_num)]
  norm_num

theorem threeAtom_cdf (L : ℝ) (hL : 0 < L) :
    cdf (threeAtomLaw L) 0 = (1 : ℝ) / 4 ∧ cdf (threeAtomLaw L) L = (1 : ℝ) / 2 := by
  have hL0 : ¬L ≤ 0 := not_le_of_gt hL
  have h20 : ¬2 * L ≤ 0 := by linarith
  have h2L : ¬2 * L ≤ L := by linarith
  constructor
  · rw [cdf_eq_real]
    norm_num [Measure.real, threeAtomLaw, Measure.add_apply,
      Measure.smul_apply, hL0, h20]
  · rw [cdf_eq_real]
    norm_num [Measure.real, threeAtomLaw, Measure.add_apply,
      Measure.smul_apply, ENNReal.toReal_add, h2L, le_of_lt hL]

-- Fixed omitted mass permits arbitrarily large coordinate displacement.
example (L : ℝ) (hL : 0 < L) :
    cdf (upperConditionedLaw (threeAtomLaw L) L) 0 = (1 : ℝ) / 2 ∧
      cdf (threeAtomLaw L) L = (1 : ℝ) / 2 ∧
      (threeAtomLaw L).real (Set.Ioi L) = (1 : ℝ) / 2 ∧ 0 < L := by
  obtain ⟨h0, hU⟩ := threeAtom_cdf L hL
  have hpos : 0 < cdf (threeAtomLaw L) L := by rw [hU]; norm_num
  refine ⟨?_, hU, ?_, hL⟩
  · rw [upperConditionedLaw_cdf _ L 0 hpos, min_eq_left (le_of_lt hL), h0, hU]
    norm_num
  · rw [upperGate_tail_probability, hU]
    norm_num

-- The secant certificate is exact for this atomic family and depends on L.
example (L : ℝ) (hL : 0 < L) :
    0 < (1 : ℝ) / (4 * L) ∧
      (1 : ℝ) / (4 * L) * (L - 0) =
        cdf (threeAtomLaw L) L - cdf (threeAtomLaw L) 0 := by
  obtain ⟨h0, hU⟩ := threeAtom_cdf L hL
  constructor
  · exact one_div_pos.mpr (mul_pos (by norm_num) hL)
  · rw [h0, hU]
    field_simp [ne_of_gt hL]; ring

-- Zero omitted mass does not order arbitrary CDF-equation solutions on a plateau.
noncomputable def plateauLaw : Measure ℝ :=
  ENNReal.ofReal ((1 : ℝ) / 2) • Measure.dirac 0 +
    ENNReal.ofReal ((1 : ℝ) / 2) • Measure.dirac 3

instance plateau_probability : IsProbabilityMeasure plateauLaw := by
  constructor
  simp only [plateauLaw, Measure.add_apply, Measure.smul_apply,
    Measure.dirac_apply_of_mem (Set.mem_univ _), mul_one]
  rw [← ENNReal.ofReal_add (by norm_num) (by norm_num)]
  norm_num

example : cdf (upperConditionedLaw plateauLaw 4) 2 = (1 : ℝ) / 2 ∧
    cdf plateauLaw 1 = (1 : ℝ) / 2 ∧ 1 < (2 : ℝ) ∧ cdf plateauLaw 4 = 1 := by
  have h4 : cdf plateauLaw 4 = 1 := by
    rw [cdf_eq_real]
    norm_num [Measure.real, plateauLaw, Measure.add_apply, Measure.smul_apply,
      ENNReal.toReal_add]
  have h2 : cdf plateauLaw 2 = (1 : ℝ) / 2 := by
    rw [cdf_eq_real]
    norm_num [Measure.real, plateauLaw, Measure.add_apply, Measure.smul_apply]
  have h1 : cdf plateauLaw 1 = (1 : ℝ) / 2 := by
    rw [cdf_eq_real]
    norm_num [Measure.real, plateauLaw, Measure.add_apply, Measure.smul_apply]
  refine ⟨?_, ?_, by norm_num, h4⟩
  · rw [upperConditionedLaw_cdf _ 4 2 (by rw [h4]; norm_num)]
    norm_num [h2, h4]
  · exact h1
