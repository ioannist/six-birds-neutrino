#define _GNU_SOURCE
#include <execinfo.h>
#include <fenv.h>
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

/* Loaded only into the separate diagnostic executable, never into inference. */
static void invalid_operation(int signal_number, siginfo_t *information, void *context) {
  void *frames[64];
  int count;
  (void)context;
  dprintf(STDERR_FILENO, "FIRST_INVALID_OPERATION signal=%d code=%d address=%p\n",
          signal_number, information->si_code, information->si_addr);
  count = backtrace(frames, 64);
  backtrace_symbols_fd(frames, count, STDERR_FILENO);
  _exit(128 + signal_number);
}

__attribute__((constructor)) static void enable_invalid_trace(void) {
  struct sigaction action = {0};
  action.sa_sigaction = invalid_operation;
  action.sa_flags = SA_SIGINFO;
  sigemptyset(&action.sa_mask);
  sigaction(SIGFPE, &action, NULL);
  feenableexcept(FE_INVALID);
}
