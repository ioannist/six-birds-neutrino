# Mathematics and mechanization review

The Gaussian mechanism is correct under its explicitly stated Gaussian,
constant-prior and independence assumptions, and its Lean coverage has been
strengthened. This is conditional mathematics; the Gaussian approximation and
required uniform CDF-error bridge have not been established for the actual
cosmological posterior. Numerical audit accounting, likelihood evaluation,
backend provenance and chain diagnostics required substantive repairs.

Fresh finite candidate evaluations retain large directional disagreements,
SPT-only forward TT localization, and a small effect of the specified staging
restriction. Several full-CMB forward controls are instead EE-dominated, with
TT dominating the reverse direction in the matched comparison. These signed
correlated allocations are not independent chi-square contributions, global
profile optima or an identification of the pipeline root cause. The broad
localization claim therefore does not survive in its broad form; retained
localization statements require the baseline and transfer direction.

The original archived chains do not establish converged posterior bounds or
the original approximately0.109eV SPT-only tightening. An earlier six-family
assessment passed the empirical gates and gave approximately0.030eV on a
current-CAMB numerical target, but its native-evaluation qualification was
subsequently suspended after the cache-return discrepancy. That historical
readout is not a currently qualified replacement for the headline. Separate
solver-version controls also show a changed likelihood shape, so a target
change cannot be reported as a sampling-only correction.

At the latest assessed checkpoint, all five fresh-transfer CAMB comparison
groups, all four sigma_time_v3 candidate numerical-policy groups and the first
fresh CLASS quad-A production assessment remain unqualified. Selected saved
calculations replay exactly, but this does not supply posterior convergence or
uniform physical accuracy. The other three fresh CLASS cohorts have no completed
production assessment. After the user instructed dropping attempts to justify
wrong or likely wrong original claims, the claim-restoration sampling campaign
was withdrawn. All61 then-live owned samplers have verified terminal exits and
preserved outputs; all80 registrations are accounted for, with no registered
sampler live. Deliberate interruption is not evidence of scientific falsity.

The broad TT-dominance statement has audited full-CMB forward counterexamples
and should be withdrawn in that broad form. The original numerical headline
is unsupported and should not be used as a result; these diagnostics alone do
not prove its numerical value false. The suspended historical near0.030eV
readout is not an admissible replacement. The completed review retains the
strongest evidence-supported mathematics and finite comparisons. Further
sampling to recover the advertised claims is withdrawn. The paper and canonical
results remain unchanged for the later manuscript phase. Completion refers to
this mathematical/code/Lean review and its verified repairs; it does not approve
the original paper's empirical claims.

Review started: 2026-10-03; continuations: 2026-10-04 and 2026-10-05. The requested pre-review checkpoint is `ffdaf4b`, following
snapshot `261d810`. Scope: all mathematical equations and conclusions in
`paper/sections`, all local Lean declarations, Gaussian metrics, toy experiments,
real-data localization and profiling, BAO calculations, posterior extraction,
and relevant inference recipes.

A later classical-diagnostic review found that finite changes of units could
produce ESS zero or a false zero-variance error, and nonfinite split Rhat.
Exact constant decimal histories could also acquire a tiny artificial variance
from a rounded mean: identical 60-step histories at 0.1 gave Rhat=0.983192.
The helpers now remove a common offset and normalize by powers of two before
forming moments. Exact constant rows retain zero within variance; identical
constant histories have undefined Rhat, distinct constant histories give
infinite Rhat, and constant histories have undefined ESS. Finite adjacent-float
variation is preserved by the tests. Twelve new tests bring the Python suite
to 119 passing tests. Twenty ordinary controls and classical mass readouts from
the four frozen guarded cohorts and two six-family SPT cohorts agree with their
pre-repair values within 1e-12 relative tolerance and preserve the classical
Rhat=1.05 decisions. These are classical helper checks, not replacement ArviZ
assessments or uniform floating-point certificates. The rank diagnostic
algorithm, native likelihood targets and running samplers are unchanged.
Before-code, failing controls, validation and distinct self-review receipts are
in `runs/20261004_math_review_ESS_scale_repair`. Its current owned-process check
confirms 24 inference samplers remain live, comprising eight SPT and sixteen
guarded CLASS families. Lean sources and the manuscript are unchanged.

The chain diagnostic provenance guard now covers CAMB as well as CLASS.
Previously identical configuration files could be pooled despite different
recorded CAMB native hashes or imported versions. Controls use actual native
hashes from the preceding version audit and explicitly labeled fixture bundles:
the old guard ignored both, while the repaired guard rejects incompatible
builds, recorded/unknown identities and conflicting or differing versions.
CAMB versions come from saved Cobaya updated metadata or explicit launch
receipts, never from the diagnostic reader's installed environment. Matching
recorded targets remain accepted; all-unrecorded legacy build identities retain
an explicit assumption. All 32 valid frozen or first-row bundles pass the guard,
and the twelve existing SPT chain bundles have matching recorded CAMB 2.0.4
versions. These checks do not recompute every diagnostic or certify native
accuracy. The rank algorithms, gates and sampled target definitions are unchanged.
A fresh full check passes 145 Python tests, the unchanged Lean build and all
74 public axiom outputs. Sources, before/after controls, frozen observed metadata
and distinct self-review are in
`runs/20261004_math_review_CAMB_backend_provenance_repair`.

## Gaussian mathematics and formal coverage

For two independent Gaussian likelihood factors with positive precisions `a,b`,
the combined mean is `μ*=(a*μ₁+b*μ₂)/(a+b)` and variance is `1/(a+b)`. Completing
the square gives

```
a*(x-μ₁)^2 + b*(x-μ₂)^2
  = (a+b)*(x-μ*)^2 + a*b/(a+b)*(μ₁-μ₂)^2.
```

The unique Gaussian mode on `x>=0` is `max(0,μ*)`. The original
`unnorm_antitoneOn_Ici` and `unnorm_le_at_zero` proofs are valid. New `Mode.lean`
proves the full unique-mode statement for every mean, positive constant
rescaling, the completed-square identity, nonnegativity of the combined mean
when both component means are nonnegative, the exact numerator criterion for a
nonpositive mean, and invariance under common scaling of both precisions.
`Product.lean` now proves these mode and boundary statements for the actual
product of exponential factors, including the inverse-variance bridge back to
the original `unnorm` factors and the exact deterministic offset gate. This
closes the algebra-to-density bridge without an assumed maximizer.

The posterior-mode statement requires a prior constant on the gated domain;
a varying prior can move the mode. Independence and exactly Gaussian factors
are toy premises, not established properties of actual CMB likelihoods.
A negative combined mean requires a negative effective component mean.
Tension between two positive means alone cannot produce it.

For the sweep law `μ₂=μ₁+ε`, `ε~Normal(-d,s²)`, the boundary probability is exactly

```
Phi((d - μ₁*(1+σ₂²/σ₁²))/s).
```

`Tightening.lean` now connects the actual product's maximum at zero to the
closed offset event and its exact lower-halfline threshold. It proves
measurability, increasing event inclusion for `μ₁>=0`, decreasing inclusion
for `μ₁<=0`, the precision-independent zero-mean event, and invariance under
positive common precision rescaling. For any one fixed offset measure it
proves the corresponding non-strict measure laws. When that measure is a
probability law these are boundary-probability inequalities. Changing the
noise law while tightening is outside the theorem. Strict inequalities for
an arbitrary measure and the Gaussian CDF identity are not supplied by the
tightening formalization. The standard-deviation bridge now defines
the boundary event by maximizing the original `unnorm` kernel product and
proves equality to the precision event. It proves the exact threshold
`-μ₁*(1+σ₂²/σ₁²)` and the corresponding non-strict measure laws directly as
functions of positive `σ₂`: antitone for `μ₁>=0`, monotone for `μ₁<=0`, with
`σ₁` and the offset law held fixed. Seven additional Lean examples check the
positive-mean inclusion, negative-mean reversal, zero-mean halfline, and an
offset showing why strict change cannot hold for every measure. At that checkpoint, all 43 exported
theorems pass transitive axiom inspection using only the three previously
allowed standard axioms. Distinct self-review receipts are in
`runs/20261004_math_review_class_backend_transition/tightening_formal_review.json`
and `standard_deviation_formal_review.json` in the same directory.

`GaussianSweep.lean` now also closes the Gaussian CDF and strictness bridge.
It defines the offset distribution as Mathlib's Gaussian measure with mean
`-d` and variance `s²`, and derives it by affine transport of the standard
normal measure. For `s>0`, standardization gives the displayed CDF formula
for the actual standard-deviation boundary event. Strict increase of the
standard normal CDF is derived from its positive density on every nonempty
interval. With the first width, mean, offset and positive noise fixed,
the probability is strictly antitone in the second width for positive mean,
strictly monotone for negative mean, and constant for zero mean. Nine formal
self-review examples check the offset sign, variance scaling, both strict
directions, zero mean, a zero-noise atom, negative-scale reversal, and failure
of strictness for an arbitrary atomic offset measure. These statements concern
exact real probabilities, with no claim of strict binary64 CDF changes or
Gaussianity of cosmological likelihoods. Receipts are in
`runs/20261004_math_review_gaussian_cdf_bridge`.

`Normalization.lean` now derives the normalization constant rather than
assuming it. For every real mean and positive standard deviation, the actual
`unnorm` kernel is Lebesgue integrable. Its integral on the closed nonnegative
half-line is strictly positive. The explicit density obtained by multiplying
by the reciprocal of that integral and setting it to zero outside the gate is
nonnegative, integrable, and has integral one. Its exact unique gated mode is
`max(0,μ)`. This proves normalization and the normalized-density mode without
a supplied normalization constant. Seven Lean examples check both signs of the
mean, the physical support, boundary uniqueness, and the excluded zero-deviation
case. At zero deviation the totalized Bochner integral returns its undefined
value zero; the positive-deviation premise prevents that convention from being
used as a normalizer. The construction does not certify the binary64
implementation or cover a varying prior or an additional finite upper gate. The distinct self-review and
full `make math_check` receipt are in
`runs/20261004_math_review_class_backend_transition/normalization_formal_review.json`.

`GaussianNormalization.lean` now also derives the closed expression
`Z=σ*sqrt(2π)*Phi(μ/σ)` for this actual half-line integral. Reflection of the
Gaussian measure gives its physical-gate probability `Phi(μ/σ)`; the Gaussian
PDF's scale identifies the original `unnorm` kernel. Integrating that identity
derives the normalizer, and the integral-derived density equals the gated
Gaussian PDF divided by `Phi(μ/σ)`. All four new results require positive
sigma and concern exact real functions. Nine formal self-review examples check
the mean sign, scale, exponent, physical support, boundary positivity, negative
sigma, and the excluded zero-width kernel and zero-variance atom. The CDF is
that of Mathlib's actual standard normal probability measure. There is no
floating-point tail or density error certificate. Receipts are in
`runs/20261004_math_review_gaussian_normalizer_cdf`.

`GaussianMeasure.lean` now constructs an actual measure from the previously
integral-normalized density. For positive sigma its total mass is one, derived
from the density integral rather than supplied as an instance. The law is
absolutely continuous with respect to Lebesgue measure, assigns zero mass to
negative coordinates, and gives every singleton (including zero) zero mass.
Every interval `(0,epsilon]` has positive mass when epsilon and sigma are
positive. Thus a density mode or positive density at zero is distinct from a
posterior atom at zero; positive-width boundary fractions have a different
readout. The random-offset probability of obtaining a boundary mode is also
distinct from the parameter-law mass of that point. A formal example proves
positive boundary-mode frequency alongside zero posterior singleton mass.
At zero sigma the constructed totalized-integral measure is zero and fails
probability normalization; an actual zero-variance Gaussian is instead a Dirac
atom. Ten formal examples check these distinctions and excluded cases. All
65 public theorem declarations are now included in the fresh transitive axiom
audit, with only the three allowed standard axioms. The combined `make math_check`
also passes all 119 Python tests. Validation and distinct self-review receipts
are in `runs/20261004_math_review_gaussian_probability_law`. These results concern
the exact Gaussian toy law and do not establish native cosmological Gaussianity,
a finite upper gate, a varying-prior extension, floating-point accuracy or MCMC
convergence. The manuscript is unchanged.

`GaussianGatedCDF.lean` extends the exact law bridge to event probabilities.
The density-built measure equals the actual Gaussian restricted to the physical
half-line and rescaled by its derived gate probability. This identity supplies
conditional probabilities for every measurable event and the CDF-difference
formula for `(a,b]` when `0<=a<=b`. For `x>=0` the constructed law has CDF
`[Phi((x-mu)/sigma)-Phi(-mu/sigma)]/Phi(mu/sigma)`; for all nonpositive x the
CDF is zero, including at the boundary. The CDF is strictly increasing on
`[0,infinity)` for every real mean and positive sigma. Thus a boundary density
mode is compatible with a strictly increasing parameter CDF and positive-width
boundary fractions. That module proves each given CDF value has at most one
nonnegative coordinate; quantile existence is supplied below. The probability
normalizer and its positivity are derived, not supplied as premises. Ten formal
self-review examples check mean signs, standardized scales, boundary zero,
positive intervals, CDF uniqueness, and the failures of an unguarded formula at
negative thresholds or reversed endpoints. Further controls distinguish zero
sigma's totalized law from a Dirac Gaussian and show positive mass beyond an
arbitrary finite upper gate. The six new exported theorems bring the axiom audit
to 71 declarations, with only the same three allowed standard axioms. The fresh
combined `make math_check` also passes all 130 Python tests. Source, failed proof
attempts, corrected builds and distinct self-review are in
`runs/20261004_math_review_gaussian_gated_CDF`. These exact Gaussian statements
retain the constant-prior and positive-width hypotheses, with no cosmological
Gaussianity, MCMC convergence, finite-upper-gate extension or floating-point
accuracy claim. The manuscript remains untouched.

`GaussianQuantile.lean` closes the exact-law quantile existence gap. CDF
continuity, including at zero, follows from the constructed law's zero singleton
mass through its Stieltjes measure; no continuity premise is supplied. The
derived probability law has CDF limit one at infinity. Continuity and the
intermediate value theorem therefore produce a positive finite coordinate for
every `0<q<1`, and strict increase proves its uniqueness. The CDF remains
strictly below one at every finite coordinate, so probability level one is
excluded substantively. Nine formal self-review examples cover negative,
zero and positive means, continuity at the boundary, excluded probability
levels, nonuniqueness at level zero across the real line, and the failure of
interior CDF-level existence for a zero-variance Gaussian Dirac law. The three
new exported theorems bring the transitive axiom audit to 74 declarations;
the combined check also passes all 130 Python tests. Evidence and preserved
failed elaboration attempts are in `runs/20261004_math_review_gaussian_quantile`.
This is an exact real-law result for positive width and the half-line gate,
retaining the constant-prior interpretation. It does not establish a numerical
inverse algorithm, floating-point error bound, finite-upper-gate quantile law,
cosmological Gaussianity or posterior convergence. The paper is unchanged.

Tightening the second constraint raises this probability when `μ₁>0`, leaves it
unchanged when `μ₁=0`, and lowers it when `μ₁<0`. Common tightening leaves the
combined mean and boundary event unchanged. The script now reports the probability from this analytic formula and Monte
Carlo standard errors. Extended-precision evaluation
avoids premature squared-ratio overflow, including the zero-mean limiting case
and representable cases where a tiny mean compensates a large precision ratio.
Unconditional monotonicity under
tightening would be false.

The old density used `1-Phi(-μ/σ)`, which rounded to zero for valid negative means.
For negative means it now evaluates
`h(alpha)/sigma * exp(-alpha*y-y^2/2)`, with `alpha=-mu/sigma`, `y=x/sigma`,
and `h=phi/SF`, using the scaled complementary error function. This avoids
subtracting enormous nearly equal log tails. SciPy remains in use for
nonnegative means; quadrature tests cover minus forty standard deviations.
For `mu=-1e100, sigma=1e-100`, the previous SciPy evaluation returned NaNs at
`x=0,1e-300,2e-300`, although the densities are finite, approximately
`1e300 * (1,exp(-1),exp(-2))`. The repaired readout recovers those values.
For `alpha>=1e150`, the implementation uses `h=alpha`: the Mills bounds
`alpha<h(alpha)<alpha+1/alpha` bound this approximation's relative error by
`alpha^-2<=1e-300`, before floating-point error. To obtain these bounds,
integrating the normal tail by parts gives
`I=exp(-alpha^2/2)/alpha - integral_alpha^infinity exp(-t^2/2)/t^2 dt`;
bounding the latter integral by `I/alpha^2` and bounding the original tail
by `exp(-alpha^2/2)/alpha` gives the stated strict inequalities.
NaN coordinates and nonfinite final numerical densities are rejected. The
receipt is `runs/20261003_math_review_validation/gaussian_density_tail_verification.json`,
and the default toy sweep was rerun in `runs/20261003_math_review_toy_density_tail`.
These are numerical checks and an analytic tail bound. The new integral-derived
normalization theorem supplies a real-valued density, but it does not certify
the implementation or the numerical Mills approximation.
Combination uses scaled precisions with extended
intermediate precision to avoid both overflow and premature weight underflow.
For `μ₁=0, σ₁=1e-100, μ₂=1e300, σ₂=1e100`, binary64 squaring previously
discarded the second weight and returned zero, falsely selecting the boundary.
The repaired mean and SD are both approximately `1e-100`: the lost shift is one
combined SD. The regression checks positive and negative second means and the
swapped order, with no absolute tolerance that could mask this small scale.
The receipt records the extended precision available on the validation platform;
this numerical check is not an interval certificate.

An additional portability control emulated binary64 intermediate arithmetic.
Combining two identical large finite means overflowed the unnormalized numerator
and returned infinity even though their convex mean is unchanged and finite.
Mixed vector cases also lost a representable three-quarter-maximum mean. The
exact-rational fallback now handles nonfinite intermediate means, preserving
both signs and exact cancellation. The native wide-intermediate controls already
passed; the emulated binary64 controls now return the exact rounded means with
no arithmetic warnings. Separate actual wide-scalar controls found an infinite
mean readout and a standard deviation rounded to zero; these unrepresentable
outputs are now explicitly rejected. A follow-up binary64 control also found
that a nonzero subnormal weight around `1e-320` gives a relative mean error of
about `1.11e-5` when multiplied by a large component mean. The fallback now
repairs subnormal weights before they round to zero. Both signs and swapped
constraints reproduce the exact rounded input-fraction mean. Six regression
cases raise the Python suite to 79 passing tests. Before/after source and output evidence is in
`runs/20261004_math_review_gaussian_binary64_intermediates`. The real-valued
Gaussian statements are unchanged; numerical readouts retain their finite,
positive-width representation requirements.

A further adversarial check found cancellation even with ordinary finite inputs.
With `epsilon=2^-52`, `mu1=sigma1=1`, `sigma2=1+epsilon`, and
`mu2=-(1+2*epsilon)`, the combined mean is strictly positive,
`epsilon^2/(2+2*epsilon+epsilon^2)`, approximately 2.465e-32. Extended arithmetic
returned zero and falsely selected the boundary. The sweep threshold similarly
lost `-epsilon^2` when `d=2+2*epsilon`; with `s=epsilon^2`, it returned 0.5
instead of `Phi(-1)`, approximately 0.15866. Exact rational evaluation of the
binary64 inputs now repairs near-cancellation, and an underflowed precision
weight is also repaired when the intermediate dtype has insufficient range.
Positive and negative cases, swapped constraints, mixed array broadcasting,
and true zero are checked. A nonzero combined mean too small for the binary64
output is rejected rather than silently assigned a zero mean. This narrows the
numerical readout's representable range, while the real-valued theorem is
unchanged. Before/after and regression receipts are in
`runs/20261003_math_review_validation/gaussian_cancellation_verification.json`;
the default toy sweep was rerun in `runs/20261003_math_review_toy_cancellation`.
The original scaled-density result assumes a positive constant. The new
normalization theorem now constructs that constant from the actual integrable
kernel and proves integral one. `GaussianNormalization.lean` now proves its
equality to the closed Gaussian-CDF expression for positive sigma, as described
above. The floating-point density implementation and Mills approximation retain
their separate numerical scope.

## Directional statistics and covariance accounting

`-2*(logL_test(train)-logL_test(best))` is nonnegative if the reference likelihood
is at least as large as the transferred point's likelihood. Global maximization
on a domain containing that point is sufficient; optimizer success is not.
`Audit.lean` proves the conditional ordering result and finite-sum identity for
actual additive likelihood terms.

Both localization runners previously inverted each block's marginal covariance.
For correlated blocks those forms do not sum to the joint quadratic form:
covariance `[[1,.9],[.9,1]]` with residual `[1,2]` gives a joint form about 7.368,
while the marginal forms sum to 5.

The repair uses signed coordinate accounting `q_i=r_i*(C^-1 r)_i`, sharing each
cross term equally between its two coordinates. Any exhaustive partition sums
to the full form. Individual terms can be negative and are not independent
block likelihoods. Uncovered bins are retained explicitly, including 2018 TE
and EE below ell 400.

`CovarianceLedger.lean` now proves the exact-real solve and grouping bridges.
Positive definiteness derives invertibility, so an actual covariance solve
equals inverse multiplication. Signed coordinate allocations sum to the full
quadratic form; exhaustive finite grouping preserves the endpoint difference
even when the precision matrices differ. Optional group labels retain the
unlocalized remainder. Only the full inverse-covariance form is proved
nonnegative. The coordinate-sum bridge itself is definitional. Formal
self-review examples verify a positive definite precision matrix with
allocations -1 and 3, a displayed sum -1 with remainder 3, an empty index set,
and different endpoint precision matrices. This is exact algebra, with neither
a floating-point error certificate nor an assumed native likelihood identity.

Each endpoint uses its actual effective covariance, including parameter-dependent
SPT2018 beam covariance and Hartlap correction where present. Nuisance prior
penalties and covariance normalization are checked independently against native
`-2 logL`. The complete ledger is

```
native Delta chi2 = heatmap Delta Q + uncovered Delta Q
                   + Delta prior penalty + Delta covariance normalization.
```

Covariance must be finite, symmetric, and positive definite. Only floating
roundoff asymmetry is symmetrized; singular covariance is not replaced by a
pseudoinverse. These native reconstruction checks are numerical consistency
checks, not interval certificates.
Finite input and positive definiteness do not guarantee a representable
floating-point solve or allocation. Diagonal positive-definite examples with
variance 1e-308/residual 1e308 and variance 1e-320/residual 1 previously returned
NaN or infinity from the covariance solver. With unit covariance and residual
1e200, the solve remains finite but its quadratic allocation overflows.
The shared solver and signed-allocation helper now reject these nonfinite
outputs explicitly. Three regression cases cover the observed failures;
finite computations retain their existing formulas and results.
BAO callers that only validate covariance or precision now use a zero
right-hand side, rather than solving for the mean or residual as a side
effect of validation. This preserves finite quadratic forms whose unrelated
inverse solve is unrepresentable. The BAO helper separately rejects nonfinite
means/predictions, overflowing residuals or quadratics, and negative computed
quadratics; dataset loading also rejects an unrepresentable inverse covariance.

A further projection bug affected positive subnormal covariance entries.
Symmetrizing by `C/2+Cᵀ/2` erased the smallest positive diagonal, and changed
other already-symmetric tiny variances. For one-bin variance equal to 3 or 17
units of the smallest binary64 subnormal and residual equal to that variance,
the old wrapper returned 0.75 or 1.0625 instead of the correct solve near one;
the one-unit case was rejected as singular. The repaired projection preserves
already-symmetric entries and averages only unequal pairs. The tolerance
arithmetic also avoids an incidental NumPy underflow exception under strict
error settings. Three regression cases agree with direct Cholesky solves,
and twenty ordinary or roundoff-asymmetric controls are bit-identical to the
old calculation. Both authoritative native audit rechecks are byte-identical
to the preceding accepted results. These are representable-solve controls,
not an inverse or uniform floating-point error certificate. Receipts are in
`runs/20261004_math_review_covariance_subnormal_repair`.

The localizer had a further signed-aggregation failure: subtracting each pair
of finite coordinate allocations could overflow before group cancellation.
For covariance `[[5,2],[2,1]]`, train residual `[sqrt(5e307),sqrt(5e307)]`,
and reference residual `[sqrt(1.5e308),0]`, both endpoint quadratic forms are
finite. The old code returned a negative infinite group and a NaN accounting
error, accepting the two infinities as equal. It also silently broadcast
different endpoint dimensions. The repair sums endpoint allocations with
`math.fsum`, using exact rational accumulation when intermediate sums overflow,
and rejects unrepresentable reported groups, nonfinite or nonvector edges,
and mismatched endpoint dimensions. Six new regression cases cover these
failures. Both authoritative fixed-spectrum audit bundles pass fresh native
rechecks; ranked groups are unchanged and all heatmap changes are below
9.3e-13. Native reconstruction discrepancies are at most 5.6e-10. Receipts and
archived failure reproduction are in
`runs/20261004_math_review_signed_localization_repair`. Exact rational
accumulation concerns the computed floating allocations, not the exact
covariance solve or an interval certificate.

## Profiling domains and optimization

The old reference fixed shared parameters at the old test fit, rather than
releasing them. Cross and reference starts could also freeze unoptimized
nuisance values differently. The repaired cross profile starts from the
evaluated transferred point; the reference releases shared and selected nuisance
parameters, retains the same frozen values, and uses cross and own-fit starts.
Failures in either direction give a nonzero exit code. Exported endpoints allow
accounting verification without repeating optimization. These are numerical
multistart optima, not globally certified maxima.

Missing shared parameters are no longer replaced by test defaults. Cosmological
shared parameters are rejected because this runner does not recompute spectra.
The twelve-parameter nuisance cap remains explicit. Incorrect amplitude bounds
on CIB spectral indices have been removed.

Three full-nuisance MAP configurations used `gtol=1000000`. Their successful
archived fits stopped after zero iterations, with absolute gradients around
23677 for 2018 and 3522 for D1. These are not full-nuisance optima. The configured
tolerance is now `1e-6`; outputs state their fixed-spectrum scope and absence of
global certification.

## Fresh SPT evaluations and their scope

The review environment uses `candl-like 2.2.0` and the original data revisions:
`candl_data` commit `c4eb8fbc5b0eb259ba487494b3cff918eac5c47a` and
`spt_candl_data` commit `bfe809a140087d19412aa6bc8c8d4ba18840b315`.
The package list is retained in `runs/20261003_math_review_validation`.

Native unprofiled totals reproduce the archived values to numerical roundoff:
approximately 2222.172 for D1 given 2018 and 313.568 in reverse. Corrected
accounting still puts the largest positive contribution in TT at ell 2500–3000.
Repaired multistart profiled totals are 849.627 and 414.390. The specified
common-staging restriction gives 837.153 and 415.793, about a 1.47 percent
reduction in the first direction and a 0.34 percent increase in reverse.

Endpoints and independent native-accounting verification are in
`runs/20261003_math_review_profiled_multistart` and
`runs/20261003_math_review_profiled_staging_multistart`. The comparison is in
`runs/20261003_math_review_staging_compare`; fresh unprofiled verified accounting
is in `runs/20261003_math_review_verified_native_covariance`.

The explicitly shared parameters are tSZ and kSZ amplitudes. The fits use
packaged test spectra, not cosmologies fitted from each survey. They establish
nuisance-transfer diagnostics at those spectra, not cosmological cross
prediction. The missing bridge requires a Boltzmann calculation at the train
cosmology and target nuisance profiling. Different seasons, noise, and nuisance
models also require a declared statistical comparison before treating shifts as
deterministic packaging inconsistency. The SBT discussion is operational framing,
not a formal theorem supplying these missing steps.

The staging restriction removes extra D1 support; it does not match full window
functions or resolution. D1 cannot supply 2018 TE/EE modes between ell 300 and
400. This tests the specified extensions rather than every staging explanation.

## Posterior summaries and convergence evidence

The old extractor labeled odd and even rows as first and second halves, ignored
holding times in its autocorrelation calculation, and concatenated separate
chains for sequential diagnostics. Those Rhat and ESS values do not establish
convergence. The repair retains chain boundaries, restores integer holding times,
uses chronological split Rhat with unbiased within-chain variances, and an FFT
autocorrelation estimate with initial positive monotone pairs. Noninteger weights
or excessive expansion leave diagnostics explicitly unavailable. Burn-in remains
a per-file fraction of stored rows. These are scalar proxies, not rank-normalized
bulk and tail convergence certificates; bad Rhat and small ESS produce warnings.

The interpolated quantile depended on how identical samples were split into
compressed rows. The new inverse empirical CDF is invariant to that representation.
An additional threshold control found that floating cumulative normalization could
still violate this property: weights `[418,22]` on values `[0,10]` gave p95 zero,
while the identical distribution represented by weights `[201,217,22]` on
values `[0,0,10]` gave ten. Quantile thresholds now use exact integer mass and
the rational representation of the supplied binary64 probability. Integer
holding times use a checked int64 cumulative sum; fractional or larger weights
use arbitrary-precision integer mass after clearing their dyadic denominators.
Positive support is retained at both endpoints, and a tiny positive weight
between equal endpoint weights correctly determines the median. These are exact
empirical calculations for the represented inputs, not exact cosmological
posterior quantiles. Rechecking 127 quantile fields across the five archived
summaries and all second-snapshot variables finds no changes to their recorded
values. The control and impact receipt is
`runs/20261003_math_review_validation/exact_quantile_impact.json`.
The following are empirical sample summaries, not converged cosmological bounds.

| Archived run | Corrected p95 in eV | Chronological split Rhat | Scalar ESS proxy |
| --- | ---: | ---: | ---: |
| SPT2018 plus DESI | 0.194525 | 1.8604 | 4.81 |
| D1 plus DESI | 0.098077 | 1.2011 | 11.39 |
| CMB2018 plus DESI | 0.079818 | 0.9998 | 8.99 |
| CMB D1 plus DESI | 0.067653 | 1.4835 | 5.04 |
| Short CMB2018 seed repeat | 0.089263 | 1.3159 | 5.75 |

Inputs and corrected diagnostics are in
`runs/20261003_math_review_chain_diagnostics`. Native CMB2018 and CMB D1 progress
files report `Rminus1=22.408235` and `15.011355`. Scalar Rhat near one cannot
override poor multivariate or tail evidence. Histogram mode estimates and mass
inside an arbitrary small boundary interval do not certify an exact boundary mode.

The extractor follows relocated files, handles derived `.paramnames` entries,
validates weights and column names, resolves the explicit `mnu=mnu_sample`
identity's prior, and reports unknown when no lower bound is declared. CLASS
recipes now serialize species masses with seventeen significant digits instead
of eight decimal places. Comparison JSON, Markdown summaries, density overlays,
and quantile tables now explicitly identify empirical chain summaries. The
summaries include diagnostic warnings; the figures state that they do not verify
convergence or quantile precision. Corrected archived CMB summaries were rendered
and visually checked in `runs/20261003_math_review_comparison_scope`, without
altering their source bundles or the manuscript.

A further coordinate-identity check found that duplicate names in a chain
header or `.paramnames` file were silently resolved to the first column. A
synthetic record containing two conflicting mass columns (0.02/0.03 eV and
4.9/4.8 eV) could therefore produce an unambiguous-looking mass summary.
The loader now requires nonempty, unique names after removing the GetDist
derived marker, and checks the complete header of each chain even when metadata
lists only a prefix of its coordinates. The diagnostic workflow rejects such
ambiguity before writing results. Three format controls and an integration
control bring the Python suite to 123 passing tests. All 32 frozen SPT and
guarded CLASS/grid-12 family reads plus five archived original histories retain
exactly their previous values and holding weights; mass summaries are unchanged.
Lean sources match the prior 65-theorem audit, with no new Lean build claimed.
Before-code, probes, impact validation and distinct self-review are in
`runs/20261004_math_review_chain_column_identity_repair`. This changes input
identity validation, with no change to likelihood targets, sampler rules or
diagnostic thresholds.

The comparison density loader also needed this coordinate contract. Its
GetDist path bypassed the extractor's checks and could silently plot the wrong
mass column. Two actual GetDist controls reproduce a density mode near
4.80019 eV while the intended first mass coordinate lies in 0.01--0.03 eV:
one uses duplicate `mnu`/`mnu*` metadata, and the other swaps unique metadata
names relative to the chain header. The comparison now validates the requested
mass through the existing raw loader before calling GetDist. Both inconsistent
inputs are refused; a valid control's complete density grid remains byte-identical.
The added path accepts all 32 latest frozen SPT/CLASS/grid-12 family bundles
and five original histories, with unchanged downstream arguments and chain
bytes. This is a validation compatibility check, not a recomputation of all
37 smoothed density grids. Two regression controls pass, and the fresh combined
`make math_check` passes 132 Python tests, the unchanged Lean build, and all
74 theorem axiom audits. Before-code, fixtures, actual readout probes,
compatibility checks and distinct self-review are in
`runs/20261004_math_review_density_column_identity_repair`. Likelihoods,
samplers, quantile estimators, diagnostic gates, Lean sources, canonical
summaries and the paper are unchanged.

The relative quantile-MCSE scale had a separate floating-point defect: direct
squaring of raw parameter coordinates gave population SD infinity for
`[-1e200,1e200]` and zero for `[-1e-200,1e-200]`, though both SDs are finite
and representable. Sixty identical decimal values at 0.1 also acquired an
artificial SD of 4.16e-17. The diagnostic CLI now computes the same
full-postburn population SD from represented integer holding-time draws with
power-of-two scaling and offset removal before squaring. Exact constant
histories retain SD zero; fractional importance weights are rejected and
existing expansion resource limits apply. Equal-length deletion is not used
to define this scale. Large opposite-sign values, adjacent floating-point
coordinates and subnormal variation are covered by analytic controls. The
ordinary known-normal diagnostic report is byte-identical to the pre-repair
report. Multiplying its coordinates and prior width by 2^700 or 2^-700 no
longer causes false diagnostic rejection; rank diagnostics and the appropriately
scaled MCSE and quantiles agree. Seven controls bring the suite to 130 passing
tests. All 54 parameter assessments in the six then-latest frozen SPT and
guarded CLASS cohorts retain every individual gate decision, and their SDs
agree within 1e-12 relative tolerance. A distinct self-review independently
computes the weighted first and second moments with exact binary64 rational
arithmetic. The absolute mass targets, rank/MCSE algorithm, physical targets,
and running samplers remain unchanged. Current Lean sources match the prior
65-theorem audit; no fresh Lean build or universal floating-point certificate
is claimed. Before-code, probes, impact checks and self-review are in
`runs/20261004_math_review_relative_MCSE_scale_repair`.

The upper-prior interpretation in `paper/sections/methods.tex:98` needs an
additional scope distinction. The 28 families in the six latest frozen SPT
and guarded CLASS assessments all use the declared flat mass prior `[0,5]`.
Their largest saved postburn mass is 0.36260186 eV, and none is near the upper
gate. This supports no observed contact with that gate; it does not establish
insensitivity to widening the prior. The currently declared posterior has zero
mass above 5 by definition. The unknown tail relevant to a prior-sensitivity
claim belongs to the posterior under a specified wider prior, which the
currently conditioned histories cannot estimate.

An exact continuous counterexample fixes one nonnegative likelihood: density
47/10 on `[0,1/5]`, 3/50 on `[5,6]`, and zero elsewhere. With a flat prior on
`[0,5]` its p95 is 19/100 eV; with a flat prior on `[0,6]` its p95 is 31/6 eV.
The likelihood is unchanged and the prior's constant density cancels in each
posterior normalization. Thus a small conditional p95 alone cannot certify an
inactive upper prior. This counterexample does not claim the actual cosmological
likelihood has a distant mode or substantial mass beyond 5.

If a specified wider nonnegative posterior has independently established tail
probability epsilon beyond U, with `0<=epsilon<1`, then conditioning on `[0,U]`
changes its CDF by at most epsilon uniformly, attaining that difference at U.
For `x<=U`, the difference is `F(x)*epsilon/(1-epsilon)<=epsilon` because
`F(x)<=1-epsilon`; for `x>U`, it is `1-F(x)<=epsilon`. This is a probability-scale
bound; a coordinate quantile-error bound also needs an inverse-CDF modulus or
suitable local density control. A distinct self-review integrates the
counterexample by a separate exact-rational rectangle accumulation and recounts
all saved holding times and extrema directly from text. It includes atomic
controls for the tail-CDF bound, which does not require an atom-free posterior.
Existing fixed-prior readouts, their qualified/provisional statuses, native
models and claim decisions remain unchanged. Sources, exact calculations,
scope clarification and self-review are in
`runs/20261004_math_review_upper_prior_scope`; the paper remains untouched.

The target checks now also enforce unit sampler temperature. Previously,
matching priors, likelihoods, and physical settings could still combine raw
chains from different heated distributions, and the extractor accepted
declared heated output. Cobaya samples `p^(1/T)` when `T!=1`; raw holding
weights therefore describe that target. For a unit half-normal on `x>=0`,
heating to `T=2` multiplies the 95th percentile by `sqrt(2)` while leaving its
mode at zero. This illustrates why matching model configuration or mode alone
does not protect original-posterior quantiles. Diagnostics reject non-unit
temperature, and raw summaries and overlays reject available metadata that
declares it. Cooling needs a separate explicit workflow; these routines do not
treat importance weights as Markov holding times. The dependency follows the
official [Cobaya tempered-MCMC specification](https://cobaya.readthedocs.io/en/latest/sampler_mcmc.html#tempered-mcmc).
Six integration cases exercise diagnostic, extraction, and comparison refusal
with both supported sampler identifiers; two controls preserve summaries for
default versus explicit unit temperature. A prior-version extractor replay,
the repaired refusal, and checks of all 24 existing restoration-chain targets
are recorded in `runs/20261003_math_review_validation/temperature_guard_verification.json`.

## BAO and other numerical checks

`D_M=(1+z)D_A`, `D_H=c/H`, and `D_V=(z*D_H*D_M²)^(1/3)` are correct with consistent
units. The loader permutes mean and covariance together. All eight vendored
subsets have positive definite covariance. The ELG alias now matches the filename;
ambiguous selections fail. Gaussian precision and predictions are validated.
BAO utilities are importable without the optional CMB stack.

TT/TE/EE conversion uses the usual ell factor and explicit microkelvin-squared
units. Missing required or truncated spectra fail instead of being fabricated.
The optional lensing branch previously used incorrect pp normalization and zero
kk. It is rejected in favor of the native candl lensing adapter; no production
configuration uses it. The installer requests `candl-like`, rather than the
unrelated `candl` neural-network package.

The toy rewrite is a covariance-weighted projection. Its improvement identity
is correct for nonzero templates; an arbitrary near-zero cutoff violated template
rescaling invariance and has been removed. Residual-selected templates give a
descriptive fitted improvement, not calibrated independent predictive success.

## Cosmological restoration continuation

The full inference stack is now installed in
`/tmp/neutrino-math-review-venv`; exact package versions are recorded in
`runs/20261003_math_review_validation/restoration_environment.txt`.
The original full-model smoke evaluation failed because the BAO adapter cast
Cobaya's length-one distance arrays directly to Python floats. NumPy 2.4 rejects
that conversion. The repaired bridge accepts a single finite observation per
redshift and rejects multiple values. Both complete CLASS/Planck/SPT/DESI models
now evaluate finitely at the reference point; the failed and intermediate smoke
bundles remain as history, and `20261003_math_review_cosmology_smoke_declared` is
the successful receipt.

The candl adapter now declares its actually consumed nuisance and prior scalar
parameters through Cobaya's support API, including `tau`. It receives current
values through declared inputs, rather than opportunistically reading unrelated
provider scalars. This makes shared scalar dependencies explicit in likelihood
cache keys. A real Cobaya toy-provider regression changes a parameter consumed
by two components and checks cached results against uncached reevaluation. The
two full-baseline configs let Cobaya infer these inputs rather than supply an
incomplete explicit list. Structural candl errors now propagate rather than
silently returning an impossible likelihood.

The first full-model smoke also showed slightly different Planck likelihoods at
identical cosmological parameters, because each SPT release requests a different
maximum multipole and thereby changes the CLASS calculation settings. The new
`run_cosmological_audit.py` constructs one model containing both SPT likelihoods
and one shared Boltzmann backend. It rejects differences in theory, sampled
parameterization, hard priors, or configured completion components. Each fit
maximizes its own SPT likelihood plus the common configured completion, while
excluding the separate Cobaya prior density and retaining the hard prior bounds.
Native candl internal priors remain part of each packaged lens. Its shared
transfer vector contains the cosmological parameters, including mass. Sampled
non-cosmological parameters are profiled on the target lens. Other candl nuisance
parameters remain at the explicitly recorded packaged defaults.

This objective is distinct from maximizing SPT alone. The output therefore
separates the joint candidate-reference difference from signed SPT, BAO, and
Planck contributions. It does not label the SPT component as a difference from
an SPT-alone maximum. The numerical reference domain contains the cross candidate;
a reference fit starts there and retains the better candidate if optimization
fails. This proves ordering between retained witnesses, not attainment of a
global supremum. The run records optimizer termination, endpoints, fresh spectra,
full covariance accounting, internal prior and determinant terms, and their
native likelihood bridge. `verify_cosmological_audit.py` independently recomputes
exported endpoints and spectra with a fresh model. The SPT+DESI baseline and
one-sided D1 support-cut audit are completed and freshly verified; results are
recorded below. The original full CMB+DESI multistart run remains live in
`runs/20261003_math_review_cosmological_cmb_desi`; incomplete fit progress is not
final audit evidence. Symmetric support cuts remain a separate optional control.

`diagnose_cobaya_chains.py` adds optional ArviZ rank/folded split Rhat, bulk and
tail ESS, quantile ESS, and quantile Monte Carlo standard error. Integer holding
times are expanded, chain chronology is preserved, and any prefix draws dropped
to equalize chain lengths are reported. Full-chain quantiles and chronological
half differences retain the complete post-burn-in records. Distinct bundles
must have distinct recorded seeds and identical targets and parameterizations;
separate starts remain an explicit independence assumption. Diagnostic thresholds
are empirical checks, never mathematical convergence certificates. Zero quantile
MCSE from tied order statistics is flagged as unresolved continuous-posterior
precision, rather than exact knowledge of a mass bound.

The adaptation-scope review checks the pinned Cobaya implementation against
28 existing frozen histories and complete proposal-log prefixes. Covariance
updates occur strictly inside the retained history of all twelve SPT families
and all eight guarded quadrature families. The eight medium families have no
logged covariance updates at this observation. Cobaya's learning checkpoint
coordinate is the number of stored collection rows, not the smaller accepted
count reported by its internal convergence test after discarding a split.
Output thinning is disabled; the review preserves each family's actual
oversampling settings. All eight guarded quadrature families have now logged
an update, superseding the earlier seven-family observation at its later time.

Target invariance of each fixed proposal kernel alone does not prove that
history-dependent adaptation preserves the target. An exact two-state control
uses a uniform target and symmetric kernels with flip probabilities 1/4 and
3/4. Both kernels are reversible, irreducible and aperiodic. Selecting the
faster kernel in state 0 and the slower kernel in state 1 produces identical
transition rows (1/4, 3/4), whose stationary distribution is nonuniform. This
refutes the general inference; it does not demonstrate a failure of Cobaya's
particular adaptation. Existing SPT empirical gate passes remain intact, and
the CLASS readouts remain provisional. No adaptive-MCMC convergence theorem,
new burn rule or proposal-freezing rule is asserted. Source inspection, exact
holding-time recounts, separate log-coordinate parsing and rational controls
are retained in `runs/20261004_math_review_adaptive_history_scope`. Samplers,
diagnostic gates, production Python, Lean and the paper are unchanged.

The archived CMB2018 seed-0 and short seed-1 check has rank Rhat approximately
1.185, bulk ESS 9.88, tail ESS 35.26, and chronological p95 drift 0.0101 eV. It
fails the recorded thresholds. The receipt is
`runs/20261003_math_review_chain_diagnostics/cmb2018_rank_tail_seed_check.json`.
Canonical-summary code now preserves diagnostic warnings and marks legacy
unrecomputed diagnostics explicitly; neither canonical paper artifacts nor the
paper were regenerated.

Replacement SPT+DESI chain configurations are prepared in
`runs/20261003_math_review_spt_desi_chain_configs`. They explicitly set the same
CAMB lmax of 4095, taken from the released window-function support, retain the
original target priors and likelihood components, and use dispersed normal
starting references centered on numerical fit candidates. Only starting
references and sampler settings are changed. Seeds are distinct across all
prepared replicas. Eight jobs (A301–304, B305–308) have started, four per lens,
with a 20,000 stored-sample cap, native convergence stopping, and no oversampling
thinning. These settings are resource/stopping controls, not evidence of
convergence. No replacement mass bound is claimed before independent-chain
rank/tail and quantile-precision checks pass. For SPT+DESI, assess p95 MCSE at
0.005 eV; for the smaller full-baseline shift, target 0.001 eV. Additional prepared
replicas or longer chains remain available if diagnostics require them.

A separate continuation self-review checked that matched completion is rejected
when substantive inputs differ, source and reference domains nest, fresh native
endpoints can be reconstructed without trusting stored audit scalars, and tied
or fractionally weighted rows cannot masquerade as resolved mass-limit precision.
The original full CMB multistart optimization, its controls, and all replacement
chains remain empirical work in progress. The warm-start baseline is complete
and freshly verified below.

## Completed cosmological candidate audits and sampling restoration

The completed SPT+DESI baseline uses seven shared cosmological parameters,
including neutrino mass, one CAMB backend, and the recorded packaged nuisance
defaults. Its directional joint differences are 488.2968 (D1 given 2018) and
79.1330 (2018 given D1). The signed SPT contributions are 487.8205 and 79.6093;
the BAO contributions are +0.4763 and -0.4763. Fresh model evaluation reproduces
all endpoint likelihoods, spectra, ledger fields, and localization entries. The
native SPT reconstruction errors are below 5e-11. Both directions retain
TT ell 2500–3000 as the largest positive localized contribution. These are
retained numerical candidates, not globally certified optima or SPT-alone fits.

The one-sided D1 cut retains TT ell 750–3000 and TE/EE ell 300–3000 while
leaving the 2018 support intact. Its freshly verified joint differences are
486.6099 and 80.5226, changes of -0.3455% and +1.7561%. Native SPT contributions
are 486.1509 and 80.9643, with reconstruction errors below 5e-11. TT ell
2500–3000 still leads both directions. Both baseline and staging use CAMB
lmax 4095. Each run refits numerical candidates; the unchanged 2018 source fit
improves by about 0.1056 in log likelihood in the warm-started staging run, so
this comparison does not certify the isolated support effect at an exact global
optimum. It does retain the large asymmetry and small candidate-level change.
Receipts are the baseline and staging `accounting_verification.json` files and
staging `comparison.json` under `runs/20261003_math_review_cosmological_*`.

`build_cmb_bao_proposal.py` constructs response-based positive-definite proposal
matrices for these MCMC targets. It records Gauss–Newton SPT/BAO and native
Gaussian-prior contributions. For the full baseline it also reconstructs the
Plik TT and PR4 lensing native Gaussian components at every difference point,
and adds only positive diagonal low-l curvature. Covariance derivatives,
nonlinear residual curvature, and low-l cross curvature are omitted explicitly.
Spectral regularization is allowed only for the sampler proposal; these matrices
are never treated as posterior covariances or replacements for likelihood data.
Saved matrices reconstruct both SPT and full-CMB proposals, all are positive
definite, and none required eigenvalue flooring in these runs.

Eight full CMB+DESI chains have started (A501–504, B505–508). They retain the three-species CLASS mass mapping and the
original completion and priors. Eight CLASS threads reproduce all six native
likelihood components exactly at a shared benchmark point and reduce elapsed
evaluation time from 33.0 to 8.1 seconds. This checks the benchmark point only.
The four additional SPT chains and the CMB chains use the verified correlated
proposals and proposal learning every ten sampled dimensions. These sampler
choices leave the target unchanged. Bounds remain unclaimed until the recorded
independent-chain diagnostics and quantile precision checks pass.


The early immutable chain snapshots in
`runs/20261003_math_review_chain_snapshots_early` fail the independent-chain
thresholds for both baselines and both lenses. SPT mass rank Rhat is about 1.05
and 1.18 with bulk ESS 79 and 25; full CMB mass rank Rhat is about 1.71 and 1.59
with bulk ESS below 4. These short, drifting chains provide progress checks,
not replacement mass bounds. Sampling continues. The completed warm-start full CMB audit uses explicit starting witnesses and
eight threads. The original multistart job remains running; its incomplete
endpoints are not final results.

The retained native priors require an additional attribution distinction.
The pinned [2018 dataset configuration](https://github.com/Lbalkenhol/candl_data/blob/c4eb8fbc5b0eb259ba487494b3cff918eac5c47a/candl_data/SPT3G_2018_TTTEEE_v0/SPT3G_2018_TTTEEE.yaml)
contains a Gaussian optical-depth factor with mean 0.054 and SD 0.0074, while
[D1](https://github.com/SouthPoleTelescope/spt_candl_data/blob/bfe809a140087d19412aa6bc8c8d4ba18840b315/spt_candl_data/SPT3G_D1_TnE_v0/SPT3G_D1_TnE.yaml)
uses mean 0.051 and SD 0.006. The packaged targets therefore vary this prior as
well as SPT data and transformations. The full baseline additionally includes
Planck low-l EE. The repository does not establish independence of this
additional optical-depth factor from that completion. Current runs compare
these explicitly packaged targets; they cannot isolate SPT data alone.

The adapter now supports explicit `exclude_prior_parameters`. It removes whole
prior factors before any native JIT evaluation, rejects missing names and
partial removal of correlated factors, and records retained means and covariance
matrices. Default targets remain packaged. Prepared full CMB control configs
remove only the native optical-depth factor and retain Planck low-l EE and every
other packaged prior. Native evaluation verifies that removal changes only the SPT likelihood, by
the exact Gaussian optical-depth penalty, with all other completion components
equal at each tested point. The receipt is `native_verification.json` under
`runs/20261003_math_review_tau_prior_control_configs`. These configs define a
distinct target, with no inference result yet.
This creates a reproducible route to assess prior attribution without silently
changing running jobs or accepting a material claim downgrade.


The full CMB+DESI warm-start candidate audit is now completed and independently
recomputed with a fresh model. Directional joint differences are 62.3901 and
23.1908, with signed SPT contributions 60.4275 and 25.1711. Native SPT accounting
errors are below 1e-11. Unlike the SPT+DESI audit, EE ell 2000–2500 leads in the
D1-given-2018 direction (23.4833), followed by EE ell 2500–3000 (12.5445) and TT
ell 2000–2500 (10.0766). TT ell 2500–3000 leads in reverse (10.3573). Thus TT
localization is established for the recorded SPT+DESI scope and does not hold
universally across the two implemented baselines. Their theory backends and
foreground freedom also differ, so this comparison does not isolate completion
as the sole cause. Both baselines explicitly use three massive neutrino species.
The 2018 full-baseline source candidate and the
reverse profile reach the configured kSZ upper bound of 10; these are conditional
on that foreground domain. No global optimum or calibrated significance is
claimed. The original full-baseline multistart audit has also completed and
passed fresh endpoint, spectrum, localization, and native component verification.
Its joint candidate differences are 62.5905 and 23.1658, changes of +0.3211%
and -0.1076% from the warm-start audit. Signed SPT contributions are 60.6104 and
25.1468, with native reconstruction errors below 8e-12. EE ell 2000–2500 leads
forward (23.5248), while TT ell 2500–3000 leads in reverse (10.4465). Source
parameterization, priors, completion, and likelihoods match the warm-start
baseline; multistart candidates and retained references remain numerical,
without global optimum or calibrated significance certificates. Endpoint and
comparison receipts are in `runs/20261003_math_review_cosmological_cmb_desi`.

The one-sided support-cut full CMB audit has completed and passed fresh native
verification in both directions. Its joint candidate differences are 64.6220
and 23.3945, increases of 3.5772% and 0.8785% from the packaged warm-start
baseline. Signed SPT contributions are 62.6032 and 25.4811, with native accounting
errors below 2e-12. EE ell 2000–2500 still leads in the first direction and TT
ell 2500–3000 in reverse. The A source likelihood is unchanged, and exported
SPT spectra retain ell coverage through 4095 in both runs. The intervention
removes extra D1 support; it does not equate the surveys' windows or resolution.
These separate bounded numerical fits show a small effect for the recorded
candidates, without certifying a global optimum or the exact optimized effect.
Endpoints, verification, and comparison receipts are in
`runs/20261003_math_review_cosmological_cmb_desi_staging`.

A CAMB threading control recomputes three identical points using one, four, and
eight threads. Native component differences remain below 1.2e-12, while warmed
evaluation times decrease from about six seconds to 1.2 seconds. Four additional
SPT chains (A401–402, B403–404) now use eight threads and the verified correlated
proposals, leaving the original eight chains running. Eight full CMB chains are
now running, four per lens. More draws remain necessary for posterior precision.

`verify_chain_targets.py` checks selected stored rows against fresh native
likelihoods, including every component, the joint likelihood, and external prior
and posterior accounting. Three rows from each of eight early SPT snapshots pass
with explicitly recorded text-rounding tolerances. This is pointwise consistency
evidence, not a check of every transition or a convergence certificate. The first
CMB row initially fails: rounding its slow cosmological parameters to Cobaya's
default eight significant figures changes the fresh posterior by about 0.0635.
Replaying the seeded exact initial slow parameters reduces this error to 1.1e-5,
consistent with the rounding of stored likelihoods and fast parameters. This
identifies an output-fidelity issue for that row; it does not independently
validate all rounded CMB rows or quantify Boltzmann numerical error.

`run_cobaya.py` now selects `FullPrecisionMCMC` in the resolved bundle for all
future runs, preserving the input target and sampler options. It writes seventeen
significant figures. On resumption it
restores the file with a round-trip reader and freshly evaluates its last point,
correcting the upstream pandas reader's small conversion losses without changing
the target or acceptance rule. An actual Gaussian sampler test compares saved values to
its full in-memory collection with exact binary64 equality, including appended
resumed output and preservation of the existing file prefix. This tests numeric
serialization, not the upstream RNG checkpoint/continuation semantics. A503–504 and B507–508
use this format. Three stored A503 rows also reproduce fresh native likelihoods
with absolute tolerance 1e-7 and relative tolerance 1e-10. Original outputs are
preserved. Sampler seed handling and diagnostic seed checks accept both supported
sampler identifiers, retaining distinct-seed and matched-target requirements.
Receipts are in `runs/20261003_math_review_chain_precision_check` and the numerical
validation folder. Both output formatting and row verification are distinct from
posterior convergence, which remains unresolved.

The second immutable snapshots include all twenty running replicas and repeat
the diagnostics for every sampled variable. All four baseline/lens combinations
still fail the declared thresholds. The mass diagnostics are:

| Baseline and lens | Chains | Rank/folded Rhat | Bulk ESS | Tail ESS | p95 MCSE (eV) | Target (eV) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPT+DESI, 2018 | 6 | 1.0973 | 51.2 | 76.3 | 0.01711 | 0.005 |
| SPT+DESI, D1 | 6 | 1.1350 | 34.0 | 138.1 | 0.01162 | 0.005 |
| Full CMB+DESI, 2018 | 4 | 1.1516 | 29.7 | 55.1 | 0.00626 | 0.001 |
| Full CMB+DESI, D1 | 4 | 1.1741 | 18.3 | 30.0 | 0.01918 | 0.001 |

These snapshots provide no replacement mass bounds. Fresh native checks of the
first, middle, and last stored rows from each of the four full-precision CMB
replicas reproduce every component and prior/posterior field exactly: twelve
rows with zero recorded discrepancy. Receipts, source hashes, and diagnostics
are in `runs/20261003_math_review_chain_snapshots_second`. This remains pointwise
target consistency evidence, distinct from posterior convergence. The recorded
runtime check confirms that all twenty samplers are live with empty stderr.

The eighth snapshots repeat every sampled-variable diagnostic on larger records,
retaining all six SPT+DESI and all four full CMB+DESI replicas per lens and the
original thresholds. All four groups still fail at least one declared gate.
Mass diagnostics at that snapshot are:

| Target | Replicas | Mass Rhat | Bulk ESS | Tail ESS | Mass p95 MCSE (eV) | Required MCSE (eV) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPT+DESI, 2018 | 6 | 1.0078 | 787.9 | 945.8 | 0.00541 | 0.005 |
| SPT+DESI, D1 | 6 | 1.0100874 | 557.6 | 634.6 | 0.00480 | 0.005 |
| Full CMB+DESI, 2018 | 4 | 1.0086 | 351.7 | 471.9 | 0.00544 | 0.001 |
| Full CMB+DESI, D1 | 4 | 1.0145 | 263.4 | 340.1 | 0.00406 | 0.001 |

All twenty complete-line chain snapshots and forty configuration snapshots pass
the recorded hash and row-count integrity checks in
`runs/20261003_math_review_chain_snapshots_eighth`. All twenty snapshots also
extend the seventh snapshots as identical byte prefixes; group row counts have
grown by 27.6–29.6%. All forty source configuration hashes match the seventh
snapshots. Resolved configurations change only the output location.
The previous third through seventh snapshots remain archived with their failed
diagnostic results. All four new diagnostic jobs exit successfully, with no
parameter-level execution error. Five of seven SPT 2018 sampled variables still
fail at least one threshold; its cold-dark-matter density and optical depth
pass. All seven SPT D1 and all ten full-CMB sampled variables still fail in
their respective groups. SPT 2018 mass passes Rhat and both ESS gates but misses
the quantile-error target. SPT D1 mass passes both ESS and quantile-error gates
but its unrounded Rhat is 1.0100874, exceeding 1.01. Full-CMB 2018 mass now
passes Rhat and tail ESS but misses bulk ESS and quantile error. Full-CMB D1
mass still fails Rhat, ESS, and quantile error. All mass Rhat values improve
from the seventh snapshot; this does not ensure subsequent improvement.
Diagnostic improvement is not monotonic in stored sample count. All original
thresholds and replicas are retained. The separately launched intermediate-
precision posterior controls are excluded from these default-target groups.
Integrity checks
verify the artifacts; these progress diagnostics supply no replacement posterior
bounds or convergence certificate.

The ninth snapshot at 23:43 UTC retains the same twenty replica families and
thresholds. Eighteen uninterrupted histories extend their eighth-snapshot byte
prefixes. The restarted A503 and B507 families use only their 78/69 saved fresh
rows, excluding their archived 2478/2430-row historical prefixes; burn-in is
applied within each selected segment. All forty original configuration hashes
remain unchanged. Snapshot configurations for those two families explicitly
retain the new seeds 1003/1007 and remove the resume flag. Byte reconstruction,
configuration transformations, finite integer holding weights, selected seeds,
and successful execution of all four diagnostic jobs are verified in
`runs/20261003_math_review_chain_snapshots_ninth/completion_verification.json`.

| Target | Replicas | Mass Rhat | Bulk ESS | Tail ESS | Mass p95 MCSE (eV) | Required MCSE (eV) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPT+DESI, 2018 | 6 | 1.0029211 | 1154.1 | 1516.0 | 0.004909 | 0.005 |
| SPT+DESI, D1 | 6 | 1.0092738 | 678.9 | 901.6 | 0.004416 | 0.005 |
| Full CMB+DESI, 2018 | 4 | 1.7294947 | 6.4 | 26.4 | 0.005093 | 0.001 |
| Full CMB+DESI, D1 | 4 | 1.2160867 | 15.5 | 40.9 | 0.005672 | 0.001 |

Both SPT mass variables now pass their declared gates. SPT 2018 has six of seven
sampled variables passing; H0 still misses its quantile-error target. SPT D1
has only mass passing, with other variables failing Rhat or quantile error.
All four complete parameter groups therefore still fail. Full-CMB diagnostics
retain only 203/196 equal-length expanded draws per family because of the young
restarted segments, and every sampled variable fails. Those shortened records
also materially change the estimated mass quantiles under equal-length
selection. They do not establish deterioration of the underlying target or a
replacement bound. The older complete histories remain archived as historical
evidence. All posterior convergence and numerical-accuracy certificates remain
false; passing the two marginal mass diagnostics alone does not discharge the
full posterior or precision obligations.

Exact chain readback does not bound Boltzmann numerical error. Separate
CLASS sensitivity controls compare six declared points at default settings
and selected numerical settings from the upstream
[v3.4.0 reference precision file](https://raw.githubusercontent.com/lesgourg/class_public/v3.4.0/cl_ref.pre).
It keeps the three-species mass mapping, physical cosmology, packaged priors,
and likelihood components fixed. The sampled points include the exact/rounded
initial slow-parameter pair, both audit source candidates, and mass offsets of
plus/minus 0.001 eV at the A candidate. This uses seven specified integration,
sampling, and quadrature settings; it is not the complete reference preset.
The seven-setting control has completed in
`runs/20261003_math_review_class_accuracy_control`; its default evaluations
reproduce both stored source-candidate objectives exactly. At those candidates,
the refined joint chi-square changes are -0.2389 for A and -0.2976 for B.
At the initial exact/rounded slow-parameter pair, the A joint chi-square
discrepancy falls from 0.12706 to 0.000369. At the A source candidate, holding
all other coordinates fixed, mass offsets of -0.001 and +0.001 eV change
chi-square by +0.0760 and +0.1851 with defaults, versus -0.0453 and +0.0534
with the selected settings. Thus numerical sensitivity is relevant to local
optimization and cannot be settled by exact text readback alone. These point
comparisons do not determine marginalized posterior bias.

A completed four-setting control keeps default neutrino quadrature and changes
only integration and spectrum-grid settings. Its refined evaluations take
about 42–48 seconds, compared with about 119–123 seconds for the seven-setting
initial pair and eight seconds for defaults. The faster subset does not
reproduce the seven-setting results: the unprofiled D1 chi-square at the A
source candidate differs by about 9.19. The intermediate quadrature-tolerance
control has also completed. At the A and B candidates and both A mass offsets,
its own joint chi-square differs from the seven-setting control by less than
0.0007, with evaluations near 51 seconds. This is convergence evidence at those
tested coordinates, without a uniform numerical or posterior bound. A completed
matched cosmological audit refits with these intermediate settings;
physical parameterization, priors, and completion are retained, with a common
declared lmax of 4095. Its inputs are in
`runs/20261003_math_review_cmb_accuracy_configs` and completed outputs in
`runs/20261003_math_review_cosmological_cmb_desi_accuracy`. Control receipts are in
`runs/20261003_math_review_class_accuracy_control_fast` and
`runs/20261003_math_review_class_accuracy_control_medium`. The runner rejects
changes to parameters absent from the installed CLASS precision declarations,
and snapshots retain the exact executed runner. None of these sampled controls
provides an interval or posterior error certificate.

The controlled audit's forward B-given-A transfer first completed while the
reverse reference optimization was still live. An immutable snapshot passed a
fresh native endpoint, component, ledger, localization, and exported-spectrum
check at `1e-7` absolute and `1e-10` relative tolerances. The forward joint
candidate mismatch is 61.38756, down 1.6069% from the default warm-start audit
and 1.9219% from the default multistart audit. Its native SPT contribution is
58.90373; ledger reconstruction differs by about -2.25e-12. The largest signed
group remains EE ell 2000–2500 (22.70752), followed by EE ell 2500–3000
(12.22627); TT ell 2000–2500 contributes 9.75551. Thus this precision refit
preserves forward EE dominance at these numerical candidates. It does not
certify global optimality or a posterior effect. Snapshot, native verification,
and default comparisons are in
`runs/20261003_math_review_cosmological_cmb_desi_accuracy_forward_check`.
The verifier's default still requires both directions; its new explicit
`--direction` option permits a completed direction to be checked separately.
Three CLI checks confirm rejection of an incomplete default audit, a missing
selected direction, and a duplicate selected direction, with no output written.
Both controlled directions have now completed and passed fresh native
verification. Their joint candidate mismatches are 61.38756 and 23.07565,
changes of -1.6069%/-0.4965% from the default warm-start audit and
-1.9219%/-0.3893% from the default multistart audit. The reverse signed SPT
contribution is 25.80283, with a reconstruction error of about 5.89e-11; TT
ell 2500–3000 leads with 8.02700. The comparison verifies that the effective
theory settings differ only in the declared seven precision parameters.
The extra explicit `l_max_scalars=4095` equals Cobaya's likelihood-derived
baseline value, as checked on both initialized theory configurations. The
original executed runner hash matches its recorded source commit. Completed
native records, spectra, and checks are in
`runs/20261003_math_review_cosmological_cmb_desi_accuracy`, including
`comparison_verification.json`.

The reverse reference search improves A's original source log-likelihood by
0.39563, moving its mass coordinate from 0.05825 to 0.01741 eV. The completed
forward transfer remains conditional on that original source. A forward replay
from the best found parent candidates has now completed in
`runs/20261003_math_review_cosmological_cmb_desi_accuracy_improved_source`.
It first reproduces the selected candidates' native objectives and then repeats
nuisance profiling and reference refinement with the same model and domains.
Its explicit source record prevents silently treating a later reference
improvement as the source of an earlier forward result. The completed reference
search returns -941.05467, below the retained B candidate at -939.36352, so that
stronger B reference is retained. Fresh native endpoint, spectrum, fixed-source,
and domain-nesting checks pass. The forward joint candidate mismatch is
64.17407, with SPT native contribution 61.45187 and accounting error -5.81e-12.
This is 4.5392% above the original parent forward value after changing the A
source; it is not a precision-only comparison. The replay and completed parent
reverse direction now use the same strongest found A/B source-reference pair,
with masses 0.01740945/0.05660113 eV. The reverse mismatch remains 23.07565.
Within the exact half-open ell range [2000,3000), forward signed quadratic
allocations are EE 37.13992, TT 14.53774, and TE 4.28189. Reverse allocations
are TT 12.37014, EE 0.91689, and TE -0.16402. Improving the A source therefore
preserves the direction-dependent localization. The native checks and
reproducible pair/range comparison are `accounting_verification.json` and
`comparison_verification.json` in the replay directory. No global optimality,
posterior accuracy, independent spectral-block chi-square law, or causal
attribution is certified.

An immutable proposal-shape comparison checks the intermediate chains' static
response covariance against covariance learned by default-target precise chains
A seed 503 and B seed 507. Static mass standard deviations are 1.83989 and
1.96371 times the learned widths; A's kSZ width is 3.08895 times larger. The
generalized variance eigenvalue ranges are 0.71054–10.37867 for A and
0.70050–4.96109 for B. Input antisymmetry is at most 1.67e-16 in correlation
units and is recorded before averaging this roundoff-scale part; all matrices
pass Cholesky factorization. The default-target learned covariances come from
unconverged chains and are only proposal-shape references. These data neither
certify posterior covariance nor establish intermediate-target efficiency.
The running samplers are unchanged. Snapshots, hashes, and reproducible checks
are in `runs/20261003_math_review_cmb_proposal_shape_check`.

Two additional intermediate-target trials launched at 23:57 UTC use those
archived default-target learned covariances, with independent seeds 811/813.
Their configuration reconstruction checks preserve the physical model,
packaged likelihoods, priors, initialization distributions, numerical precision,
and all stopping thresholds of the original A601/B603 controlled runs. Allowed
changes are run name, seed, initial proposal covariance, and its explanatory
note. Parameter order and positive definiteness pass; the copied covariance
bytes match the earlier immutable comparison. Existing samplers remain live.
The preparations and process ownership are in
`runs/20261003_math_review_cmb_learned_proposal_configs`, with run bundles
`runs/20261003_math_review_cmb_accuracy_learned_proposal_A_seed811` and
`runs/20261003_math_review_cmb_accuracy_learned_proposal_B_seed813`.
Both trials have loaded all ten parameters' covariances and begun sampling.
Immutable first snapshots contain 7/8 saved rows; fresh native checks of the
first and last row from each reproduce all components, priors, and posteriors
with zero discrepancy at tolerances 1e-7/1e-10. The startup evidence and four
native checks are in `activation_verification.json` and
`native_verification_summary.json` in the preparation directory. These are proposal trials,
not posterior covariance certificates, and no efficiency improvement or
convergence has been established. Different fresh seeds produce different
realized initial points despite identical initialization distributions; a later
rate comparison must not attribute that difference solely to the proposal.

A separate exact-range check addresses the paper's wording about high-ell TT
around ell 2000–3000, rather than inferring range dominance from the largest
individual group. It aggregates the existing half-open bands [2000,2500) and
[2500,3000) for all 14 directions in seven native-verified runs. SPT-only TT
range totals are 291.32157/74.53665, compared with EE 121.51875/0.65692.
For the controlled full-CMB forward direction, EE contributes 34.93379,
TT 13.79116, and TE 4.83686 within that range. In reverse, TT contributes
12.37014, EE 0.91689, and TE -0.16402. The full-CMB warm, prior, support,
and multistart controls show the same range-specific direction dependence.
This confirms the scope concern without confusing a single band with the
stated multipole range. It does not assert reverse TT dominance at every
multipole or across all reported bands. Signed allocations retain cross terms;
negative values remain signed, unlocalized rows are retained separately, and
native prior/covariance-normalization corrections are not assigned to spectral
sectors. These range sums are not independent likelihoods or causal allocations.
Paper claim-source hashes, native hashes, full quadratic reconciliation, and
reproducible results are in `runs/20261003_math_review_localization_range_check`.

Four independent full-CMB posterior controls have now been launched using these
same seven intermediate settings: A seeds 601/602 and B seeds 603/604. Their
physical parameterization, all sampled prior boxes, fixed and derived mappings,
and likelihood components match the default-precision restoration chains.
The preparation checks that only the seven declared numerical settings differ
in the target. Starting distributions use the completed intermediate-precision
source fits; the existing checked static response covariances initialize the
proposal. They retain full binary64 coordinate output, integer holding times,
and no oversampling thinning. Configurations, copied proposals, source hashes,
launch handles, and the target-contract receipt are in
`runs/20261003_math_review_cmb_accuracy_chain_configs`. These chains must be
diagnosed separately from default-precision chains because their numerical
likelihoods differ. No convergence or numerical-accuracy claim follows from
their launch; they provide the necessary route to testing posterior sensitivity
beyond the fixed-coordinate comparisons.
Fresh native verification of the first two stored rows from each of these
four runs has completed. All eight rows reproduce every likelihood component,
the prior, and the posterior exactly at full recorded precision. Immutable
two-row snapshots, verifier handles, and the summary are in
`runs/20261003_math_review_cmb_accuracy_chain_precision_check`. This checks
pointwise target accounting and does not certify convergence.
Two further independently seeded sampler trials, A701 and B702, use upstream
fast-parameter dragging with `oversample_power=0.4`, explicit temperature 1,
and the same intermediate ndf15 numerical target, likelihoods, priors, fixed
mappings, and initial proposal covariances. The purpose is to test mixing
efficiency under the measured fast/slow hierarchy. Internal bridge states are
not target draws; stored integer weights count outer-chain holding times.
This uses the installed Cobaya algorithm and existing serialization wrapper,
without changing the sampler implementation. The method and its dependency
are documented by [Cobaya](https://cobaya.readthedocs.io/en/latest/sampler_mcmc.html#taking-advantage-of-a-speed-hierarchy).
Inputs, source and implementation hashes, and live handles are in
`runs/20261003_math_review_cmb_accuracy_dragging_configs`. Both runs have
activated dragging with seven slow cosmological coordinates and three fast
nuisance coordinates, using eight A and five B interpolation steps. The actual
block receipt is archived. Native row replay and efficiency improvement remain
distinct checks. Fresh replay of the initial state and first accepted dragged
state from each trial has completed: all four rows reproduce every native
component, prior, and posterior exactly at full recorded precision. Immutable
snapshots and verifier receipts are in
`runs/20261003_math_review_cmb_accuracy_dragging_precision_check`. This verifies
pointwise accounting, without certifying every transition, convergence, or
efficiency improvement.

A broader reference-setting control has completed at both warm-start source
candidates and the A mass offsets. Its 67 keys cover further hierarchy,
line-of-sight, approximation, and lensing settings from the same upstream file.
The installed precision schema excludes the legacy `recfast_Nz0` key; inputs
record that exclusion explicitly. This is a broader reference comparison,
without a claim that every setting tightens its default or that the preset is
complete. Prepared inputs, executed runner, and launch hashes are in
`runs/20261003_math_review_class_accuracy_control_reference`. All four default
native records match the earlier controls exactly, and both source objectives
match the stored warm-start fits. Its first
completed point took about 2365 seconds and changes the A source joint
chi-square by -0.31853 from the seven-setting control (-0.31875 from the medium
control). Thus agreement between the earlier subsets did not settle the broader
approximations. The first-point native receipt is saved separately. The B source point has also
completed: broader-reference own joint chi-square changes are +0.51520 from the
seven-setting control, +0.51454 from medium precision, and +0.33672 from the
lensing control. Its evaluation took about 2640 seconds. The two source-point
comparisons are saved in `source_points_comparison.json`. With only A's mass
changed by -0.001 and +0.001 eV, broader-reference own joint chi-square changes
are -0.04309 and +0.05321, versus medium precision's -0.04540 and +0.05332.
The largest difference between these local mass changes is 0.00231; source
offsets are therefore largely constant over this tested interval. This does
not establish accuracy across the posterior domain. The completed native
comparison and source hashes are in `completed_comparison_verification.json`.
Neither source agreement nor posterior accuracy is established by the earlier
subset controls. A further
control adds only the three upstream lensing settings to medium precision in
`runs/20261003_math_review_class_accuracy_control_lensing`, to assess their
contribution to this discrepancy before selecting inference settings. This
lensing control has completed: its own source joint chi-square changes from
medium precision are +0.00275 for A and +0.17782 for B. All four points,
default native components, requested spectrum coverage, and source objectives
pass the saved comparison receipt. At the
first A point it differs from the broader reference by +0.32150 in source joint
chi-square, so those lensing settings leave almost all of that source difference.
Another control keeps the broader settings but uses intermediate quadrature
tolerances and the installed default ndf15 integrator, in
`runs/20261003_math_review_class_accuracy_control_reference_medium`. This tests a
possible practical alternative to the roughly forty-minute reference evaluations;
all four declared coordinates have now completed. Its A/B own joint chi-square changes
from the broader reference are -0.000446/-0.003292, while changes from the
seven-setting intermediate control are -0.31919/+0.51125. Thus this combined
quadrature/integrator change leaves almost all of the earlier source discrepancy
between intermediate and broader settings. The runs take about 7529/8371
seconds, versus 2365/2640 seconds for the broader reference; this proposed
alternative is slower in these recorded runs. A reproducible comparison checks
identical coordinates, all default native components against both prior controls,
and TT/EE coverage through ell 4095. Its immutable input and native receipt are
`source_points_progress_snapshot.json` and `source_points_comparison.json`.
The source-point receipt preceded completion of the local A mass offsets.
The minus-0.001 eV point has now completed in about 8526 seconds. Its own joint
chi-square differs from the broader reference by -0.00163831 and from the
intermediate control by -0.31807596. Relative to the fixed A source, the local
mass-minus change is -0.04428603, differing from the broader reference change
by -0.00119265 and from the intermediate change by +0.00111569. A reproducible
check confirms that only sampled mass varies within this pair, all archived
default native components agree exactly, and TT/EE coverage is unchanged at
ell 4095. Its immutable native snapshot and comparison are
`mass_minus_progress_snapshot.json` and `mass_minus_comparison.json`.
The positive mass offset completes in about 7991 seconds. Its own joint
chi-square differs from the broader reference by -0.00057463 and from the
intermediate control by -0.31943025. Its fixed-source local change is +0.05307651,
differing from the broader reference by -0.00012898 and from the intermediate
control by -0.00023860. Across all four coordinates, the largest own joint
difference from the broader reference is 0.003292; both tested local mass-change
differences are below 0.001193. The completed process exits with code zero;
`completed_comparison_verification.json` checks the launch input hashes, complete
point sets, identical default native components, and fixed-coordinate mass
pairs. Earlier comparison archives omit explicit coverage metadata. Initializing
each saved baseline and selected configuration verifies their requested TT/EE
coverage through ell 4095, identical baseline configuration, and changes only
to the declared numerical settings. That separate evidence is recorded in
`legacy_coverage_verification.json`; it performs no new spectrum or likelihood
calculation. These pointwise comparisons do not certify posterior-wide accuracy.
The simultaneous quadrature and integrator changes do not isolate either
numerical setting's individual effect.

A further CLASS control tests four coordinates selected from the immutable
fifth full-CMB chain snapshot: the first retained rows exactly matching each
selected file's holding-time weighted mass median and 95th percentile after
discarding 20% of stored rows. The files and row indices are declared before
evaluation: A seed 503 supplies masses 0.05164/0.10668 eV, and B seed 507 supplies
0.02481/0.07891 eV. These are test coordinates from unconverged files, without
a posterior-bound claim. All sampled parameters vary between each pair, so a
difference cannot be attributed solely to mass. Fresh default-precision replay
has completed: all native components, the prior, and the posterior reproduce
the precise archived rows at the declared `1e-7` absolute and `1e-10` relative
tolerances. The intermediate-versus-broader reference comparison has now completed.
Its four intermediate-precision evaluations have completed. Own joint
chi-square changes from defaults are -0.42386/-0.35320 at A's selected
median/tail coordinates and -0.42628/-0.08166 at B's. The tail-minus-median
change in this numerical discrepancy is therefore +0.07066 for A and +0.34461
for B. These differences support testing numerical posterior sensitivity,
without translating directly into a mass-quantile bias. The completed
intermediate/default comparison is archived in `medium_default_comparison.json`.
Both broader-reference evaluations have completed at A's selected median/tail
coordinates: own joint chi-square changes by -0.12219/-0.19857 from intermediate
precision and -0.54605/-0.55177 from defaults, with evaluation times of about
2901/2803 seconds. The tail-minus-median numerical correction changes by
-0.07638 relative to intermediate precision and -0.00572 relative to defaults.
The nearly constant default-to-broader correction at these two coordinates
does not establish its behavior throughout the posterior. A reproducible check
confirms identical coordinates, all archived intermediate baseline components,
and TT/EE coverage through ell 4095; its immutable inputs and comparison are in
`A_broader_progress_snapshot.json` and `A_broader_comparison.json`.
B's selected median coordinate has also completed, taking about 3171 seconds:
own joint chi-square changes by +0.30099 from intermediate precision and
-0.12529 from defaults. A reproducible check confirms identical declared
coordinates, exact agreement of all archived intermediate baseline components,
finite native components, and TT/EE coverage through ell 4095. The immutable
snapshot and native comparison are in `B_median_broader_progress_snapshot.json`
and `B_median_broader_comparison.json`. The final B tail coordinate took about
2957 seconds: its own joint chi-square correction is -0.09359 from intermediate
precision and -0.17525 from defaults. The tail-minus-median correction is
therefore -0.39458 relative to intermediate precision and -0.04996 relative to
defaults. All four final records pass a reproducible reconciliation with the
archived intermediate components and fresh default-target checks; the input
hashes match the launch receipt. The complete native records and verification
are in `metrics.json` and `completed_comparison_verification.json`. These
comparisons do not identify a pure mass effect or posterior bias.
Prepared inputs, selection and launch receipts, executed runner, and native
replay evidence are in `runs/20261003_math_review_class_accuracy_posterior_points`.
This extends the sensitivity assessment beyond fitted source candidates,
without supplying an interval or posterior-accuracy certificate.

A six-point control changes only the perturbation integrator under the seven
intermediate precision settings, comparing installed-default ndf15 with rk.
The installed headers declare `ndf15=1` and `rk=0`; the upstream reference
preset chooses rk. This tests runtime and native-likelihood sensitivity before
considering a faster sampling target. It uses the same four archived CMB
coordinates and the two completed intermediate-precision source fits.
Inputs, source hashes, installed enum/schema hashes, executed runner, and the
live handle are in `runs/20261003_math_review_class_accuracy_control_medium_rk`.
The control has completed, with all four archived-coordinate baselines
reproducing the earlier native records exactly and both intermediate source-fit
objectives reproduced exactly. Changing only the integrator changes own joint
chi-square by at most 0.00133 at these six points. RK runtimes range from
0.9406 to 1.0425 times ndf15 runtimes, so this test shows no substantial speed
gain. The comparison receipt is `comparison_verification.json`; existing
posterior runs retain their ndf15 target. These six comparisons do not supply
a uniform numerical or posterior-accuracy bound.

A six-point CAMB control for the SPT+DESI baseline has completed, comparing
its defaults with `AccuracyBoost`, `lAccuracyBoost`, and `lSampleBoost` all set
to two. These are numerical settings; the explicit three-species cosmology,
priors, and native likelihoods are retained. The first run completed all native
evaluations but failed its spectrum comparison because CAMB returns differing
numbers of extra multipoles under the two settings. That failure is retained in
`runs/20261003_math_review_camb_accuracy_control`. The repaired shared runner
compares the spectrum domain requested by the likelihoods and requires both
outputs to cover that entire domain. The corrected run is in
`runs/20261003_math_review_camb_accuracy_control_matched_coverage`.
All twelve native records agree exactly with the earlier evaluations, and both
baseline source objectives reproduce stored fits within 4e-12. Source joint
chi-square changes are -0.22004 for A and +0.19694 for B. At mass offsets of
plus/minus 0.001 eV, changes from each setting's own source chi-square differ
by less than 0.001 between defaults and doubled accuracy. This is a sampled
local comparison, without a uniform numerical or posterior error bound. A
further run with all three boosts at three has completed in
`runs/20261003_math_review_camb_accuracy_control_boost3`. From doubled to tripled
accuracy, own source joint chi-square changes are +0.19158 for A and -0.07284
for B. The tested mass-offset changes differ by at most 0.00153, while the
unprofiled opposite-lens contributions also vary. These results do not yet
establish numerical convergence of the full likelihood across the posterior.

A new two-versus-three boost comparison tests four actual chain coordinates
near the within-file empirical mass median and p95, taken from the fixed fourth
snapshot A401 and B403 files after the declared stored-row burn-in. The receipt
records source hashes and exact row indices. Its mass range extends to about
0.15 eV, beyond the source-fit offsets above. The coordinates provide finite
sensitivity tests; their selection supplies no posterior bounds or convergence
claim. This run is in
`runs/20261003_math_review_camb_accuracy_posterior_points`. This control and a
fresh default-target replay have completed. All four source hashes, exact row
indices, sampled coordinates, native spectrum requirements, and finite native
components pass the saved verification. Default own-target log likelihoods
reproduce the stored rounded rows within 3.8e-5. From doubled to tripled
accuracy, own joint chi-square shifts are +0.21332 and +0.21818 at A's selected
median and tail points, versus +0.02845 and -0.10390 at B's. Tripled minus default
shifts are -0.10683 and -0.18153 for A, and +0.21725 and +0.16086 for B. Thus the
relative tripled-versus-default shift differs by -0.07470 between A's two
points and -0.05639 between B's. All sampled cosmological coordinates can differ
between each selected pair; these comparisons do not isolate mass as the cause
or determine marginalized quantile bias. A uniform numerical error bound and
posterior accuracy certificate remain unavailable.

`check_class_numerical_accuracy.py` retains its CLASS-only entry point, while
`check_boltzmann_numerical_accuracy.py` implements the common control. Seven
rejection controls verify that neither entry point admits physical parameter
changes, nonfinite CAMB boosts, or nonpositive boosts. These controls preserve
the target; they do not certify numerical error.

The full CMB optical-depth-prior control has now completed and passed fresh
native verification. Its joint candidate differences are 61.2807 and 23.1061,
changes of -1.7781% and -0.3651% from the packaged warm-start baseline. Native SPT
accounting errors are below 3e-11. EE ell 2000–2500 still leads in the first
direction and TT ell 2500–3000 in reverse. This is a small effect on these
refitted audit candidates. It does not quantify the change in marginalized
mass posteriors, and it does not certify exact global optima. The control and
comparison receipts are in
`runs/20261003_math_review_cosmological_cmb_desi_tau_control`.

## Controlled-chain termination and recovery

On 2026-10-03 around 20:37 UTC, all six intermediate-precision and dragging
samplers stopped. The precise time and external cause are unestablished;
their owned managed sessions return exit code 143, consistent with SIGTERM.
Their stderr files are empty. The original twenty sampler processes and both
numerical calculation processes remain live. The six partial chains, configs,
checkpoints, covariance files, logs, and previous runtime records are preserved
in `runs/20261003_math_review_controlled_chain_recovery`. A termination receipt
records the original PIDs and handles. Before recovery, fresh first/last
native checks pass for all twelve selected rows with zero discrepancy in
likelihood components, prior, and posterior at the declared precise tolerances.

Cobaya's recorded checkpoint does not retain RNG state. `FullPrecisionMCMC`
now permits a new seed during resume, while retaining the existing target,
recorded sample prefix, blocking, and proposal settings. The actual sampler
regression verifies that the new seed is selected and that resumed disk output
still exactly matches memory and preserves the old prefix. This supports a
fresh RNG segment, not reproduction of the uninterrupted trajectory or recovery
of unwritten holding times. The six continuations use seeds 801–804 and 901–902,
recorded separately from their original seed identities. Their startup logs
confirm those seeds and the saved blocking/covariance. Native verification and
resume inputs are archived; runtime state now records both previous and current
process ownership. By 21:07 UTC, all six continuations have saved new rows.
Immutable snapshots preserve each complete pre-recovery prefix and contain
5/2/2/5/1/2 new rows, respectively. Fresh native checks at all six post-recovery
saved endpoints pass with zero discrepancy in likelihood components, prior,
and posterior at tolerances 1e-7/1e-10. The growth snapshots, executable verifier,
process exits, and component checks are recorded in the recovery directory.
These endpoint checks do not verify every transition or recover unwritten
holding times. These short chains still have no convergence certificate.

Inspection of the installed Cobaya implementation confirms that its initial
resumed point is discarded at the first acceptance: `burn_in_left` includes
one initial accepted step even when configured burn-in is zero. The interval
between the old saved prefix and the fresh segment therefore does not preserve
the interrupted realized holding history. Future controlled-chain diagnostics
will use the post-recovery segments, with burn-in applied within each segment,
and the recorded fresh seeds. `segment_boundaries.json` records the exact six
starting row indices, original prefix sizes/hashes, and installed sampler source
hash. Preserved prefixes remain useful native-accounting and provenance
evidence. Their concatenation with the fresh segments is not an uninterrupted
realized trajectory.

`snapshot_fresh_segments.py` implements that separation without overwriting
existing artifacts. Its first immutable snapshots contain 16/9/15/7/6/10
post-recovery rows. Byte-slice checks reconstruct the exact complete source
prefixes; snapshot configurations differ from the saved resume inputs only in
output location and removal of the resume flag. Each segment retains the
previously native-verified post-recovery row, with identical coordinates and
posterior value. This reuses the existing selected native evidence and performs
no new likelihood evaluations. These very short segments establish the recovery
and extraction workflow, not posterior convergence.

At 23:50 UTC, the six owned controlled-sampler identities are live and their
logs show continued sampling. Their latest internal mean R-1 checks are
15.629338/9.603572/5.316537/3.656769 for seeds 601–604 and
24.172286/14.297585 for the dragging trials 701–702. All exceed the configured
proposal-learning maximum of 2.0, and the logs explicitly record skipped updates.
No fresh-segment proposal update is recorded; each saved covariance remains
byte-identical to its recovery archive. The recorder and receipt are
`runs/20261003_math_review_validation/record_controlled_learning_progress.py`
and `controlled_learning_progress_2350.json`. This explains the current lack
of proposal adaptation; it does not isolate the cause of slow mixing. These
internal single-process checks use upstream sampler bookkeeping and are not
substitutes for the independent multi-chain diagnostics on fresh segments.
Sampler settings and stopping thresholds remain unchanged.

The 01:33 UTC follow-up verifies the same six active identities. Latest internal
mean R-1 values are 9.439673/9.603572/5.316537/3.656769 for seeds 601–604 and
16.978223/4.929192 for 701–702. Every last learning check still skips adaptation
above 2.0; no fresh-segment covariance update has occurred, and all six saved
covariances still match their recovery archives. During a subsequent verified
wait, all twenty-eight current sampler identities remain live and save 521
additional rows in total. The quadrature-only families have 82/70/81/74 rows
for A and 85/81/93/73 for B at the end of this observation, before their first
learning checks. Complete source-file row counts for restarted families include
historical prefixes and must not be interpreted as uninterrupted histories.
Receipts in `runs/20261004_math_review_cohort_progress_0132` retain the observed
times, ownership checks, source/log prefix hashes, and learning evidence. The
independent convergence assessment remains the ninth snapshot; no posterior
gate or numerical target has changed.

## Validation and remaining work

At 00:04 UTC on October 4, the rounded-output default B505 sampler stopped
with managed exit code 1 after a native CLASS tight-coupling initialization
error, leaving 2695 complete saved rows. Its complete run, checkpoints,
covariance, logs, and runtime metadata are preserved in
`runs/20261004_math_review_class_tca_failure_seed505`. The error log gives exact
CLASS theory arguments at total mass approximately 0.026697 eV. Fresh isolated
replays reproduce the identical failure with one and eight threads at ell_max
4095. Starting perturbations earlier, using the upstream reference value of
`start_small_k_at_tau_c_over_tau_h`, does not repair this point. The established
seven-setting intermediate control succeeds. Tightening only `tol_ncdm_bg`
from its installed default 1e-5 to 1e-8 also succeeds, preserving every physical
argument and producing finite lensed spectra through 4095. This establishes
a tested numerical repair at this input, not a general root-cause diagnosis
or posterior-wide accuracy guarantee.

The four canonical CLASS configuration files have been updated to explicitly
use `tol_ncdm_bg: 1e-8`, with explanatory numerical-provenance notes. Their
likelihoods, priors, physical neutrino mapping, reference points, and sampler
settings are unchanged. Their actual initialized native spectrum requirements
are ell_max 3200 for SPT 2018 and 4095 for SPT D1. Both are tested: default
quadrature fails at the same cosmology and tightened quadrature succeeds.
All four configurations
reconstruct their pre-change dictionaries exactly after removal of that setting
and note, and their initialized CLASS arguments match the respective successful
native replay. `configuration_repair_verification.json` and
`replay_comparison_verification.json` bind the configuration and native spectra
hashes. The repaired background-only and seven-setting spectra differ at this
point; successful computation alone does not certify numerical accuracy.
Historical configurations and outputs are preserved, and no numerical targets
are silently pooled. B505 remains stopped: restarting it with altered precision
would create a distinct numerical target, not an unchanged default continuation.
The other twenty-seven owned sampler identities are live at the latest check.
After this repair, `make math_check` with the established review interpreter
passes 66 Python tests, the Lean build, and all 20 exported theorem axiom checks.
The initial system-Python dependency failure and the successful receipt are
preserved in the failure/review directory.

At 00:49 UTC, the seven remaining legacy default full-CMB processes were
deliberately retired after verification of the replacement target and an
isolated four-thread replay of the repaired failure point. Exact ownership and
PID descriptors were checked before signaling. All seven managed sessions
return 143 after the requested SIGTERM; this cause is established and differs
from the earlier externally unexplained terminations. All eight legacy families,
including the already failed B505, are preserved in
`runs/20261004_math_review_cmb_legacy_retirement`. Every archived file hash
passes; frozen source chain bytes match the archives, and all complete saved
rows have finite fields and positive integer holding weights. Unknown unwritten
holding histories are not reconstructed. This retains the historical default
diagnostics as historical evidence and creates no completed default posterior.

Eight fresh replacement chains launched at 00:50 UTC, four per lens, with seeds
1101–1108 and four OpenMP threads each. Their common CLASS coverage remains
4095 and only background quadrature is tightened to 1e-8; the other precision
parameters use installed defaults. Physical parameterization, priors, and native
likelihood components match the respective legacy parents. Each uses a fixed
last saved point from a distinct family in the immutable ninth snapshot as
initialization, and the archived unconverged learned covariance as a proposal.
These borrowed points and covariances are not new-target posterior evidence.
Independent fresh streams and fresh output files separate the new histories
from the old targets. Internal stopping thresholds, integer holding options,
and independent diagnostic gates remain unchanged. Both initialized native
targets and all eight configuration contracts pass. The four-thread repaired
failure-point spectra equal the earlier eight-thread spectra exactly.

The new preparations and proof receipts are in
`runs/20261004_math_review_cmb_quad_chain_configs`. All eight samplers have begun
sampling with empty stderr and temperature one. Early immutable snapshots
contain 6/7/12/9/9/9/13/10 rows. Fresh first/last native checks verify sixteen
rows with zero component, prior, or posterior discrepancy at tolerances
1e-7/1e-10; `native_verification_summary.json` records the closed verifier
processes and hashes. The twelve SPT default chains and eight seven-setting
intermediate chains continue, for twenty-eight live owned samplers in total.
The new quadrature-only target, intermediate target, and retired default target
are distinct numerical approximations and are not pooled. No posterior
convergence, efficiency improvement, or uniform accuracy certificate follows
from this replacement. Full-CMB restoration now proceeds with the two repaired
numerical cohorts; the ninth legacy snapshot remains archived, and new posterior
assessments will identify their numerical target explicitly.

An isolated diagnostic CLASS executable now reproduces the B505 failure at
the exact archived physical arguments. It adds only logging after the initial
approximation selection; the native library used by inference remains unchanged.
At the failing initial time, tau=606.7539369746 and a=0.0027431170436, the
interpolated photon scattering rate is NaN. Both ratios used by tight-coupling
selection are therefore NaN. The installed source's comparisons explain the
immediate error: a NaN ratio does not exceed the initial-time threshold during
bisection, but also does not satisfy the strict inequalities that enable tight
coupling. Changing only the early-start threshold cannot establish valid initial
conditions in this situation. For positive finite quantities satisfying the
two scalar startup bounds, aH/kappa' <= 0.0015 and k/(aH) <= 0.07 imply
k/kappa' <= 0.000105, below the tight-coupling threshold 0.01, with the Hubble
ratio also below its threshold 0.015. This conditional arithmetic argument does
not apply to the observed NaNs and is not an upstream numerical root diagnosis.

The installed Python backend independently computes only background and
thermodynamics at this point, before perturbations. Both default and repaired
background tables are finite. The default thermodynamics table has 22 nonfinite
ionization, scattering-rate, and baryon-temperature entries at redshifts
0 through 0.3150315032. Its optical-depth exponential is nonfinite at 28332
of 28333 rows, and every visibility entry is nonfinite. With only
tol_ncdm_bg=1e-8 changed, both native tables are entirely finite. The same
standalone executable then completes the repaired full calculation in 16.02
seconds, whereas the default input exits 1 in 0.26 seconds. Exact inputs, full
compressed native tables, diagnostics, hashes, build records, and verification
receipts are in `runs/20261004_math_review_class_tca_diagnostic`. They identify
corrupt thermodynamics before the final tight-coupling error; the numerical
cause of the first low-redshift nonfinite values remains unestablished. This
is a pointwise repair check, not a uniform numerical accuracy or convergence
certificate. The receipt verifies all twenty-eight owned sampler identities
and the unchanged installed native module.

Further isolated diagnostics identify the low-redshift corruption mechanism at
the failed coordinate. CLASS's dense numerical Jacobian perturbs its residual
helium coordinate upward by 1.8212145015e-13 at z=0.3158436049. HyRec freezes
the helium equation when xHeII=x_He*fHe is below 1e-6. The base state has
xHeII=9.999999898309207e-7 and zero helium rate; the perturbed state has
xHeII=1.0000000047320817e-6 and crosses into the active helium calculation.
At photon temperature 3.5863 K, that calculation contains exponentially large
excited-level factors and returns an infinite rate. The numerical Jacobian
then contains negative infinity, its LU matrix contains positive infinity,
and the first trapped invalid operation occurs in scaled pivot selection.
The trap observes FE_INVALID; preceding overflow is not trapped. Exact rational
products of the captured binary64 inputs independently verify the cutoff
crossing. A logging-only executable without traps still reproduces the original
tight-coupling error, linking the diagnostic path to the original failure.

An isolated repair candidate retries a nonfinite dense finite-difference
evaluation with the opposite increment and checks that the retry is finite.
The denominator changes sign with the increment. The larger increment used
for roundoff control has the same protection; two nonfinite directions cause
an explicit numerical error. Physical derivative formulas and inference
libraries are unchanged. At B505's coordinate under default precision, this
candidate takes one retry and completes in 15.87 seconds, with finite saved
spectra and all 28333 thermodynamics rows. Under the previously successful
quadrature-only setting it takes no retries, and its saved lensed spectra
equal the original standalone spectra exactly. This is a candidate numerical
repair at tested coordinates, not a general convergence proof for the ODE
solver or an installed inference-backend repair.

During these checks, the resumed intermediate dragging trial A701, active
segment seed 901, stops with managed exit code 1 and the same native CLASS
error. Its exact physical point has total mass 0.05791543261 eV and already
uses the seven tighter precision settings, including tol_ncdm_bg=1e-8.
Its 152-row source prefix, including 69 historical rows from the first
segment, configurations, checkpoints, covariance, and complete recovery log
are preserved in `runs/20261004_math_review_class_tca_failure_seed701`.
Hashes pass; unwritten holding histories are not reconstructed. An unchanged
solver restart has not been attempted. This establishes that tightening
precision alone does not prevent all occurrences of the bug.

Fresh isolated replays of A701's exact inputs reproduce the error and identify
the same helium-cutoff crossing at z=0.3207440245. The finite-difference repair
candidate completes that point under its original seven-setting precision,
with finite saved spectra and thermodynamics. `invalid_probe_receipt.json`,
`finite_retry_replay_receipt.json`, and `extended_verification_receipt.json`
in the diagnostic directory bind the source, executables, exact crossings,
output tables, and scopes; the second failure directory has its own replay
receipt. The original installed CLASS module is unchanged. At that checkpoint,
twenty-seven owned samplers remained live: twelve SPT, eight quadrature-only,
and seven intermediate precision chains. Recovery of A701 awaited a defined,
verified solver repair; the subsequent private-backend trial is recorded below. Other chains continue, and no uniform accuracy or posterior
convergence claim follows from these isolated repairs.

The finite-difference repair is now available as a pinned source patch in
`patches/class-3.4.0-finite-jacobian.patch` and a separately compiled Python
backend. Only `tools/evolver_ndf15.c` differs among 125 copied source/resource
files; the original installed native module remains unchanged. The private
module hash is
`7a5d736220b3d236f3dc7c89944d025fe3e4c7cb4c8e4473ef807c898fc71539`.
Seven native regression cases pass against the actual patched library,
covering both perturbation stages, a smooth control, recovery of a small
slope, explicit nonfinite errors, and callback-error propagation. Both failed
coordinates now complete through the Python backend with finite spectra
through ell=4095 and finite background and thermodynamics tables. At the
quadrature-only B505 control every saved spectrum array is bit-identical to
the unmodified backend. These checks do not establish differentiability
across the frozen-species cutoff or uniform numerical accuracy.

Fresh full-native likelihood checks at the first and last of A701's 152
archived rows reproduce all six components, prior, and posterior exactly.
The source/build/test/pointwise receipts and rebuild instructions are in
`runs/20261004_math_review_class_python_repair` and `patches/README.md`.
Seed 1201 has launched with this private backend from the last saved parent
point. It retains the parent's seven precision settings, physical likelihoods,
priors, dragging configuration, and stopping criteria, with a fresh RNG stream
and output prefix. Its native module and launch implementation are hash-pinned.
Its history is a distinct numerical-backend trial, and the failed A701/901
prefix remains archived. Selected-row equality does not authorize pooling
these histories or establish convergence.
Its first and last rows in an immutable three-row snapshot now pass fresh
full-native checks with exactly zero discrepancy for all six components,
prior, and posterior. The initialized theory arguments retain all seven
precision controls, three massive species, and ell coverage through 4095.
Actual automatic speed measurement activates one slow block and six
interpolating fast steps; its saved oversampling factors are 1/14/14.
The selected-row receipt also pins the later covariance/BAO helper sources,
whose finite likelihood values reproduce those saved by the sampler before
those helper guards were added. The sampler remains live. These checks verify
selected accounting and activation, not every transition or convergence;
receipts are under `guarded_initial_rows` in the private-backend build records.

The tenth snapshot at 03:00 UTC assesses only the twelve uninterrupted SPT
chains, separately from all CLASS targets. Each has roughly 20–37% more saved
rows than the ninth snapshot. Both six-chain neutrino-mass groups pass the
unchanged diagnostic gates: A Rhat=1.004374, bulk ESS=1368.16, tail ESS=1943.55,
95th-percentile MCSE=0.003236 eV; B Rhat=1.004750, bulk ESS=895.47,
tail ESS=1214.46, MCSE=0.003765 eV. Six of seven A parameters pass; the baryon
density's quantile MCSE exceeds its fixed relative gate. Five of seven B
parameters pass; H0 and tau exceed their quantile MCSE gates. Both complete
parameter groups therefore still fail. Descriptive full-draw mass percentiles
are 0.14082737/0.10853264 eV; retained-draw percentiles are
0.14386469/0.11051908 eV. No replacement bound or convergence certificate
is adopted. All twelve families, configuration transformations, finite rows,
positive integer holding weights, and executed diagnostics are verified in
`runs/20261004_math_review_spt_chain_snapshots_tenth/completion_verification.json`.

The separate eleventh assessment at 05:45 UTC updates only the six SPT D1
families. Their equal-length post-burn-in histories grew from 6,454 to 8,075
represented draws per family, a 25.1% increase; the completed B404 history
remains included. Lens A was assessed separately after comparable history
growth in the twelfth assessment below. Snapshot byte prefixes, all twelve B configuration hashes, integer
holding weights, and the unchanged diagnostic command are verified in
`runs/20261004_math_review_spt_chain_snapshots_eleventh_B/completion_verification.json`.
D1 mass passes with Rhat 1.005496, bulk ESS 1089.6, tail ESS 1446.6 and p95
MCSE 0.003253 eV. H0 and tau now pass their gates. Baryon and dark-matter
density quantile MCSEs are 8.6185e-6 versus 8.5655e-6 and 4.5515e-5 versus
4.5090e-5, respectively, so only five of seven variables pass and the full
D1 group still fails. The numerical gates are not relaxed or rounded to pass.
Descriptive full-history and equal-length retained p95 values are 0.10963508
and 0.1125472 eV; they do not replace the reported posterior bound. At 05:48
UTC the nine live SPT and sixteen guarded CLASS processes retain their
recorded identities, and all observed stderr files are empty. The three
completed SPT families remain in the twelve-family cohort.

The twelfth assessment at 06:04 UTC updates only the six SPT 2018 families,
including the two completed at the sample cap. Equal-length post-burn-in
histories grew from 9,273 to 11,156 represented draws per family, a 20.3%
increase. All seven sampled parameters now pass the original gates. Mass
Rhat is 1.003911, bulk ESS 1574.0, tail ESS 2361.6 and p95 MCSE 0.002917 eV.
The previously failing baryon-density MCSE is 1.3822e-5, below its 1.4882e-5
relative gate. Descriptive full-history and retained p95 values are 0.14054709
and 0.1421685 eV. Configurations, byte prefixes, completed-history identity,
weights and diagnostic execution are verified in
`runs/20261004_math_review_spt_chain_snapshots_twelfth_A/completion_verification.json`.
This discharges the specified sampled convergence-diagnostic gates for the
SPT 2018 group at this checkpoint. It is statistical evidence, with no
mathematical convergence proof or uniform Boltzmann-accuracy certificate.
The D1 group retains its failed eleventh assessment, and the guarded full-CMB
cohorts remain separate. The overall restoration therefore remains open.

A direct follow-up at the second failed coordinate shows that quadrature-only
precision also fails under the unmodified backend. Removing the six later
perturbation/spectral controls leaves the same physical inputs and background
tolerance; the original Python backend again raises the tight-coupling
initialization error. The guarded backend completes all spectra and finite
tables in 17.36 seconds, and every thermodynamics array is bit-identical to its
seven-setting guarded control. `runs/20261004_math_review_class_quadrature_hole_seed701`
preserves both results. The background tolerance alone is therefore a
pointwise workaround at B505, not a solver repair across the stated prior.

The fifteen remaining unmodified CLASS samplers have been retired with
verified agent-requested SIGTERM and managed exit code 143. Complete chain
prefixes, covariances, configurations, logs, and recorded recovery segments
are preserved byte-for-byte in
`runs/20261004_math_review_class_backend_transition/archives`.
The stopped prefixes retain positive integer weights and finite complete
rows. Unknown final holding time is not reconstructed. A preparation check
caught source configs that omit temperature; their actual saved sampler
options establish temperature 1, which is now explicit in replacement configs.
The initial preparation error and corrective run are retained.

All fifteen replacements use the private guarded native module, new seeds
1301–1308 for quadrature-only precision and 1401–1407 for seven-setting
precision, new output prefixes, the last archived point as a fixed initializer,
and the archived current covariance as a proposal only. Physical likelihoods,
priors, precision controls, and effective sampler/stopping settings are
preserved. Thirty fresh native evaluations of the archived first and last
rows reproduce all components, priors, and posteriors exactly. This is selected
consistency evidence, not identity of the unmodified and guarded numerical
targets across their domain. Historical prefixes are not appended or pooled.

The active scientific families are twelve SPT, eight guarded quadrature-only,
and eight guarded seven-setting chains, including the existing A1201 trial.
The two CLASS precision targets remain distinct. At 03:58 UTC all twenty-eight
processes were verified by their actual commands and process start times, and
all sixteen CLASS processes mapped the pinned guarded extension, with the
original extension absent from their maps. The original installed package is unchanged. All sixteen selected new quadrature-only rows now reproduce all native
components, priors, and posteriors exactly. All fourteen selected rows from the seven new medium-precision chains also
reproduce all six native components, priors, and posteriors exactly; both
managed verifiers have completed with exit zero. The previous A1201 checks
remain valid. The thirty new endpoints and thirty archived parent endpoints
cover the fifteen replacement chains at selected coordinates only. No new posterior bound, convergence certificate,
or uniform numerical-accuracy claim follows from the transition.

The four canonical CLASS recipes now declare the verified private extension
hash and build receipt. Both the sampler launcher and the reference evaluator
reject a mismatched native module before creating output. For accepted builds
they set Cobaya's CLASS path to `global`, preserving the checked import instead
of allowing a package-directory solver to take priority. All four actual
canonical model initializations use the guarded native `Class` type; the
original installed binary is rejected, conflicting explicit solver paths are
rejected, and the final Python suite passes all 73 tests. The physical theory
settings, priors, likelihoods, and sampler settings in the canonical YAML files
are unchanged. Runtime build selection and selected-point agreement do not
certify a posterior-wide numerical error bound.

Two SPT chains subsequently completed successfully at the configured
20,000-sample cap. Both managed handles returned exit zero; complete bundles
and hashes are preserved in `runs/20261004_math_review_spt_sample_cap_completion`.
Their logs identify the cap as the stopping reason, rather than establishing
convergence. Both families remain in the next diagnostic assessment without
a restart or changed gate. At 04:33 UTC twenty-six scientific processes remained
live: ten SPT samplers and sixteen guarded CLASS samplers. The twelve SPT
families remain the diagnostic cohort, including the two completed histories.

The original launch and terminal tool records resolve a later-discovered swap
in that completion receipt's session labels: A401 used session 44762, and
A402 used session 92240. Both terminal exits were zero. The receipt is corrected;
its prior version and the primary evidence are preserved in
`runs/20261004_math_review_sampler_session_provenance`. Scientific files,
their hashes, and diagnostics are unchanged.

B404 subsequently completed at 05:24 UTC after 18,760 accepted samples,
meeting Cobaya's configured internal stopping test rather than its sample cap.
Its managed handle returned exit zero; the complete output bundle and source
hashes are preserved in
`runs/20261004_math_review_spt_internal_completion_B404`. Fresh native checks
of its first and last stored rows pass the existing text-rounding tolerance;
the largest component discrepancy is 1.96e-4. The checked source chain's
hash matches the frozen archive. This internal stopping result does not
replace the separate twelve-family diagnostic gates or establish a converged
posterior bound. All twelve SPT families remain in that cohort. At 05:32 UTC,
twenty-five scientific processes remained live: nine SPT and sixteen guarded
CLASS samplers. Their process identities match the earlier recorded start
times and commands, all observed stderr files are empty, and all sixteen
CLASS processes map the pinned guarded module.

B403 subsequently completed at its configured 20,000-sample cap, with managed
exit zero and checkpoint `converged: false`. Its complete bundle is preserved
in `runs/20261004_math_review_spt_sample_cap_completion_B403`. Fresh native
checks of rows 0 and 19999 pass the unchanged text-rounding tolerance, with
maximum component discrepancy 1.8427e-4. The checked completed source and
frozen chain have the same hash. The 06:28 UTC observation verifies twenty-four
live scientific processes: eight SPT and sixteen guarded CLASS samplers.
All twelve SPT families, including the four completed histories, remain in
the diagnostic cohort. Cap completion does not establish convergence; the
latest B assessment remains the eleventh, which predates B403's completion.

All eight quadrature-only chains have now reached their first learning check.
Internal mean R-1 values are 14.544519/12.677564/15.935770/15.950357 for A and
13.011911/5.649968/8.434037/9.036896 for B. Every check skips adaptation above
the configured maximum 2.0; no update is recorded, and all saved covariances
match their initial learned proposal within the declared text-roundtrip
tolerance. Frozen logs, covariances, updated configurations, and hashes are in
`runs/20261004_math_review_quadrature_learning_first`. These internal checks
are not independent multi-chain convergence evidence, and the stopping and
diagnostic thresholds remain unchanged.

Two precise default-target samplers, A503 and B507, stopped around 23:10 UTC
with managed exit code 143 and absent scientific processes; their external
termination cause is unestablished. The other twenty-four owned sampler
identities remain live. Their complete 2478/2430-row prefixes, configurations,
checkpoints, learned proposal covariances, and logs are preserved in
`runs/20261003_math_review_default_chain_recovery`. Fresh first/last native checks
pass at both prefixes with zero component, prior, or posterior discrepancy.
The two same-target continuations use fresh seeds 1003/1007 and retain the
configured stopping criteria. First post-recovery snapshots contain 26/18 rows;
all four selected new native rows also pass with zero discrepancy. Runtime
ownership records distinguish original and resumed processes. As with the six
earlier recoveries, these are fresh segments and do not reconstruct interrupted
holding histories. The prepared ninth default-target snapshot uses only each
restarted family's fresh segment, preserving all four families per full-CMB
lens and recording the excluded historical prefix. Its procedure has now run
and passed artifact verification. It remains the latest historical default
full-CMB assessment; those eight chains have since been retired. The separate
tenth SPT assessment remains the latest joint assessment for all twelve
SPT families. The separate fourteenth assessment is the latest for lens A,
and the thirteenth assessment is the latest for lens B and includes its completed B404 history.
Historical data remain archived, and no convergence claim follows from restart
or endpoint consistency.

`make math_check` runs the regression suite, Lean build, and transitive axiom
inspection. Receipts are in `runs/20261003_math_review_validation`. The
latest combined run passes 88 Python tests and checks 60 exported Lean theorems.
The subsequent additive-accounting repair passes all 94 Python tests; Lean
sources have not changed since that combined run.
The later weighted-RMSE repair passes all 100 Python tests, with the same
unchanged 60-theorem Lean coverage.
The subsequent CLASS chain-identity guard passes all 107 Python tests; Lean
sources remain unchanged.
The latest covariance-guard receipts are in
`runs/20261004_math_review_class_python_repair`.
All exported
theorems use only `propext`, `Classical.choice`, and `Quot.sound`; no local axiom
or admitted proof supplies a conclusion. Tests exercise correlated accounting,
uncovered bins, invalid covariance, beam and Hartlap terms, native reconstruction,
compressed representation, chronological drift, fractional weights, tail density,
profile-domain nesting, and template rescaling. Toy MAP, audit, rewrite, and sweep
were rerun.

The generic additive-loglike block helper also required a numerical repair.
Subtracting separately rounded endpoint sums could reject valid decompositions
or silently return zero for a small surviving likelihood difference. The
aggregate now sums the exact rational values of the supplied binary64 terms
before rounding once. Signed block sums recover intermediate overflow, and
the existing 1e-12 absolute and relative consistency tolerances remain in force.
The returned total follows the aggregate; `accounting_error` reports the sum
of rounded block statistics minus that total. A discrepancy outside tolerance
raises an explicit error. Six regression controls cover common offsets,
insertion order, intermediate overflow, an unrepresentable total, and small
signals hidden by rounded blocks. The shared signed accumulator preserves
localization behavior. Receipts are in
`runs/20261004_math_review_block_accounting_repair`. This repair concerns the
generic helper, currently used by its tests and demonstration; it does not
declare correlated covariance subblocks additive or provide a new native
cosmological likelihood certificate.

Weighted RMSE had a separate numerical defect: forming the squared quadratic
form could erase a nonzero result by underflow or overflow when the requested
RMS was finite. Computing `C^-1 r` could also overflow even when whitening and
the RMS were representable. The helper now validates and factors the same SPD
covariance, solves `L w=r` for its lower Cholesky factor, and computes a scaled
RMS of `w`. The identity `r^T C^-1 r=||L^-1 r||^2` preserves the statistic without
forming the unscaled squared norm. It returns 1e200 and 1e-200 for those residuals
under identity covariance, and preserves the smallest subnormal residual.
Finite whitened coordinates are still required, and no uniform floating-point
error bound is claimed. The public covariance solver and signed allocations
retain their existing guards; twenty ordinary and roundoff controls produce
bit-identical public solves. Fresh native checks of both authoritative profiled
audit ledgers are byte-identical to their previous receipts. Analytic controls,
native checks, and a distinct self-review are preserved in
`runs/20261004_math_review_weighted_rmse_repair`.

The multi-chain diagnostic script now checks recorded CLASS native-module
hashes as well as model configurations. Matching YAML alone can conceal a
solver-build change. Conflicting hashes, recorded/unknown mixtures, malformed
hashes, conflicting witnesses within a bundle, and declared contracts without
matching launch evidence are rejected before computing diagnostics. Matching
content hashes can use different filesystem paths. An all-unrecorded legacy
cohort retains its workflow with the target-identity assumption explicit in
the report; the current installed module is never used to infer an archived
chain's backend. All sixteen guarded launch records agree on the pinned module
hash, while their distinct numerical precision cohorts remain separate.
This is a CLASS metadata consistency check, not a uniform numerical accuracy
or convergence certificate. Seven workflow controls and a distinct self-review
are preserved in `runs/20261004_math_review_chain_backend_identity`.

Fresh precision comparisons now use the pinned repaired CLASS module at six
selected coordinates from guarded quadrature-only and seven-setting chains,
plus a 0.01 eV mass offset at each selected quadrature median. Separate A and B
likelihood models are retained. Frozen rows reproduce all six native likelihood
components exactly under their matching target; priors and posteriors were not
recomputed in this control. Selection uses empirical mass quantiles of
unconverged prefixes, not verified posterior bounds. The common solver
`l_max_scalars` is 4095; the tool records the likelihood-requested TT/EE coverage,
3200 for A and 4095 for B, matched between settings within each lens.

Seven-setting minus quadrature-only total native chi2 offsets span -0.6885 to
-0.5821 for A and -0.7112 to +0.07983 for B across the four selected points.
The 0.01 eV mass step changes total chi2 by -0.563915 versus -0.575354 for A,
and 2.872991 versus 3.188711 for B. The mass-response discrepancies are therefore
-0.0114395 and +0.315721 respectively. These are sampled sensitivity results,
not uncertainty bounds. Their variation rules out assuming a common constant
offset on these coordinates, and the two posterior precision cohorts remain
separate. A finer control at the same median and mass-offset coordinates is
the next numerical accuracy check. Complete outputs, source hashes, target
closures, and a distinct self-review are in
`runs/20261004_math_review_guarded_posterior_precision`.

Two medium-versus-fine mass-response jobs are now running at those identical
median and +0.01 eV coordinates. The finer dictionary tightens the integration
and neutrino tolerances and spectrum grids, while retaining the same background
quadrature, native module, physical model, likelihoods, and priors. Their launch
and process-identity evidence is in
`runs/20261004_math_review_guarded_medium_fine_mass_response/launch_receipt.json`.
No accuracy conclusion follows while those evaluations remain pending. The
same observation verifies all twenty-four continuing inference samplers.

Both jobs subsequently complete with managed exit zero. Their four medium
replays reproduce the preceding six-component native likelihood values exactly.
The finer 0.01 eV mass responses are -0.575502 for A and 3.080373 for B, versus
-0.575354 and 3.188711 at medium precision. The discrepancies are -0.000148112
and -0.108338 respectively. A's selected response is nearly stable at these
levels; B retains substantial numerical sensitivity. The fine-minus-medium
offset changes from +0.126711 to +0.0183733 between B's two coordinates, so a
constant-offset explanation is again insufficient. The source/configuration
checks confirm six numerical control changes and otherwise identical models.
These pointwise results do not supply a uniform error bound or an established
convergence rate. Completion and distinct self-review receipts are in the same
directory. Isolating spectrum-grid changes from integration and neutrino
tolerances is the next B sensitivity check.

Two B factor checks are now running at the same median and mass-offset points:
one changes only `l_logstep` and `l_linstep`; the other changes only the four
integration, sampling and neutrino-tolerance controls. Previously verified
medium and fine results supply the anchors and are explicitly reused, not
reported as fresh evaluations. New native evaluations and spectra are being
saved separately for the two factors. Launch identities and hashes are in
`runs/20261004_math_review_guarded_precision_factor_controls_B`. No factor
attribution is established before their completed results are checked.

Both factor jobs subsequently complete with managed exit zero. B's 0.01 eV
native chi2 responses are 3.188711 at medium precision, 3.079792 with the
spectrum-grid change alone, 3.189732 with the dynamics changes alone, and
3.080373 with both. Relative to medium, the grid factor contributes -0.108920
and the dynamics factor +0.00102076; the explicitly retained interaction is
-0.000439209. At these coordinates the spectrum grid therefore dominates the
observed discrepancy. The full fine result differs from grid-only by 0.00058155.
This does not establish a global attribution, a convergence rate, or a uniform
error bound. New TT/TE/EE/BB spectra through 4095 and PP through 2500 are
preserved and verified finite. Completion and distinct self-review receipts
are in the same factor-control directory. Refining the spectrum grid with
medium dynamics fixed is the next accuracy check.

Two denser B spectrum-grid jobs are now running with medium dynamics fixed:
`l_logstep=1.0065, l_linstep=6` and `l_logstep=1.00325, l_linstep=3`.
They use the identical median and +0.01 eV points; the verified grid-12 result
is reused as an anchor. Source hashes, numerical-control dictionaries, and
owned process identities are in
`runs/20261004_math_review_guarded_B_spectrum_grid_refinement/launch_receipt.json`.
No convergence rate or accuracy bound is inferred before the new results are
checked.

Both denser-grid jobs complete with managed exit zero and matching native
module, input and coordinate hashes. B's selected 0.01 eV native chi2 responses
are 3.079792 (grid 12), 3.082343 (grid 6), and 3.080147 (grid 3). The successive
changes, +0.00255176 and -0.00219673, reverse direction. They are smaller than
the earlier medium-to-grid-12 change, but establish neither a convergence rate
nor a uniform error bound. Medium dynamics and all physical, nuisance and prior
definitions stay fixed. Six native likelihood components and requested spectra
are verified finite; the grid-12 anchor is explicitly reused. Completion and
distinct self-review receipts are in the grid-refinement directory. A
source-grounded dense-multipole endpoint is the next selected-point check.

The unit-multipole endpoint comparison also completes with managed exit zero.
Only `l_logstep` changes from 1.00325 to 1.0; `l_linstep=3` and medium dynamics
stay fixed. In the primary CLASS transfer-list function, this sets every
logarithmic increment to one. Both actual native geometry rescalings equal one
and satisfy `l_linstep*angular_rescaling>1`, so that loop retains unit increments
through the requested internal endpoint. A compiled call of the actual source
function verifies consecutive multipoles at representative endpoints and these
geometries; a sparse-grid control fails consecutiveness. The probe isolates
list construction with zero mode count and does not represent a full solver
evaluation or an observed native internal multipole cap. Native full-model
evaluations supply the six likelihood components and finite requested spectra.
The unit-grid 0.01 eV response is 3.079649, differing from grid 3 by -0.000498045
chi2. Its absolute likelihood changes at the two points are +0.00125414 and
+0.000756092. This provides a selected-point endpoint for the sparse angular
transfer grid; integration, wavenumber and lensing errors, and posterior-wide
accuracy remain uncertified. Completion, source controls and distinct self-review
receipts are in `runs/20261004_math_review_guarded_B_unit_multipole_grid`.

Selected native boundary checks also succeed in both complete A/B models at
`mnu_sample=0`. All six likelihood components, the Cobaya prior, and posterior
are finite under the guarded medium target. The actual CLASS input has
`N_ncdm=3` and `m_ncdm=0,0,0`, and the derived total mass is zero. Controls at
`mnu_sample=-0.001` are rejected by the prior before evaluating a likelihood.
Only mass was changed from each frozen median point. This verifies support
for these native boundary evaluations; a finite endpoint density does not
establish a boundary mode or Gaussianity. Complete outputs, hashes, and a
distinct self-review are in `runs/20261004_math_review_native_zero_mass_gate`.

At the 07:12 UTC observation the guarded quadrature cohort had progressed
beyond its initial learning checks. Seven of eight families had logged one
or more proposal covariance updates under the unchanged maximum internal R-1
of 2.0; B1305 had not yet updated. Frozen current covariance matrices pass the existing finite Cholesky
check, and changes from the original proposal agree with the logged updates.
Logs, configurations, and covariances were frozen individually rather than as
an atomic sampler state. Stopping rules remain R-1=0.01 and tail R-1=0.05.
These internal adaptation checks do not supply multi-chain convergence evidence
or change a likelihood target. Receipts are in
`runs/20261004_math_review_guarded_quadrature_learning_progress`.

The thirteenth SPT B assessment freezes all six families after the minimum
postburn represented history grows from 8075 to 9703 steps (+20.16%). Both
completed B families (403 at its sample cap and 404 at its internal stop) remain
in the assessment. All seven sampled parameters now pass the unchanged gates,
including the previously failing baryon and cold-dark-matter quantile precision
checks. Mass Rhat is 1.002697, bulk ESS 1310.26, tail/quantile ESS 1819.23, and
95th-percentile MCSE 0.00304350 eV, below the fixed 0.005 eV target. Complete
prefixes, original configurations, process identities and an independent
holding-time recount are verified. Twenty-four samplers remain live: eight SPT
and sixteen guarded CLASS. Receipts are in
`runs/20261004_math_review_spt_chain_snapshots_thirteenth_B`.

At the thirteenth checkpoint, paired with the earlier twelfth A assessment,
the separate SPT assessments pass every fixed gate. Their equalized retained p95 values are
0.1421685 eV (A) and 0.1124497 eV (B), with MCSE 0.00291663 and 0.00304350 eV.
The retained difference is 0.0297188 eV; the full-postburn difference is
0.03138551 eV. Combining the two quantile MCSE estimates in quadrature gives
0.00421540 eV under the stated independence assumption for Monte Carlo errors.
This uncertainty describes numerical quantile estimation, not statistical
significance for a cosmological mass difference. A is explicitly reused at its
earlier snapshot time, rather than newly reassessed or reported as a simultaneous
joint snapshot. The sampled cosmological prior ranges and CAMB configuration
match; the SPT packages and fixed nuisance definitions remain target-specific.
No pure completion causality, mathematical MCMC convergence certificate,
uniform solver bound or full-CMB posterior result is inferred. The paired readout
and distinct self-review are in the same B directory. Subsequent SPT assessments
require minimum postburn represented histories of 13388 (A) and 11644 (B).

A headline-magnitude audit compares these qualified SPT readouts with the
unchanged canonical summary and manuscript table. The original exact canonical
p95 difference is 0.1086063 eV (rounded to 0.109 eV in the table). The qualified
retained and full-postburn differences are 0.0297188 and 0.0313855 eV, about
27--29% of the original value. Qualitative tightening survives, but the original
numerical magnitude is not restored. The old sparse SPT chains have corrected
chronological Rhat 1.8604 and 1.2011 and scalar ESS 4.81 and 11.39; they cannot
supply the diagnostic qualification missing from that original magnitude.
A distinct self-review reconstructs every gate for all fourteen current
parameter assessments and recomputes endpoint differences from exact binary64
fractions. The current A/B readouts have distinct snapshot times, their MCSE
quadrature requires independent Monte Carlo errors, and neither a cosmological
significance statement nor complete attribution of the numerical change to
sampling or code repairs follows. Sources, computations and self-review are in
`runs/20261004_math_review_SPT_headline_magnitude_audit`. The user has been asked
whether to finish another growth-qualified stability assessment before deciding
or accept the smaller measured tightening for the later paper revision. This is
a separate material numerical-claim issue from full-CMB TT localization; no
revision has been adopted, and the paper and canonical summary are untouched.

An effective CAMB settings audit now isolates the explicit multipole setting
on the current stack. The original SPT YAML omitted lmax; Cobaya raises it to
the likelihood request, rather than leaving a solver default. Current native
A support requests 3200 and B requests 4095. Reconstructing the original
configuration style negotiates those limits, whereas both restoration models
explicitly use 4095. Both pre-review and current adapters derive the request
from the native ell support. This supports a conditional inference about the
historical configuration; the old effective setting was not directly recorded
and the historical numerical stack has not been replayed.

Twenty current-stack native evaluations compare both styles at four frozen
saved-row coordinates per target (old and restored mass medians and p95 rows)
and a +0.01 eV mass perturbation of each restored median. Priors, likelihood
definitions, fixed nuisance defaults and internal prior factors match within
each target. Candl receives sampled tau; an archived empty input_params field
did not prove fixed tau, since the old adapter queried provider scalars. A's
largest selected total chi-square change is 0.0683410 and its selected
mass-step response changes by 0.0109519. B's selected likelihood components
and supported spectra are bit identical. The old coordinates are controls
from diagnostically unqualified histories, not qualified old quantile results.

The archived updated YAML reports CAMB 1.6.5 and Cobaya 3.6.1, while these
controls and restoration use CAMB 2.0.4 and Cobaya 3.6.2. Numerical target
identity across that version change and historical package/data identity
remain unresolved. These pointwise controls do not bound posterior quantile
sensitivity or attribute the original-to-restored p95 difference entirely to
sampling or lmax. Sources, frozen coordinates, native outputs, exact binary64
accounting and a distinct self-review are in
`runs/20261004_math_review_SPT_effective_CAMB_settings`. The two initial audit
jobs failed an empty-input assertion before native evaluation; their sources
and errors are preserved and the sampled tau accounting is corrected. No
sampler, gate, paper or canonical result changed. The new runtime observation
verifies all 28 samplers; none of the six previously assessed cohorts had yet
reached its next fixed growth threshold at that observation time.

An isolated solver-version control resolves part of the preceding uncertainty.
Downloaded CAMB 1.6.5 and Cobaya 3.6.1 wheels were installed in a separate
package prefix, preserving the live environment. Actual imports, native module
and wheel hashes are recorded. Twenty native evaluations use the same frozen
points and configuration styles, current Python 3.12, current adapter and
current likelihood/data packages. The original Python 3.10 machine and native
binary are not reconstructed, and full historical data identity is not proved.

Within an identical configuration style, solver-version changes shift selected
total chi-square by up to 9.20907 (A original style), 5.94199 (A restoration
style) and 6.16744 (B). These differences are not only additive constants:
selected offset ranges are 1.24217, 0.696922 and 3.66551 respectively. With
identical priors this gives nonconstant likelihood ratios at the observed
points, so a sampling-only comparison lacks an established unchanged numerical
likelihood target. The +0.01 eV median mass response changes by -0.00817546 for
A original style, +0.0263041 for A restoration style and -0.687017 for B.
No posterior quantile direction or magnitude follows from these selected-point
controls alone.

At the old median and p95 saved coordinates, the archived-version original-style
controls reproduce all four stored total chi-square values within 0.000029,
all likelihood components within 0.000065, and sampled logpriors within
0.000000024. These are observed errors at rounded saved coordinates, not a
certified rounding bound or complete historical target identity. They provide
a concrete route toward restoring inference on the archived solver target.
A distinct self-review reconstructs nonconstant likelihood ratios from exact
binary64 fractions and checks that the live solver hashes are unchanged.
Sources, package provenance, native outputs and self-review are in
`runs/20261004_math_review_SPT_archived_solver_version_control`.

The near-0.030 eV qualified result remains valid for its current numerical
target. It has not established the converged old-target shift or ruled out
restoration of the original magnitude. A matched archived-solver comparison
must precede treating the new number as a sampling-only revision of the main
claim. No numerical downgrade or new posterior result is adopted here, and
no existing sampler, diagnostic threshold, paper or canonical result changed.
The latest observation again verifies all 28 samplers; all six existing
assessment growth thresholds remained pending. The previous full Python
and Lean check remains applicable because production and Lean sources are
unchanged (132 tests and 74 public axiom outputs).

Eight archived-version SPT chains are now launched with fresh seeds
1601--1608 and four distinct fixed starting coordinates per target. Their
scientific priors, likelihood and nuisance definitions match the earlier
original-style controls; lmax is explicitly 3200 for A and 4095 for B.
An isolated launcher verifies the actual CAMB native hash, package versions
and wrapper before creating output. Full-precision serialization retains the
ordinary Cobaya 3.6.1 proposals and acceptance rule. The covariance is initially
the declared diagonal proposal, with normal proposal learning. Earlier
unqualified or different-target coordinates supply starting points only.
All eight initial native evaluations are finite and reproduce the preceding
selected controls within 0.000000000016 in component chi-square. A first
bit-equality assertion across contexts failed; the measured replay difference
is below the explicitly stated 0.000000001 tolerance, and bit identity is not
claimed. Failed sources and receipts are preserved.

A managed verifier froze every first complete saved row and its solver metadata.
Seven first rows replay exactly with both shared and freshly constructed native
models. Seed 1604 does not: its SPT chi-square differs by -0.19519155, with
BAO and sampled prior differences zero. Its posterior discrepancy is the
corresponding +0.09759577. Only logA and ns changed from its initial point;
the saved As matches the declared exponential mapping exactly. The first
batch verifier stopped at this mismatch and its failed run is retained.
Subsequent triage verifies the seven other frozen rows, but the batch is not
qualified for inference. Simple initial-to-fast-move controls, including the
ordinary logposterior path, give identical cached and forced-recalculated
likelihoods on both CAMB versions. They do not reproduce the failed stored
likelihood, so transfer reuse alone is not an established cause. The next
control records an isolated one-row sampler trajectory and preceding evaluation
history; this probe is excluded from all posterior diagnostics. No archived
posterior result or native accuracy certificate is inferred. The sampler
histories remain separate from current-version and CLASS cohorts.

The completed isolated trace reproduces seed 1604's original first saved
row byte for byte, including its likelihood discrepancy. It records 37
posterior calls, and call 35 has exactly the saved cosmological point and
stored chi-square. The trace process exits successfully and is absent.
Ordered replay reproduces 35 of the 37 recorded posterior calls exactly.
Calls 2 and 3 differ in SPT chi-square by +0.03035957 and +0.04770586;
the BAO components agree. The failing call 35 and saved-row likelihood
reproduce exactly without replaying internal speed-measurement evaluations.
A forced fresh calculation at that same point changes SPT chi-square by
-0.1951915483. Thus preceding calculation state affects this selected native
likelihood evaluation; speed-measurement calls are not necessary to reproduce
that failure. The omitted speed-measurement history may still explain the
early differences, but that cause has not been established. A private prototype
copying native transfer objects before spectrum calculation retains the same
call-35 discrepancy. Neither a specific mutation nor a validated repair is
established. Reduced histories with getter instrumentation are now being tested.
These debugging controls are excluded from inference-chain counts and posterior
diagnostics; no tolerance is relaxed and no live sampler or backend is changed.

Reduced histories localize the failure to returning to an older cached transfer
state after evaluating a different cosmology. The five-point window
[0,32,33,34,35] reproduces the full archived call-35 discrepancy exactly.
Getter instrumentation confirms that the copy override runs and retains
pristine primordial parameters in its cached objects, but still fails. A
three-point window [0,1,35] gives chi-square error +0.04844394. On CAMB 2.0.4,
those three/five-point errors are +0.00050748/+0.00236760. In both versions,
keeping only one transfer state removes both selected errors exactly against
forced-fresh calculations. This is a private selected-point repair candidate,
not a proof of a specific native global-variable cause or a uniform numerical
certificate. Full 37-point histories now match separate-model forced-fresh
baselines exactly on both versions, comparing likelihood components, sampled
priors and posterior totals. Each comprises 36 finite native evaluations and
one negative-mass prior rejection without likelihood evaluation. Distinct
self-review checks every point and the archived call-35 reference. However,
a two-model challenge rejects one-state caching as a general repair: an
intervening native calculation in a separately constructed model restores the
same selected three-point discrepancy on both versions. The corresponding
zero-state transfer-cache controls match forced-fresh likelihoods exactly.
Thus the single-model 37-point results remain valid, but do not justify a
general one-state cache guard. Native spectral isolation, persistent
fresh-transfer integration and actual sampler/cohort revalidation remain open.
No numerical tolerance is relaxed to accept the rejected candidate.

Subsequent spectral isolation confirms that the selected A discrepancy
precedes the candl likelihood: native TT spectra change after an intervening
model by up to 0.01744955 microkelvin squared on CAMB 1.6.5 and 0.00471736 on
2.0.4, using the standard ell-weighted spectrum convention. Selected B
returns match exactly. Recomputing transfers removes both the spectrum and
likelihood discrepancies at these A/B controls. The specific native shared
variable responsible has not been established.

`FreshCAMB` now keeps the ordinary Cobaya CAMB numerical settings, parameter
requirements, priors and spectrum calculation while forcing a fresh transfer
calculation. Its helper ignores requests to reuse transfer results even after
sampler cache resizing. Spectrum and likelihood caches retain their usual
input/dependency matching. The four standard CAMB recipes name this adapter;
the generic sampler, common cosmological optimizer and proposal builder also
configure it before recording effective configurations. Custom CAMB classes
are rejected rather than silently replaced. Fast moves now cost an additional
native transfer calculation.

On both native versions, the production adapter matches every component,
sampled prior and posterior total at all 37 traced points for each SPT recipe:
148 exact result comparisons in total, comprising 144 finite targets and four
prior rejections. Separate native models also leave the adapter's selected
spectrum and posterior returns unchanged. Four actual finite MCMC runs
produce eight saved rows; all match upstream forced-fresh evaluations exactly,
within the unchanged predeclared 1e-9 gate. Both finite probe processes exit
successfully and are absent. These controls are excluded from posterior
inference. A full check passes 168 Python tests, the unchanged Lean build and
74 public axiom exports. An initial class-name import mistake and accidental
pytest discovery of its archived failed test are preserved with corrected
sources and receipts. The production/native checks are in
`runs/20261004_math_review_CAMB_fresh_transfer_repair`, with distinct self-review.
No private native library is changed. Historical chains are not repaired by
changing future code: guarded cohort revalidation/replacement remains open.
The previous SPT chain gates remain valid diagnostics of their saved
histories; qualification of the native fixed-point evaluation requires this
additional repair and validation.

Preparation, launches, frozen rows, measured discrepancies, failed attempts
and distinct partial self-review are in
`runs/20261004_math_review_SPT_archived_solver_chain_preparation`. All 36 inference
samplers remain live at the latest birth/command/module observation. The native
first-row issue is unresolved and restoration continues; no paper or main
claim revision has been adopted. The generic run helper now enforces declared
CAMB native SHA256 and exact version before creating output, alongside the
existing CLASS guard. It records the actual import and forces global loading.
The actual archived native import passes its declared contract; the current
import is rejected for that archived contract, while both matching native
contracts pass. Ten rejection tests verify that no output directory is created.
A full check passes 158 Python tests, the unchanged Lean build and all 74 public
axiom outputs. The CLASS validation function remains unchanged. This native
identity guard does not itself repair cache-return errors. Completed validation
and distinct self-review are in
`runs/20261004_math_review_CAMB_launch_guard_repair`.

The fourteenth SPT assessment updates A after its minimum postburn represented
history grows from 11156 to 13388 steps (+20.01%). All six families remain,
including both completed histories, and all seven sampled parameters again
pass the unchanged gates. Mass Rhat is 1.003428, bulk ESS 1933.82,
tail/quantile ESS 2966.77 and p95 MCSE 0.00256291 eV. Retained p95 is
0.14240484 eV, only 0.00023634 eV above the twelfth assessment; full-postburn
p95 is 0.14031501 eV, a change of -0.00023208 eV. Integer holding-time
recounts, byte-prefix extension, completed-history identity, configurations
and diagnostic dependency hashes are checked. A distinct self-review
reconstructs all fourteen A/B parameter gate sets.

That paired readout uses fresh A from 10:10 UTC and explicitly reuses
B from 08:34 UTC; this is not a simultaneous joint snapshot or a new B
assessment. The retained p95 difference is 0.02995514 eV and full-postburn
difference 0.03115343 eV. Quantile MCSE combined in quadrature is
0.00397887 eV assuming independent Monte Carlo errors. This supplies further
A stability evidence near the smaller tightening, without restoring the
original 0.109 eV magnitude, establishing cosmological significance, or
adopting a material claim revision. The numerical targets, priors and gates
remain unchanged. The runtime observation verifies the same 28 owned live
samplers: eight SPT and twenty guarded CLASS. Next SPT assessments require
minimum represented histories of 16066 (A) and 11644 (B). Sources, diagnostic
execution, paired readout and self-review are in
`runs/20261004_math_review_spt_chain_snapshots_fourteenth_A`.

The fifteenth SPT B assessment freezes all six families after the minimum
postburn represented history grows from 9703 to 11712 (+20.70%). Completed
families 403 and 404 retain their exact final histories. All seven sampled
parameters again pass the unchanged gates. Mass Rhat is 1.002216, bulk ESS
1501.79, tail/quantile ESS 2202.80, and p95 MCSE 0.00272671 eV. Retained p95
is 0.11220337 eV, a change of -0.00024633 eV from B's thirteenth assessment;
full-postburn p95 is 0.10958005 eV, a change of +0.00041847 eV. A distinct
self-review recounts all six holding-time histories and reconstructs all
fourteen parameter gate sets across the fresh B and reused A assessments.

The latest paired readout explicitly reuses A's fourteenth assessment and
freshly assesses B's fifteenth; it is not a simultaneous joint snapshot.
The retained p95 tightening is 0.03020147 eV and the full-postburn tightening
is 0.03073496 eV. Quantile MCSE combined in quadrature is 0.00374212 eV under
the explicit assumption of independent Monte Carlo errors; this is not
cosmological significance or pure completion causality. Both additional
growth-qualified stability assessments are now complete, with results still
near the smaller tightening rather than the original 0.10860629 eV. The user
has been asked whether to use the qualified approximately 0.030 eV result in
a later revision or first investigate remaining differences from the original
target. No answer or material revision is adopted. Next SPT minima are 16066
for A and 14055 for B. Sources, verification and paired readout are in
`runs/20261004_math_review_spt_chain_snapshots_fifteenth_B`. The paper,
canonical summaries, targets and diagnostic gates are unchanged; all 28 owned
samplers remain live.

The first guarded CLASS multi-chain assessment freezes all 16 fresh families
in four distinct A/B quadrature/medium cohorts and preserves their recorded
native-build witnesses. Postburn equalized represented histories are 1331,
1199, 363 and 260 steps per chain, respectively. Mass Rhat is 1.04579, 1.05673,
1.06911 and 1.12884; mass quantile MCSE is 0.004636, 0.009130, 0.015872 and
0.012469 eV, above the fixed 0.001 eV target. None of the ten sampled parameters
passes all gates in any cohort. All frozen histories extend the earlier
native-verified guarded prefixes, and the pinned build hashes agree. Different
numerical precision cohorts and retired-backend histories are not pooled.
The running samplers, targets and stopping gates are unchanged. These young
chains supply progress diagnostics, not converged bounds or numerical accuracy
certificates. Completion and distinct self-review receipts are in
`runs/20261004_math_review_guarded_CLASS_first_diagnostics`. Subsequent assessments
require at least 20% growth of the minimum postburn represented history in each
cohort. A snapshot helper initially assumed every launcher command included its
seed; the seed-1201 trial instead requires its recorded seed/pid and pinned
launcher identity. Partial snapshots and failed wrappers were excluded, and
the correction is recorded in the bundle.

A distinct self-review checked theorem quantifiers, native likelihood bridges,
profile-domain nesting, chain ordering and multiplicities, and artifact scope.
This was self-review, not independent review. The native ledger bridge is checked
independently of the stored directional scalar from exported endpoints;
optimization remains numerical.

The second guarded CLASS assessment extends all 16 frozen histories after
minimum represented-history growth of 25.47%, 21.93%, 33.88% and 25.00% in
quadrature A/B and medium A/B. Equalized postburn histories are now 1670,
1462, 486 and 325 steps per chain. Mass Rhat is 1.05684, 1.05828, 1.09989 and
1.12586; bulk ESS is 98.16, 90.12, 38.05 and 27.96; mass quantile MCSE is
0.003413, 0.007925, 0.015022 and 0.007314 eV. None of the ten sampled parameters
passes every unchanged gate in any cohort. A distinct self-review recounts
integer holding times and reconstructs all decision gates. The next assessment
requires minimum postburn represented histories of 2004, 1755, 584 and 390,
respectively. Native witnesses, previous-prefix extensions and target separation
are verified in `runs/20261004_math_review_guarded_CLASS_second_diagnostics`.

The third guarded CLASS assessment updates only B's two four-family cohorts,
after their minimum postburn represented histories grow from 1462 to 1769
steps (+21.00%) and from 325 to 401 (+23.38%). Both A cohorts retain their
separate second assessment, and the young grid-12 cohort is excluded. No
precision targets, native builds, physical models or diagnostic gates change.
Mass Rhat is 1.030851 for quadrature B and 1.120257 for medium B; bulk ESS is
110.61 and 26.68, tail/quantile ESS 220.57 and 71.68, and mass quantile MCSE
0.00816111 and 0.00631289 eV, respectively, against the unchanged 0.001 eV
target. None of the ten parameters passes every gate in either cohort. Full-CMB
posterior bounds therefore remain provisional. Prefixes, unchanged source
configurations, all eight native-build witnesses and actual process birth
identities are checked. A distinct self-review recounts holding times with
exact integer arithmetic and reconstructs all twenty parameter gate sets,
including chronological drift and equalized-history selection. The next
minimum histories are 2123 (quadrature B) and 482 (medium B); the A thresholds
remain 2004 and 584. The owned runtime observer verifies all 28 live samplers.
Receipts are in
`runs/20261004_math_review_guarded_CLASS_third_B_diagnostics`. No paper or
canonical summary change or material claim revision is adopted.

The third quadrature A assessment separately freezes its four families after
minimum postburn represented history grows from 1670 to 2039 steps (+22.10%).
Mass Rhat is 1.012629, bulk ESS 130.32, tail/quantile ESS 264.83, and quantile
MCSE 0.00472389 eV. All ten parameters still fail at least one unchanged gate;
no qualified full-CMB posterior bound follows. The new precision-scale repair
is used in this assessment and its production dependency hashes are retained.
Exact integer recounts, byte-prefix extension, unchanged source configurations,
recorded native builds and actual process birth identities are verified; a
distinct self-review reconstructs all ten complete parameter gate sets. No
medium A, B or grid-12 history is pooled or reassessed. Next minimum history
for quadrature A is 2447; medium A remains at 584. The slowest medium A chain
is still advancing through rejected proposals with the same accepted count;
unwritten holding times are not reconstructed. The runtime observer verifies
all 28 owned samplers. Sources and verification are in
`runs/20261004_math_review_guarded_CLASS_third_quad_A_diagnostics`. The paper
and canonical summary remain unchanged.

The separate third medium A assessment retains all four families once the
minimum postburn represented history grows from 486 to 593 (+22.02%).
Mass Rhat is 1.060846, bulk ESS 49.27, tail ESS 61.33, quantile ESS 113.75,
and quantile MCSE 0.00851297 eV against the unchanged 0.001 eV target.
All ten sampled parameters still fail at least one gate. Prefixes, actual
process birth identities, unchanged source configurations, holding weights,
and native-build witnesses are checked; a distinct self-review reconstructs
all ten complete gate sets. No other cohort is reassessed or pooled.
The latest four guarded CLASS assessments are now individually growth-qualified
third assessments at distinct times, not a simultaneous joint snapshot.
Every cohort remains provisional, and the grid-12 cohort is still separate and
young. Medium A's next minimum represented history is 712; the other thresholds
remain 2447 (quadrature A), 2123 (quadrature B), and 482 (medium B). The observer
verifies the same 28 live samplers. Sources and verification are in
`runs/20261004_math_review_guarded_CLASS_third_medium_A_diagnostics`.

The fourth quadrature B assessment freezes its four families after the minimum
postburn represented history grows from 1769 to 2128 (+20.29%). A managed
watcher verifies the original sampler birth identities and mapped native
modules while waiting for the unchanged 2123-step threshold; only then are
complete saved prefixes frozen. Mass Rhat is 1.045702, bulk ESS 97.59,
tail/quantile ESS 219.02, and p95 MCSE 0.00742248 eV against the unchanged
0.001 eV target. All ten parameters still fail at least one gate. The full
postburn p95 is 0.09031825 eV and the equalized-history p95 is 0.08836700 eV;
both remain provisional. Longer histories have not yet resolved the convergence
concerns. Source configurations, prefix extension, recorded native builds,
holding times and process identities pass verification; a distinct self-review
reconstructs all ten complete gate sets. Other cohorts are not reassessed or
pooled. Quadrature B's next minimum history is 2554; its fourth assessment and
the other cohorts' third assessments have distinct snapshot times. The latest
joint four-cohort assessment remains the second one. All 28 owned samplers are
verified live. Receipts are in
`runs/20261004_math_review_guarded_CLASS_fourth_quad_B_diagnostics`. Sampler
settings, production Python, Lean, the paper and canonical summaries are
unchanged, and neither material claim decision is adopted.

Quadrature A's separate fourth assessment retains its four families after
minimum postburn represented history grows from 2039 to 2452 (+20.25%). The
managed watcher verifies the same owned process identities and waits for the
unchanged 2447-step threshold before freezing complete prefixes. Mass Rhat is
1.010548, still above 1.01; bulk ESS is 140.60, tail/quantile ESS 346.49,
and p95 MCSE 0.00371530 eV against 0.001 eV. All ten parameters still fail
at least one unchanged gate. Native build identities, source configurations,
prefix extension and holding weights pass verification; a distinct self-review
reconstructs all ten gate sets with exact integer recounts. Its next minimum
history is 2943. Both quadrature cohorts now have fourth assessments, while
both medium cohorts retain their third assessments, all at distinct times;
the latest joint four-cohort assessment remains the second one. No other
cohort is reassessed or pooled. All 28 inference samplers remain live, and
the temporary watcher exits after successful freezing. Receipts are in
`runs/20261004_math_review_guarded_CLASS_fourth_quad_A_diagnostics`. The new
density comparison repair does not change this diagnostic command or its
dependencies. The paper and canonical summaries remain unchanged; no posterior
convergence certificate or material claim revision is adopted.

Medium B's fourth assessment freezes its four families after the minimum
postburn represented history grows from 401 to 499 (+24.44%). Mass Rhat is
1.054645, bulk ESS 55.18, tail/quantile ESS 86.39, and p95 MCSE 0.00668785 eV
against the unchanged 0.001 eV target. All ten parameters fail at least one
gate; the full-postburn p95 of 0.08023741 eV and retained p95 of 0.08071746 eV
remain provisional. Saved-prefix extension, unchanged source configurations,
actual process identities and native-build witnesses are verified, and a
distinct self-review recounts all holding times and reconstructs all ten gate
sets. Medium B's next minimum history is 599. Its fourth assessment, both
quadrature fourth assessments and medium A's third assessment remain separate
in time; the latest joint assessment is still the second one. A copied observer
initially duplicated the medium list and failed its unique-PID assertion before
writing a runtime receipt; the failed script is preserved and the corrected
observer verifies all 28 inference samplers. No likelihood, sampler, diagnostic
dependency, Lean, paper or canonical-summary change is made. Sources are in
`runs/20261004_math_review_guarded_CLASS_fourth_medium_B_diagnostics`.

Medium A's fourth assessment separately freezes its four families after the
minimum postburn represented history grows from 593 to 728 (+22.77%). Mass
Rhat is 1.044382, bulk ESS 50.55, tail ESS 49.47, quantile ESS 75.80, and p95
MCSE 0.00973557 eV against the unchanged 0.001 eV target. Tail and quantile ESS
are distinct here. All ten parameters fail at least one gate. Source
configurations, native-build witnesses, actual process birth identities and
saved-prefix extension pass verification; the distinct self-review recounts
all four holding-time histories and reconstructs all ten gate sets. Medium A's
next minimum history is 874. The four guarded CLASS cohorts now each retain
a fourth assessment at distinct times, all provisional; their last joint
assessment remains the second one. Neither the grid-12 cohort nor another
precision target is pooled or reassessed. All 28 inference samplers are verified
live. Sources are in
`runs/20261004_math_review_guarded_CLASS_fourth_medium_A_diagnostics`. The
diagnostic dependencies, Lean sources, paper and canonical summaries are
unchanged; both material claim decisions remain pending.

A proposal scout uses the immutable first quadrature snapshots to construct
two finite positive-definite weighted empirical covariances. All eight medium
proposals still equal their initial matrices at the scout time and have no
logged adaptation updates. Generalized covariance eigenvalues and marginal
variance ratios describe possible initialization choices; the pilot is
unconverged and uses a different numerical precision target. It supplies neither
a posterior covariance estimate nor a promised efficiency gain. Frequency-weight
covariances and generalized eigenvalues were recomputed by distinct formulas in
`runs/20261004_math_review_guarded_medium_proposal_scout`.

A single fresh B trial, seed 1501, uses the frozen B pilot to investigate the
grid-12 target with medium dynamics. Its angular controls are l_logstep=1.013
and l_linstep=12; its other model, prior and nuisance definitions match medium B.
Before launch, an actual pinned native replay reproduced all six archived
grid-12 likelihood components exactly at the selected initial point and checked
finite prior/posterior accounting and the three-species mass mapping. Fresh
random state, output and process identity are recorded. This is one trial,
excluded from the four-cohort diagnostics; it cannot supply multi-chain evidence
or be pooled with another grid. Existing samplers and gates remain unchanged.
The first complete saved row (six represented steps) also passed a fresh native
replay with zero discrepancies in all six likelihood components, total
likelihood, prior and posterior. Its mass is 0.0157880 eV, distinct from the
initial point, and the three-species mapping matches. A distinct self-review
checks the frozen prefix, posterior accounting and exact target definitions.
An initial metadata comparison needed to canonicalize an omitted backend path
and the explicit default global path; actual imported and mapped native build
identities agree. This correction changes no likelihood or prior. Its preparation,
launch, initial-point and saved-row evidence are in
`runs/20261004_math_review_guarded_grid12_trial_B_seed1501`. The second assessment's
runtime observer verifies 25 live samplers: eight SPT and seventeen guarded
CLASS, including this separate trial. Historical observations of 24 samplers
retain their earlier time scope.

After seed 1501 began sampling and its saved row passed native replay, three
additional B grid-12 chains were prepared with fresh seeds 1502--1504 and distinct
immutable starting points. Their initial masses are 0.1051773, 0.0627491 and
0.0298598 eV. All three starting points passed actual pinned native evaluations
with finite prior, posterior and six likelihood components. The four chains
have exactly the same numerical target, sampled priors, fixed nuisance
definitions, mass mapping, frozen pilot covariance and sampler rules; only
starting references and seeds differ. A distinct configuration self-review
checks these equalities and the source-row provenance. Old-target coordinates
are initialization inputs, not new-target posterior draws or independence
certificates. This establishes a four-start grid-12 cohort for later assessment,
with no quadrature or grid-25 pooling and no convergence or uniform solver claim.
Launch receipts verify fresh output, actual process birth identities and mapped
native modules. Managed workers have now frozen and natively replayed the first
complete saved rows of all three new chains. Their first saved masses are
0.1023803, 0.0797134 and 0.0298598 eV; all six likelihood components, total
likelihood, prior and posterior have zero replay discrepancy. The four-chain
saved-row self-review checks exact target definitions, saved-prefix provenance,
integer holding times, posterior accounting and the three-species mass mapping.
Only selected initial rows are verified; no convergence or uniform accuracy
certificate follows. The post-replay observation verifies
28 live inference samplers: eight SPT and twenty guarded CLASS, including all
four B grid-12 chains. Preparation and native preflight evidence are in
`runs/20261004_math_review_guarded_grid12_B_replica_preparation`, with each seed's
launch and completed saved-row evidence in its own trial directory. Existing
samplers and diagnostic gates remain unchanged; the paper remains untouched.

Each new cosmological direction now records its source candidate explicitly.
The verifier also checks that all shared cosmological coordinates equal that
source, that exactly the nuisance parameters were free during profiling, and
that the selected reference is no worse than the nested cross candidate.
Legacy bundles use their retained initial source fits. Thirteen earlier
archived directions pass the standalone source/domain checks; the receipt is
`runs/20261003_math_review_validation/transfer_source_verification.json`.
These checks do not certify global optima. The completed controlled reverse search
found an A reference candidate better than its original own-fit source.
The earlier forward audit is therefore conditional on the original declared A
source. The completed forward replay from the improved final A candidate now
has fresh native evidence and an exact source-reference pair check against
the completed reverse direction.

The fifth guarded quadrature B assessment retains all four families after
minimum postburn represented history grows from 2128 to 2623 (+23.26%).
Mass Rhat improves to 1.027011, bulk ESS to 183.43 and tail/quantile ESS to
290.27, but all ten sampled parameters still fail the unchanged gates.
Mass p95 MCSE is 0.00654607 eV, above the 0.001 eV target. Retained p95
is 0.08836700 eV; full-postburn p95 is 0.08833480 eV. Exact integer recounts,
prefix extension, unchanged source configurations and private native build,
first native witness preservation and all nine gates per parameter are checked.
This B assessment does not reassess the other three CLASS cohorts or pool
numerical grids. The next B minimum history is 3148; the historical joint
CLASS assessment remains the second. The runtime observer verifies 36 live
samplers, including the eight newly launched archived-version SPT chains,
which have no posterior qualification. Evidence and distinct self-review are
in `runs/20261004_math_review_guarded_CLASS_fifth_quad_B_diagnostics`.

To preserve the main empirical strength, obtain multiple
converged chains with bulk and tail diagnostics and quantile uncertainty small
enough to resolve the shift. Assess the CLASS precision sensitivity and refit
or repeat inference with controlled settings where needed. Current artifacts are compatible with this direction
but do not prove it. Restoration is continuing toward preserving the claims.
The user has been asked whether to record TT dominance as conditional on the
SPT-only model, with direction-dependent full-CMB localization, or to keep
restoration of full-CMB TT dominance open for further investigation. This is
prompted by repeated native-verified full-CMB forward EE dominance under the
starting-point, prior, and support controls. No answer or material narrowing
has been adopted. The improved-source replay adds another native-verified
instance of forward EE and reverse TT dominance in the stated range. Posterior
controls continue independently of that decision. Completed numerical controls
provide pointwise sensitivity evidence, with posterior-wide accuracy still
uncertified. The goal remains open until the remaining mathematical and
empirical obligations have been verified under the agreed claim scope;
discussing a scope change alone does not establish completion.

Source checks used the pinned local candl implementation and official
[candl API](https://candl.readthedocs.io/en/latest/api/like_api.html),
[Cobaya output](https://cobaya.readthedocs.io/en/latest/output.html), and
[Cobaya MCMC](https://cobaya.readthedocs.io/en/cosmo_package/sampler_mcmc.html) documentation.

The optional rank and quantile diagnostics follow the official
[ArviZ diagnostic API](https://python.arviz.org/projects/stats/en/stable/api/index.html)
and its [rank/folded Rhat definition](https://python.arviz.org/projects/stats/en/stable/api/generated/arviz_stats.rhat.html).


The fifth guarded CLASS A-quadrature assessment freezes all four families
once the minimum postburn holding-time history grows from 2452 to 3464
(+41.27%). Mass Rhat is 1.021013, bulk ESS 160.52, tail/quantile ESS 176.55,
and p95 MCSE 0.00697752 eV. Retained/full-postburn p95 values are
0.10616384/0.10671602 eV, with half-history drift 0.01478775 eV. All ten
parameter gate sets still fail. The next minimum-history threshold is 4157.
The fifth B-medium assessment freezes its four families after growth from
499 to 676 (+35.47%). Mass Rhat is 1.053629, bulk ESS 78.01,
tail/quantile ESS 135.18 and p95 MCSE 0.00570884 eV. Retained/full-postburn
p95 values are 0.07760689/0.07676388 eV, with half-history drift 0.01108773 eV.
All ten parameter gates fail; the next threshold is 812. These are separate
precision targets and observation times; the latest joint CLASS assessment
remains the second historical bundle. Complete-prefix, native-module,
configuration and owned-process checks pass, and distinct self-review
reconstructs every gate from exact integer holding times. The latest observer
confirms the same 36 inference samplers, excluding finite repair probes.
Bundles are `runs/20261004_math_review_guarded_CLASS_fifth_quad_A_diagnostics`
and `runs/20261004_math_review_guarded_CLASS_fifth_medium_B_diagnostics`.
No posterior bound is qualified from these still-failing assessments.

The repaired CAMB transfer policy now has twenty fresh inference chains,
with four fixed starts for each of five separate numerical targets:

| Target | CAMB | Cobaya | Explicit lmax | Seeds |
| --- | --- | --- | --- | --- |
| Archived-version A | 1.6.5 | 3.6.1 | 3200 | 1701–1704 |
| Archived-version B | 1.6.5 | 3.6.1 | 4095 | 1705–1708 |
| Current restoration A | 2.0.4 | 3.6.2 | 4095 | 1801–1804 |
| Current B | 2.0.4 | 3.6.2 | 4095 | 1805–1808 |
| Current original-settings A | 2.0.4 | 3.6.2 | 3200 | 1901–1904 |

All use the current Python, likelihood and dataset stack. Archived-version
targets do not reconstruct the entire historical environment. Initial points
come from the four previously declared original/restoration median/p95 labels;
these coordinates do not supply posterior evidence. Byte-identical covariance
files from completed families 401 and 404 supply proposal heuristics only.
Their seven-coordinate headers, finite positive-definite matrices, completion
witnesses and hashes are checked. No source samples are pooled into a fresh
cohort. Priors, likelihood definitions, mass species and numerical settings
match each explicitly declared target. The two comparisons that reuse current
B share that B estimate and must not be treated as independent comparisons.

All twenty initial likelihood/prior results match independent upstream
forced-fresh models exactly, including after cache resizing to 50. Earlier
selected controls reproduce within the predeclared component tolerance 1e-9;
the largest difference is 2.57e-11 under the new single-thread environment.
Launch contracts check the native module, wrapper, production adapter, sampler,
runner, configuration and proposal hashes before creating output. Actual
process birth identities, mapped modules, effective FreshCAMB class and
FullPrecisionMCMC metadata pass activation checks. All twenty first saved rows
also replay within 1e-9, with exact production-adapter agreement to independent
upstream fresh results. Distinct self-review recounts the frozen byte prefixes,
finite coordinates, integer holding times, backend witnesses and effective
metadata. These are selected evaluation checks, not convergence or uniform
native accuracy certificates. The first diagnostic history threshold is 1000
represented postburn steps for every family in a target; established posterior
gates remain unchanged.

Ten remaining samplers using the superseded transfer-cache policy were stopped
only after the replacement native checks passed. Their managed exits are 143.
Six earlier SPT samplers were already absent without completion summaries, and
their managed handles were unavailable; their terminal causes and exit codes
remain unknown. All sixteen old-policy output bundles are frozen and verified
against the original bytes. No timeout prompted a restart or retirement, and
not every individual older chain is proved incorrect. The final runtime check
verifies forty live inference identities: twenty fresh CAMB and twenty guarded
CLASS. Production sources remain byte-identical to the completed 168-test and
74-export Lean validation. Evidence is in
`runs/20261004_math_review_fresh_CAMB_posterior_preparation`.

Earlier near-0.030 eV posterior gate results remain historical empirical
diagnostics; their native evaluation bridge is not currently qualified after
the transfer-cache counterexample. They cannot resolve the original near-0.109
eV headline. The separate fresh solver/cutoff cohorts must establish that
comparison with passing posterior diagnostics. No material claim revision is
adopted, and neither the paper nor canonical results are changed.

The sixth CLASS quadrature-B assessment freezes four extended prefixes with
postburn represented-step counts [3582, 3474, 3588, 3428], exceeding the previous
minimum 2623 by 30.69%. Mass Rhat is 1.026983, bulk ESS 266.63 and tail/quantile
ESS 375.91. The p95 MCSE is 0.00474238 eV, above the unchanged 0.001 eV limit;
retained/full-postburn p95 values are 0.08292533/0.08478488 eV, with half-history
drift 0.00446664 eV. All ten parameter gate sets fail. The fifth medium-A
assessment retains families 1201, 1401, 1402 and 1406 with represented-step
counts [983, 1388, 1332, 1001], a minimum increase of 35.03% from 728. Mass Rhat
is 1.047722, bulk ESS 86.55 and tail/quantile ESS 142.08. The p95 MCSE is
0.00613163 eV; retained/full-postburn p95 values are 0.10828141/0.10515632 eV,
with half-history drift 0.01031072 eV. All ten parameter gates also fail here.
Every saved prefix, native build and configuration witness is verified, and
distinct self-review reconstructs all nine gates per parameter using exact
integer holding times. The two diagnostic workers finish with exit code zero.
No precision tiers are pooled and no new joint CLASS result is adopted.

The next minimum-history triggers are 4114 for quadrature B and 1180 for
medium A. Quadrature A and medium B remain below their existing 4157 and 812
triggers. The four grid12 B trials and the five fresh CAMB targets are below
their first 1000-step triggers; these are scheduling thresholds, not altered
acceptance gates. All forty inference processes remain live with their owned
birth identities and native modules verified. The two closed assessment bundles
are `runs/20261004_math_review_guarded_CLASS_sixth_quad_B_diagnostics` and
`runs/20261004_math_review_guarded_CLASS_fifth_medium_A_diagnostics`. Their
results remain unqualified for posterior-bound replacement or uniform solver
accuracy. The paper and canonical results are untouched.

A further data-selection review found that a copied bundle's absolute
`resolved.yaml` output could redirect extraction, diagnosis, native version
lookup and row-target verification to an existing chain outside the bundle.
The new seed1701 first-row snapshot contains one frozen row, but its stored
output path selected the active source and read 62 rows at the failing probe.
Thus local configuration/native witnesses could be paired with different chain
bytes. The first-row native proofs themselves read the frozen files directly
and are unaffected.

The shared prefix resolver now selects actual chain data inside the requested
bundle. A stale output path is matched by prefix name to its local saved copy;
missing matching data and ambiguous local copies are rejected. A metadata-free
bundle must have one unambiguous prefix. Explicit `--chains_prefix` access
remains available for a deliberately external chain. Seven regression cases
cover active source growth, absent local data, named selection among multiple
chains, missing named data, ambiguity, relative nested/single-file outputs,
and an actual diagnostic report using 32 frozen draws rather than 800 active
draws. The before implementation fails five of the six initial controls;
the final full check passes 175 Python tests, the unchanged Lean build and all
74 public axiom outputs using only the allowed standard axioms.

The impact check covers all 547 tracked resolved bundles: 441 prefixes stay
unchanged, 70 external outputs now select their local saved chains, and 27
previously returned prefixes are refused because those bundles contain no local
chain data. All twenty new native first-row bundles resolve to exactly their
frozen mass and holding time. The latest quadrature A/B and medium A/B reports
are recomputed into separate files and agree with the original full reports
exactly. No original report, native model, sampler configuration or diagnostic
gate is changed. Forty owned native inference identities remain live. The
before source, failing controls, complete impact records, report replays,
full validation and distinct self-review are in
`runs/20261004_math_review_bundle_chain_resolution_repair`. Posterior restoration
and the material claim discussions remain open; the paper and canonical results
are unchanged.

`UpperGate.lean` now formalizes the finite-upper-prior step for actual laws.
For any real-coordinate probability measure with positive retained CDF F(U),
it constructs the conditional measure on `(-infinity,U]`, derives its probability
normalization, and proves its exact CDF is `F(min(x,U))/F(U)`. The omitted mass
is the actual event probability `P(X>U)=1-F(U)`, including when U carries an
atom. The CDF increase lies between zero and this omitted mass at every
coordinate, with equality at U. These conclusions concern probability levels;
they do not supply a coordinate quantile-error bound without further inverse
regularity. A CDF-level solution below U corresponds exactly to original
probability level `q*F(U)`.

For the previously constructed positive-width physical-gated Gaussian, the
retained mass below every positive finite U is proved positive. Conditioning
therefore gives an actual law on `[0,U]`, and for every `0<q<1` it has exactly
one quantile in `(0,U)`. Both normalization steps and the quantile existence
are derived. This extends the formal Gaussian coverage to a finite upper gate
while retaining arbitrary real mean, positive sigma, and constant-prior
interpretation. It does not assume cosmological Gaussianity or certify that
mass omitted by widening a cosmological prior is small.

Ten formal self-review examples cover the actual conditioned law, atom at U,
the strict upper-tail event, a 95-percent level with U=5, original-level
rescaling, a strictly positive Gaussian CDF error at the cap, nonunique
endpoint levels across real coordinates, a nonpositive cap's zero retained
measure, and the absolute probability-scale error. A first elaboration attempt
failed on the numeral type in a set-membership proof; its source and log are
retained. The corrected proof, controls, and full check pass 175 Python tests,
the Lean build and all 83 public theorem axiom outputs using only `propext`,
`Classical.choice`, and `Quot.sound`. Distinct self-review verifies exact
premises, actual-law construction and coverage. Evidence is in
`runs/20261004_math_review_finite_upper_gate_formalization`. All forty native
inference identities remain live. The manuscript, canonical results, numerical
targets and unresolved material claim decisions remain unchanged.

The sixth CLASS medium-B assessment freezes all four prefixes with represented
postburn histories [1105, 919, 814, 1014]. The minimum grows from 676 to 814
(20.41%), meeting the existing 812-step trigger. Mass Rhat is 1.041845,
bulk ESS 99.28 and tail/quantile ESS 119.62. Its p95 MCSE is 0.00624222 eV,
above the unchanged 0.001 eV target; retained and full-postburn p95 coincide at
0.07679691 eV, with half-history drift 0.00384913 eV. All ten parameter gate
sets remain failing. Native/configuration witnesses, complete-prefix extension
and exact holding times are verified, and distinct self-review reconstructs
all gates. The diagnostic exits zero; the next minimum-history trigger is 977.
No precision tier or joint CLASS result is replaced. Evidence is in
`runs/20261004_math_review_guarded_CLASS_sixth_medium_B_diagnostics`.

The five fresh CAMB targets now have a prepared assessment contract and workflow
in `runs/20261004_math_review_fresh_CAMB_diagnostic_preparation`. They retain
four families each, the existing 1000-step first trigger, 20-percent stored-row
burn-in, 1.2 subsequent growth factor, unchanged rank/ESS gates, 0.001 eV mass
MCSE and 0.05 relative MCSE target for other parameters. Frozen snapshots must
retain their verified first-row bytes and exact native/configuration identities.
Before diagnostics, three selected frozen rows per family must replay against
the upstream original class with forced-fresh native transfers at the unchanged
1e-9 absolute tolerance and zero relative tolerance. Later verification
recounts integer weights, provenance and every acceptance gate. Separate
targets and cache policies cannot be pooled, and comparisons reusing current
B are explicitly dependent.

The final insufficient-history controls observe group minima of 542, 513, 454,
448 and 594 steps for old A3200, old B4095, current A4095, current B4095 and
current A3200 respectively. Every control returns the declared scheduling exit
3 and creates no assessment snapshot. Distinct self-review checks the target
contracts, syntax and these branches; full snapshot/native/diagnostic execution
is still pending and is not represented as completed validation. All forty
native inference identities remain live. Production Python and Lean sources
are unchanged since the 175-test/83-theorem check. Neither paper nor canonical
results are edited.

The previously prepared CAMB workflow is now exercised end to end on two separate
short-prefix control bundles, current A3200 and archived-version A3200. The
control copy changes only its first scheduling trigger from 1000 to eight;
all numerical targets, native checks and diagnostic acceptance settings stay
identical. Its contract explicitly excludes scientific posterior qualification.
The authoritative production contract remains at 1000, and these controls do
not replace either target's first production assessment.

Current-version represented postburn histories are [779, 754, 739, 733];
archived-version histories are [751, 713, 735, 744]. The full frozen snapshot,
upstream forced-fresh replay, diagnostic and verification paths all exit zero.
Each checks first, middle and last stored rows in every family: all 24 selected
rows have exactly zero native component discrepancy. A current-environment
attempt against the archived target is correctly refused at native-module
identity, before constructing a model. All seven parameter gate sets fail in
both diagnostic reports. Distinct self-review recounts exact holding times,
physical configurations and selected component coverage, and independently
reproduces every relative MCSE limit by direct extended-precision weighted
moments. This validates the tested workflow branches and selected native rows;
it does not prove posterior convergence or uniform solver accuracy. Evidence is
in `runs/20261004_math_review_fresh_CAMB_workflow_control`.

A fresh process/native-map observation verifies all forty inference identities.
No cohort meets its next saved-history trigger: CLASS quadrature A/B minima are
4110/3777 against 4157/4114; medium A/B are 1073/827 against 1180/977; grid12 B
is 297 against 1000. Fresh CAMB old A3200/B4095 and current A4095/B4095/A3200
minima are 744, 686, 601, 562 and 788 against 1000. These are complete-prefix
observations with stored-row burn-in and exact integer holding times, rather
than convergence assessments. Evidence is in
`runs/20261004_math_review_posterior_growth_after_checkpoint`. The review state
now points its latest full validation to the completed 175-Python/83-Lean check
and states explicitly that no fresh SPT posterior readout is qualified. The
paper and canonical results remain unchanged.

The sixth CLASS quadrature-A assessment freezes histories [4186, 4511, 4238,
4159], extending the previous four prefixes and growing the minimum from
3464 to 4159 (20.06%). This meets the unchanged 4157-step trigger. Mass Rhat
is 1.023769, bulk ESS 196.21, tail/quantile ESS 213.47, and p95 MCSE
0.00599807 eV against 0.001 eV. Retained/full p95 are 0.10423310/0.10436030 eV,
with half-history drift 0.01607140 eV. All ten parameter gate sets fail.
Snapshot/native/configuration witnesses and exact holding times are checked;
distinct self-review reconstructs every acceptance gate. Its managed diagnostic
exits zero, and the next minimum-history trigger is 4991. The latest joint CLASS
assessment remains the historical second assessment; no precision tiers are
pooled or new posterior result qualified. Evidence is in
`runs/20261004_math_review_guarded_CLASS_sixth_quad_A_diagnostics`. All forty
inference identities are verified live. Paper and canonical results are unchanged.

The BAO volume-distance helper had an additional intermediate-range defect:
finite positive inputs with z=1 and DH=DM=rd=1e200 return infinity, and the
analogous 1e-200 inputs return zero, although DV/rd=1 in both cases. A large
z*DH followed by zero DM can return NaN when the mathematical volume distance
is zero. The helper now handles zero numerators first and, only when the
ordinary product is nonfinite or underflows, separates binary mantissas and
exponents. It cancels the sound-horizon exponent before cube-root rescaling.
A nonrepresentable final ratio is explicitly refused for every observable.
The ordinary DV expression is preserved exactly, including its operation order.

Nine regression cases fail before the repair; all twenty targeted tests pass
after it. A first fallback used math.cbrt, which is unsuitable for the declared
Python>=3.9 support; distinct self-review replaced that new dependency with
NumPy's existing cube-root function. The initial combined check passes 186
Python tests, the Lean build and all 83 standard-axiom outputs. After the
compatibility repair, the complete Python suite again passes 186 tests; the
Lean sources are unchanged. All 108 separate 100/180-digit reference controls
pass at a declared 3e-15 relative tolerance. Final-source native replay checks
first and last saved rows for one family in each CAMB version, at the unchanged
1e-9 absolute tolerance and zero relative tolerance. Each row's full BAO
prediction vector agrees exactly with the before implementation. Self-review
also compares the ordinary expressions' syntax trees and verifies validation
scope, actual output hashes, native identity and all forty live inference
identities. These are selected numerical controls, not global interval accuracy
or posterior convergence certificates. Evidence, including the failed before
controls and compatibility attempt, is in
`runs/20261004_math_review_BAO_distance_range_repair`. No sampler is restarted;
ordinary cosmological target arithmetic, paper and canonical results are unchanged.

The first fresh-CAMB current A3200 production assessment meets the unchanged
1000-step scheduling trigger with exact postburn histories [1076, 1088, 1046,
1031]. It freezes the actual prefixes, declared target and native-version
witnesses, and replays first/middle/last stored rows in all four families
against upstream CAMB with forced-fresh transfers. All twelve selected rows
have exactly zero native component discrepancy. The diagnostic and frozen-data
verification both exit zero, with all seven parameter gate sets failing.
Mass Rhat is 1.040004, bulk ESS 99.54, tail ESS 140.74, quantile ESS 166.75,
and p95 MCSE 0.02043319 eV against 0.001 eV. Retained/full empirical p95 are
0.14446583/0.13930197 eV, with half-history drift 0.01602719 eV. These empirical
statistics are not a qualified posterior bound or an accepted headline result.
The next minimum-history trigger is 1238. Evidence is in
`runs/20261004_math_review_fresh_CAMB_first_current_A3200_diagnostics`.
The other first production assessments and all material claim decisions remain
pending. No targets are pooled, and the paper and canonical results are unchanged.

The first fresh-CAMB archived-version A3200 production assessment also meets
its unchanged 1000-step trigger, with exact histories [1099, 1023, 1033, 1067].
All twelve selected first/middle/last rows replay exactly against upstream
CAMB 1.6.5/Cobaya 3.6.1 with forced-fresh transfers. The diagnostic and frozen-data
self-review exit zero, with all seven parameter gate sets failing. Mass Rhat
is 1.032767, bulk ESS 88.73, tail ESS 143.54, quantile ESS 210.60, and p95 MCSE
0.01115820 eV against 0.001 eV. Retained/full empirical p95 are
0.12428535/0.12295932 eV, with half-history drift 0.00973501 eV. The next
minimum-history trigger is 1228. Evidence is in
`runs/20261004_math_review_fresh_CAMB_first_old_A3200_diagnostics`.
These are version-controlled native targets on the current Python/likelihood
stack, not an exact reconstruction of the historical whole environment.
Neither A3200 target supplies a qualified posterior comparison; no solver-version
or lens-swap result is adopted from these short failing histories.

The closing observation verifies all forty owned process/native identities.
Fresh old A3200/B4095 and current A4095/B4095/A3200 minima are 1057, 950, 859,
811 and 1122 against their current triggers 1228, 1000, 1000, 1000 and 1238.
CLASS quadrature A/B minima are 4333/3936 against 4991/4114; medium A/B are
1113/842 against 1180/977, and grid12 B is 339 against 1000. No next assessment
is due. All posterior qualifications, precision conclusions, upper-prior
insensitivity and material claim decisions remain pending. Paper and canonical
results are unchanged.

The first fresh-CAMB archived-version B4095 production assessment meets the
unchanged 1000-step trigger with exact histories [1019, 1035, 1083, 1100].
All twelve selected rows replay exactly against upstream CAMB 1.6.5/Cobaya 3.6.1
with forced-fresh transfers. The diagnostic and frozen-data self-review exit
zero. All seven parameter gate sets fail. Mass Rhat is
1.043082, bulk ESS 131.47, tail ESS
224.09, quantile ESS 224.09, and p95 MCSE
0.00792757 eV against 0.001 eV. Retained/full empirical p95 are
0.10590137/0.10590137 eV, with
half-history drift 0.00298068 eV. The next minimum
history is 1223. Evidence is in
`runs/20261004_math_review_fresh_CAMB_first_old_B4095_diagnostics`.
No original headline or solver-version result is qualified from these failing
histories; original-style A3200 and B4095 also retain their different cutoffs.
The two current-version 4095 targets await their first production assessments.
Paper and canonical results remain unchanged.

The raw chain reader had another coordinate-identity defect: it assumed column
zero contained weights without checking a supplied header's label. For the
header `minuslogpost weight mnu` and rows [99,1,0.1], [1,1,0.2], it reads 99:1
weights and reports empirical p95=0.1, whereas the labeled 1:1 weights give
p95=0.2. A labeled chain now requires its first column to be `weight` before
raw diagnostics or GetDist can consume it. Every numbered chain is checked,
including when `.paramnames` supplies coordinate names. Unheaded standard
GetDist chains and the unused second-column label `minusloglike` remain valid.

Five before controls fail, including raw, diagnostic and density paths; the
final combined check passes 193 Python tests, the Lean build and all 83 public
standard-axiom outputs. All seven latest complete CLASS/fresh-CAMB reports are
recomputed into separate files and agree exactly. Distinct self-review verifies
that removing the added header premise leaves every original reader function's
syntax tree unchanged. Evidence is in
`runs/20261004_math_review_chain_weight_header_repair`.

The source-pinned fresh-CAMB workflow is updated separately in
`runs/20261004_math_review_fresh_CAMB_header_guard_diagnostic_preparation`.
Its predecessor transition permits only the verified reader source update;
all other contract fields must agree exactly, including target configurations,
native identities, starts and gate settings. The seven-report replay receipt
and predecessor contract are checked by hash. Nine negative controls reject
unknown predecessors, altered native/configuration identities, lowered history
or replay requirements, unreviewed reader changes and incorrect validation
hashes. Exact old frozen prefixes and the original 1.2 growth factor are retained.
The final snapshot verifier independently derives the trigger and checks
predecessor contract identity and prefix extension. No history counter resets.

The second current-A3200 assessment exercises that transition on genuine
histories [1320,1350,1317,1317], growing the prior minimum 1031 by 27.74% and
meeting the unchanged 1238 trigger. All twelve selected rows replay exactly;
native, diagnostic and snapshot-verification stages exit zero. All seven
parameter gate sets fail. Mass Rhat is 1.036892, bulk ESS 148.27, tail/quantile
ESS 247.71 and p95 MCSE 0.01052513 eV against 0.001 eV. Retained/full empirical
p95 coincide at 0.13071401 eV; half-history drift is 0.03353985 eV. The next
minimum history is 1581. Evidence is in
`runs/20261004_math_review_fresh_CAMB_second_current_A3200_diagnostics`.
No posterior bound is qualified, no targets are pooled, and no sampler is
restarted. Paper and canonical results remain unchanged.

The first fresh-CAMB current A4095 production assessment meets its unchanged
1000-step trigger with exact histories [1040, 1052, 1063, 1041].
All twelve selected rows replay exactly against upstream CAMB 2.0.4/Cobaya 3.6.2
with forced-fresh transfers. Native, diagnostic and frozen-data verification
exit zero; all seven parameter gate sets fail. Mass Rhat is
1.026280, bulk ESS 97.44, tail ESS
114.25, quantile ESS 114.25, and p95 MCSE
0.01237429 eV against 0.001 eV. Retained/full empirical p95 are
0.12499940/0.12499940 eV, with
half-history drift 0.04241356 eV. The next minimum
history is 1248. Evidence is in
`runs/20261004_math_review_fresh_CAMB_first_current_A4095_diagnostics`.
No solver-version, cutoff or lens-swap comparison is qualified from these
short failing histories. Current B4095 is the remaining first fresh-CAMB
production assessment. Paper and canonical results are unchanged.

The first fresh-CAMB current B4095 production assessment meets the unchanged
1000-step trigger with histories [1057, 1046, 1008, 1033]. All twelve
selected rows replay exactly against upstream CAMB 2.0.4/Cobaya 3.6.2 with
forced-fresh transfers. Native, diagnostic and frozen-data verification exit
zero. All seven parameter gate sets fail. Mass Rhat is
1.034195, bulk ESS 131.82, tail ESS
159.10, quantile ESS 159.10, and p95 MCSE
0.00799867 eV against 0.001 eV. Retained/full empirical p95 are
0.10467387/0.10372106 eV, with
half-history drift 0.01032511 eV. Its next minimum
history is 1210. Evidence is in
`runs/20261004_math_review_fresh_CAMB_first_current_B4095_diagnostics`.
All five targets now have first production assessments, with sixty selected
native rows replaying exactly and none supplying qualified posteriors. These
are separate targets, and reused current-B contrasts remain dependent. No
headline, version or cutoff comparison is adopted from the failing histories.
The actual process/native-map observation verifies all forty inference identities
and finds archived-version A3200 and B4095 ready for their second assessments;
those frozen snapshots are being verified separately. Paper and canonical
results remain unchanged.

The second fresh-CAMB archived-version A3200 assessment has exact represented post-burn-in
histories [1494, 1375, 1398, 1399]. All twelve selected rows replay exactly against upstream
CAMB 1.6.5/Cobaya 3.6.1 with forced-fresh transfers. Native replay, diagnostic
execution and snapshot verification exit zero, and distinct self-review
reconstructs every gate. All seven parameter gate sets fail. Mass Rhat is
1.031994, bulk ESS 139.54, tail ESS
208.28, quantile ESS 238.96 and p95 MCSE
0.00926394 eV against 0.001 eV. Retained/full empirical p95 are
0.12855788/0.12855788 eV; half-history
drift is 0.00433279 eV. The next minimum history is
1650. Evidence is in `runs/20261004_math_review_fresh_CAMB_second_old_A3200_diagnostics`. These solver versions do not reproduce the
entire archived environment, and these failing histories qualify no headline
or version/cutoff comparison.

The second fresh-CAMB archived-version B4095 assessment has exact represented post-burn-in
histories [1284, 1307, 1322, 1346]. All twelve selected rows replay exactly against upstream
CAMB 1.6.5/Cobaya 3.6.1 with forced-fresh transfers. Native replay, diagnostic
execution and snapshot verification exit zero, and distinct self-review
reconstructs every gate. All seven parameter gate sets fail. Mass Rhat is
1.027867, bulk ESS 146.27, tail ESS
239.54, quantile ESS 239.54 and p95 MCSE
0.00708758 eV against 0.001 eV. Retained/full empirical p95 are
0.10185033/0.10088250 eV; half-history
drift is 0.00280687 eV. The next minimum history is
1541. Evidence is in `runs/20261004_math_review_fresh_CAMB_second_old_B4095_diagnostics`. These solver versions do not reproduce the
entire archived environment, and these failing histories qualify no headline
or version/cutoff comparison.

The seventh guarded CLASS quadrature-B assessment extends all four earlier
prefixes with histories [4281,4204,4326,4119], meeting the unchanged 4114
trigger. Diagnostic execution, frozen snapshot verification and distinct
self-review pass. No parameter passes all gates. Mass Rhat is
1.016437, bulk ESS 314.80, tail/quantile ESS
399.85 and p95 MCSE 0.00500567 eV against
0.001 eV. Retained/full empirical p95 are
0.08364963/0.08322698 eV; half-history
drift is 0.00636396 eV. The next minimum history is
4943. Evidence is in `runs/20261004_math_review_guarded_CLASS_seventh_quad_B_diagnostics`. An initial runner invocation exited 2 before
scientific execution because the chosen predecessor lacked that script;
the preparation receipt preserves this failure and records the shared runner
copied from quadrature A. The successfully frozen snapshot was preserved.

The generic latest CLASS summary pointers and both scheduling maps are
reconciled to the separately verified quadrature A sixth, quadrature B seventh,
medium A fifth and medium B sixth assessments. The latest joint assessment
remains the historical second assessment; separate observation times supply no
new joint comparison. The runtime observation verifies forty live inference
identities. No posterior bound, uniform precision certificate or upper-prior
insensitivity follows. Both material claim decisions remain open. Paper and
canonical results remain unchanged.

The third fresh-CAMB current-A3200 assessment reaches minimum represented
post-burn-in history 1669, above its unchanged 1581
trigger. Its four histories are [1701, 1724, 1670, 1669]. All twelve
selected rows replay exactly. Native replay, diagnostics and verification exit
zero; all seven parameter gate sets fail. Mass Rhat is
1.029406, bulk ESS 154.60, tail ESS
175.38, quantile ESS 175.38 and p95 MCSE
0.02102559 eV against 0.001 eV. Retained/full empirical p95 are
0.15333412/0.15333412 eV; half-history
drift is 0.00641407 eV. The next minimum history is
2003. Evidence is in `runs/20261004_math_review_fresh_CAMB_third_current_A3200_diagnostics`. The preceding runtime observer
checks all forty actual process/native identities and derives CLASS thresholds
from the reconciled latest state. No posterior comparison is qualified.

Header fallback previously globbed every prefix.*.txt while raw loading filtered
numeric chain suffixes. With no .paramnames, a progress sidecar can supply the
wrong header and reject a valid single or numbered chain. A numeric-looking
directory also enters either discovery path, including with explicit paramnames.
Both paths now share regular numbered-file selection, preserving the single-file
fallback and existing numbered-family precedence. Eight before controls fail;
all nine new controls pass in the combined 202-Python-test check. Lean builds,
and all 83 public axiom outputs use only the standard foundations. Distinct
self-review compares syntax trees after replacing the two selection blocks:
no numerical calculation or other reader behavior changes. All nine latest
complete cohort reports replay identically, including the seventh CLASS B and
third current CAMB A3200 reports. Evidence is in
`runs/20261004_math_review_chain_header_fallback_repair`.

The new source-pinned workflow in
`runs/20261004_math_review_fresh_CAMB_file_selection_diagnostic_preparation`
accepts the two earlier contract hashes only through the checked reader update
and nine-report replay receipt. All other contract fields agree exactly.
Self-review rejects nine unsafe transitions, checks both predecessors, and
exercises all five live growth branches: three refuse without output, while
the current A4095 and B4095 branches freeze genuinely due second assessments.
No growth counter, gate, native build or target is reset.

The second fresh-CAMB current_A4095 assessment uses exact histories
[1308, 1302, 1281, 1278]. All twelve selected native rows replay exactly;
native replay, diagnostics and snapshot verification exit zero. All seven
parameter gate sets fail. Mass Rhat is 1.041730, bulk ESS
129.12, tail ESS 187.08, quantile ESS
187.08 and p95 MCSE 0.00840473 eV against
0.001 eV. Retained/full empirical p95 are
0.12468739/0.12468739 eV; half-history
drift is 0.02169496 eV. The next minimum history is
1534. Evidence is in `runs/20261004_math_review_fresh_CAMB_second_current_A4095_diagnostics`.
These separate, failing histories qualify no headline, solver-version or cutoff
comparison. No physical target or main claim changes; paper and canonical
results remain unchanged.

The second fresh-CAMB current_B4095 assessment uses exact histories
[1272, 1216, 1221, 1240]. All twelve selected native rows replay exactly;
native replay, diagnostics and snapshot verification exit zero. All seven
parameter gate sets fail. Mass Rhat is 1.013323, bulk ESS
165.66, tail ESS 216.73, quantile ESS
216.73 and p95 MCSE 0.00643421 eV against
0.001 eV. Retained/full empirical p95 are
0.10263614/0.10288917 eV; half-history
drift is 0.01291394 eV. The next minimum history is
1460. Evidence is in `runs/20261004_math_review_fresh_CAMB_second_current_B4095_diagnostics`.
These separate, failing histories qualify no headline, solver-version or cutoff
comparison. No physical target or main claim changes; paper and canonical
results remain unchanged.

After the reader-selection checkpoint, a fresh observation checks all forty
owned PID/birth/command/native-map identities and zero stderr. All ten
cohorts remain below their next scheduling thresholds. Minimum represented
post-burn-in histories are quadrature A/B 4681/4215 (triggers 4991/4943),
medium A/B 1168/904 (1180/977), grid12 B 387 (1000), archived-version
A3200/B4095 1632/1479 (1650/1541), current A4095/B4095 1317/1250
(1534/1460), and current A3200 1777 (2003). These observations are scheduling
evidence only. The latest distinct assessments continue to fail every parameter
gate set; no native posterior bound or material claim revision is adopted.
Evidence is in `runs/20261004_math_review_post_reader_selection_runtime_observation`.

The third fresh-CAMB archived-version A3200 assessment meets its unchanged
1650 trigger with exact histories [1751, 1652, 1656, 1693]. All twelve
selected native rows replay exactly under forced-fresh transfers; diagnostic
execution, native replay and snapshot verification exit zero. All seven
parameter gate sets fail. Mass Rhat is 1.031962, bulk ESS
160.93, tail ESS 254.08, quantile ESS
347.76 and p95 MCSE 0.00725501 eV against
0.001 eV. Retained/full empirical p95 are
0.12884334/0.12993601 eV; half-history
drift is 0.00994072 eV. Its next minimum history is
1983. Evidence is in `runs/20261004_math_review_fresh_CAMB_third_old_A3200_diagnostics`.
The runtime observation checks all forty live process/native identities and
places archived B4095 at 1528 versus trigger 1541. These separately observed,
failing histories qualify no headline or version/cutoff comparison.

The third fresh-CAMB archived-version B4095 assessment meets its unchanged
1541 trigger with exact histories [1593, 1629, 1563, 1632]. All twelve
selected native rows replay exactly; native replay, diagnostics and snapshot
verification exit zero. All seven parameter gate sets fail. Mass Rhat is
1.023029, bulk ESS 194.14, tail ESS
266.29, quantile ESS 281.43, and p95 MCSE
0.00731019 eV against 0.001 eV. Retained/full empirical p95
coincide at 0.09750879 eV; half-history drift is
0.00422435 eV. Its next minimum history is
1876. Evidence is in `runs/20261004_math_review_fresh_CAMB_third_old_B4095_diagnostics`.

The sixth guarded CLASS medium-A assessment extends all four earlier prefixes
with histories [1183, 1685, 1712, 1235], meeting its unchanged 1180
trigger. Diagnostics, snapshot verification and distinct self-review pass;
all ten parameter gate sets fail. Mass Rhat is 1.022730,
bulk ESS 96.53, tail/quantile ESS 161.75, and
p95 MCSE 0.00613163 eV against 0.001 eV. Retained/full empirical
p95 are 0.10535783/0.10731856 eV;
half-history drift is 0.01031072 eV. Its next minimum
history is 1420. Evidence is in `runs/20261004_math_review_guarded_CLASS_sixth_medium_A_diagnostics`.
The runtime observation verifies all forty process/native identities. The
latest joint CLASS assessment remains historical; these separate snapshot
times do not qualify a joint posterior or precision comparison.

Six additional UpperGate theorems connect probability-scale cutoff effects
to quantile ordering and conditional coordinate bounds under actual measures.
For a probability law with positive retained mass F(U), a CDF-equation
quantile x of the conditioned law at 0<q<1 lies below U and has F(x)=q F(U).
If y solves F(y)=q, then F(y)-F(x)=q(1-F(U)). With positive omitted mass,
monotonicity of the actual CDF proves x<y, even when the law has atoms.
If a positive constant c has separately been certified to satisfy
c(y-x) <= F(y)-F(x), then 0<y-x <= q(1-F(U))/c. That CDF-growth premise is
explicit and is not supplied by the omitted mass or Gaussian-looking plots.

For the actual positive-width physically gated Gaussian and every real mean,
positive finite caps derive positive retained and omitted masses. Existing
quantile-existence theorems supply realizable witnesses: the finite-cap quantile
is strictly below the uncapped one, and increasing the finite cap strictly
increases every interior-level quantile. These claims are exact measure/CDF
statements; neither cosmological Gaussianity nor inverse-CDF floating accuracy
is inferred.

Formal self-review retains the ten preceding controls and adds eight controls,
including three actual atomic probability laws with normalization derived.
The strongest counterexample has masses 18981/20000 at 0, 19/20000 at L,
49/1000 at 2L and 1/1000 at 3L, for any L>0. Conditioning at 2L retains
999/1000, gives a 0.95 CDF-equation solution at 0, and the underlying law has
a 0.95 solution at L. The omitted tail is exactly 0.001 while the coordinate
displacement can be arbitrarily large. Its exact positive secant coefficient
is 19/(20000 L), which supplies the missing scale information. A zero-tail
atomic plateau gives reversed arbitrary same-CDF-level solution coordinates,
showing why positive omitted mass is required for the generic strict-order
claim. Endpoint q=0/q=1 and nonpositive-cap controls remain in the review.

The first module build passes. Three failed formal-control attempts are
preserved: notation scope, extended-real normalization arithmetic and scalar
simplification errors were repaired in the control file. The final eighteen
controls compile without warnings or admissions. The combined check passes
202 Python tests, the Lean build and all 89 public standard-axiom outputs.
Distinct self-review verifies the nine previous UpperGate declarations are
unchanged, the six exports are added to the axiom audit, and the coordinate
bridge retains every required premise. Evidence is in
`runs/20261004_math_review_upper_gate_quantile_bridge`. No cosmological prior
insensitivity certificate, posterior bound, main-claim revision or paper edit
is adopted. Both material claim discussions remain pending.

The fourth fresh-CAMB current-A3200 assessment meets the unchanged 2003
trigger with exact histories [2011, 2099, 2031, 2020]. All twelve
selected native rows replay exactly; native replay, diagnostics and snapshot
verification exit zero. All seven parameter gate sets fail. Mass Rhat is
1.019627, bulk ESS 202.46, tail ESS
205.84, quantile ESS 205.84, and p95 MCSE
0.01722530 eV against 0.001 eV. Retained/full empirical p95 are
0.13653699/0.13846834 eV; half-history
drift is 0.01034857 eV. Its next minimum history is
2414. Evidence is in `runs/20261004_math_review_fresh_CAMB_fourth_current_A3200_diagnostics`. The preceding process/native-map
observation verifies all forty inference identities. No posterior comparison
or main claim revision follows.

Weighted empirical summaries still had unchecked binary64 mass accumulation:
finite weights [2^1023,2^1023,1.5*2^1023,1.5*2^1023] at values [0,0,1,1]
overflow both two-bin masses and the total. The old histogram selects midpoint
0.25 instead of 0.75, and the boundary fraction becomes NaN instead of 0.4.
Even without overflow, weights [1e308,1e308,1e-300] at [0,1,1] lose a strictly
positive mass that makes the second bin heavier. Zero-weight outliers change
the old histogram range; finite large coordinates can overflow midpoint sums
or endpoint spans. Nine final before controls fail, while four scaling/empty
event controls pass. The original first attempt's eight failures are retained.

The repaired reader validates positive sample support, places bins using the
usual rounded NumPy equal-width edges, and sums binary64 dyadic weights as
exact Python integer masses. It compares bin masses exactly, retains first-bin
tie behavior, and rounds an exact rational bin midpoint. If a finite endpoint
span overflows, exact convex combinations produce finite rounded edges.
Boundary fractions use exact event/total mass and one final binary64 rounding.
An interior event fraction rounding to either zero or one is reported unknown
with a reason; empty and full events still report exact zero and one. This
preserves positive event/complement support rather than declaring it absent.

The initial combined check passes 214 Python tests, Lean build and 89 public
standard-axiom outputs. Self-review found the complementary endpoint issue;
the added final control and guard pass the complete 215-Python-test suite.
Lean sources are unchanged between the checks. Independent Fraction sums
with interval membership check 96 histogram cases and 672 boundary-fraction
cases, including extreme and subnormal coordinates/weights. All nine latest
full diagnostic reports replay identically. Across all thirty-six frozen
production families, median, p95, histogram mode and boundary fraction are
identical to the preserved reader. Distinct self-review confirms every other
reader syntax tree is unchanged. These are empirical histogram midpoints and
weighted event fractions, not continuous-posterior mode or convergence proofs.
Evidence is in `runs/20261004_math_review_weighted_summary_range_repair`.
Raw failed pytest logs retain their original whitespace and nonfinite outputs.

The active source-pinned CAMB workflow is now
`runs/20261004_math_review_fresh_CAMB_weighted_summary_diagnostic_preparation`.
All three earlier contract hashes are accepted only through the checked reader
update and nine-report replay receipt. Other contract fields agree exactly;
nine unsafe transitions are rejected, and all five live growth branches run.
Three branches refuse without output, while current A4095 and B4095 freeze
actual third assessments at their unchanged triggers. No history counter or
diagnostic gate resets.

The third fresh-CAMB current_A4095 assessment has exact histories
[1590, 1604, 1591, 1570]. All twelve selected native rows replay
exactly; native replay, diagnostic and snapshot-verification stages exit zero.
All seven parameter gate sets fail. Mass Rhat is 1.025147,
bulk ESS 146.28, tail ESS 183.59, quantile ESS
183.59 and p95 MCSE 0.00761890 eV against
0.001 eV. Retained/full empirical p95 are
0.13073951/0.13073951 eV; half-history
drift is 0.00178667 eV. The next minimum history is
1884. Evidence is in `runs/20261004_math_review_fresh_CAMB_third_current_A4095_diagnostics`.
No posterior bound, solver/cutoff comparison, main-claim revision or paper edit
is adopted from these failing histories.

The third fresh-CAMB current_B4095 assessment has exact histories
[1585, 1480, 1499, 1507]. All twelve selected native rows replay
exactly; native replay, diagnostic and snapshot-verification stages exit zero.
All seven parameter gate sets fail. Mass Rhat is 1.036885,
bulk ESS 163.81, tail ESS 176.10, quantile ESS
176.10 and p95 MCSE 0.00739071 eV against
0.001 eV. Retained/full empirical p95 are
0.11050255/0.11298400 eV; half-history
drift is 0.01997862 eV. The next minimum history is
1776. Evidence is in `runs/20261004_math_review_fresh_CAMB_third_current_B4095_diagnostics`.
No posterior bound, solver/cutoff comparison, main-claim revision or paper edit
is adopted from these failing histories.

The fourth fresh-CAMB archived-version A3200 assessment reaches its unchanged
1983 trigger with histories [2109, 1987, 2016, 2048]. All twelve
selected native rows replay exactly against the upstream original class with
forced-fresh transfers; native replay, diagnostics and snapshot verification
exit zero. All seven parameter gate sets fail. Mass Rhat is
1.015274, bulk ESS 211.14, tail ESS
333.34, quantile ESS 376.29 and p95 MCSE
0.00750749 eV against 0.001 eV. Retained/full empirical p95 are
0.12884334/0.12869677 eV; half-history
drift is 0.00513102 eV. The next minimum history is
2385. Evidence is in `runs/20261004_math_review_fresh_CAMB_fourth_old_A3200_diagnostics`. A new process/native-map
observation verifies all forty inference identities and zero stderr. All ten
cohorts remain below their next triggers: quadrature A is 4943 versus 4991,
archived B4095 is 1859 versus 1876. These are scheduling observations, and
no posterior or main-claim revision is adopted. Paper and canonical results
remain unchanged.

The fourth fresh-CAMB archived-version B4095 assessment freezes only after
its unchanged 1876 trigger. An initial growth check at 1874 returned the
scheduling-only code 3 and wrote no snapshot; after a verified live wait,
the exact histories are [2000, 1996, 1889, 1973], minimum 1889.
All twelve selected native rows replay exactly against the original upstream
CAMB class with forced-fresh transfers; native, diagnostic and snapshot
verification stages exit zero. Distinct self-review reconstructs every gate.
All seven parameter gate sets fail. Mass Rhat is 1.015937,
bulk ESS 241.49, tail ESS 302.99, quantile ESS
355.56 and p95 MCSE 0.00735733 eV against
0.001 eV. Retained/full empirical p95 are
0.09750879/0.09983947 eV; half-history
drift is 0.00183558 eV. Its next minimum history is
2267. Evidence is in `runs/20261004_math_review_fresh_CAMB_fourth_old_B4095_diagnostics`. The latest process/native-map
observation verifies all forty identities and zero stderr; all ten cohorts
are below their next trigger, with quadrature A at 4974 versus 4991.
Reader source and Lean are unchanged from their 215-Python/89-public-axiom
checks. No posterior bound, main-claim revision or paper edit is adopted.

The seventh guarded-CLASS quadrature A assessment reaches its unchanged
4991 trigger with exact retained histories [4992, 5330, 5037, 5073].
The frozen prefixes preserve all four prior families, model/configuration
hashes and recorded guarded-native identity. Diagnostic execution, snapshot
verification and distinct self-review exit zero. All ten parameter gate sets
fail. Mass Rhat is 1.019415, bulk ESS 262.08, tail/quantile ESS 326.38,
and p95 MCSE is 0.00562808 eV against the 0.001 eV target. Retained/full
empirical p95 are 0.10606878/0.10589076 eV; half-history drift is
0.00880306 eV. Its next minimum history is 5991. Evidence is in
`runs/20261004_math_review_guarded_CLASS_seventh_quad_A_diagnostics`.
An actual runtime observation verifies all forty process identities, mapped
native hashes and zero stderr. The other cohort assessments remain separately
scoped to their own observation times and precision targets. No posterior
bound, numerical stability claim, prior-insensitivity claim or material
main-claim revision is adopted. Reader and Lean sources are unchanged from
their 215-Python-test and 89-public-axiom checks; paper and canonical results
remain unchanged.
A following dynamic observation uses the updated 5991 quadrature-A trigger
and verifies all ten cohorts below their next assessment thresholds. Fresh
current A3200 is closest at 2401 versus 2414; medium B is 952 versus 977.
This scheduling evidence is in
`runs/20261004_math_review_post_CLASS_seventh_A_runtime_observation`.

The fifth fresh-CAMB current A3200 assessment reaches its unchanged 2414
trigger. A first live-growth check at 2405 returned scheduling-only code 3
without creating a snapshot. After a verified 45-second live wait, the
frozen histories are [2441, 2545, 2484, 2414]. All twelve selected
native rows replay exactly against upstream original CAMB with forced-fresh
transfers. Native replay, diagnostics and the distinct exact-data/gate
self-review stages exit zero. All seven parameter gate sets fail. Mass Rhat
is 1.018229, bulk ESS 226.60, tail/quantile ESS 261.28, and p95 MCSE
is 0.01227070 eV against the 0.001 eV target. Retained/full empirical
p95 are 0.12896459/0.13226422 eV; half-history drift is 0.04462415 eV.
The next minimum history is 2897. Evidence is in
`runs/20261004_math_review_fresh_CAMB_fifth_current_A3200_diagnostics`.
The following dynamic observer verifies all forty live identities and zero
stderr, with all ten cohorts below their updated triggers. Current B4095 is
1716 versus 1776, current A4095 is 1796 versus 1884, and medium B is 956
versus 977. These remain scheduling observations. Selected exact native
replay does not establish uniform solver accuracy or posterior convergence.
No target/precision pooling, main-claim revision or qualified posterior
readout is adopted. Paper and canonical results remain unchanged, as do the
reader and Lean sources covered by the 215-test and 89-axiom-output checks.

The fourth fresh-CAMB current B4095 assessment freezes after its unchanged
1776 trigger, with histories [1886, 1782, 1800, 1818]. Four preceding
live-growth checks at 1750, 1757, 1773 and 1773 return scheduling-only code
3 without creating a snapshot. Those closed observations and verified short
waits are recorded in `runs/20261004_math_review_cohort_observation_195729`.
All twelve selected native rows replay exactly against upstream original
CAMB with forced-fresh transfers. Native replay, diagnostics and the distinct
exact-data/gate self-review stages exit zero. All seven parameter gate sets
fail. Mass Rhat is 1.020166, bulk ESS 204.21, tail/quantile ESS 231.31,
and p95 MCSE is 0.00645309 eV against the 0.001 eV target. Retained/full
empirical p95 are 0.11050255/0.10891948 eV; half-history drift is
0.01818516 eV. The next minimum history is 2139. Evidence is in
`runs/20261004_math_review_fresh_CAMB_fourth_current_B4095_diagnostics`.
The following dynamic observation verifies all forty process/native-map
identities and zero stderr; all ten cohorts remain below their updated
assessment triggers. Current A4095 is closest at 1864 versus 1884, while
archived A3200 is 2329 versus 2385. These empirical diagnostics do not
establish a posterior bound, uniform solver accuracy or prior insensitivity.
No target/precision pooling, qualified posterior readout, material main-claim
revision or paper edit is adopted. Reader and Lean sources remain unchanged
from their 215-Python-test and 89-public-axiom-output checks.

The fourth fresh-CAMB current A4095 assessment reaches its unchanged 1884
trigger, with exact histories [1964, 1941, 1979, 1894]. A preceding
live-growth check at 1883 returns scheduling-only code 3 without creating
a snapshot. Both checks and verified 45-second live waits are recorded in
`runs/20261004_math_review_cohort_observation_200910`.
All twelve selected native rows replay exactly against upstream original
CAMB with forced-fresh transfers. Native replay, diagnostics and the distinct
exact-data/gate self-review stages exit zero. All seven parameter gate sets
fail. Mass Rhat is 1.015016, bulk ESS 205.73, tail/quantile ESS 248.30,
and p95 MCSE is 0.00724196 eV against the 0.001 eV target. Retained/full
empirical p95 are 0.13112039/0.13089025 eV; half-history drift is
0.00038089 eV. The next minimum history is 2273. Evidence is in
`runs/20261004_math_review_fresh_CAMB_fourth_current_A4095_diagnostics`.
The following dynamic observation verifies all forty process/native-map
identities and zero stderr. All ten cohorts remain below their updated
assessment triggers; archived A3200 is closest at 2377 versus 2385, and
archived B4095 is 2215 versus 2267. Selected native replay and empirical
diagnostics do not establish a posterior bound, uniform solver accuracy
or prior insensitivity. No target/precision pooling, qualified posterior
readout, material main-claim revision or paper edit is adopted. Reader and
Lean sources remain unchanged from their 215-Python-test and
89-public-axiom-output checks.

The fifth fresh-CAMB archived-solver-version A3200 assessment reaches its
unchanged 2385 trigger with histories [2466, 2404, 2402, 2446], minimum
2402. All twelve selected native rows replay exactly against upstream
original CAMB 1.6.5 with forced-fresh transfers, in the pinned archived
solver/Cobaya package environment. This does not recreate the entire original
historical software stack. Native replay, diagnostics and the distinct exact
history/gate self-review stages exit zero. All seven parameter gate sets
fail. Mass Rhat is 1.012472, bulk ESS 270.55, tail ESS 399.70, quantile
ESS 488.20, and p95 MCSE is 0.00727328 eV against the 0.001 eV target.
Retained/full empirical p95 are 0.13657669/0.13653701 eV; half-history
drift is 0.01293241 eV. The next minimum history is 2883. Evidence is in
`runs/20261004_math_review_fresh_CAMB_fifth_old_A3200_diagnostics`;
the initial live identity/growth observation is in
`runs/20261004_math_review_cohort_observation_201552`.

The seventh guarded-CLASS medium B assessment reaches its unchanged 977
trigger with histories [1360, 1150, 977, 1291]. Frozen prefixes preserve all
four prior families, model/configuration hashes and guarded-native identity.
Diagnostic execution, snapshot verification and distinct self-review exit
zero. All ten parameter gate sets fail. Mass Rhat is 1.044489, bulk ESS
96.91, tail/quantile ESS 158.58, and p95 MCSE is 0.00564875 eV against
0.001 eV. Retained/full empirical p95 are 0.08231626/0.08171978 eV;
half-history drift is 0.00153106 eV. The next minimum history is 1173.
Evidence is in `runs/20261004_math_review_guarded_CLASS_seventh_medium_B_diagnostics`.
Other cohorts retain their own separately verified assessments; no numerical
targets or observation times are pooled into a new joint comparison.

The following dynamic observation uses the updated thresholds and verifies
all forty process/native-map identities and zero stderr. Archived B4095 is
now due at 2273 versus 2267; the other nine cohorts are below their next
triggers. This scheduling evidence is in
`runs/20261004_math_review_post_CLASS_seventh_medium_B_runtime_observation`.
Neither new assessment qualifies a posterior bound, uniform solver accuracy
or prior insensitivity. No material main-claim revision or paper edit is
adopted. Reader and Lean sources remain unchanged from their
215-Python-test and 89-public-axiom-output checks.

The fifth fresh-CAMB archived-solver-version B4095 assessment reaches its
unchanged 2267 trigger with exact histories [2365, 2387, 2296, 2340],
minimum 2296. All twelve selected native rows replay exactly against upstream
original CAMB 1.6.5 with forced-fresh transfers, in the pinned archived
solver/Cobaya package environment. This remains a solver-version control,
not a reconstruction of the entire historical software stack. Native replay,
diagnostics and distinct exact-data/gate self-review stages exit zero.
All seven parameter gate sets fail. Mass Rhat is 1.008862, now passing its
1.01 gate, while bulk ESS 267.99, tail/quantile ESS 389.43 and p95 MCSE
0.00652401 eV still fail their respective 400 and 0.001 eV gates.
Retained/full empirical p95 are 0.09867660/0.10066278 eV; half-history
drift is 0.00118307 eV. The next minimum history is 2756. Evidence is in
`runs/20261004_math_review_fresh_CAMB_fifth_old_B4095_diagnostics`.
The following dynamic observation uses the updated thresholds and verifies
all forty process/native-map identities and zero stderr. All ten cohorts
are below their next assessment triggers; current A3200 is 2726 versus
2897, current B4095 is 1939 versus 2139, and quadrature B is 4740 versus
4943. Passing the mass Rhat gate alone does not qualify a posterior bound,
uniform solver accuracy or prior insensitivity. No target/precision pooling,
qualified posterior readout, material main-claim revision or paper edit is
adopted. Reader and Lean sources remain unchanged from their
215-Python-test and 89-public-axiom-output checks.

A bounded growth watcher makes seventeen actual observations of all forty
inference identities, mapped native hashes, source configuration hashes and
saved integer holding times, at 45-second intervals. The first sixteen
observations are below all ten triggers; the seventeenth observes current
A3200 at 2900 versus 2897. The worker exits zero without restarting,
stopping or changing any sampler. Distinct self-review checks that its
observation statements and returned payload are syntax-tree identical to the
previously verified dynamic observer; only bounded delivery/waiting changes.
Evidence is in `runs/20261004_math_review_wait_for_next_trigger_203033`.
These are live scheduling observations, not posterior or uniform-accuracy
certificates.

The sixth fresh-CAMB current A3200 assessment freezes at histories
[2975, 2990, 3019, 2920], after the unchanged 2897 trigger. All twelve
selected native rows replay exactly against upstream original CAMB 2.0.4
with forced-fresh transfers. Native replay, diagnostics and distinct exact
history/gate self-review stages exit zero. All seven parameter gate sets
fail. Mass Rhat is 1.010335, bulk ESS 267.49, tail/quantile ESS 296.52,
and p95 MCSE is 0.01079382 eV against the 0.001 eV target. Retained/full
empirical p95 are 0.12893843/0.12812009 eV; half-history drift is
0.02120268 eV. The next minimum history is 3504. Evidence is in
`runs/20261004_math_review_fresh_CAMB_sixth_current_A3200_diagnostics`.
The following dynamic observation verifies all forty process/native-map
identities and zero stderr, with all ten cohorts below their updated
triggers. Current B4095 is 2096 versus 2139; quadrature B is 4837 versus
4943. No qualified posterior readout, target/precision pooling, uniform
solver accuracy, prior-insensitivity conclusion, material main-claim revision
or paper edit is adopted. Reader and Lean sources remain unchanged from
their 215-Python-test and 89-public-axiom-output checks.

A second bounded growth wait makes six actual observations of all forty
inference identities, mapped native hashes, configuration hashes and saved
integer holding times, at 45-second intervals. The first five observations
are below all ten triggers; the sixth observes current B4095 at 2140 versus
2139. The worker exits zero without restarting, stopping or changing any
sampler. Distinct self-review checks byte identity to the first watcher,
observation-statement/payload syntax-tree identity to the original dynamic
observer, and all six actual check records. Evidence is in
`runs/20261004_math_review_wait_for_next_trigger_204833`.

The fifth fresh-CAMB current B4095 assessment freezes at exact histories
[2248, 2140, 2151, 2156], after the unchanged 2139 trigger. All twelve
selected native rows replay exactly against upstream original CAMB 2.0.4
with forced-fresh transfers. Native replay, diagnostics and distinct exact
history/gate self-review stages exit zero. All seven parameter gate sets
fail. Mass Rhat is 1.027738, bulk ESS 229.69, tail/quantile ESS 306.59,
and p95 MCSE is 0.00640358 eV against the 0.001 eV target. Both retained
and full empirical p95 are 0.10726534 eV; half-history drift is
0.00193671 eV. The next minimum history is 2568. Evidence is in
`runs/20261004_math_review_fresh_CAMB_fifth_current_B4095_diagnostics`.
The following dynamic observation verifies all forty process/native-map
identities and zero stderr. All ten cohorts remain below their updated
triggers; current A4095 is 2206 versus 2273 and quadrature B is 4866 versus
4943. No qualified posterior readout, target/precision pooling, uniform
solver accuracy, prior-insensitivity conclusion, material main-claim revision
or paper edit is adopted. Reader and Lean sources remain unchanged from
their 215-Python-test and 89-public-axiom-output checks.

A third bounded growth wait makes nine actual observations of all forty
inference identities, mapped native hashes, configuration hashes and saved
integer holding times, at 45-second intervals. The first eight observations
are below all ten triggers; the ninth observes current A4095 at 2280 versus
2273. The worker exits zero without restarting, stopping or changing any
sampler. Distinct self-review checks byte identity to the previously verified
watcher, observation-statement/payload syntax-tree identity to the original
dynamic observer, and all nine actual check records. Evidence is in
`runs/20261004_math_review_wait_for_next_trigger_205850`.

The fifth fresh-CAMB current A4095 assessment freezes at exact histories
[2361, 2316, 2375, 2280], after the unchanged 2273 trigger. All twelve
selected native rows replay exactly against upstream original CAMB 2.0.4
with forced-fresh transfers. Native replay, diagnostics and distinct exact
history/gate self-review stages exit zero. All seven parameter gate sets
fail. Mass Rhat is 1.014249, bulk ESS 239.61, tail/quantile ESS 311.17,
and p95 MCSE is 0.00608014 eV against the 0.001 eV target. Retained/full
empirical p95 are 0.12911049/0.12960156 eV; half-history drift is
0.02174824 eV. The next minimum history is 2736. Evidence is in
`runs/20261004_math_review_fresh_CAMB_fifth_current_A4095_diagnostics`.
The following dynamic observation verifies all forty process/native-map
identities and zero stderr. All ten cohorts remain below their updated
triggers; quadrature B is closest at 4931 versus 4943 and archived A3200
is 2805 versus 2883. No qualified posterior readout, target/precision pooling,
uniform solver accuracy, prior-insensitivity conclusion, material main-claim
revision or paper edit is adopted. Reader and Lean sources remain unchanged
from their 215-Python-test and 89-public-axiom-output checks.

The bounded observer returns on its first actual check, verifying all forty
inference identities, native hashes, configuration hashes and integer holding
times, and finding quadrature B due at 4951 versus 4943. No wait, restart,
stop or sampler change occurs. Distinct self-review checks watcher byte
identity, observation-statement/payload syntax-tree identity to the original
dynamic observer and the actual due-cohort record. Evidence is in
`runs/20261004_math_review_wait_for_next_trigger_211045`.

The eighth guarded-CLASS quadrature B assessment freezes at exact retained
histories [5110, 4968, 5124, 4954], after its unchanged 4943 trigger.
The frozen prefixes preserve all four prior families, model/configuration
hashes and recorded guarded-native identity. Diagnostic execution, snapshot
verification and distinct self-review exit zero. All ten parameter gate sets
fail. Mass Rhat 1.007323 now passes 1.01, and tail/quantile ESS 497.02
passes 400. Bulk ESS 395.75 still fails 400, and p95 MCSE 0.00372734 eV
still fails the 0.001 eV target. Retained/full empirical p95 are
0.08159207/0.08145275 eV; half-history drift is 0.00787554 eV. Its next
minimum history is 5945. Evidence is in
`runs/20261004_math_review_guarded_CLASS_eighth_quad_B_diagnostics`.
Other assessments retain their separate observation times and precision
targets; no new joint comparison or precision pooling is inferred.

The following dynamic observation verifies all forty process/native-map
identities and zero stderr using updated triggers. All ten cohorts are below
their next thresholds; archived A3200 is 2841 versus 2883 and archived
B4095 is 2695 versus 2756. Evidence is in
`runs/20261004_math_review_post_CLASS_eighth_quad_B_runtime_observation`.
Passing some mass gates does not qualify a posterior bound, uniform solver
accuracy or prior insensitivity. No material main-claim revision or paper
edit is adopted. Reader and Lean sources remain unchanged from their
215-Python-test and 89-public-axiom-output checks.

Six model-only upper-prior controls isolate mass caps of 5, 10 and 20 eV
for current A4095 and B4095. Distinct self-review reconstructs each target
from its original sampler configuration and verifies that only the uniform
mass-prior upper endpoint changes; neither a sampler nor an output block is
present. The bounded single-thread preflight evaluates eighteen supported
points and six declared-prior rejections. Each supported point agrees exactly
in every likelihood component with the independent upstream original CAMB
class using forced-fresh transfers. Masses of 6 and 12 eV exercise the added
support. At eight common points, all likelihood components are unchanged and
the logprior/logposterior shift is minus log of the cap ratio. Maximum
absolute arithmetic residuals are 2.22e-16 and 1.10e-13, respectively.
Execution and the separate reconstruction pass exit zero. Evidence is in
`runs/20261004_math_review_upper_prior_control_preparation`.

These are selected native evaluations, not posterior tail or quantile
estimates. With an identical likelihood and other priors, and a proper wide
posterior with positive evidence, the 5 eV posterior is the wide posterior
conditioned on mass at most 5 eV. Those premises remain explicit; this
preflight does not establish them uniformly, supply an omitted-tail bound,
or establish prior insensitivity. Wider-prior posterior controls remain
pending. No additional long sampler was launched while observed CPU load
was about 142 on 128 logical CPUs.

The following dynamic observer verifies all forty original inference
identities, mapped native hashes, configurations and zero stderr. Archived
A3200 and B4095 are now due at minimum histories 3032 and 2954, against
triggers 2883 and 2756. Current A3200 is 3408 versus 3504; the remaining
cohorts are below their triggers. All existing posterior qualifications
remain false. No material main-claim revision or paper edit is adopted.
Core Python and Lean sources remain unchanged from the 215-test and
89-public-axiom-output checks.

The sixth fresh-transfer archived-version A3200 assessment freezes at
exact retained histories [3156, 3117, 3050, 3146], after the unchanged
2883 trigger. All twelve selected native rows replay exactly
against upstream original CAMB 1.6.5 with forced-fresh transfers. Native
replay, diagnostics and distinct exact history/gate self-review stages exit
zero; all seven parameter gate sets fail. Mass Rhat is
1.018604, bulk ESS 268.40, tail/quantile ESS
312.97, and p95 MCSE 0.00893911 eV against the
0.001 eV target. Retained/full empirical p95 are
0.14119551/0.14137931 eV; half-history drift is
0.01922247 eV. The next minimum history is 3660.
Evidence is in `runs/20261004_math_review_fresh_CAMB_sixth_old_A3200_diagnostics`.
This restores the solver version under the current Python/data environment,
not the whole original stack. No posterior bound is qualified or pooled
with other numerical targets or cache policies.

The sixth fresh-transfer archived-version B4095 assessment freezes at
exact retained histories [3015, 3037, 2958, 2972], after the unchanged
2756 trigger. All twelve selected native rows replay exactly
against upstream original CAMB 1.6.5 with forced-fresh transfers. Native
replay, diagnostics and distinct exact history/gate self-review stages exit
zero; all seven parameter gate sets fail. Mass Rhat is
1.013968, bulk ESS 298.74, tail/quantile ESS
506.14, and p95 MCSE 0.00516909 eV against the
0.001 eV target. Retained/full empirical p95 are
0.09704408/0.09704408 eV; half-history drift is
0.00046471 eV. The next minimum history is 3550.
Evidence is in `runs/20261004_math_review_fresh_CAMB_sixth_old_B4095_diagnostics`.
This restores the solver version under the current Python/data environment,
not the whole original stack. No posterior bound is qualified or pooled
with other numerical targets or cache policies.

The following dynamic observation verifies all forty process/native-map
identities and zero stderr using the updated thresholds. All ten cohorts
are below their triggers; current A3200 is closest at 3463 versus 3504.
Evidence is in
`runs/20261004_math_review_post_archived_sixth_runtime_observation`.
No qualified posterior readout, uniform numerical accuracy, prior-insensitivity
conclusion, material main-claim revision or paper edit is adopted. Core
sources remain unchanged from their 215-Python-test and 89-public-axiom-output
checks.

A bounded growth wait makes five actual observations of all forty inference
identities, native hashes, configurations and integer holding times, at
45-second intervals. The first four observations are below all ten triggers;
the fifth observes current A3200 at 3504 versus 3504. The worker exits zero
without changing any sampler. Distinct self-review checks watcher byte
identity, observation-statement/payload syntax-tree identity to the original
dynamic observer, and all five actual check records. Evidence is in
`runs/20261004_math_review_wait_for_next_trigger_214415`.

The seventh fresh-CAMB current A3200 assessment freezes at exact retained
histories [3630, 3606, 3607, 3516], after its unchanged 3504
trigger. All twelve selected native rows replay exactly against upstream
original CAMB 2.0.4 with forced-fresh transfers. Native replay, diagnostics
and distinct exact history/gate self-review stages exit zero; all seven
parameter gate sets fail. Mass Rhat is 1.017604, bulk ESS
255.87, tail/quantile ESS 354.36, and p95 MCSE
0.01039044 eV against the 0.001 eV target. Retained/full empirical
p95 are 0.12704008/0.12993984 eV; half-history
drift is 0.02404128 eV. The next minimum history is
4220. Evidence is in `runs/20261004_math_review_fresh_CAMB_seventh_current_A3200_diagnostics`.
The numerical estimates remain unqualified; no target or precision pooling
is inferred.

The following dynamic observation verifies all forty process/native-map
identities and zero stderr using updated thresholds. All ten cohorts remain
below their triggers; current B4095 is closest at 2534 versus 2568. Evidence
is in
`runs/20261004_math_review_post_current_A3200_seventh_runtime_observation`.
No qualified posterior readout, uniform solver accuracy, prior-insensitivity
conclusion, material main-claim revision or paper edit is adopted. Core
sources remain unchanged from their 215-Python-test and 89-public-axiom-output
checks.

A bounded growth wait makes eight actual observations of the forty primary
inference identities, native hashes, configurations and integer holding
times, at 45-second intervals. The first seven observations are below all
ten triggers; the eighth observes current B4095 at 2574 versus 2568. The
worker exits zero without changing any sampler. Distinct self-review checks
watcher byte identity, observation-statement/payload syntax-tree identity
to the original dynamic observer, and all eight actual check records.
Evidence is in `runs/20261004_math_review_wait_for_next_trigger_215323`.
This observation predates the separate wider-prior sampler activation.

The sixth fresh-CAMB current B4095 assessment freezes at exact retained
histories [2723, 2608, 2574, 2643], after its unchanged 2568
trigger. All twelve selected native rows replay exactly against upstream
original CAMB 2.0.4 with forced-fresh transfers. Native replay, diagnostics
and distinct exact history/gate self-review stages exit zero; all seven
parameter gate sets fail. Mass Rhat is 1.024017, bulk ESS
273.48, tail/quantile ESS 387.51, and p95 MCSE
0.00510065 eV against the 0.001 eV target. Retained/full empirical
p95 are 0.10710344/0.10698977 eV; half-history
drift 0.02245771 eV exceeds four times the precision
scale. The next minimum history is 3089. Evidence is in
`runs/20261004_math_review_fresh_CAMB_sixth_current_B4095_diagnostics`. No posterior bound
is qualified or pooled with other targets, precision settings or priors.

Two current-version A4095 and B4095 wider-prior posterior controls now use
uniform mass priors on [0,20] eV. Four fresh RNG/output runs per target
start from the original reference, a selected frozen point, 6 eV and 12 eV.
Each complete configuration is reconstructed in a distinct self-review:
only the mass-prior upper endpoint changes the posterior target. Other
priors, likelihoods, native settings and MCMC options are preserved;
initial references, seeds, output names and metadata identify the new runs.
The fixed proposal matrices are copied byte-for-byte as heuristics only.
All eight starting points replay exactly to both the prior model-only
preflight and independent upstream CAMB 2.0.4 with forced-fresh transfers.
The eight new samplers use one native thread each and Linux nice level 5;
the original forty jobs are not restarted, stopped or reconfigured.

All eight first complete saved rows replay with zero discrepancy in the
recorded likelihood, prior and posterior components. Both finite first-row
workers exit zero. Separate self-review recounts the frozen rows, native
metadata and configuration provenance, and confirms the workers have exited.
The combined runtime observer preserves the original forty-process check
body and return payload exactly by syntax-tree comparison, and additionally
verifies all eight new PID/start-tick/command/native identities, configurations,
first-row witnesses and scheduling priorities. All forty-eight records are
revalidated in a distinct self-review. Evidence is in
`runs/20261004_math_review_upper_prior_posterior_preparation`.

The separately prepared wider-prior diagnostic contract retains the existing
1000-step first trigger, later factor 6/5, native replay tolerance, source
hashes, burn-in rule and all acceptance gates. Its five helper files are
byte-identical to the established primary workflow. Both premature snapshot
requests return code 3 without creating output directories, and a primary
5 eV snapshot contract is rejected as a wider-prior predecessor. Evidence is
in `runs/20261004_math_review_upper_prior_diagnostic_preparation`.
These checks establish preparation and selected native evaluation, not
posterior convergence, an omitted-tail bound or prior insensitivity. Future
qualified comparisons cover caps 5 and 20 eV under the stated current target;
they cannot establish invariance for every finite cap or infinite support.

At the combined observation, all twelve cohorts are below their assessment
triggers. The wider-prior minima are only 22 and 14 retained steps. Current
A4095 is 2697 versus 2736, and guarded medium A is 1385 versus 1420.
No posterior bound is newly qualified. No material main-claim revision,
uniform numerical accuracy or paper edit is adopted. Core sources remain
unchanged from their 215-Python-test and 89-public-axiom-output checks.

The future bounded growth watcher now covers all forty-eight process
identities and twelve assessment triggers. Its complete observation body
and return payload are syntax-tree identical to the successful combined
runtime observer; its 20-check, 45-second wait loop is syntax-tree identical
to the previously exercised bounded watcher. Preparation only is claimed;
each execution must use a new output root. This extends scheduling and
identity coverage without pooling histories or changing diagnostic gates.
Evidence is in `runs/20261004_math_review_all_cohort_growth_workflow`.

The first expanded bounded watcher returns on its first actual observation,
verifying all forty-eight inference identities and twelve growth records.
Current A4095 is due at 2764 versus 2736; the separate wider-prior controls
remain below their first 1000-step triggers, at minima 84 and 75. The
worker exits zero without waiting or changing any sampler. Distinct
self-review checks watcher byte identity, complete observation/payload
syntax-tree identity to the successful combined observer, and every actual
growth record. Evidence is in
`runs/20261004_math_review_all_cohort_wait_for_next_trigger_221426`.

The sixth fresh-CAMB current A4095 assessment freezes at exact retained
histories [2881, 2773, 2880, 2790], after its unchanged 2736
trigger. All twelve selected native rows replay exactly against upstream
original CAMB 2.0.4 with forced-fresh transfers. Native replay, diagnostics
and distinct exact history/gate self-review stages exit zero; all seven
parameter gate sets fail. Mass Rhat is 1.011814, bulk ESS
269.86, tail/quantile ESS 319.30, and p95 MCSE
0.01037384 eV against the 0.001 eV target. Retained/full empirical
p95 are 0.13426908/0.13390649 eV; half-history
drift is 0.00260195 eV. The next minimum history is
3328. Evidence is in `runs/20261004_math_review_fresh_CAMB_sixth_current_A4095_diagnostics`.
No posterior bound is qualified or pooled with other targets, settings or
priors. The separate latest cohort observations are not a new joint
comparison.

The following combined runtime observation and distinct identity/growth
self-review verify all forty-eight processes, native mappings and hashes,
and eight lower scheduling priorities. All twelve cohorts are below their
updated triggers; guarded medium A is closest at 1393 versus 1420. Wider
prior minima have grown to 114 and 97 steps and remain unassessed. The
receipt is in the sixth current A4095 assessment root. No qualified posterior,
uniform numerical accuracy, prior-insensitivity conclusion, material
main-claim revision or paper edit is adopted. Core sources remain unchanged
from their 215-Python-test and 89-public-axiom-output checks.

A second expanded bounded growth wait completes twenty actual observations
of all forty-eight inference identities and all twelve scheduling triggers,
with 45-second sleeps between checks. Every check remains below every
assessment trigger. The worker returns the documented scheduling code 3
at its observation limit; this is neither a native verification failure
nor a stopped sampler. Distinct self-review checks watcher byte identity,
complete observation/payload syntax-tree identity to the successful combined
observer, all twenty trigger records, and all final PID/start-tick/command/
native-map identities and eight lower scheduling priorities. Evidence is in
`runs/20261004_math_review_all_cohort_wait_for_next_trigger_222037`.

At the final observation, guarded medium A is 1411 versus 1420, archived
A3200 is 3542 versus 3660, and quadrature A is 5790 versus 5991. Wider-prior
minima are 214 and 212 versus 1000. Separate current progress lines also
confirm that all four medium-A processes continue stepping while the shortest
complete saved prefix remains below its trigger. No diagnostic snapshot is
created, no gate is weakened and no sampler is restarted, stopped or
reconfigured. No qualified posterior readout, uniform solver accuracy,
prior-insensitivity conclusion, material main-claim revision or paper edit
is adopted. Core sources remain unchanged from their 215-Python-test and
89-public-axiom-output checks.

The next expanded watcher returns on its first observation, verifying all
forty-eight identities and all twelve growth records and finding guarded
medium A due at 1421 versus 1420. The wider-prior controls remain below
their first trigger, at minima 251 and 229. Distinct self-review checks
source byte and observation/payload syntax-tree identity, and every actual
trigger record. Evidence is in
`runs/20261004_math_review_all_cohort_wait_for_next_trigger_223855`.

The seventh guarded-CLASS medium A assessment freezes exact retained
histories [1421, 2001, 2058, 1468], after the unchanged 1420 trigger.
The four original families and every prior frozen prefix are preserved,
with identical model/configuration and guarded-native identities. Diagnostic
execution, snapshot verification and distinct exact holding-time/gate
self-review exit zero. All ten parameter gate sets fail. Mass Rhat is
1.019936, bulk ESS 139.33, tail ESS
268.28, quantile ESS 270.42, and p95 MCSE
0.00646789 eV against the 0.001 eV target. Retained/full empirical
p95 are 0.10408924/0.10515632 eV; half-history
drift is 0.01000990 eV. The next minimum history is
1706. Evidence is in `runs/20261004_math_review_guarded_CLASS_seventh_medium_A_diagnostics`.
Other cohort assessments retain their separate observation times; the
historical joint-assessment pointer is unchanged. No new joint comparison
or precision pooling is inferred.

The original forty-process runtime observer initially exits one because
its retired-process check requires each old PID number to be absent.
PID 660424, formerly sampler seed 303 with start tick 328869762, is now
used by an unrelated Lean process with start tick 342315083; two adjacent
retired PID numbers are also reused by unrelated Lean identities. The
counterexample is observed directly and does not show an old sampler
returning. The failed observer and receipt are preserved. No unrelated
process is signaled, stopped or modified.

The corrected retirement check pins the original identity receipt by hash
and compares each retired PID with its recorded process-start tick. The
original live identity is still refused; a different start time is recorded
as PID reuse. Missing stat records imply absence, while unreadable records
propagate an error; even a matching zombie remains an original identity.
Nine controls pass, including an actual matching live process, a distinct
start at the same live PID, absent and reused fixtures, a name containing
parentheses, and input/error refusals. Historical receipts lacking start
ticks obtain them from the pinned earlier identity witness. The forty
primary live-process checks remain unchanged, and the corrected observer
exits zero, allowing the unchanged CLASS self-review to complete.
Evidence is in `runs/20261004_math_review_retired_PID_identity_repair`.

Continuation on 2026 10 04 preserves two actual wider-prior native failures.
Seed 2003, initially at 6 eV, has managed exit one after its last logged
431 steps and 217 accepted points. Seed 2004, initially at 12 eV, subsequently
has managed exit one after its last logged 622 steps and 225 accepted points.
Both report `ValueError: provider spectrum tt must be finite and 1D.`
The exception does not itself distinguish nonfinite values from an invalid
array dimension. Their original process identities are absent and their
failed bundles are frozen with seventeen files each. The saved chains contain
217 and 225 rows, representing 349 and 534 retained steps after the established
row burn-in. Each initial saved native witness remains a prefix. Neither
checkpoint contains the failing proposal or RNG state: its sampler fields are
only convergence, last R minus one, burn-in, and MPI size. Exact checkpoint
resume is therefore unsupported by the saved state. Failure archives and
distinct self-reviews are in
`runs/20261004_math_review_upper_prior_seed2003_native_failure_v2` and
`runs/20261004_math_review_upper_prior_seed2004_native_failure`.

The first archive attempt is preserved after its check mistakenly expected
two trailing newlines in stderr instead of the actual one. No source output
was altered. The identity-aware forty-eight-process observer first stops
on the actual absent seed 2003; its corrected status-aware successor later
stops on the newly absent seed 2004. Those failed attempts have separate
receipts. They are distinct from the earlier PID-reuse defect. The retirement
repair completes its own reverse-byte source review, sixteen original identity
witness checks and nine controls; the remaining live checks are unchanged.

The final status-aware observer and distinct self-review account for all
forty-eight registered inference families: forty primary and six wider-prior
samplers remain live, while seeds 2003 and 2004 are explicitly terminal.
The complete primary observer has an identical AST; the wider-prior live
loop is identical after removing the added terminal branch. Each terminal
branch verifies the pinned failed bundle, original identity absence and
failure self-review. Neither failed family is discarded or counted as live.
The wider-prior A minimum remains 349 represented retained steps across all
four families, with assessment eligibility false while recovery is unresolved.
Wider-prior B has all four live families and a minimum of 417 against its
unchanged first trigger of 1000. No numerical failure becomes a prior or
posterior rejection, and no convergence or prior-stability qualification
is inferred. Evidence is in
`runs/20261004_math_review_status_aware_runtime_preparation_v3`.
The former PID-only/all-eight-live watcher is marked superseded for execution.

Six selected successful rows, the first, middle and last from each failed
family, replay with zero error in every recorded posterior, prior and
likelihood component against original upstream CAMB with fresh transfers.
This is a selected-point accounting control and does not certify the failed
transition or uniform solver support. Two isolated diagnostic replays now
attempt the original seeded trajectories. Their actual resolved configurations
are equal to the originals after removing only the output path; sampler,
seed, prior, numerical settings and native/source identities are preserved.
They run with one thread and scheduling nice ten, separately from the
forty-six live inference samplers. A recording wrapper returns each successful
original evaluation unchanged and, after an exception, records the sampled
proposal and spectrum dimensions/nonfinite indices before rethrowing the
original exception. Controls verify exact argument forwarding, successful
result identity and exception identity. Distinct activation self-review verifies
the live process identities and the wrapper's successful path and final bare
raise. Exact trajectory-prefix reproduction remains to be checked; neither
replay is a qualified posterior family and neither is pooled with inference
samples. Evidence is in
`runs/20261004_math_review_upper_prior_native_failure_reproduction_preparation`.
Core mathematical code, Lean, paper and canonical results are unchanged in
this continuation.

The first isolated reproduction observation freezes twenty complete stored
rows for seed 2003 and eighteen for seed 2004. Both frozen files are exact
byte prefixes of their respective failed original chains; every saved binary64
value, including holding weights and all target components, is equal. The
same recorded process identities remain live before and after each snapshot.
This verifies early saved trajectory reproduction, while the complete failing
transition and its cause remain pending. The immutable witnesses and receipt
are under `early_prefixes` and `early_prefix_verification.json` in the diagnostic
reproduction preparation root. The next available primary assessments are
archived-version A and B and current A at cutoff 3200; their individual
scheduling triggers were met in the forty-eight-family runtime observation.

Continuation on 2026 10 04 completes three separate primary CAMB assessments.
Archived-version A and B receive their seventh assessments, while current
version A at cutoff 3200 receives its eighth. The saved histories are
[3950, 4000, 3978, 4055], [3798, 3812, 3720, 3786], and
[4488, 4433, 4533, 4361], respectively. All four families and earlier
frozen prefixes are retained, with unchanged targets, priors and gates.
Each target has twelve selected first, middle and last saved rows replayed
against its pinned upstream solver with fresh transfers; every recorded
posterior, prior and likelihood component has zero error.

The first outer wrappers exit one after those native checks because their
redirection used the filenames reserved for exclusive diagnostic output.
The failed roots are preserved. Fresh recovery roots reuse the identical
frozen chain bytes and native receipts, rebase only the snapshot output
paths, and execute the remaining diagnostic and verification stages with
separate outer log names. Both remaining stages exit zero in all three
roots. Additional distinct self-review reverses the worker change, verifies
the original native stage exit zero, checks every reused native point against
its frozen row, and verifies that output rebasing changes no target provenance.
No closed writer is rerun and no validated native computation is repeated
on the identical rows. Evidence is in the `diagnostics_v2` roots for
`fresh_CAMB_seventh_old_A3200`, `fresh_CAMB_seventh_old_B4095`, and
`fresh_CAMB_eighth_current_A3200`; their corresponding roots without `_v2`
preserve the failed attempts.

Archived A mass Rhat is 1.011665, bulk ESS 328.33, tail and quantile
ESS 400.95, and quantile MCSE 0.00706397 eV. Retained/full p95 are
0.14524481/0.14519426 eV, with half-history drift 0.01561166 eV.
Archived B mass Rhat is 1.017306, bulk ESS 372.85, tail and quantile
ESS 649.95, and MCSE 0.00494814 eV. Retained/full p95 both equal
0.10112756 eV, with drift 0.00529306 eV. Every parameter gate set
fails in both archived cohorts. Their next minimum histories are 4740
and 4464. These retain the established scope of the archived solver-version
control on current Python and data, rather than restoration of the entire
original software stack.

Current A at cutoff 3200 has mass Rhat 1.009496, bulk ESS 356.52,
tail and quantile ESS 446.97, and MCSE 0.00533956 eV. Its mass Rhat
and tail gates pass, while bulk ESS and the 0.001 eV MCSE target fail.
Retained/full p95 are 0.12360310/0.12393798 eV, with drift 0.00903709 eV.
Only `omegach2` passes its complete parameter gate set; the six other
parameter sets fail, so the posterior remains unqualified. Its next minimum
history is 5234. None of these separately timed assessments is pooled or
turned into a qualified headline comparison.

A selected nearby-point scout tests twelve strict prior-interior points
using the same current CAMB target with fresh transfers. The two last
successful saved A rows serve as baselines; changes to cold dark matter
density at 0.0011, 0.002 and 0.005, and mass at 16 and 19 eV, give ten
additional controls. All twelve evaluations are finite. Distinct self-review
checks their declared prior bounds, normalized uniform prior density and
posterior component accounting. This selected evidence does not identify
the original failing proposal, establish a failure mechanism, or certify
uniform solver support. Evidence is in
`runs/20261004_math_review_upper_prior_native_failure_neighbourhood_scout`.

The subsequent runtime check verifies all forty primary samplers and then
finds absent wider-prior B seed 2007. Direct managed-session checks establish
that both high-mass B starts, seeds 2007 and 2008, exited one with the same
TT spectrum validation exception. Their last logged progress is 798 steps
and 320 accepted points for seed 2007, and 742 steps and 301 accepted points
for seed 2008. Their preserved chains contain 320 and 301 rows, with 624
and 612 retained represented steps. Each seventeen-file terminal bundle
preserves its first saved native witness. Neither checkpoint contains RNG
state or the failing proposal. The failed runtime attempt is preserved
separately from the completed primary assessment. Terminal archives and
witness reviews are in
`runs/20261004_math_review_upper_prior_B_terminal_failure_preservation`.

The updated status-aware observer and distinct self-review account for all
forty-eight registered inference families: forty primary and four wider-prior
samplers remain live; seeds 2003, 2004, 2007 and 2008 are explicitly terminal.
The primary observer and remaining wider-prior live checks have identical
ASTs to their reviewed predecessors. Both wider-prior cohorts retain all
four families, their minima remain 349 and 612, and both assessment
eligibility flags are false pending recovery. No error is interpreted as
prior or posterior rejection. Evidence is in
`runs/20261004_math_review_status_aware_runtime_preparation_v4`.

The two isolated A diagnostic replays remain live with zero stderr. New
immutable observations freeze 128 and 123 stored rows, respectively. Both
are exact byte prefixes of their original failed trajectories, and every
recorded binary64 value is equal. These later prefix witnesses preserve
the original seeds and targets and remain separate from inference samples.
The complete failing transition is still pending. They are stored under
`later_prefixes` in the latest status-aware runtime preparation root.
Core mathematical code, Lean, paper and canonical results remain unchanged.


The October 5 continuation closes three more separately timed assessments.
Current CAMB A and B at cutoff 4095 receive seventh assessments; guarded
CLASS quadrature A receives its eighth. Their minimum retained histories
are 3428, 3297 and 6127, with next growth triggers 4114, 3957 and 7353.
Both CAMB cohorts again verify twelve selected first, middle and last rows
against upstream fresh calculations with zero error in every recorded
posterior, prior and likelihood component. All three CAMB verification
stages exit zero for each cohort. CLASS diagnostics, the corrected
forty-process identity observation, snapshot verification and distinct
self-review also exit zero.

| Cohort | Mass Rhat | Bulk ESS | Tail and quantile ESS | Quantile MCSE eV | Retained p95 eV |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current CAMB A 4095 | 1.011744 | 325.53 | 416.71 | 0.00988270 | 0.13425808 |
| Current CAMB B 4095 | 1.016580 | 357.36 | 343.59 | 0.00575576 | 0.11050255 |
| Guarded CLASS quadrature A | 1.009978 | 340.56 | 437.85 | 0.00519591 | 0.10817197 |

Both CAMB cohorts fail every complete parameter gate set. CLASS quadrature
A passes only the complete `TT_kSZ_Amp` set; its mass Rhat and tail gates
pass, but bulk ESS and the 0.001 eV quantile MCSE target fail. None is a
qualified posterior. Targets, precision cohorts and observation times remain
separate. Evidence is in the seventh current A4095/B4095 and eighth guarded
CLASS quadrature A diagnostic roots.

Both isolated seeded A failure replays are now terminal exit one. The
second captured proposal arrives on October 5 at 00:08:49 UTC. New frozen
bundles verify every byte and binary64 value in the original saved chains:
217 original rows are an exact prefix of 220 replay rows for seed 2003;
225 original rows are an exact prefix of 227 replay rows for seed 2004.
The original unflushed internal tails and original failing proposals are
unavailable. These facts establish saved-prefix preservation and repeated
failure with the same seeds, rather than equality of the entire internal
trajectories. The first attempted full-file-equality check is preserved as
a failed verification; its corrected review states this narrower, exact
scope explicitly. The archive name containing `exact_failure_reproduction`
does not strengthen that scope.

The captured replay masses are 11.43687824 and 17.67540798 eV; every sampled
coordinate lies strictly inside its declared prior. Each provider spectrum
is correctly one-dimensional with 4101 entries, but TT, EE, BB, TE and ET
contain 4099 NaNs at multipoles 2 through 4100. Thus these captured validation
failures arise from nonfinite values. Fresh isolated models reproduce both
failures with unchanged production numerical settings: native unlensed
scalar spectra are finite, whereas lens-potential and lensed scalar spectra
are NaN above multipole one. No MCMC history is required for either captured
point to fail. The original runs did not record their failed arrays or
proposals, so their precise unlogged transitions remain outside this claim.

Selected native ablations copy the effective native parameters and change
exactly one displayed model field. Both original Mead 2020 and Mead 2016
return NaN lensing spectra at both points; linear lensing and Takahashi
return finite spectra. Direct native original-model calculations reproduce
the original isolated arrays exactly, including NaN positions. Distinct
self-review reconstructs all eight controls and verifies the exact parameter
changes. This locates a failure in the HMcode nonlinear-lensing path at these
two points; finite alternative-model controls do not repair or qualify the
production target, and no alternative is adopted as a fallback.

The matching official [CAMB 2.0.4 source release](https://pypi.org/project/camb/2.0.4/)
is acquired with its publisher SHA256 verified; all 31 distributed Python
sources match the installed package. A compiler and runtime are extracted
only into external scratch space. A debug build of unchanged official
Fortran source reproduces the NaN pattern, while its finite unlensed values
differ slightly from the wheel; numerical target equality is not claimed.
Two initially failed build attempts are retained before the successful
link with the missing compiler support path and runtime supplied.

A separate instrumented source copy changes only a local declaration and
a guard before the halo-model fractional power. At the two captured points
it intentionally stops with a negative one-halo component, a positive
two-halo component, and exponent exactly one half. For seed 2003 the witness
is at redshift 0.71590931 and wavenumber 1.28893344e-5 h/Mpc, with one-halo
power -7.64512904e-81. For seed 2004 it is at redshift 6.60749776 and
wavenumber 1.53989295e-5 h/Mpc, with one-halo power -6.42492942e-237.
A negative real base raised to one half explains a NaN in this operation.

Each witness dumps all 256 mass, sigma, peak-height and quadrature-weight
nodes. Masses increase, but peak heights are nonmonotone; respectively 43
and 7 quadrature weights are negative. Distinct self-review reproduces every
weight exactly in binary64 from the official Sheth–Tormen expression and
the recorded peak-height differences, and confirms a negative total weight
using exact rational summation of the recorded floats. All other Fortran
sources retain their publisher bytes, and the instrumentation change is
reversed exactly in review. These are concrete signed-quadrature failure
witnesses, not a justified repair. The next obligation is to compare direct
sigma integration with its interpolation at the offending nodes, establish
why the table loses monotonicity, and repair the numerical approximation
without silently changing the nonlinear model or prior support.

Evidence is in `runs/20261005_math_review_native_failure_checkpoint`, the
two October 5 frozen replay archives, `runs/20261004_math_review_CAMB204_source_failure_triage`,
and `runs/20261005_math_review_CAMB204_native_debug_preparation`. The refreshed
status-aware observation and distinct self-review still account for all 48
inference families: 44 live and four explicit preserved failures. Both
wider-prior cohorts remain ineligible for qualification. Both diagnostic
reproduction workers are terminal and excluded from inference samples.
Core mathematical code, Lean, paper and canonical results remain unchanged;
the two material claim discussions remain open.


The next October 5 continuation identifies the upstream sigma-integration
failure at both captured points. New isolated source copies probe all 256
halo nodes and all 64 sigma-table points in each case. Direct sigma values
are compared with the cubic table lookup and with integrations that defer
convergence checks until refinement levels 12 and 14 at a declared relative
stopping tolerance of 1e-6. Distinct self-review reverses every source change
and confirms that the cloned audit integrator has the original numerical
statements, with only the minimum refinement and observational output added.
The first probe build fails because its cloned function result declaration
retains the old name; the failed source and build receipt are preserved
before the corrected copy is compiled.

The original table at seed 2003 has a sigma value 0.00321896 at radius
0.000774264 Mpc/h, whereas the level-14 reference gives 0.08875836 at the
same failure redshift. Seed 2004 has an anomalous value 0.02531885 at radius
0.01668101 Mpc/h, versus reference 0.04451296. Repeating the original
integral reproduces the stored table values to roundoff. Both anomalies
satisfy the original stopping rule at level five, a grid of 17 points.
The preceding relative estimate changes are below the declared 1e-4
stopping tolerance, yet one further refinement changes the integral
estimates by factors approximately 2774 and 3.88. Thus adjacent coarse-grid
agreement has missed substantial integrand structure. Cubic interpolation
of the resulting table dip generates the large local oscillations and
overshoots seen in the earlier peak-height and signed-weight witnesses.

Across the 256 original node lookups, sigma increases with radius 47 times
for seed 2003 and 10 times for seed 2004. Original direct node integration
has 66 and 3 increases, respectively. Both refined node sequences are
strictly decreasing at all 256 observed radii. Maximum relative differences
between original lookup and original direct integration are 0.95990 and
0.42906. The level-12/14 node comparisons differ by at most 3.17e-6 and
2.10e-5. Those are empirical comparisons, not rigorous error bounds; in
particular, agreement is not everywhere within the nominal 1e-6 stopping
threshold. No uniform numerical-accuracy certificate is inferred.

Two isolated candidate policies change only sigma integration's stopping
tolerance to 1e-6 and defer its convergence check to levels 12 and 14.
The existing integrand, transfer settings, nonlinear model, prior and
likelihood remain the same. Other uses of the integrator retain their
original minimum level. Neither candidate clamps negative halo power,
substitutes a different nonlinear model or assigns zero posterior to a
numerical error. Both candidates return finite provider and native spectra
and finite posterior components at the two previously failing captured
points. Their maximum log-posterior difference there is 2.546e-8.

Six additional low-mass controls use the first, middle and last already
verified saved points from current A seed 1801 and current B seed 1805.
All are evaluated under one common wider-prior A4095 configuration for the
numerical comparison, rather than treated as an original A/B posterior
comparison. All eighteen evaluations across original debug source and both
candidates are finite. Priors and the BAO component are identical in each
comparison. The maximum absolute log-posterior change from original debug
source to the level-12 candidate is 1.0347e-4; the largest level-12/14
change is 3.7518e-6. Distinct self-review verifies source reversibility,
point selection, component accounting and every saved array hash. These
selected controls support the sigma-only repair direction; both candidates
remain separate from production inference and neither establishes full
prior support or a uniform integral error bound. The next implementation
step is to package the reviewed source patch as a reproducible, explicitly
identified native policy and broaden its controls before fresh inference.
Old numerical-policy histories must remain separate.

The guarded CLASS quadrature B cohort also reaches its next growth gate
and receives a ninth assessment. Its retained histories are
[6025, 6010, 6175, 6010], and its next minimum history is 7212.
All four diagnostic, corrected process-identity observation, snapshot
verification and distinct self-review stages exit zero. Mass Rhat is
1.005255, bulk ESS 514.41 and tail/quantile ESS 557.20; these gates pass.
Quantile MCSE is 0.00397342 eV, above its 0.001 eV target, and every
complete parameter gate set fails. The posterior remains unqualified.

Evidence is in the October 5 `CAMB204_sigma_probe_preparation` roots,
`sigma_table_probe_preparation_v3`, `CAMB204_sigma_integration_candidate12`
and `candidate14`, `sigma_candidate_low_mass_controls`, and
`guarded_CLASS_ninth_quad_B_diagnostics`. Core mathematical code, Lean,
paper and canonical results remain unchanged. The pending headline
magnitude and full-CMB localization discussions are unchanged.


Three other CAMB targets subsequently reach their growth gates: archived
A3200 and B4095 receive eighth assessments, and current A3200 receives its
ninth. An initial launch mistakenly copies a recovery wrapper containing
only diagnostics and snapshot verification. The diagnostic guard refuses
all three because native verification has not been performed. No diagnostics
are written; those snapshots and failure receipts are preserved. Fresh
`_v2` roots freeze later complete prefixes from the same previously validated
predecessors and execute all three stages with the full wrapper. All three
stages exit zero, and each cohort again verifies twelve selected native rows
with zero component error. The snapshot verifier itself writes the completed
self-review receipt; an attempted lookup of a nonexistent separate review
script executes no code and is recorded separately.

| Cohort | Retained minimum | Mass Rhat | Bulk ESS | Tail and quantile ESS | Quantile MCSE eV | Retained p95 eV | Next minimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Archived CAMB A3200 | 4836 | 1.013575 | 380.47 | 569.96 | 0.00644077 | 0.14628207 | 5804 |
| Archived CAMB B4095 | 4629 | 1.015087 | 509.30 | 796.25 | 0.00476040 | 0.09837927 | 5555 |
| Current CAMB A3200 | 5394 | 1.009372 | 499.28 | 622.71 | 0.00429426 | 0.12393798 | 6473 |

Archived A fails every complete parameter gate set. Archived B passes only
`omegabh2`; current A3200 passes only `omegach2`. Current A3200 mass Rhat,
bulk and tail gates pass, but its quantile MCSE remains above target.
No posterior is qualified and no differently timed or differently defined
targets are pooled. The completed assessments are in the October 5 eighth
archived A3200/B4095 and ninth current A3200 `_v2` roots; their counterparts
without `_v2` preserve the failed launches.

The final checkpoint scope audit initially used the upper middle row for
even-length histories, rather than the lower middle row selected by the
native verifier. A corrected distinct self-review uses the contract and
verifier selection, binds all 36 selected points to their frozen rows at
binary64 precision, and checks every component error is zero. All twelve
failed-launch prefixes are preserved within the later successful snapshots.
The failed audit is recorded without changing original receipts. A generic
intentional-guard field in the candidate12 execution receipt is inapplicable:
both candidate12 evaluations actually exited zero. The first probe build
failed with exit two before point evaluation. Completed worker statuses and
these qualifications are recorded in the sigma-policy checkpoint.

The next continuation seals the previous evidence in commit `b180f5d` and
packages the level-14 sigma policy as
`native_policies/camb204_sigma_refinement_v1.json`, with opt-in builder
`scripts/build_camb_sigma_policy.py`. The builder requires the SHA-pinned
CAMB 2.0.4 source distribution and a new private destination. It applies
the six reviewed source replacements, checks the complete original and
patched halofit hashes, and records every source member, build command,
compiler identity and resulting native library hash. It builds through the
upstream makefile with declared O0 bounds-checking flags and leaves the
installed production solver untouched. Prepare-only mode needs no compiler;
normal mode requires gfortran, make and the release's build prerequisites.
A compiler directory can be supplied for a private toolchain. Existing
destinations, including dangling links, are refused. Seven meaningful
provenance and refusal tests pass; the full Python suite now has 222 passes.
Lean sources remain unchanged from the previously verified build.

A fresh archive build exits zero. Distinct self-review verifies all 113
file members, with only halofit changed, and reverses the patch exactly.
At both captured failures and all six earlier low-mass controls, every
provider/native array and every posterior component is exactly identical
to the earlier private level-14 candidate. These are selected empirical
readouts, not a uniform solver or posterior certificate.

Broader controls expose another limitation before any production adoption.
A declared twelve-point grid sets mass to 0.05, 1, 4.9, 5.1, 10 and 19 eV
on each of the two captured-failure backgrounds, under one common
wider-prior A4095 evaluation configuration. Both candidate12 and the fresh
packaged14 worker fail at the first point, mass 0.05 eV on the seed2003
background, with `HMCode INTEGRATE, Integration timed out`. The other eleven
points are not reached. The exact point, scripts and both terminal exit-one
logs are preserved; no failed native evaluation is assigned a posterior
value or counted as an MCMC rejection.

A separate observational source copy reproduces the same error and records
three sigma-table integrals at redshift zero and radii approximately
0.000100000, 0.000129155 and 0.000464159 Mpc/h. Each reaches the existing
level-20 maximum, a grid of 524289 points. The latest adjacent integral
changes are 3.04020e-6, 1.25083e-6 and 1.66814e-6, respectively, exceeding
the promoted nominal 1e-6 stopping tolerance. The unchanged native
GlobalError is propagated. Thus the error is a refinement-limit event,
not a wall-clock timeout. Distinct self-review reverses the observation
patch exactly and verifies the captured point is strictly inside all
declared priors. The next repair experiment must extend sigma refinement
separately and recheck this witness, followed by broader controls. The
packaged policy remains unadopted in production.

Current CAMB A4095 and B4095 reach their next growth gates and complete
eighth assessments, including native replay, diagnostics and snapshot
verification. Each checks twelve selected native rows with zero component
error. A has minimum retained history 4181, mass Rhat 1.011466, bulk ESS
377.54, tail/quantile ESS 479.62, quantile MCSE 0.0105899 eV and retained
p95 0.13647321 eV; its next minimum is 5018. B has minimum 4011, Rhat
1.014999, bulk ESS 428.71, tail/quantile ESS 416.91, MCSE 0.00505648 eV
and retained p95 0.10735935 eV; its next minimum is 4814. Every complete
parameter gate set fails in both cohorts. The latest runtime observation
again accounts for 48 families: 44 live and four explicitly terminal.
No posterior is qualified and no numerical policies or targets are pooled.
The paper and canonical results remain untouched, and both material claim
discussions remain open.

The next continuation extends only sigma's maximum refinement from 20 to
22, with a separate level-24 reference. Other HMcode integrator calls keep
maximum 20 and minimum 5; sigma keeps minimum 14 and nominal tolerance
1e-6. Both source transformations reverse byte-for-byte to the reviewed
level-14 candidate. All twenty declared controls are evaluated using fresh
models, preserving each result or native error in its own immutable record.
The set includes the complete twelve-point mass grid, both original NaN
proposals and six ordinary low-mass controls, under one common wider-prior
A4095 configuration. Both audit builds return finite spectra and posterior
components at every selected point. Their arrays and components are
exactly identical. A separate observational clone records ninety successful
integrations at the three previously failing radii: all accept at level
21, with 1048577 points. The first three previous estimates are binary64
identical to the original timeout's final level-20 estimates.

The reproducible builder now accepts explicitly selected policy v2 and an
optimized profile with O3, unsafe math optimization disabled and contraction
disabled. Default policy v1 and audit profile retain their previous
selection. Source preparation binds the selected policy, and building
refuses changed policy bytes or changed prepared source members. Eleven
policy/provenance tests and all 226 Python tests pass. A fresh optimized
archive build changes only halofit among the 113 release file members.
All twenty optimized controls are finite, giving sixty selected evaluations
across the three builds. Maximum optimized-versus-audit absolute log
posterior difference is 5.24742e-8; the largest array difference normalized
by reference infinity norm is 5.08507e-11. Priors and the BAO component
remain binary64 identical. The declared selected-comparison limits are
1e-5 for log posterior and 1e-8 for normalized arrays. These are empirical
comparisons, not integral or posterior error bounds. The initial review
incorrectly assumes a warning count from incomplete progress logs; its
failed assertion is preserved and the corrected review reports final counts.

Each of these completed twenty-point workers emits 521 native warnings
about mismatched integrated transfer times. An isolated observational
probe at the 4.9 eV control on the second background identifies 260
wave-number modes with actual final time 16156.756399699818 Mpc and
requested time 16156.756481187496 Mpc. The difference is -8.14877e-5 Mpc,
or 5.04357e-9 relative to the requested coordinate. The observational
source leaves the arrays and posterior exactly unchanged. Source review
identifies the cause: background tau0 comes from one whole-interval time
quadrature, whereas the transfer time array sums separately approximated
intervals. Exact integrals agree by additivity, but these numerical
coordinates differ. Small relative mismatch alone is not a certificate
of harmlessness for the likelihood.

Two private endpoint-only candidates are rejected before CMB evaluation.
The first can override explicitly requested integration tolerances. The
second guards those tolerances, but setting only the last endpoint to
tau0 breaks ordering on ten of fifteen valid sorted redshift grids with
a preceding request at 1e-12. The failed ordering witness and source
versions are retained. An initial probe uses the Python ordering flag
incorrectly and receives native ERROR STOP; this is preserved before
the corrected ordering-contract control.

The third candidate instead normalizes the complete default-tolerance
past-time array when its final redshift is zero: tau0 times partial
cumulative time divided by accumulated present-day time. For finite
positive total and tau0 and ordered nonnegative partials, this map
preserves order and sets the endpoint exactly, including in floating
arithmetic on the bounded ratio interval. It introduces no clipping.
Explicit tolerance requests and arrays without zero keep their original
calculations. All fifteen near-zero grids preserve order and have exactly
the tau0 endpoint. Forty-five explicit-tolerance and fifteen nonzero-array
records match the original optimized build bit-for-bit; empty arrays are
also preserved. Three selected CMB evaluations cover the two warning
cases at 4.9 and 5.1 eV and the original 0.05 eV sigma timeout witness.
All are finite, with no remaining integrated-time warnings, unchanged
priors and BAO, maximum log-posterior change 3.97995e-9 and maximum
normalized spectrum change 4.50985e-12. Distinct self-review reverses the
source correction and verifies all these controls. Full twenty-point
validation and reproducible packaging of this additional time correction
remain pending. No candidate is adopted into production and no global
physical-accuracy, prior-support or posterior certificate is inferred.
The paper, canonical results and Lean remain unchanged.

The closing runtime observation accounts for all 48 inference families:
44 remain live, and the same four wider-prior failures remain explicitly
terminal. Guarded CLASS medium B reaches its growth gate and completes
an eighth frozen assessment with represented histories [1747, 1553,
1213, 1672]. Its mass Rhat is 1.024822, bulk ESS 117.00, tail/quantile
ESS 113.34 and quantile MCSE 0.00658921 eV. All ten complete parameter
gate sets fail; the next minimum history is 1456. Snapshot verification,
corrected process-identity observation and distinct self-review all exit
zero. No posterior qualifies, and targets or numerical policies are not
pooled. This continuation changes only the opt-in native builder and its
tests among established Python code; the mathematical modules and Lean
remain unchanged. Both material claim discussions remain open.


### 2026-10-05 continuation: combined native policy and complete selected validation

The previous continuation is sealed at fb42833 with 288 explicitly staged
paths and 287 content hashes. Its ten roots contain only completed diagnostic
or verification artifacts. Raw Fortran whitespace and the verbatim whitespace
check transcript remain byte-preserved with exact-path hash-bound exclusions.
Active inference outputs remain excluded; the production native module,
mathematical modules, Lean, paper and canonical results are unchanged.

The opt-in builder now supports an explicit combined v3 policy. It checks every
listed source against the pinned release and checks every resulting patch
before creating output. Duplicate, empty or parent-traversing source lists,
a changed second source or patch, and a modified second prepared source are
refused. V1 and v2 retain their source and default selection. The combined
policy reproduces the previously reviewed sigma-limit22 and normalized default
time-array sources exactly. A fresh optimized build from the pinned sdist
changes precisely halofit.f90 and results.f90 among all 113 release files.
The candidate module SHA256 is
85a091c53d9c81ee6443a1a4492ee45a35b487f7d360dfd6df190b9e3856cfc6.
All 234 Python tests pass; established math and Lean files remain unchanged.

The numerical comparison tolerances, baseline receipt and twenty-point
selection are hash-bound before the new CMB worker starts. All twenty controls
are finite and no integrated-time warning remains. Against the sigma-only
optimized v2 baseline the maximum absolute log-posterior change is
1.15396688e-8 and maximum normalized spectrum difference is 6.39886441e-11.
All priors and BAO components remain binary64-identical. The packaged build
also passes the fifteen adversarial near-zero ordering and exact-endpoint
controls and preserves all sixty explicit-tolerance/nonzero API records,
as well as the empty array. Distinct self-review reverses both source patches,
compares every release member and binds individual evaluation receipts, NPZ
arrays, selection, configuration, policy, build and numerical contract.
These are selected numerical controls, not a uniform physical-error theorem
or a full-prior support or posterior certificate. The positive normalization
law retains its stated finite, positive, ordered-input premises.

An initial runtime attempt omits the private Fortran shared-library path and
fails at import before any model or output directory is created. Its original
logs and actual exit1 remain preserved, and the corrected worker uses the
build receipt's private library path. A separate preparation attempt correctly
refuses all four preflights at a distribution-version assertion before models
start: this source archive contains an incomplete camb.egg-info directory
with only SOURCES.txt, making importlib.metadata.version('camb') return None.
The loaded module and pinned root PKG-INFO both report 2.0.4. The failed packet
is closed and retained. A fresh v2 preparation checks the actual loaded
module version, source/native identities and SHA-bound original PKG-INFO,
and records the None distribution metadata observation without inventing it.

Sixteen configurations prepare four separate experimental native targets:
A4095 and B4095, each under mass caps 5 and 20 eV. Existing likelihoods, other
priors, CAMB arguments and sampler options are rederived from the previous
wider-prior configurations; only the declared native build, mass endpoint,
starts, seed and output identities change. The same positive-definite proposal
heuristic is copied for both caps of each likelihood. Four starts cover the
original reference, an already frozen selected point, and masses at 30 and
60 percent of each cap. Every start is strictly inside its declared prior.
All sixteen starts are finite and match forced-fresh upstream native
likelihoods, priors, posterior and provider arrays exactly, including a
cache-resize challenge. The actual launcher validates each loaded candidate
and rejects a deliberately wrong native hash. A separate actual launcher
invocation under the production native environment exits2 before creating
output. Four shared points have exactly equal likelihood components across
caps; posterior changes agree with the uniform-prior normalization -log4
within 1e-10. Distinct preparation self-review reconstructs all targets and
checks all native proofs. No sampler has launched at preparation closure,
and the candidate is not adopted into production.

The runtime observation still accounts for 48 registered families: 44 live
and the same four explicitly preserved terminal wider-prior failures.
Existing old_A3200 and old_B4095 reach their next growth gates, at minimum
represented postburn histories 5822 and 5621 respectively; their next frozen
assessments are due. No current target is newly qualified. Fresh candidate
activation, first saved native-row replay and later separate four-target
qualification are the next obligations. The two material claim discussions
remain open and the paper is unchanged.


The reviewed preparation and combined source policy are checkpointed at
edba123 before activation. Sixteen experimental candidate samplers now launch
with fresh output directories and RNG seeds 2101 through 2116, at nice5 and
one numerical thread per process. Actual activation verifies every PID with
start ticks, mapped module, effective configuration, backend receipt and
FullPrecisionMCMC seed. The four targets remain separate from all previous
histories. The historical and candidate registrations cover sixty-four families.
The original-runtime and candidate-activation observations are separate;
contemporaneous combined liveness still requires the closing check.
First complete saved-row freeze and forced-fresh native replay workers are
running independently for each new target. They remain an explicit pending
obligation and no posterior qualifies. The ninth old_A3200 and old_B4095
snapshots also freeze at minimum represented postburn histories 5860 and5670
respectively, and their unchanged three-stage native/diagnostic verification
workers are running.


All four first saved-row workers complete with exit0. Sixteen complete first
rows are frozen and replayed against forced-fresh upstream CAMB and the
candidate adapter, including cache resizing. Every stored prior, likelihood,
posterior and chi2 component matches exactly, with maximum replay error0.
Distinct self-review rederives binary64 points, exact integer holding times,
complete source prefixes, configuration/backend identities and all native
component bindings. This certifies the selected rows and retains separate
target identities; it does not qualify their posterior readouts.

The ninth old_A3200 and old_B4095 assessments finish with all twelve selected
native rows exactly replayed per target. Only tau passes the complete gate
set for oldA, and no parameter passes for oldB. Mass Rhat is1.011522/1.010132,
bulk ESS426.87/590.83, tail ESS520.36/880.27 and quantile MCSE
0.00748924/0.00453338eV respectively. Their next history minima are7032
and6804. Current_A3200 subsequently reaches its growth gate and completes
a tenth assessment at minimum represented history6616. Its twelve selected
native rows also match exactly. Its mass Rhat is 1.0051852, bulk ESS 623.449185, tail ESS 867.738206 and quantile MCSE 0.00513114569 eV. Complete gate sets pass for ['logA']; the target remains unqualified. Its next history minimum is 7940.

The first closing legacy observer fails, without producing a runtime snapshot,
because its all-primary-live assumption no longer holds. CLASS seed1201's
original PID719894 is absent. Seed1301/PID313611 is also absent. Both original
managed handles report Unknown process id. Neither stderr records an error,
and neither run has a success summary. Exit codes, reasons and final unsaved
states are unavailable: no numerical failure, prior rejection, successful
completion or exact-resume state is inferred. Both complete output trees are
frozen byte-for-byte, their last observed process identities and launch
receipts are bound, and exact complete-prefix holding histories are recounted.
Their final represented postburn histories are1664 and7236. No restart or
old-prefix append is performed. The mediumA and quadA family sets retain these
registrations and are currently ineligible pending terminal review/recovery.
The failed observer and both unknown exits remain explicitly preserved.

A new registered-family observer handles terminal status explicitly and is
verified by a distinct recount. Its snapshot accounts for64 families:58 live,
four previously known wider-prior native failures and the two CLASS unknown
exits. All sixteen candidate samplers have the expected mapped library and
verified first saved native rows. The four candidate cohorts remain separate,
and the old wider-prior and affected CLASS cohorts retain all their terminal
families. No exit cause is invented or numerical error treated as rejection.
The only eligible due target in this closing snapshot is current_A3200,
whose tenth assessment is subsequently completed as recorded above.
The next obligations are candidate fixed-gate diagnostics and separately
identified CLASS recovery; global accuracy, prior stability and both material
claim discussions remain open. The paper and canonical results are unchanged.


The four sigma_time_v3 targets now have a separate diagnostic workflow with
the same first-history gate1000, subsequent growth6/5, holding-time accounting,
20-percent stored-row burn-in and all existing acceptance thresholds. Four
actual production attempts refuse insufficient history before snapshot creation.
Separate prethreshold controls exercise native replay, seven-parameter diagnostics
and distinct self-review for every target: all48 selected native rows match
exactly, and no control posterior qualifies. Cross-cap predecessors, an old-policy
contract and a deliberately wrong loaded native module are rejected. The source
overlay's incomplete distribution metadata is checked through loaded version2.0.4
and SHA-bound original PKG-INFO; no installed-version value is invented.

Two fresh CLASS recovery trials use new seeds2201/2202 and new output prefixes,
starting at the last complete preserved rows of unknown-exit seeds1201/1301.
The preserved learned covariances are finite positive-definite proposal heuristics.
Likelihoods, priors, native arguments and each original sampler profile remain
unchanged. Checkpoints lack the complete proposal/RNG state for exact resume;
the original histories are neither appended nor pooled with these trials.
Both initial native controls match exactly and both guarded launchers reject
bad native identities. Actual activation checks PID/start ticks, command,
mapped module, effective configuration and OS priority. CLASS reportsv3.4.0,
its distribution3.4.0.1, and Cobaya3.6.2.

Both trials now produce a complete first saved row. The dragging trial2201
takes longer to save a row but remains the same owned live process; no failure
or causal performance explanation is inferred. Forced-fresh native replay gives
zero error for every individually checked prior, posterior and likelihood chi2
component. Distinct self-review reconstructs exact integer holding times,
binary64 points, source prefixes and backend/configuration bindings; it also
checks the CMB type aggregate separately from individual likelihood terms.
Two failed self-review assumptions are preserved: treating that aggregate as
another likelihood component, and expecting runtime class types in resolved
configuration. The corrected review derives types from actual imported classes.
These are selected-row certificates, not uniform accuracy or posterior convergence.

The ninth current_A4095 and current_B4095 assessments complete all three stages
with exit0 and all12 selected native rows exact per target. Their minimum
represented postburn histories are5172/5003, and their next history gates
are6207/6004. No parameter passes all gates for A; only omegach2 does for B.
Both targets remain unqualified. A failed preparation using a guessed prior
directory suffix is preserved; the successful preparations use saved state paths.

The first66-registration observer fails because parent terminal provenance was
mistaken for a recovery trial's own terminal status. Its failed receipt remains
preserved. The corrected observer checks explicit own terminal status, and a
fresh closing observation additionally requires both recovery first-row proofs.
It accounts for66 registrations:60 live, four known wider-prior native failures
and two preserved unknown CLASS exits. All sixteen original/candidate four-family
groups retain their membership; the two new recovery trials are listed separately.
No eligible group is currently due. Candidate minimum histories are269-297,
below the unchanged first-assessment gate1000. Constructing an explicitly declared
four-family CLASS recovery design remains open. Uniform physical accuracy,
prior stability and both material main-claim discussions remain open. The paper
and canonical results are unchanged.


Six fresh CLASS companion configurations now define two separate four-start
recovery designs: medium_A seeds2201/2301/2302/2303 and quad_A seeds2202/2304/2305/2306.
The six new starts are the fixed original references of surviving seeds
1401/1402/1406 and1302/1303/1304 respectively. Only those initialization values
are reused. Every start is strictly inside its original prior, all four starts
per group are distinct, and each new companion preserves its existing recovery
anchor's declared likelihoods, priors, native settings and sampler profile.
The shared learned covariance per group is a finite fixed numerical
proposal heuristic that passes a Cholesky check. New RNG seeds and output prefixes are mandatory.

All six surviving original launch receipts bind source hashes that differ from
the current public launcher, MCMC, metrics and BAO implementation. The old
receipts do not bind every likelihood adapter source file. These differences
do not prove target change; they leave uniform historical/current numerical
target identity unproved. Original histories remain separately registered and
are not pooled with fresh recovery histories. Both fresh cohorts retain the
first-history gate1000 and later growth6/5, with actual diagnostic workflow
construction still pending.

The first design packet is preserved after semantic self-review refuses its
claim of conditional independence: different fixed seeds and starts do not
supply an independence theorem for random streams. A fresh v2 packet correctly
states distinct declared seeds/starts without proving probabilistic independence.
All six actual v2 native attempts then exit1 before model evaluation because
the runner omitted the private backend PYTHONPATH. The real public launcher
guard rejects the unguarded installed module; these complete failed attempts
remain preserved. A fresh v3 runner derives its backend search path from the
declared module and runs at most two native controls concurrently.

All six v3 native starts are finite, with finite provider arrays and individual
native log-likelihood components. Every actual launcher guard is exercised and
rejects a deliberately wrong native contract. Distinct self-review reconstructs
all six configurations, proposal/source bindings, four-start designs, native
proofs and preserved corrections. No additional sampler is activated at packet
closure. Activation, first saved-row replay and separate convergence assessments
are the next obligations; independence, stationarity and uniform solver accuracy
remain unproved. The paper and canonical results are unchanged.

Both actual fresh companion launchers, tested once per recovery target under
the installed unguarded native environment, exit1 before producing any launch
receipt or run output. Their positive native preflight proofs remain unchanged.


All six reviewed CLASS companions activate with new output prefixes and RNG
seeds2301-2306, at nice5 and the existing recovery anchors' OMP8/4 profiles.
Actual activation and a distinct recount verify PID/start ticks, command,
mapped native library, effective configuration and process environment.
Every first complete saved row is frozen and forced-fresh replayed against
the declared guarded CLASS target. All checked prior, posterior and individual
likelihood chi2 components match exactly. Combined selected-row self-review
also reconstructs exact holding times, source prefixes, binary64 coordinates,
configuration/backend bindings and the separate CMB type aggregate. All eight
fresh recovery first-row proofs, including anchors2201/2202, now exist.

The first72-registration observation encounters absent original CLASS seed1302.
A complete identity scan finds nine additional absent original identities:
1302/1303/1307/1308/1401/1402/1403/1404/1405. All nine managed handles report
Unknown process id; stderr is empty and no success summary exists. Their complete
output trees and launch receipts are frozen byte-for-byte, complete holding
histories are recounted, and last verified live identities are bound. Exit codes
and reasons remain unavailable; no numerical failure, prior rejection, successful
completion or exact-resume state is inferred. Checkpoints lack proposal/RNG state.
No old prefix is appended or restarted. All original four-family registrations
remain present. Old mediumA/B and quadA/B cohorts now retain unavailable-exit
families and remain assessment-ineligible; the fresh A recovery cohorts are separate.

A corrected72-registration observer requires first-row proofs, with temporary
pending permission restricted to the newly activated companion seeds. Its first
snapshot and distinct self-review account for57 live and15 terminal registrations:
four known wider-prior CAMB native failures and eleven CLASS unknown exits.
A fresh closing observation after all eight recovery row proofs preserves the
same counts, every original family and all eighteen declared cohorts. No eligible
cohort is due at that observation. Fresh B precision posterior designs remain
an open restoration obligation if required for the broader comparison.

The two fresh CLASS targets now have a separate snapshot/native/diagnostic
workflow. It preserves first-history threshold1000, later growth6/5, exact
integer holding histories, 20-percent stored-row burn-in, native replay tolerance
1e-9 with zero relative tolerance, and every existing rank/ESS/quantile precision,
chronological drift and equalized-selection gate. All ten sampled parameters
are checked, with absolute mass MCSE target0.001eV and other-parameter precision
relative to empirical posterior standard deviation. A short native-row count
refuses before output creation; it does not relax the three-row native obligation.
Both actual production attempts refuse insufficient history with exit3. Actual
cross-target and control-as-production predecessor attempts also refuse before
output. No historical target or control contract is declared compatible.

The initial CLASS contract preparation fails because a dotted import resolves
an exported class rather than the module, so __file__ is unavailable. The failed
packet is closed and preserved. Fresh v2 helpers explicitly import the module;
both complete separately frozen prethreshold controls then execute upstream
forced-fresh native replay, ten-parameter diagnostics and distinct self-review
with exit0. All24 selected native rows match exactly. Neither short control
qualifies. A real replay worker under the installed unguarded native environment
exits1 before model evaluation, leaving its existing positive native proof
unchanged. Recorded launch solver-version metadata remains absent; the loaded
replay module's v3.4.0 label is reported separately rather than substituted into
historical provenance. Uniform solver accuracy, posterior stationarity, prior
stability and both material main-claim discussions remain open. The paper and
canonical results are unchanged.


A fresh post-workflow72-registration observation and distinct self-review
retain57 live and15 terminal families, all eighteen declared cohorts and no
eligible cohort due. Eight new B configurations form two separate four-start
cohorts: mediumB2401-2404 and quadB2405-2408. Fixed original reference points
are distinct and strict prior-interior. Frozen terminal learned covariances
from original1403 and1307 are shared finite numerical proposal heuristics
that pass Cholesky checks.
No historical history is pooled. Every original likelihood, prior, mapping,
native precision and per-source sampler profile is preserved, including the
dragging profile of original1405. The new profiles retain OMP8/4 and nice5.
All eight actual native starts exit0, with finite posterior, component likelihoods
and provider arrays. Distinct self-review reconstructs target equality within
each cohort, source/config/proposal/build bindings and actual native proofs.
Both actual fresh B launchers under the installed unguarded module exit1 before
launch receipt or output. The first control wrapper initially expects the wrong
error-message substring and exits1 after the native guard correctly refuses;
its original capture is checked without repeating that control. No sampler is
activated at this preparation checkpoint. Activation, first saved-row replay
and separate B diagnostic contracts remain pending. Distinct seeds and starts
do not establish stream independence, stationarity or uniform physical accuracy.
The paper and canonical results remain unchanged.


Eight fresh B samplers activate with new RNG seeds/output prefixes2401-2408.
Actual startup verification checks each PID/start tick, command, mapped native
module, effective configuration, OMP8/4, BLAS/MKL1 and nice5. All eight identities
are reconstructed by distinct self-review. Two reviewer attempts fail while
reversing a prefix substitution that also matches a preparation path; full
forward reconstruction applies the exact recorded source substitutions and
passes. Original unsuccessful attempts remain preserved. This repair changes
review evidence plumbing only. Four quadrature B first saved rows are frozen
and replay exactly, with distinct holding-time, binary64-coordinate, native
component and CMB aggregate reconstruction. Medium B first-row witnesses are
still pending in a managed runner with at most two replay workers.

The initial80-family observer refuses when original1406 is absent. Identity
scans and actual managed-handle queries also find original1407 and1502 absent
with unavailable exits, empty stderr and no successful summary. All three
complete output trees are frozen byte-for-byte, prior owned identities are bound
and exact complete holding histories/checkpoint fields reconstructed. No native
failure, prior rejection, successful completion or exact resume is inferred.
Original mediumA/B and grid12B registrations are retained with ineligible
terminal families. A fresh observer accounts for80 registered,62 live and18
terminal families: four known wider-prior CAMB native failures and fourteen
CLASS exits with unavailable reasons. All twenty declared cohorts remain. Its
first review is mistakenly attempted before the observer terminates; a fresh
identical review runs after actual observer exit0 and passes.

That observation makes oldA3200 due. Its tenth same-target assessment freezes
minimum7059 postburn represented steps against the unchanged7032 trigger.
Twelve selected archived-solver native rows replay exactly; native replay,
all-parameter diagnostics and distinct snapshot review all exit0. Only tau
passes all gates. Mass Rhat1.008895, bulkESS524.7 and tailESS693.7 pass their
individual thresholds; mass quantile MCSE0.00569747eV exceeds the unchanged
0.001eV precision target. No posterior qualifies. Next same-target history
trigger is8471. Helpers for the separate B diagnostic workflow are prepared,
but its contract is not yet populated: all eight native first-row proofs are
required first. Mathematical code and Lean are unchanged since their verified
checkpoint; the paper and canonical results remain unchanged.


All eight fresh B first complete saved rows are now frozen and replayed exactly,
with combined distinct self-review of holding times, binary64 points, input/
backend bindings, component chi2 values and the separate CMB aggregate. All
sixteen fresh CLASS recovery first-row witnesses now exist across four separate
A/B precision cohorts. B contracts preserve first-history1000, growth6/5,
20-percent stored-row burn-in, three native rows per family and every existing
ten-parameter precision/ESS/Rhat/drift/equalized-selection gate. Both actual B
production attempts refuse insufficient history with exit3. Actual cross-target
and control-as-production predecessor attempts exit1 before output. No historical
contract or short control is declared production-compatible.

The initial mediumB control also refuses exit3 before snapshot creation because
seed2403 has only one stored complete row, below the unchanged three-row native
obligation. A fresh medium control root is created after enough real rows exist;
its helpers and control contract are byte-identical to the refused packet.
The quadB and fresh mediumB full snapshot/native/diagnostic/self-review control
paths all exit0. All24 selected native rows match exactly and all ten parameter
gate sets are reconstructed; neither short control qualifies. A real replay
worker under the installed unguarded CLASS environment exits1 before model
creation, preserving its existing positive native proof. Recorded solver-version
metadata remains absent, with the loaded CLASS version kept separately. Distinct
workflow self-review verifies both complete controls, all eight B row bindings,
unchanged thresholds and actual refusals. Both B workflows are ready; production
posterior assessments still await the unchanged history threshold.

A later closing observer encounters original grid12B seed1503 absent. Its actual
managed handle reports Unknown process id. Empty stderr and absent success summary
supply no cause. The full output tree, prior identity and exact complete holding
history are frozen and reviewed, retaining this original registration. A fresh
80-family observation verifies61 live and19 terminal registrations: four known
wider-prior CAMB native failures and fifteen CLASS unavailable exits. Every one
of the twenty original/fresh cohort registrations remains. Old grid12B retains
its terminal families and is assessment-ineligible.

That observation makes oldB4095 and currentA3200 due. Their tenth and eleventh
same-target assessments freeze minimum6880 and8049 postburn represented steps.
All24 selected native rows match exactly; native replay, all-parameter diagnostics
and distinct snapshot review all exit0. OldB4095 only logA passes, with mass
Rhat1.010479 and MCSE0.00377214eV. CurrentA3200 logA/tau pass, with mass
Rhat1.004533 and MCSE0.00436466eV. Both still fail posterior qualification; the
unchanged mass precision target is0.001eV. Exact next growth gates are8256 and9659.
A fresh final80-family observation and distinct review preserve61 live/19 terminal
families and all twenty cohorts, with no eligible cohort due. Its growth review
reconstructs every current production next gate by exact ceiling of6/5 times
its prior frozen minimum; new candidate/CLASS first gates remain1000. Short
controls do not reset production thresholds or qualify a posterior.

A distinct covariance audit clarifies the earlier SPD wording for four fixed
fresh CLASS proposal inputs. All four parsed binary64 matrices have tiny nonzero
asymmetry, so a numerical symmetry tolerance and Cholesky success do not establish
exact symmetry of their raw bytes. Raw matrices and sampler configurations remain
unchanged. The exact rational symmetric interpretation S=(M+transpose(M))/2 is
positive definite, certified by exact LDL factorization. If delta is the largest
entrywise difference between M and S, exact LDL also proves S-10*delta*I positive
definite. Any symmetric matrix obtained by copying a represented triangle,
including after any simultaneous row/column permutation, differs entrywise from
S by at most delta. Its quadratic error is bounded by
  delta*(sum_i abs(x_i))^2 <= 10*delta*||x||^2,
so this exact positivity margin proves positive definiteness of every such
symmetric triangle interpretation. A separate integer Bareiss principal-minor
algorithm checks all80 positive exact determinants and matches the LDL pivots.
The actual LDL hinge rejects singular and indefinite false targets. This is
self-review with a distinct arithmetic algorithm, not independent human/agent
review. It does not certify floating correlation-normalization roundoff,
random-stream independence, sampling invariance or posterior convergence.
Earlier proposal-heuristic descriptions are clarified accordingly. Source and
Lean remain unchanged from their verified checkpoints. The paper and canonical
results remain unchanged; uniform physical accuracy, qualified posterior/prior
comparisons and the two material main-claim discussions remain open.


A concrete two-claim decision packet now binds the actual abstract/conclusion,
canonical magnitude, original short-chain failures, suspended near0.030eV
historical readout, current failing validated-policy assessments, and same-pair
full-CMB signed localization. It does not adopt a material revision. The original
0.108606eV shift remains unsupported by its one-chain archived diagnostics.
The near0.030eV value passed earlier empirical gates but is not a currently
qualified numerical replacement after the native-cache qualification suspension.
The constructive magnitude route is to complete the already separate solver/
cutoff posterior comparisons without lowering any gate or asserting global native
accuracy. A future narrowing route would retain the mechanism and report a
specified numerical effect only once that target is actually qualified.

The localization decision is separate: in2000<=ell<3000, the same-pair full-CMB
forward allocation is EE37.1399 versus TT14.5377; reverse allocation is TT12.3701,
EE0.9169 and TE-0.1640. SPT-only forward allocation remains TT-dominated. The
concrete scoped route reports baseline/direction dependence while retaining
directional mismatch and staging audits. More posterior history cannot by itself
restore a broad TT statement contradicted by these finite forward controls.
A broader statement would need new controlled evidence on a prespecified domain.
Signed correlated allocations are not independent chi-square contributions,
global profile optima or pure packaging-cause proofs. Gaussian/gate theorems
retain their explicit hypotheses; the absent cosmological CDF-error bridge is
not supplied by sampler diagnostics. Distinct self-review checks both decision
routes and source hashes. Stale recovery summaries are corrected to four fresh
CLASS cohorts, sixteen first-row witnesses, fifteen unavailable exits and four
known failures, preserving the original historical summaries. No paper edit or
main-claim revision is adopted.


Three first sigma_time_v3 production assessments now close with native replay,
all-seven-parameter diagnostics and distinct snapshot review each exiting0.
A cap5 freezes minimum1007 retained represented steps, B cap5 minimum1022 and
B cap20 minimum1005, all after the unchanged first1000 gate. All36 selected
native rows replay exactly against the separately identified upstream fresh
CAMB2.0.4 module. No parameter passes every gate in any of these three groups.
The mass Rhat values are1.73787,1.93642 and2.40773 respectively, with MCSE
0.798978,0.161769 and0.489764eV; none supplies a qualified posterior. Next
minimum-history gates are1209,1227 and1206 by exact ceiling of6/5. A real B
cap20 preparation earlier refused exit3 at minimum992 and a real A cap20
preparation refused exit3 at907, each before snapshot creation. These failed
attempts remain preserved.

A distinct combined self-review binds the three production snapshots, their
actual closed workers, source adaptations, exact saved-row weights and all
seven gate sets. Its first attempt expects an absent receipt count field;
a fresh script reconstructs the actual seven-parameter key set and exits0.
The original failed script and schema-repair receipt are retained. The very
large unqualified raw quantiles in these snapshots are not read as a
stationary high-mass tail or prior-cap effect: the fixed high starts still
show large transients, and the chain disagreement/precision gates fail.
Selected native equality is not uniform physical accuracy or convergence.

A fresh runtime observation at06:26:54 UTC binds all80 registrations,61 live
samplers and19 preserved terminals, with all20 cohort memberships retained.
Exact growth review checks the eight currently assessed target bindings and
keeps first1000 gates for all unassessed fresh targets. This makes current
A4095 and B4095 due. Their tenth same-target assessments freeze minimum6312
and6173 retained represented steps against unchanged6207 and6004 triggers.
All24 selected native rows replay exactly and all three verification stages
exit0 for each assessment. A4095 logA/tau pass; mass Rhat1.004709 and bulk/tail
ESS617.9/840.5 pass those individual thresholds, but mass MCSE0.00603316eV
exceeds the unchanged0.001eV limit. B4095 only omegach2 passes; mass Rhat
1.012153 and MCSE0.00269880eV fail. Neither posterior qualifies. Next exact
history triggers are7575 and7408. A state-summary helper initially expects
incorrect ESS field names and exits1 before writing state; its schema-repair
receipt preserves that failure, and the actual diagnostic fields are used
without repeating closed verification workers. Mathematical source and Lean
remain unchanged from their verified checkpoints. The paper and canonical
results remain unchanged, and no main-claim revision is adopted.


The second real A cap20 preparation refuses exit3 at minimum999, before output,
and remains preserved separately. A fresh third output root then freezes its
first production snapshot at minimum1004 against the unchanged1000 gate.
All12 selected native rows match exactly; native replay, seven-parameter
diagnostics and distinct snapshot review each exit0. No parameter passes all
gates. Mass Rhat2.295788, bulkESS5.04, tailESS21.82 and MCSE0.0382823eV fail;
next exact history gate is1205. All four candidate numerical-policy targets
now have a first production assessment, with48 exact selected native rows
and no qualified posterior. A fresh four-target combined self-review
reconstructs saved weights, first/last mass and log-posterior coordinates,
worker/source bindings and all gate sets; it exits0. Large raw quantiles remain
unqualified startup transients, not stationary-tail or prior-sensitivity results.
A separate combined review of the two tenth4095 CAMB assessments also exits0,
checking all predecessor prefixes, holding times and exact growth gates.

The closing runtime observation and distinct review again bind80 registered,
61 live and19 preserved terminal families across20 declared cohorts. Exact
growth review reconstructs all nine latest production predecessor bindings,
keeps the first1000 threshold for the four unassessed fresh CLASS cohorts,
and preserves ineligible original cohorts. No posterior, uniform physical
accuracy or material main-claim revision is certified. This checkpoint adds
no mathematical-source, Lean, script/test, paper or canonical-results changes.


A current precision-obstacle audit binds all nine latest assessed CAMB numerical
targets, their actual closed three-stage workers and all63 parameter gate sets.
It checks108 selected native-row comparisons remain exactly equal. Distinct
self-review reconstructs all nine gate predicates from the numeric diagnostic
fields and recounts all36 frozen weighted histories; both audit and corrected
review exit0. Only currentA4095 fails precision gates alone at its bound snapshot.
CurrentA3200 also fails chronological drift in at least one sampled parameter;
oldA3200 additionally fails Rhat/drift, oldB4095 and currentB4095 additionally
fail Rhat. All four sigma_time_v3 groups fail Rhat and bulk/tail/quantile ESS
as well as precision; A cap5/cap20 and B cap20 also fail chronological drift
and equalized-selection checks. No target qualifies. These are the failures
of actual finite diagnostic estimates, not formal stationarity or physical
error certificates. No completion-time or required-sampling-length prediction
is made, and no acceptance gate is relaxed. The report opening is corrected
to mark the near0.030eV readout as historical and currently suspended, with
its previous text preserved. This report correction does not revise the paper
or adopt either material main-claim change. The first review script has a
syntax error and the first repair expects absent indentation; both attempts
are recorded, the original script remains, and the fresh corrected script
passes without repeating closed writers or changing diagnostic inputs.


A separate starts-witness review closes a semantic gap in the gate label:
separate_starts in the diagnostic receipt checks only the number of chains.
For each of the nine bound targets, the frozen input bytes separately witness
four distinct fixed seven-parameter reference points inside the recorded
prior, and the frozen chains witness four distinct first saved points. Exact
rational interpretations of the finite binary64 refs establish these finite
distinctness/prior assertions. Distinct seeds, refs and saved points do not
establish independent PRNG streams, stationarity or adequate prior exploration.
The starts review exits0 without changing the sampler or diagnostic gates.

A fresh runtime/growth review at06:47:19 UTC makes sigma_time_v3 A cap5 due.
Its second same-target assessment freezes minimum1209 against its unchanged
1209 growth gate, with every predecessor prefix retained. All12 selected native
rows replay exactly and all three verification stages exit0. No parameter
passes every gate; mass Rhat1.556619 and MCSE1.62496eV fail, and next history
gate is1451. A later observation at06:52:01 UTC makes B cap5 and B cap20 due.
Their second assessments freeze minimum1249 and1238 against unchanged1227
and1206 triggers. Both native replays, diagnostics and snapshot reviews exit0;
all24 selected native rows match exactly. No parameter passes all gates. B cap5
mass Rhat1.862096 and MCSE0.497296eV fail; B cap20 mass Rhat2.185037 and
MCSE0.0104570eV fail. Exact next history gates are1499 and1486. Distinct combined
review of these three second assessments exits0, reconstructing all predecessor
prefixes, holding times, source adaptations and seven-parameter diagnostics.
All three new assessments remain unqualified, without pooling targets or
reading their transient raw quantiles as stationary tails or prior-cap effects.
The obstacle audit retains its explicitly bound earlier snapshots rather than
silently changing its inputs when later assessments are registered. The latest
observation accounts for80 registered,61 live and19 preserved terminals across
20 cohorts; its two due cohorts have completed their assessments afterward.
Mathematical source, Lean, scripts/tests, paper and canonical results remain
unchanged; both material main-claim discussions and physical/posterior accuracy
obligations remain open.


Readout.lean now formalizes comparison error without a joint independence
premise. The readout is qA-qB. Given actual coordinate errors bounded by
epsilonA and epsilonB, algebra and the triangle inequality derive a paired
error at most epsilonA+epsilonB, an interval for the true difference, and
positivity when the observed difference strictly exceeds that sum. A
constructive witness with four strictly positive coordinates attains the sum
bound exactly. It does not construct four probability laws or their quantiles.
For estimates on one common measurable space, paired failure is contained in
the union of the two marginal failures. Measure subadditivity propagates
supplied marginal risks; measurable estimators supply a measurable paired
failure event. Under an actual probability law these measures are failure
probabilities. All eight declarations and helpers are checked by the kernel.
Actual coordinate errors and marginal risk bounds remain hypotheses, not
Monte Carlo standard-error estimates, and no cosmological calibration or
uniform physical-error bridge is supplied. The historical independent-error
MCSE quadrature keeps its separate meaning and suspended qualification.

The initial build fails on the triangle-inequality API name and extended-real
notation; its complete source and output are preserved. The repaired source
uses abs_add_le and the explicit ENNReal type, without changing any statement
or premise. The full Lean build exits0. Fresh dependency inspection covers
all97 public theorem/lemma declarations, including the eight new readout laws,
and finds only propext, Classical.choice and Quot.sound. Four separately
compiled hinge controls accept the actual summed-bound witness and refute
maximum-error, deterministic quadrature, and a weakened non-strict sign
margin. The quadrature counterexample is about absolute coordinate errors;
it does not refute variance addition under its own independence assumptions.
Distinct self-review checks declarations, dependencies, controls and source
repair; this is self-review, not independent human or agent review. The older
60/74/89 export metadata is retained historically, and current fields now
record97. Python numerical code, its last234-test evidence and all live sampler
implementations remain unchanged. The paper and canonical results remain
unchanged, and no material main-claim revision is adopted.

The wider A sigma_time_v3 comparison reaches its unchanged1205 growth gate.
Its second same-target snapshot freezes minimum1217 postburn represented
steps with every predecessor prefix retained. All12 selected native rows
replay exactly; native replay, all-seven-parameter diagnostics and snapshot
review each exit0. No parameter passes all gates. Mass Rhat2.275820 and
MCSE0.188882eV fail, and the next exact history trigger is1461. This is an
unqualified numerical-target assessment, not a stationary high-mass tail,
prior-cap effect or application of the new error law. The new law improves
conditional comparison coverage but does not restore the numerical headline.


The posterior credibility level used to define an upper quantile and the
probability of estimating that coordinate incorrectly are distinct. No
95-percent sampling-error guarantee is inferred from a95-percent posterior
quantile, and no Monte Carlo standard error is substituted for a coordinate
error bound in Readout.lean. The generic paired-risk theorem remains conditional
on actual marginal error risks under the chosen common probability law.

A07:26:08 UTC runtime/growth review makes A cap5 due at its unchanged1451
trigger. Its third same-target assessment freezes minimum1510, preserves all
predecessor prefixes and closes all three verification stages with exit0. All12
selected native rows match exactly. No parameter passes every gate; mass
Rhat1.382522 and MCSE2.15970eV fail, and next exact history gate is1812. A
distinct combined review with the completed second A cap20 assessment exits0
and reconstructs their source adaptations, saved weights and seven-parameter
gates. It checks24 selected native rows without pooling the two prior targets.

A closing observation at07:43:22 UTC accounts for80 registrations,61 live
samplers and19 preserved terminals across20 declared cohorts. Its exact growth
review makes B cap5 and cap20 due at1499 and1486. Their third assessments
freeze minimum1559 and1513 with all predecessor prefixes retained; native
replay, diagnostics and snapshot review each exit0, with24 exact selected
native rows. No parameter passes every gate. B cap5 mass Rhat1.698294 and
MCSE0.640781eV fail; B cap20 mass Rhat2.290801 and MCSE0.103905eV fail. Next
exact history gates are1871 and1816. Their distinct combined review exits0.
No transient raw quantile, physical tail, prior-cap effect, stationarity or
uniform native accuracy is inferred. Both cohorts due in the bound closing
observation have completed their assessments afterward. The added formal laws
and four current numerical-policy assessments do not restore the original
numerical headline or resolve the material localization discussion. The paper
and canonical results remain unchanged.


## Evidence-led review after withdrawal of claim-restoration sampling

The first fresh CLASS quad-A production assessment freezes minimum1018
postburn represented steps against the unchanged1000 first gate. All12 selected
native rows reproduce exactly; native replay, all-ten-parameter diagnostics
and snapshot verification each close with actual exit0. No parameter passes
every gate. Mass Rhat1.053537, bulk ESS62.6573, tail ESS152.333 and
MCSE0.00309795eV fail. The unchanged next history gate would have been1222.
The loaded CLASS version is v3.4.0; absent historical solver-version metadata
remains null rather than being filled from the replay environment. This first
production assessment is separate from both prethreshold controls and historical
failed cohorts.

The eleventh archived-CAMB A3200 assessment preserves its predecessor prefixes
and freezes minimum8582 against the unchanged8471 gate. All12 selected native
rows reproduce exactly and all three verification stages close with actual
exit0. Mass Rhat1.007350 and ESS checks pass, but MCSE0.00479785eV fails the
unchanged0.001eV target. Only logA, ns and tau pass every gate. Its next history
gate would have been10299. An earlier attempt used the current-CAMB environment;
the native identity guard refused it before model creation with actual exit1.
That failed attempt is preserved separately; the successful fresh attempt uses
the pinned archived environment, with no contract change. Distinct combined
self-review reconstructs17 parameter gate sets, eight complete weighted
histories and24 exact native rows. Neither assessment qualifies a posterior.

The owner then directed that original claims judged wrong or likely wrong
should no longer be defended. Claim-restoration
sampling is withdrawn, rather than continued to seek a preferred magnitude.
A final pre-stop observation verifies80 registrations,61 live owned identities
and19 historical terminals, with20 preserved cohort memberships. Its growth
review checks ten production predecessor bindings. All61 live samplers receive
SIGINT only after revalidation of PID start ticks, command and loaded native
module, using reuse-safe pidfds. All61 managed handles subsequently return
actual terminal exits:47 return130 and14 return143. A second poll of the same
1501 handle supplies its terminal130; no timeout is treated as termination.
The exit values are recorded as observed, without inferring additional signal
causality or scientific failure. No new sampler or history extension is launched.

Complete settled run trees, including raw chains, checkpoints, covariance and
logs, are frozen and hash-checked under
`runs/20261005_math_review_user_directed_restoration_shutdown`. All80 original
identities are absent:61 deliberate stops, four earlier established native
failures and15 earlier unavailable causes. Those15 causes remain unknown.
A distinct terminal self-review recounts all61 new complete weighted histories,
checks every frozen file and preserves all20 cohort memberships. Parent-terminal
provenance for2201/2202 remains separately bound when their own stop receipts
are registered. Interrupted runs do not establish stationarity, scientific
falsity, exact PRNG resumability, or a new numerical mass claim.

The bound claim disposition retains conditional Gaussian mathematics and finite
directional comparisons with their actual domains. Broad full-CMB TT dominance
has audited forward EE counterexamples and should be withdrawn in that broad
form. Both advertised posterior-tightening magnitudes lack reliable support
and should be withdrawn as established results; the original values are not
thereby proved false. The historical near0.030eV readout remains suspended.
Future manuscript edits belong to the later paper phase. The continuing review
should resolve actual mathematical or implementation issues and report only
evidence-supported claims, without more computation aimed at rescuing the
advertised conclusions. Python/Lean sources and their last234-test/97-declaration
verification evidence are unchanged; the paper and canonical results remain
unchanged. This checkpoint withdraws the restoration campaign, not the overall
mathematical-review goal.


## Remaining toy rewrite arithmetic repaired

The evidence-led continuation finds an unrepaired arithmetic path in
`run_template_rewrite.py`. For one-bin covariance1e-320 and residual1e-10,
the inverse solve overflows although the whitening and quadratic, about1e300,
are representable. Both full-residual and dominant-whitened modes previously
returned infinite/NaN diagnostics and could serialize nonstandard JSON numbers.
Covariance validation also unnecessarily solved for the mean, rejecting a valid
model with that covariance and mean1. Six of eight initial new controls fail
before the repair; the archived source reproduces both nonfinite rewrite cases.

The repair uses the shared finite symmetric positive-definite Cholesky check,
whitens residuals/templates, and normalizes the template before computing the
projection coefficient. Exact rational accumulation of represented whitened
squares avoids intermediate overflow/underflow; this is not a certificate for
Cholesky accuracy or an exact inverse-covariance quadratic. Actual finite
updated residuals are re-evaluated. Nonzero quadratics or coefficients that
cannot be represented are refused. A zero template retains its explicit zero
correction. An unrepresentable condition estimate is reported as unknown,
while all exported numerical diagnostics must be finite and strict JSON
serialization refuses NaN/Infinity. Gaussian mean/covariance validation no
longer requires an unrelated inverse solve.

Ten new regression cases exercise finite quadratics despite inverse-solve
overflow, valid mean/covariance parsing, nonfinite/unrepresentable outputs,
correlated projection, zero templates and template scales1e-200/1e200. The
existing small-template rescaling control still passes. The full Python suite
closes with actual exit0 and244 passing tests. A distinct self-review uses
exact rational1D/2D covariance inversion and the projection formula, rather
than the implemented whitening algorithm:80 ordinary controls agree with the
previous results within1e-12 relative/absolute tolerance, two extreme finite
controls now agree with the independently evaluated quadratic, and invalid
outputs are refused. Its first archive-import preparation fails because the
archived source derives a different repository path; the preserved fresh
review adds the actual src path and exits0 without changing any mathematical
hypothesis. Sources, controls and receipts are in
`runs/20261005_math_review_template_rewrite_repair`.

This validates the fitted toy covariance projection in the tested domain.
Selecting a full-residual template can remove the fitted residual by
construction; that remains descriptive fit improvement, not independent
held-out prediction or a cosmological repair. No mass result is promoted,
no sampler is restarted, and Lean, paper and canonical sources remain unchanged.


## Review completion and later manuscript obligations

The completion audit reconstructs the original requested scope and the later
evidence-priority instruction. It maps every one of the11 displayed equation
labels in the11 paper sections, plus the sweep, probability/quantile, upper-gate,
paired-error and rewrite claim families, to actual premises, code/formal
coverage and limits. It inventories paper sections/tables, all numerical
library and script sources, tests, configurations and formal sources by hash.
Operational SBT framing is not substituted for a theorem providing physical
error control, and numerical candidate searches are not reported as constructions
of the stipulated global maximizers. Within-run nuisance-profile reductions
use the same improved reference endpoint; unrelated unprofiled bundles must
not be substituted for that reference when interpreting a percentage change.

Every one of97 public Lean declarations matches the dependency request and
successful output. The latest actual build, dependency and false-target
execution receipts are checked against unchanged sources, and all nine pinned
package commits match clean tracked trees. No added axiom or admitted proof
is found. Current numerical code is covered by the final245-test successful
Python run, with the repaired toy script/test hashes bound to that execution.
The two actual toy rewrite CLI modes and80 distinct exact-rational controls
pass. All other numerical sources retain the reviewed implementation state.
A fresh terminal self-review checks the current stopped ledger, all preserved
file hashes and61 represented histories; no registered sampler is live.

The requested mathematics/code/Lean review and its known actionable repairs
are complete. The main empirical limitations are conclusions of this review,
not hidden premises or reasons to restart an advertising-driven restoration
campaign. Advertised mass magnitudes and the suspended historical replacement
remain withheld; broad full-CMB TT dominance must be withdrawn. Conditional
Gaussian mathematics and finite directional comparisons retain their
explicit domains, numerical scopes and uncertainty limits. There is no
claim of a uniform physical or floating-point certificate, MCMC convergence
theorem, global optimizer guarantee, calibrated significance, or causal
packaging identification.

The paper tree and canonical results are unchanged from the pre-review
checkpoint. Updating them to remove unsupported empirical claims and state
the supported conditional/scoped content belongs to the later manuscript
phase explicitly excluded from this task. Obsolete restoration obligations
and magnitude choices are preserved as historical records and superseded
in current state, so they cannot be mistaken for active work or a qualified
near0.030eV result. Completion evidence is under
`runs/20261005_math_review_completion_audit_v2`. This is a completed mathematical
review with distinct self-review, not independent external review or approval
of the original manuscript as written.


The first completion snapshot is preserved historically. A final inspection
finds that the newly nullable condition-number estimate was still formatted
as a float in the toy CLI summary. The summary now prints unknown, and an
actual main-path regression constructs a valid extreme-condition toy pair,
writes strict finite JSON, renders the comparison and verifies that summary.
All11 new rewrite cases pass; a fresh complete Python run closes with actual
exit0 and245 passing tests. A fresh distinct80-control rational self-review
binds the final source, and the v2 completion audit binds that source and
its final execution receipt. No mathematical hypothesis is removed, and no
scientific recovery work is restarted.
