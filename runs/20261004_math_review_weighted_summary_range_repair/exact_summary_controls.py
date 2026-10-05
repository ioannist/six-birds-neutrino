"""Independent Fraction sums and interval-membership oracle for weighted summaries."""
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import extract_mnu_limits as reader
values_sets=[np.array(v) for v in [[0,0,.5,.5,1,1],[0,0,np.nextafter(0.,1.),np.nextafter(0.,1.),2*np.nextafter(0.,1.),2*np.nextafter(0.,1.)],[1e308,1e308,1.25e308,1.25e308,1.5e308,1.5e308],[-1e308,-1e308,0,0,1e308,1e308],[1,1,1+2.**-52,1+2.**-52,1+2.**-51,1+2.**-51],[-1,-1,-.5,-.5,0,0]]]
weights_sets=[np.array([1,1,2,2,3,3]),np.ldexp(np.array([1,1,.5,.5,1.5,1.5]),1023),np.array([1e308,1e-300,1e308,1e-300,2e-300,3e-300]),np.ldexp(np.array([1,1,2,2,3,3]),-1000)]
records=[]
for values in values_sets:
 for weights in weights_sets:
  exact_weights=[Fraction(float(w)) for w in weights]
  for bins in [2,3,7,60]:
   with np.errstate(over='ignore',invalid='ignore',under='ignore'):
    edges=np.linspace(float(values.min()),float(values.max()),bins+1)
   if not np.isfinite(edges).all():
    lo,hi=Fraction(float(values.min())),Fraction(float(values.max()))
    edges=np.array([float(((bins-k)*lo+k*hi)/bins) for k in range(bins+1)])
   bin_masses=[]
   for j in range(bins):
    bin_masses.append(sum((w for v,w in zip(values,exact_weights) if edges[j]<=v and
                           (v<edges[j+1] or (j==bins-1 and v==edges[j+1]))),Fraction(0)))
   selected=bin_masses.index(max(bin_masses))
   expected=float((Fraction(float(edges[selected]))+Fraction(float(edges[selected+1])))/2)
   actual=reader._weighted_hist_mode(values,weights,bins)
   assert actual==expected,(values,weights,bins,expected,actual)
   fractions=[]
   for threshold in [-np.inf,-1.,0.,.001,.5,1.,np.inf]:
    numerator=sum((w for v,w in zip(values,exact_weights) if v<=threshold),Fraction(0))
    total=sum(exact_weights);ratio=numerator/total;rounded=float(ratio)
    endpoint_loss=0<ratio<1 and rounded in [0.,1.]
    if endpoint_loss:
     try:reader._weighted_boundary_fraction(values,weights,threshold)
     except ValueError:pass
     else:raise AssertionError('Positive event/complement mass lost at rounded endpoint')
    else:assert reader._weighted_boundary_fraction(values,weights,threshold)==rounded
    fractions.append({'threshold':str(threshold),'endpoint_loss_refused':endpoint_loss})
   records.append({'values':[float(v) for v in values],'weights':[float(w) for w in weights],
                   'bins':bins,'histogram_mode':actual,'boundary_fraction_controls':fractions})
assert len(records)==96
with (HERE/'exact_summary_controls_receipt.json').open('x') as f:
 f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'records':records,'histogram_controls':96,
                    'boundary_fraction_controls':672,'independent_Fraction_oracle':'interval membership with exact rational sums; no shared integer mass helper',
                    'reader_source_sha256':hashlib.sha256((ROOT/'scripts/extract_mnu_limits.py').read_bytes()).hexdigest(),
                    'uniform_floating_accuracy_certified':False},indent=2)+'\n')
print('96 exact histogram controls and 672 boundary-fraction controls pass.')
