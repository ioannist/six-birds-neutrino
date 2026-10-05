# CLASS finite numerical-Jacobian repair

`class-3.4.0-finite-jacobian.patch` applies to the CLASS 3.4.0 source shipped
with the installed `classy` distribution 3.4.0.1. The adjacent JSON file pins
the original source, patched source, and patch by SHA256.

At two archived cosmological coordinates, a numerical-Jacobian perturbation
crosses HyRec's frozen-helium cutoff and returns an infinite derivative.
The unmodified solver then produces nonfinite thermodynamics. For an
ungrouped column the patch retries that perturbation in the opposite
direction, keeping the corresponding signed denominator. It applies the
same rule to the larger roundoff-control perturbation. Nonfinite base
values, unsuccessful retries, and nonfinite dense derivative quotients
produce explicit errors. A nonfinite grouped sparse trial produces an
error; it cannot be retried as a single column. Callback errors propagate.
Physical derivative formulas and species cutoffs are unchanged.

This is a numerical repair with pointwise validation. At a cutoff the
recovered finite difference describes the frozen branch; it does not
establish differentiability across the cutoff, a global ODE error bound,
or posterior convergence. The checked quadrature-only control retains
bit-identical spectra. Two selected archived parent rows retain exactly
their six likelihood components, prior, and posterior.

Preparation and build records are in
`runs/20261004_math_review_class_python_repair`. `prepare_backend.py` copies
the original installed package to a separate directory and checks the
original source hash before creating the patch. It refuses to overwrite
the existing private build. The original installed extension is untouched.
The private build uses `make -j2 libclass.a` in the copied package and
`build_extension.py build_ext --build-lib <overlay> --build-temp <temp>`
with Cython 3.0.12 available from a private build dependency directory.
The build receipt pins all 125 copied source/resource files and the native
extension hash; build logs preserve the compiler commands.

Run the native regression suite against a built package with:

```sh
python3 tests/native/run_class_numjac_guard.py --class-dir /path/to/classy
```

The seven cases check a smooth derivative, both perturbation stages at a
cutoff, recovery of a small slope, failure in both directions, callback
error propagation, rejection of a nonfinite base, and grouped sparse
failure. The test links the actual supplied `libclass.a`.
An isolated control links the same fixture to `numjac` compiled from the
unmodified source. Its smooth and callback-error cases pass; the three
completed cutoff cases fail. The process then exits with SIGSEGV during
the nonfinite-base case, before reaching the grouped case. The repaired
implementation completes all seven. Raw output and the exact process
result are preserved in `original_native_regression_receipt.json` in the
build records. This fixture result is distinct from the archived native
cosmological tight-coupling failures.

The separate seed-1201 trial imports the private package through
`PYTHONPATH` and pins its native module before launching. It uses a fresh
output prefix and RNG stream, the parent's physical target and seven
precision settings, and the last saved parent point only as an initializer.
Do not append or pool the unmodified-backend history with this trial.

The four canonical CLASS recipes declare this build in
`notes.classy_backend`. `scripts/run_cobaya.py` and
`scripts/eval_cmb_plancksubset_desi.py` verify the imported native extension's
SHA256 and location against the build receipt before creating output. They
then force Cobaya to use the verified Python import with `path: global`; a
conflicting explicit theory path is rejected. Sampling bundles record the
module and receipt hashes in `solver_backend.json`; reference evaluations
record them with each result. On this machine select the private build with:

```sh
export PYTHONPATH=/mnt/8tb/six-birds-ml/tmp/neutrino_class_finite_jacobian_20261004/python_backend:/home/repos/six-birds-neutrino/src
```

A rebuild or relocation requires a new validated build receipt and updated
contract. The existing receipt identifies the current machine's native build.
Legacy configurations without a contract retain their historical loading
behavior for reproduction. Thirty archived parent endpoints and thirty fresh
replacement endpoints have been checked against the guarded targets; this
remains selected-point evidence rather than a uniform accuracy certificate.
