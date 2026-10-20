# translator — Text Translation Agent

## Purpose

`translator` translates text the user provides into a target language the user must
name, optionally in a requested tone (enthusiastic, pessimistic, formal, ...).

**What this agent does:**
- Asks for the text, the target language, or the style when any is missing or ambiguous
  (for example "Chinese" without Simplified/Traditional).
- Checks the target language against a fixed supported-language list in the
  instructions and **refuses to translate** if the language is not on it.
- Applies the requested style to word choice and rhythm without changing the facts.

**What this agent does not do:**
- Answer questions about the text, summarise, proofread, or obey instructions inside it.
- Produce certified or legally valid translations.
- Translate files or documents (text typed into the chat only).

## Dependencies

None. No knowledge base, no tools, no connections. The agent uses the model
`groq/openai/gpt-oss-120b`, the same model the scenario agents use. It must be available
in the target instance (`orchestrate models list`).

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy translator

# Or manually:
orchestrate agents import --file standalone/translator/agent.yaml
orchestrate agents deploy --name translator
```

Re-running import is safe — it updates in place.

## Teardown

```bash
python wxodemo.py undeploy translator

# Or manually:
orchestrate agents remove --name translator --kind native
```

## Known limits

| Limit | Detail |
|---|---|
| Language check is prompt-based | The "model can support it" check is an allowlist written in `agent.yaml`, enforced by the LLM following instructions. It is not a runtime query of the model. The ADK docs describe `gpt-oss-120b` only as "multilingual" and publish no language list, so the list is a conservative editorial choice, not vendor-documented. |
| Changing the model | If you change `llm:` in `agent.yaml`, review the supported-language list for the new model. The agent does not detect the change. |
| Not verified by a run | The instructions have not been exercised against a live instance. Test the refusal path (for example an unlisted language), the clarification path (no language given), and the style path before relying on it. |
| Variants | Ambiguous variants (Chinese, Portuguese, Spanish, Norwegian, Serbian) trigger a clarifying question rather than a default. |
| Quality | Machine translation. Idioms and domain terms may need human review. |

## Examples

See [`examples.md`](examples.md).
