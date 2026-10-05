"""Replay the pre-repair CLI against the same ordinary and scaled normal fixtures."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import diagnose_cobaya_chains
spec=importlib.util.spec_from_file_location('diagnose_before',HERE/'diagnose_before.py')
before=importlib.util.module_from_spec(spec);spec.loader.exec_module(before)
samples=[x for x in np.random.default_rng(20261004).normal(size=(4,2000))]
records=[]
for label,power in [('ordinary',0),('large',700),('tiny',-700)]:
 command=['diagnose']
 for seed,x in enumerate(samples,101):
  run=HERE/'fixtures'/label/str(seed);(run/'chains').mkdir(parents=True)
  prefix=run/'chains'/'sample'
  cfg={'output':str(prefix),'likelihood':{},'theory':{},'params':{'x':{'prior':{'dist':'norm','loc':0,'scale':float(np.ldexp(1.,power))}}},'sampler':{'mcmc':{'seed':seed}}}
  (run/'resolved.yaml').write_text(yaml.safe_dump(cfg))
  np.savetxt(str(prefix)+'.1.txt',np.column_stack([np.ones(x.size),x*x/2+power*np.log(2.)+np.log(2*np.pi)/2,np.ldexp(x,power)]),header='weight minuslogpost x')
  command+=['--run-dir',str(run)]
 old=HERE/(label+'_before.json');new=HERE/(label+'_after.json')
 for module,output in [(before,old),(diagnose_cobaya_chains,new)]:
  sys.argv=command+['--burnin-frac','0','--output',str(output)]
  with np.errstate(all='ignore'):assert module.main()==0
 b=json.loads(old.read_text())['diagnostics']['x'];a=json.loads(new.read_text())['diagnostics']['x']
 assert a['diagnostic_thresholds_pass']
 if power:assert 'error' in b and not b['diagnostic_thresholds_pass']
 else:assert b['diagnostic_thresholds_pass']
 records.append({'fixture':label,'binary_exponent':power,'before_pass':b['diagnostic_thresholds_pass'],'before_error':b.get('error'),'after_pass':a['diagnostic_thresholds_pass'],'after_limit':a['quantile_mcse_limit'],'before_report_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'after_report_sha256':hashlib.sha256(new.read_bytes()).hexdigest()})
with (HERE/'probe_receipt.json').open('x') as f:f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'scope':'known_normal_draws_under_exact_power_of_two_coordinate_changes','records':records,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2,allow_nan=False)+'\n')
print(json.dumps(records,indent=2))
