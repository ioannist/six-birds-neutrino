/* Exercise the actual pinned CLASS transfer_get_l_list implementation. */
#include "transfer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
  struct precision precision = {0};
  struct perturbations perturbations = {0};
  struct transfer transfer = {0};
  if (argc != 4) return 2;
  precision.l_logstep = strtod(argv[1], NULL);
  precision.l_linstep = 3;
  transfer.angular_rescaling = strtod(argv[2], NULL);
  perturbations.has_cls = _TRUE_;
  perturbations.has_scalars = _TRUE_;
  perturbations.has_cl_cmb_temperature = _TRUE_;
  perturbations.l_scalar_max = atoi(argv[3]);
  /* Zero mode count isolates list construction from mode/type bookkeeping. */
  if (transfer_get_l_list(&precision, &perturbations, &transfer) != _SUCCESS_) {
    fprintf(stderr, "%s\n", transfer.error_message);
    return 3;
  }
  int consecutive = transfer.l_size_max == perturbations.l_scalar_max - 1;
  for (int i = 0; i < transfer.l_size_max; ++i)
    consecutive &= transfer.l[i] == i + 2;
  printf("{\"logstep\":%.17g,\"rescaling\":%.17g,\"lmax\":%d,"
         "\"count\":%d,\"consecutive\":%s}\n",
         precision.l_logstep, transfer.angular_rescaling,
         perturbations.l_scalar_max, transfer.l_size_max,
         consecutive ? "true" : "false");
  free(transfer.l);
  return 0;
}
