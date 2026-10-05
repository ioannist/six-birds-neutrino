"""Bind kernel checks to the actual claims, premises and false-target controls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LIB = ROOT / "lean/trunc_gauss_proof"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source = LIB / "TruncGaussProof/Readout.lean"
text = source.read_text()
new_names = re.findall(r"^theorem\s+(\S+)", text, re.M)
assert len(new_names) == len(set(new_names)) == 8
declared = []
for module in (LIB / "TruncGaussProof").glob("*.lean"):
    declared.extend(re.findall(r"^(?:theorem|lemma)\s+([^\s(\[{]+)", module.read_text(), re.M))
assert len(declared) == len(set(declared)) == 97
audit_source = (LIB / "AuditAxioms.lean").read_text()
requested = re.findall(r"#print axioms TruncGaussProof\.([^\s]+)", audit_source)
assert len(requested) == len(set(requested)) == 97 and set(requested) == set(declared)
raw = (HERE / "axioms_stdout.txt").read_text()
outputs = re.findall(r"'TruncGaussProof\.([^']+)' depends on axioms: \[([^]]*)\]", raw, re.S)
assert len(outputs) == len({name for name, _ in outputs}) == 97
assert {name for name, _ in outputs} == set(requested)
all_axioms = set()
for _, body in outputs:
    axioms = {value.strip() for value in body.split(",") if value.strip()}
    assert axioms <= {"propext", "Classical.choice", "Quot.sound"}
    all_axioms.update(axioms)
assert all_axioms == {"propext", "Classical.choice", "Quot.sound"}
assert not re.search(r"\b(?:sorry|admit|axiom)\b", text)
assert "Readout" in (LIB / "TruncGaussProof.lean").read_text()
assert not (HERE / "build_stderr.txt").read_bytes()
assert not (HERE / "axioms_stderr.txt").read_bytes()
assert not (HERE / "false_targets_stdout.txt").read_bytes()
assert not (HERE / "false_targets_stderr.txt").read_bytes()
assert "Build completed successfully" in (HERE / "build_stdout.txt").read_text()
control = (HERE / "FalseTargets.lean").read_text()
assert len(re.findall(r"^example\s*:", control, re.M)) == 4
assert "exact tighteningReadout_error_le" in control
assert "Real.sqrt" in control and "max (1 : ℝ) 1" in control
assert "εA + εB ≤ tighteningReadout" in control
assert not re.search(r"\b(?:sorry|admit|axiom)\b", control)
repair = json.loads((HERE / "source_repair_receipt.json").read_text())
original = (HERE / "first_attempt_Readout.lean").read_text()
assert sha(HERE / "first_attempt_Readout.lean") == repair["original_sha256"]
for before, after in repair["changes"]:
    assert original.count(before) == 1
    original = original.replace(before, after, 1)
assert original == text and sha(source) == repair["repaired_source_sha256"]
roles = {
    "coordinate_inputs": "Two supplied absolute errors for fixed real true/estimated quantile coordinates.",
    "derived_error_interval": "Algebra and triangle inequality give error at most epsilonA+epsilonB.",
    "derived_positive_direction": "Strictly larger measured shift than the summed actual errors implies positive true shift.",
    "sharpness": "Four strictly positive coordinates attain the summed bound; no density or posterior is constructed.",
    "risk_inputs": "A common measurable space, measure and supplied marginal failure bounds; probabilities require a probability law.",
    "derived_risk": "Paired failure is contained in the marginal union, so measure subadditivity gives summed risk.",
    "measurability": "Measurable estimators give a measurable paired-failure event.",
    "absent_inputs": "MCSE is not an absolute error or calibrated failure probability; no sampler or physical error bridge is supplied.",
    "false_targets": "Imported sum mechanism accepts a sharp witness; max, quadrature and non-strict sign margin are refuted on it.",
}
with (HERE / "self_review_receipt.json").open("x") as f:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "distinct_self_review_not_independent_agent", "new_theorems": new_names,
        "all_public_theorem_and_lemma_axiom_outputs_checked": 97,
        "only_standard_axioms": sorted(all_axioms), "roles": roles,
        "source_sha256": sha(source), "root_import_sha256": sha(LIB / "TruncGaussProof.lean"),
        "axiom_requests_sha256": sha(LIB / "AuditAxioms.lean"),
        "axiom_output_sha256": sha(HERE / "axioms_stdout.txt"),
        "false_target_source_sha256": sha(HERE / "FalseTargets.lean"),
        "conditional_inputs_not_reported_as_constructed": True,
        "independence_not_required_or_inferred": True,
        "RMS_MCSE_and_absolute_coordinate_errors_not_identified": True,
        "no_current_cosmological_readout_qualified": True,
        "paper_or_main_claim_revision_adopted": False}, f, indent=2, allow_nan=False)
    f.write("\n")
print("Eight readout laws reviewed; all 97 public theorem axiom outputs bound, with four hinge controls.")
