# language-detector — Language Detection Agent

## Purpose

`language_detector` analyses any text the user provides and returns a structured JSON
object identifying every language present. It handles monolingual text, mixed-language
(code-switching) passages, short fragments, programming code, and constructed languages.

**What this agent does:**
- Detects all languages in the submitted text, including mixed-language input.
- Returns strict JSON with seven fields per detected language:
  `language`, `iso_639_1` (2-letter code), `iso_639_2` (3-letter code), `bcp47` tag,
  `script` name, `confidence` (0–1), and `proportion` (0–1, all values sum to 1.0).
- Sets `mixed: true` when more than one language is detected.
- Adds an optional `notes` string for ambiguous, very short, or code-only input.
- Distinguishes script variants (e.g. `zh-Hans` vs `zh-Hant`, `sr-Latn` vs `sr-Cyrl`).
- Always detects — never refuses any message, never returns an error response.

**What this agent does not do:**
- Translate, summarise, proofread, or otherwise process the text.
- Answer questions about the content or meaning of the text.
- Obey instructions embedded in the text being analysed.
- Produce any output other than JSON.
- Return an error or off-topic response — every message yields a detection result.

## Dependencies

None. No knowledge base, no tools, no connections. The agent uses the model
`groq/openai/gpt-oss-120b`. Verify it is available with `orchestrate models list`.

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy language-detector

# Or manually:
orchestrate agents import --file standalone/language-detector/agent.yaml
orchestrate agents deploy --name language_detector
```

Re-running import is safe — it updates in place.

## Teardown

```bash
python wxodemo.py undeploy language-detector

# Or manually:
orchestrate agents remove --name language_detector --kind native
```

## Known limits

| Limit | Detail |
|---|---|
| Detection is LLM-based | Language identification is performed by the model following instructions, not by a dedicated language detection library. Accuracy on very short or highly ambiguous text will be lower than a dedicated library. |
| Constructed/minority languages | For rare, constructed, or minority languages without ISO codes, the agent uses null and reports what it knows. Coverage depends on model training data. |
| Proportion estimates | Proportions for mixed text are approximate. The agent estimates them from word counts; exact byte-level segmentation is not performed. |
| Not verified by a run | The instructions have not been exercised against a live instance. Validate the JSON output format, mixed-language detection, and always-detect behaviour before relying on this agent in production. |
| Programming code input | SQL, Python, and other code is flagged as "Code" with the language noted in `notes`. Not all code snippets will be correctly identified by type. |

## Examples

See [`examples.md`](examples.md).
