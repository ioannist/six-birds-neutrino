# Redactions before publication

The following review artifacts were edited before publication to remove AI-agent
tool-call transcript content, paths to private local agent session files, and a
verbatim quotation of the owner's chat instruction:

| File | Change |
| --- | --- |
| `20261004_math_review_sampler_session_provenance/primary_tool_evidence.json` | Tool-call inputs and call identifiers replaced by a redaction marker; program outputs, exit codes, timestamps and process numbers retained. |
| `20261004_math_review_sampler_session_provenance/verify_primary_receipts.py` | Path to the private agent session log and call identifiers replaced by placeholders (the script cannot be re-run without that log). |
| `20261005_math_review_completion_audit/audit_completion.py`, `20261005_math_review_completion_audit_v2/audit_completion.py` | Removed the check that read the owner's review instruction from a private agent attachment. |
| `20261003_math_review_validation/review_state.json`, `20261005_math_review_user_directed_restoration_shutdown/claim_disposition.json`, `20261005_math_review_user_directed_restoration_shutdown/freeze_terminal.py`, `../docs/findings/math_review.md` | Verbatim quotation of the owner's instruction replaced by a paraphrase. |

SHA-256 values recorded in other receipts for these files refer to their
pre-redaction content. No numerical result, likelihood evaluation, chain or
diagnostic was changed.
