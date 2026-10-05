"""Verify review coverage and its evidence; do not certify withdrawn physics claims."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

# Redacted before publication: the original also checked the owner's review instruction,
# read from a private local AI-agent attachment.
assert git("cat-file", "-t", "ffdaf4b") == "commit"
subprocess.run(["git", "merge-base", "--is-ancestor", "ffdaf4b", "HEAD"], cwd=ROOT, check=True)
assert not git("diff", "ffdaf4b", "--name-only", "--", "paper", "docs/findings/canonical_results.json")

state_path = ROOT / "runs/20261003_math_review_validation/review_state.json"
state = read(state_path)
assert state["pre_review_checkpoint"] == "ffdaf4b" and not state["paper_modified"]
assert state["pytest_passed"] == 245
inventory = read(HERE / "statement_inventory.json")
sections = sorted((ROOT / "paper/sections").glob("*.tex"))
labels = [label for path in sections for label in re.findall(r"\\label\{(eq:[^}]+)\}", path.read_text())]
assert len(sections) == 11 and len(labels) == len(set(labels)) == 11
assert set(labels) == {item["label"] for item in inventory["equations"]}
for item in inventory["equations"]:
    assert item["premises_and_limits"] and (ROOT / item["implementation_or_formalization"]).is_file()
for item in inventory["additional_mathematical_claims"]:
    assert item["limits"] and (ROOT / item["evidence"]).is_file()

lean = ROOT / "lean/trunc_gauss_proof"
public = []
lean_files = sorted((lean / "TruncGaussProof").glob("*.lean"))
for path in lean_files:
    source = path.read_text()
    assert not re.search(r"\b(?:sorry|admit)\b|^\s*axiom\s", source, re.M)
    public.extend(re.findall(r"^(?:theorem|lemma)\s+(\w+)", source, re.M))
assert len(lean_files) == 15 and len(public) == len(set(public)) == 97
requests = re.findall(r"^#print axioms TruncGaussProof\.(\w+)", (lean / "AuditAxioms.lean").read_text(), re.M)
packet = ROOT / "runs/20261005_math_review_paired_readout_error_bound"
axioms_path = packet / "axioms_stdout.txt"
outputs = re.findall(r"'TruncGaussProof\.(\w+)' depends on axioms: \[([^]]*)\]", axioms_path.read_text())
assert set(public) == set(requests) == {name for name, _ in outputs}
assert len(requests) == len(outputs) == 97
allowed = {"propext", "Classical.choice", "Quot.sound"}
assert all(set(a.strip() for a in axioms.split(",") if a.strip()) <= allowed for _, axioms in outputs)
proof_receipt = read(packet / "self_review_receipt.json")
assert sha(lean / "TruncGaussProof/Readout.lean") == proof_receipt["source_sha256"]
assert sha(lean / "TruncGaussProof.lean") == proof_receipt["root_import_sha256"]
assert sha(lean / "AuditAxioms.lean") == proof_receipt["axiom_requests_sha256"]
assert sha(axioms_path) == proof_receipt["axiom_output_sha256"]
assert not git("diff", "752e8ab", "--name-only", "--", "lean")
proof_execution = read(packet / "execution_receipt.json")
assert all(proof_execution[key] == 0 for key in (
    "build_actual_terminal_exit_code", "axiom_actual_terminal_exit_code",
    "false_target_actual_terminal_exit_code", "self_review_direct_exit_code"))
manifest = read(lean / "lake-manifest.json")
dependencies = []
for package in manifest["packages"]:
    path = lean / ".lake/packages" / package["name"]
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    assert head == package["rev"]
    assert not subprocess.check_output(["git", "-C", str(path), "status", "--short", "--untracked-files=no"], text=True).strip()
    dependencies.append({"name": package["name"], "verified_commit": head})

repair = ROOT / "runs/20261005_math_review_template_rewrite_repair"
execution = read(repair / "final_execution_receipt.json")
assert execution["full_Python_suite"]["actual_terminal_exit_code"] == 0
assert execution["full_Python_suite"]["passed"] == 245
assert sha(ROOT / "scripts/run_template_rewrite.py") == execution["current_source_sha256"]
assert sha(ROOT / "tests/test_template_rewrite_numerics.py") == execution["regression_tests_sha256"]
assert "245 passed" in (ROOT / state["latest_python_check"]).read_text()
changed = set(git("diff", "edba123", "--name-only", "--", "src", "scripts", "tests").splitlines())
assert changed <= {"scripts/run_template_rewrite.py", "tests/test_template_rewrite_numerics.py"}
review = read(repair / "final_self_review_receipt.json")
assert review["ordinary_controls_count"] == 80 and len(review["extreme_representable_quadratic_controls"]) == 2
assert review["current_source_sha256"] == execution["current_source_sha256"]
assert execution["distinct_self_review_final_direct_exit_code"] == 0
cli = read(repair / "cli_controls_receipt.json")
assert len(cli["records"]) == 2 and all(r["actual_exit_code"] == 0 for r in cli["records"])
assert cli["strict_JSON_outputs_verified"] and not cli["fitting_or_cosmological_sampling_launched"]
for record in cli["records"]:
    output_dir = Path(record["command"][record["command"].index("--outdir") + 1])
    assert sha(output_dir / "metrics.json") == record["metrics_sha256"]

shutdown = ROOT / "runs/20261005_math_review_user_directed_restoration_shutdown"
runtime = read(shutdown / "final_runtime_verification.json")
terminal_review = read(shutdown / "terminal_final_seal_review.json")
assert runtime["registered_families"] == runtime["terminal_families"] == 80
assert runtime["owned_live_samplers"] == 0
assert sha(shutdown / "final_runtime_verification.json") == terminal_review["terminal_ledger_sha256"]
assert terminal_review["weighted_histories_recounted"] == 61
campaign = state["claim_restoration_sampling_campaign"]
assert not campaign["further_sampling_to_recover_original_claims_authorized"]
assert state["SPT_headline_magnitude_revision_decision"]["current_qualified_numeric_replacement_available"] is False
assert state["SPT_headline_magnitude_revision_decision"]["historical_near_0p030_native_qualification_suspended"]
disposition = read(shutdown / "claim_disposition.json")
assert len(disposition["claims"]) == 8 and not disposition["paper_modified"]

source_groups = {
    "original_paper_sections_and_tables": sections + sorted((ROOT / "paper/tables").glob("*.tex")) + [ROOT / "paper/main.tex"],
    "formal_statements_and_drivers": lean_files + [lean / "TruncGaussProof.lean", lean / "AuditAxioms.lean", lean / "lean-toolchain", lean / "lake-manifest.json"],
    "numerical_library": sorted((ROOT / "src").rglob("*.py")),
    "numerical_and_integration_scripts": sorted((ROOT / "scripts").glob("*.py")),
    "regression_and_native_controls": sorted((ROOT / "tests").rglob("*.py")) + sorted((ROOT / "tests/native").glob("*.c")),
    "declared_configurations": sorted((ROOT / "configs").rglob("*.yaml")),
}
source_inventory = {group: [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in paths]
                    for group, paths in source_groups.items()}
with (HERE / "source_inventory.json").open("x") as output:
    json.dump(source_inventory, output, indent=2)
    output.write("\n")
requirements = [
    {"requirement": "Checkpoint before review", "status": "verified", "evidence": "ffdaf4b is an existing ancestor checkpoint; the original review record and retained source history identify it as pre-review."},
    {"requirement": "Thorough mathematical statement and applicability review", "status": "verified",
     "evidence": "All11 displayed equation labels and five additional mathematical families are mapped to actual premises, implementation/proof and limits; the full review report covers Gaussian, covariance, profiling, BAO, posterior and native-backend issues."},
    {"requirement": "Correct mechanizations without hidden axioms or substituted targets", "status": "verified",
     "evidence": "All97 public declarations match97 successful dependency outputs and requests; unchanged sources, actual terminal build/check receipts and all pinned clean package commits are checked. Statement coverage retains explicit supplied hypotheses."},
    {"requirement": "Repair mathematical implementation errors and verify them", "status": "verified",
     "evidence": "245-test current suite, preserved failing controls, native/provenance ledgers and distinct self-reviews; latest toy repair also has80 exact-rational comparisons and both actual CLI modes. No uniform floating or physical certificate is inferred."},
    {"requirement": "Retain claim strength where support permits; discuss material downgrades", "status": "verified",
     "evidence": "Conditional mathematical coverage strengthened from the original two lemmas to97 declarations. Main magnitude/localization problems and alternatives were discussed; the user then directed dropping attempts to justify wrong or likely wrong claims. Current disposition withdraws unsupported/broad empirical claims without asserting unsupported numerical disproof."},
    {"requirement": "No smuggling or misinterpretation", "status": "verified_with_explicit_evidence_limits",
     "evidence": "Empirical summaries, signed covariance allocations, best-found endpoints, supplied error premises and local native controls keep distinct roles. The suspended historical near0.030eV readout is withheld. No current qualified mass replacement, optimizer/global proof, independence/PRNG proof, null calibration or packaging-only causal attribution is claimed."},
    {"requirement": "Do not edit the paper; leave manuscript revision for later", "status": "verified",
     "evidence": "Entire paper tree and canonical results are byte-identical in Git to ffdaf4b; the later manuscript phase remains excluded from this review."},
    {"requirement": "Honor the subsequent withdrawal of claim-rescue work", "status": "verified",
     "evidence": "All61 then-live owned samplers have actual terminal exits and frozen outputs; all80 registrations and20 cohort memberships remain accounted for. Restoration obligations and obsolete magnitude options are preserved historically and superseded in current state."},
]
with (HERE / "completion_audit.json").open("x") as output:
    json.dump({"utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Completion of the requested mathematical/code/Lean review and repairs, with the user's evidence-led withdrawal of claim restoration. Not approval of the original manuscript as written.",
        "instruction_sha256": sha(instruction), "requirements": requirements,
        "paper_equation_labels_covered": labels, "public_formal_declarations_covered": 97,
        "Python_tests_passed": 245, "pinned_dependencies_verified": dependencies,
        "statement_inventory_sha256": sha(HERE / "statement_inventory.json"),
        "source_inventory_sha256": sha(HERE / "source_inventory.json"),
        "scientific_results_withheld": ["advertised posterior-tightening magnitudes", "historical suspended near0.030eV replacement", "broad full-CMB TT dominance", "uniform solver/CDF/tail accuracy", "global optimizer or causal packaging identification"],
        "known_required_work_remaining_in_requested_review": [],
        "later_phase": "Edit the paper to adopt supported conditional/scoped content and remove unsupported empirical claims.",
        "independent_external_review_performed": False,
        "distinct_self_review_performed": True,
        "original_empirical_claims_validated": False,
        "review_completion_requirements_satisfied": True}, output, indent=2)
    output.write("\n")
print("Review completion audit passed: 11 equations, 97 Lean declarations, 245 Python tests; withdrawn physics claims remain unvalidated.")
