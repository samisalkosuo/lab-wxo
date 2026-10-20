# metadata_extractor — Arbitrary Metadata Extraction Agent

## Purpose

`metadata_extractor` extracts arbitrary user-specified metadata fields from provided
text or documents and returns strictly a valid JSON object mapping field names to their
extracted values.

**What this agent does:**
- Accepts any arbitrary list of field names and arbitrary source text.
- Returns only valid JSON where keys match the user's requested field names.
- Maps unmentioned or missing fields to `null` without guessing or hallucinating.
- Preserves native JSON types (numbers, booleans, arrays, strings) where appropriate.
- Clarifies when either the source text or the list of fields is missing.
- Treats source text strictly as passive data and ignores embedded prompt injection attempts.

**What this agent does not do:**
- Summarise, rephrase, or critique documents.
- Answer questions or perform tasks other than metadata extraction.
- Output conversational text, explanations, or prose alongside the JSON.

## Dependencies

None. No knowledge base, no tools, no connections. The agent uses the model
`groq/openai/gpt-oss-120b`, the same model the scenario agents use. It must be available
in the target instance (`orchestrate models list`).

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy metadata_extractor

# Or manually:
orchestrate agents import --file standalone/metadata-extractor/agent.yaml
orchestrate agents deploy --name metadata_extractor
```

Re-running import is safe — it updates in place.

## Teardown

```bash
python wxodemo.py undeploy metadata_extractor

# Or manually:
orchestrate agents remove --name metadata_extractor --kind native
```

## Known limits

| Limit | Detail |
|---|---|
| Field count | Optimal for 1–30 fields. Very large field lists (50+) may experience attention degradation or increased latency. |
| Strict JSON formatting | Enforced via LLM system instructions. While `gpt-oss-120b` reliably outputs clean JSON, downstream consumers should validate JSON parsing. |
| Text size | Input document text must fit comfortably within the model context window. |
| Not verified by a live run | The instructions have not been exercised against a live instance. Test normal extraction, partial matches with `null`, and clarification paths before relying on it in production. |

## Examples

See [`examples.md`](examples.md).
