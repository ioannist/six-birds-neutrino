"""Reconcile exact target coverage, edge controls and fresh transitive audit."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=ROOT/'lean/trunc_gauss_proof/TruncGaussProof/UpperGate.lean'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
text=source.read_text()
declarations=re.findall(r'^theorem\s+(\w+)',text,re.M)
assert len(declarations)==9
assert not re.search(r'\b(sorry|admit)\b|^\s*axiom\s',text,re.M)
assert 'ProbabilityTheory.cond ν (Set.Iic U)' in text
assert 'ν.real (Set.Ioi U) = 1 - cdf ν U' in text
assert 'cdf ν (min x U) / cdf ν U' in text
assert 'IsProbabilityMeasure ν' in text and 'hU : 0 < cdf ν U' in text
assert 'hσ : 0 < σ' in text and 'hU : 0 < U' in text
assert 'hq0 : 0 < q' in text and 'hq1 : q < 1' in text
assert '0 < x ∧ x < U' in text
formal=(HERE/'FormalSelfReview.lean').read_text()
assert len(re.findall(r'^example\b',formal,re.M))==10
assert not re.search(r'\b(sorry|admit)\b|^\s*axiom\s',formal,re.M)
assert not (HERE/'formal_self_review_stdout.txt').read_bytes()
assert not (HERE/'formal_self_review_stderr.txt').read_bytes()
assert 'Type mismatch' in (HERE/'attempt1_stdout.txt').read_text()
assert not (HERE/'attempt2_stdout.txt').read_bytes() and not (HERE/'attempt2_stderr.txt').read_bytes()
log=(HERE/'math_check_stdout.txt').read_text()
assert '175 passed' in log and 'Build completed successfully' in log
axioms=re.findall(r"'([^']+)' depends on axioms:\s*\[([^\]]*)\]",log)
assert len(axioms)==83 and len({n for n,_ in axioms})==83
assert all(set(a.strip() for a in values.split(','))<={'propext','Classical.choice','Quot.sound'} for _,values in axioms)
assert {f'TruncGaussProof.{n}' for n in declarations}.issubset({n for n,_ in axioms})
assert not (HERE/'math_check_stderr.txt').read_bytes()
assert not subprocess.check_output(['git','diff','ffdaf4b','--name-only','--','paper','docs/findings/canonical_results.json'],cwd=ROOT,text=True)
scope={
    'generic_law':'any actual probability measure on real coordinates, including atoms',
    'generic_retention':'cdf(U)>0 is explicit; the tail is probability strictly above U',
    'construction':'actual conditional measure; normalization and CDF are derived',
    'CDF_error':'nonnegative increase at most 1-F(U), attained at U',
    'Gaussian_specialization':'actual integral-normalized lower-gated Gaussian, arbitrary real mean, sigma>0, U>0',
    'quantile':'every 0<q<1 has exactly one x in (0,U), with original level q*F(U)',
    'not_inferred':['cosmological Gaussianity','small omitted tail','coordinate quantile-error bound','floating-point accuracy','MCMC convergence']}
with (HERE/'self_review_receipt.json').open('x') as f:
    f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reviewer':'self_review_no_independent_agent',
        'public_declarations':declarations,'exact_statement_scope':scope,'formal_edge_controls':10,
        'attempt1':{'session':84199,'exit_code':1,'scope':'numeral type mismatch, failed source retained'},
        'attempt2':{'session':11362,'exit_code':0},
        'formal_self_review':{'session':30670,'exit_code':0},
        'make_math_check':{'session':33426,'exit_code':0,'Python_tests':175,'Lean_public_axiom_outputs':83},
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [source,ROOT/'lean/trunc_gauss_proof/TruncGaussProof.lean',
            ROOT/'lean/trunc_gauss_proof/AuditAxioms.lean',HERE/'FormalSelfReview.lean']},
        'paper_or_main_claim_revision_adopted':False},indent=2,allow_nan=False)+'\n')
print('Self-review passes: nine actual-law theorems, ten edge controls, 175 Python tests and 83 public standard-axiom outputs.')
