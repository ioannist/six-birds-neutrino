# Gaussian mode and directional audit proofs

This library proves the Gaussian boundary mechanism and algebraic audit
identities. It uses Lean 4.27.0 and the pinned Mathlib revision.

Run `lake build`, then `lake env lean AuditAxioms.lean`. From the repository
root, `make math_check` also runs the numerical regression tests; set `PYTHON`
to your Python environment when necessary.

`TruncGauss.lean` retains the original antitone and boundary maximum theorems
for positive sigma and nonpositive mean. `Mode.lean` proves the unique maximum
on the nonnegative half-line is `max 0 μ` for every real mean, and that a positive
constant multiplier preserves it. It derives the completed-square identity for
positive precisions and proves that nonnegative component means cannot combine
to a negative mean. Common scaling of both precisions leaves the mean unchanged.

`Product.lean` proves the completed-square identity for the actual exponential
product, its unique gated maximum, the exact boundary-maximum equivalence,
and the deterministic offset gate. It returns these statements to the original
standard-deviation factors for positive sigmas. Interpreting the product as a
posterior still requires a constant prior on the gate.

`Tightening.lean` defines the boundary event for the actual two-factor product,
identifies its closed offset half-line, and proves the precision monotonicity
laws for one fixed offset measure. It now also defines boundary maximization
using the original standard-deviation kernels and proves its equivalence to the
precision event. Positive standard deviations give the threshold
`-μ*(1+σ₂²/σ₁²)`. Holding the first deviation and offset measure fixed, reducing
the second deviation cannot decrease the boundary measure when `μ>=0`; the
direction reverses when `μ<=0`. These are non-strict measure inequalities and
do not formalize a Gaussian CDF identity or its strictness.

`GaussianSweep.lean` derives the Gaussian offset law with mean `-d` and
variance `s²` by affine transport of Mathlib's standard normal measure.
For positive `s`, it proves the exact CDF formula for boundary maximization
of the original kernel product. The standard normal CDF is proved strictly
increasing using the positive density on nonempty intervals. For fixed
first width, offset mean and noise, the boundary probability is strictly
antitone in the second width for positive first mean, strictly monotone
for negative first mean, and constant at zero mean. This exact-real statement
does not assert strict change after floating-point CDF rounding.

`Audit.lean` proves nonnegativity under an explicit likelihood ordering
hypothesis and the sum identity under actual additive block contributions.
These are algebraic results, not proofs that an optimizer finds a global maximum
or that correlated covariance submatrices define additive likelihood blocks.

`CovarianceLedger.lean` connects an exact linear solve with a positive definite
covariance to inverse multiplication and the full residual quadratic form.
It proves nonnegativity of the full inverse-covariance form and exhaustive
grouping of signed coordinate differences, allowing different endpoint
precision matrices. An optional group label retains the unlocalized remainder.
The coordinate-sum identity is definitional; the solve and partition bridges
are derived. None of these theorems assert positivity of individual allocations,
floating-point accuracy, or equality to a complete native likelihood.

`Normalization.lean` proves integrability of the actual kernel and strict
positivity of its integral over the physical half-line. It defines the density
using the reciprocal of that integral, sets it to zero outside the gate, and
proves nonnegativity, integrability, integral one, and the unique constrained
mode. The normalization constant is constructed from the actual integral;
it is not a supplied hypothesis. Positive sigma is essential to prevent
Lean's undefined-integral convention from entering the construction.

`GaussianNormalization.lean` connects this construction to the actual Gaussian
probability density and physical-gate probability. For positive sigma it derives
`Z = σ*sqrt(2π)*Phi(μ/σ)` and identifies the density as the gated Gaussian PDF
divided by `Phi(μ/σ)`. Reflection supplies the gate probability; the PDF scaling
and integral supply the normalizer, with no assumed CDF identity.

`GaussianMeasure.lean` constructs a measure from the integral-derived density.
For positive sigma it derives total mass one and hence a probability law.
The constructed measure is absolutely continuous, has no negative support,
and gives every singleton, including zero, mass zero. Every interval `(0,ε]`
has positive mass for positive epsilon and sigma. A boundary density mode and
the random-offset frequency of obtaining that mode therefore differ from an
atom at zero. At zero sigma this integral construction gives a zero measure,
which is not the Dirac law of an actual zero-variance Gaussian.

`GaussianGatedCDF.lean` identifies the constructed law as the actual Gaussian
restricted to the physical gate and divided by its derived gate probability.
For positive sigma it proves the probability of every measurable event and
of each interval `(a,b]` with `0<=a<=b`. Its CDF is zero at all nonpositive
thresholds; for `x>=0` it is
`[Phi((x-mu)/sigma)-Phi(-mu/sigma)]/Phi(mu/sigma)`.
The CDF is strictly increasing on the physical half-line for every real mean,
including means whose density mode is at zero. These exact-real statements
retain the constant-prior premise and exclude a finite upper gate and sigma zero.

`GaussianQuantile.lean` derives continuity of the constructed law's CDF from
its absence of atoms. Its limit at infinity and the intermediate value theorem
then give exactly one positive finite coordinate for each probability level
`0<q<1`, for every real mean and positive sigma. No finite coordinate has CDF
one. The result supplies exact quantile existence and uniqueness; it does not
supply a numerical inversion algorithm or an error bound.

The library does not certify the floating-point density implementation, prove
MCMC convergence or numerical covariance accounting, or establish cosmological
data claims. A posterior interpretation retains the constant-prior premise.
A finite upper gate requires its own statement.

`AuditAxioms.lean` inspects every exported theorem's transitive dependencies.
The proofs use only `propext`, `Classical.choice`, and `Quot.sound`, with no
`sorry`, `admit`, or added axioms. No supplied maximizer hypothesis is presented
as an algorithm constructing one.
