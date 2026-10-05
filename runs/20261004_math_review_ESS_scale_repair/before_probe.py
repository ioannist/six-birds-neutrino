import json,numpy as np
from sbt_spt_audit.mcmc import ess_autocorr
v=np.sin(np.arange(512)/17.)
r={}
for label,scale in [('ordinary',1.),('large',1e200),('small',1e-200)]:
 try:
  with np.errstate(all='ignore'): r[label]={'ess':ess_autocorr(v*scale)}
 except Exception as e:r[label]={'error':type(e).__name__,'message':str(e)}
print(json.dumps(r,indent=2,allow_nan=False))
