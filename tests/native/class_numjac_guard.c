#include "evolver_ndf15.h"

enum scenario { SMOOTH, UPPER_CUTOFF, BOTH_NONFINITE, CALLBACK_ERROR, NONFINITE_BASE };

struct fixture {
  enum scenario scenario;
  double base, scale, offset;
  int calls, nonfinite_trials, size;
};

static int derivative(double t, double *y, double *dy, void *workspace, ErrorMsg error) {
  struct fixture *fixture = workspace;
  int i;
  (void)t;
  fixture->calls++;
  if (fixture->scenario == CALLBACK_ERROR && y[0] != fixture->base) {
    snprintf(error, _ERRORMSGSIZE_, "fixture callback reports an error");
    return _FAILURE_;
  }
  dy[0] = fixture->offset + fixture->scale * y[0];
  if ((fixture->scenario == UPPER_CUTOFF && y[0] > 1.) ||
      (fixture->scenario == BOTH_NONFINITE && y[0] != fixture->base)) {
    dy[0] = INFINITY;
    fixture->nonfinite_trials++;
  }
  for (i=1;i<fixture->size;i++) dy[i] = y[i];
  return _SUCCESS_;
}

static int dense_case(const char *name, enum scenario scenario, double base,
                      double scale, double offset, int success, double expected,
                      double tolerance, int minimum_nonfinite_trials) {
  struct jacobian jacobian;
  struct numjac_workspace workspace;
  struct fixture fixture = {scenario, base, scale, offset, 0, 0, 1};
  ErrorMsg error;
  double y[2] = {0., base}, f[2] = {0., offset + scale * base};
  int evaluations = 0, status, ok;
  error[0] = '\0';
  if (initialize_jacobian(&jacobian, 1, error) != _SUCCESS_ ||
      initialize_numjac_workspace(&workspace, 1, error) != _SUCCESS_) return 1;
  if (scenario == NONFINITE_BASE) f[1] = NAN;
  status = numjac(derivative, 0., y, f, &jacobian, &workspace,
                  1e-15, 1, &evaluations, &fixture, error);
  ok = (status == (success ? _SUCCESS_ : _FAILURE_));
  if (success) {
    ok = ok && isfinite(jacobian.dfdy[1][1]) &&
         fabs(jacobian.dfdy[1][1] - expected) <= tolerance &&
         fixture.calls == evaluations;
  }
  else {
    ok = ok && error[0] != '\0';
  }
  ok = ok && fixture.nonfinite_trials >= minimum_nonfinite_trials;
  if (scenario == CALLBACK_ERROR) ok = ok && fixture.calls == 1 && fixture.nonfinite_trials == 0;
  if (scenario == NONFINITE_BASE) ok = ok && fixture.calls == 0;
  printf("{\"case\":\"%s\",\"status\":%d,\"calls\":%d,\"nfe\":%d,\"nonfinite_trials\":%d,\"ok\":%s}\n",
         name,status,fixture.calls,evaluations,fixture.nonfinite_trials,ok ? "true" : "false");
  uninitialize_numjac_workspace(&workspace);
  uninitialize_jacobian(&jacobian);
  return !ok;
}

static int grouped_case(void) {
  struct jacobian jacobian;
  struct numjac_workspace workspace;
  struct fixture fixture = {UPPER_CUTOFF, 1.-1e-8, 0., 0., 0, 0, 16};
  ErrorMsg error;
  double y[17], f[17];
  int i, status, evaluations = 0, ok;
  error[0] = '\0';
  if (initialize_jacobian(&jacobian, 16, error) != _SUCCESS_ ||
      initialize_numjac_workspace(&workspace, 16, error) != _SUCCESS_) return 1;
  y[0] = f[0] = 0.; y[1] = fixture.base; f[1] = 0.;
  for (i=2;i<=16;i++) y[i] = f[i] = 0.4;
  /* Independent diagonal columns share one grouped finite-difference trial. */
  for (i=0;i<16;i++) {
    jacobian.spJ->Ap[i] = i;
    jacobian.spJ->Ai[i] = i;
    jacobian.spJ->Ax[i] = 1.;
  }
  jacobian.spJ->Ap[16] = 16;
  jacobian.repeated_pattern = jacobian.trust_sparse;
  status = numjac(derivative, 0., y, f, &jacobian, &workspace,
                  1e-15, 16, &evaluations, &fixture, error);
  ok = status == _FAILURE_ && error[0] != '\0' && fixture.calls == 1 && evaluations == 1;
  printf("{\"case\":\"nonfinite_grouped_trial_errors\",\"status\":%d,\"calls\":%d,\"nfe\":%d,\"ok\":%s}\n",
         status,fixture.calls,evaluations,ok ? "true" : "false");
  uninitialize_numjac_workspace(&workspace);
  uninitialize_jacobian(&jacobian);
  return !ok;
}

int main(void) {
  int failures = 0;
  failures += dense_case("smooth_linear_control", SMOOTH, 0.4, 3., 0., 1, 3., 1e-7, 0);
  failures += dense_case("primary_and_refined_cutoff_retries", UPPER_CUTOFF, 1.-1e-8, 0., 0., 1, 0., 0., 2);
  failures += dense_case("refined_cutoff_retry_recovers_small_slope", UPPER_CUTOFF, 1.-1e-7, 1e-9, 1., 1, 1e-9, 1e-11, 1);
  failures += dense_case("both_directions_nonfinite_error", BOTH_NONFINITE, 0.4, 0., 0., 0, 0., 0., 2);
  failures += dense_case("callback_failure_propagated", CALLBACK_ERROR, 0.4, 0., 0., 0, 0., 0., 0);
  failures += dense_case("nonfinite_base_rejected", NONFINITE_BASE, 0.4, 0., 0., 0, 0., 0., 0);
  failures += grouped_case();
  return failures ? 1 : 0;
}
