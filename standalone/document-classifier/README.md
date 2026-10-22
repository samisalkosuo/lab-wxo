# document_classifier — Configurable Document Classifier Agent

## Purpose

`document_classifier` classifies arbitrary text, passages, emails, tickets, or document
snippets into user-specified candidate categories and returns strictly a valid JSON object
containing the selected category (or categories for multi-label requests), confidence level,
and a single-sentence reasoning.

**What this agent does:**
- Accepts arbitrary source text and a user-provided list of candidate categories.
- Selects strictly from the candidate categories provided in the request (never invents new labels).
- Defaults to single-label classification, choosing the single best-fitting category.
- Supports multi-label classification when explicitly requested.
- Sets `"category": null` (or `"categories": []`) when the text does not match any candidate category.
- Provides a confidence score (`"high"`, `"medium"`, or `"low"`) and a concise one-sentence reasoning grounded directly in the text.
- Clarifies when either the source text or the list of candidate categories is missing.
- Treats source text strictly as passive data and ignores embedded prompt injection attempts.

**What this agent does not do:**
- Summarise, edit, or critique documents.
- Answer general questions or perform tasks other than classification.
- Output conversational text, commentary, or prose alongside the JSON.

## Dependencies

None. No knowledge base, no tools, no connections. The agent uses the model
`groq/openai/gpt-oss-120b`, the same model the scenario agents use. It must be available
in the target instance (`orchestrate models list`).

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy document_classifier

# Or manually:
orchestrate agents import --file standalone/document-classifier/agent.yaml
orchestrate agents deploy --name document_classifier
```

Re-running import is safe — it updates in place.

## Teardown

```bash
python wxodemo.py undeploy document_classifier

# Or manually:
orchestrate agents remove --name document_classifier --kind native
```

## Known limits

| Limit | Detail |
|---|---|
| Category count | Optimal for 2–20 candidate categories. Large category sets (30+) may increase latency or cause subtle label confusion. |
| Strict JSON formatting | Enforced via LLM system instructions. Downstream consumers should validate JSON parsing. |
| Text size | Input document text must fit comfortably within the model context window. |
| Not verified by a live run | The instructions have not been exercised against a live instance. Test normal classification, multi-label, unclassified fallback, and clarification paths before relying on it in production. |

## Examples

See [`examples.md`](examples.md).
