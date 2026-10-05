import TruncGaussProof.GaussianGatedCDF
import Mathlib.Topology.Order.IntermediateValue

namespace TruncGaussProof

open MeasureTheory ProbabilityTheory Filter
open scoped Topology

/-- The CDF of the constructed gated Gaussian is continuous, including at
the gate. Continuity follows from its derived absence of atoms. -/
theorem truncatedGaussianLaw_cdf_continuous (μ σ : ℝ) (hσ : 0 < σ) :
    Continuous (cdf (truncatedGaussianLaw μ σ)) := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  apply continuous_iff_continuousAt.mpr
  intro x
  have hz : (cdf (truncatedGaussianLaw μ σ)).measure {x} = 0 := by
    rw [measure_cdf]
    exact truncatedGaussianLaw_singleton μ σ x
  rw [StieltjesFunction.measure_singleton] at hz
  have hl : Function.leftLim (cdf (truncatedGaussianLaw μ σ)) x ≤
      cdf (truncatedGaussianLaw μ σ) x :=
    (monotone_cdf _).leftLim_le (le_refl x)
  have he : Function.leftLim (cdf (truncatedGaussianLaw μ σ)) x =
      cdf (truncatedGaussianLaw μ σ) x := by
    have hn := ENNReal.ofReal_eq_zero.mp hz
    linarith
  rw [(monotone_cdf _).continuousAt_iff_leftLim_eq_rightLim,
    StieltjesFunction.rightLim_eq, he]

/-- No finite threshold contains all of this law's probability. A finite
upper gate would therefore require a different law and endpoint statement. -/
theorem truncatedGaussianLaw_cdf_lt_one (μ σ x : ℝ) (hσ : 0 < σ) :
    cdf (truncatedGaussianLaw μ σ) x < 1 := by
  by_cases hx : 0 ≤ x
  · have h := truncatedGaussianLaw_cdf_strictMonoOn μ σ hσ hx
      (show x + 1 ∈ Set.Ici 0 by change 0 ≤ x + 1; linarith)
      (show x < x + 1 by linarith)
    exact lt_of_lt_of_le h (cdf_le_one _ _)
  · rw [truncatedGaussianLaw_cdf_of_nonpos μ σ x hσ (le_of_not_ge hx)]
    norm_num

/-- Every interior probability level has exactly one positive finite
coordinate under the actual constructed law. The CDF limit and continuity
are derived rather than supplied as hypotheses. -/
theorem truncatedGaussianLaw_existsUnique_quantile (μ σ q : ℝ) (hσ : 0 < σ)
    (hq0 : 0 < q) (hq1 : q < 1) :
    ∃! x : ℝ, 0 < x ∧ cdf (truncatedGaussianLaw μ σ) x = q := by
  letI := truncatedGaussianLaw_isProbability μ σ hσ
  have hevent : ∀ᶠ x : ℝ in atTop, q < cdf (truncatedGaussianLaw μ σ) x :=
    (tendsto_cdf_atTop _).eventually (lt_mem_nhds hq1)
  obtain ⟨b, hb0, hbq⟩ := ((eventually_ge_atTop (0 : ℝ)).and hevent).exists
  have hz := truncatedGaussianLaw_cdf_of_nonpos μ σ 0 hσ (le_refl _)
  obtain ⟨x, hx, hcdf⟩ := intermediate_value_Icc hb0
    (truncatedGaussianLaw_cdf_continuous μ σ hσ).continuousOn
    (show q ∈ Set.Icc (cdf (truncatedGaussianLaw μ σ) 0)
      (cdf (truncatedGaussianLaw μ σ) b) from
        ⟨by rw [hz]; exact le_of_lt hq0, le_of_lt hbq⟩)
  have hxpos : 0 < x := by
    by_contra h
    have hzero := truncatedGaussianLaw_cdf_of_nonpos μ σ x hσ (le_of_not_gt h)
    rw [hcdf] at hzero
    linarith
  refine ⟨x, ⟨hxpos, hcdf⟩, ?_⟩
  intro y hy
  exact (truncatedGaussianLaw_cdf_strictMonoOn μ σ hσ).injOn
    (le_of_lt hy.1) (le_of_lt hxpos) (hy.2.trans hcdf.symm)

end TruncGaussProof
