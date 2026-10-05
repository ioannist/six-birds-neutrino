- run_name: math_restoration_B_seed505
- config: /home/repos/six-birds-neutrino/runs/20261003_math_review_cmb_desi_chain_configs/B_seed505.yaml
- output_prefix: /home/repos/six-birds-neutrino/runs/20261003_math_review_cmb_chain_B_seed505/chains/math_restoration_B_seed505
- cobaya_success: False
- extraction_success: False
- metrics_path: missing
- error: CosmoComputationError: 

Error in Class: operator()(L:1047) :error in perturbations_solve(ppr, pba, pth, ppt, index_md, index_ic, index_k, &pw);
=>perturbations_solve(L:3210) :error in perturbations_vector_init(ppr, pba, pth, ppt, index_md, index_ic, k, interval_limit[index_interval], ppw, previous_approx);
=>perturbations_vector_init(L:4602) :condition (ppw->approx[ppw->index_ap_tca] == (int)tca_off) is true; scalar initial conditions assume tight-coupling approximation turned on
