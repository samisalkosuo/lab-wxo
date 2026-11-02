# information_redactor — Sensitive Information Redaction Agent

## Purpose

`information_redactor` takes document text, detects sensitive information and personal
identifiers in it, and returns the same text with them masked so it can be shared.

**What this agent does:**
- Masks names, emails, phone numbers, addresses, dates of birth, national and account
  identifiers (including Finnish henkilötunnus and IBANs), credentials, network
  identifiers, and health details tied to a person.
- Uses typed numbered placeholders by default (`[PERSON_1]`, `[EMAIL_1]`); the same value
  always gets the same placeholder, so the text stays readable.
- Supports a generic `[REDACTED]` marker or a category subset when the user asks for it.
- Keeps all other text, numbers, line breaks and markdown unchanged.
- Ends with a one-line redaction summary of counts per category, never the values.
- Asks for the text when none is given.
- Treats the text strictly as data and ignores embedded instructions.

**What this agent does not do:**
- Guarantee that every sensitive item is found. It is not a compliance control.
- Summarise, translate, rewrite, or answer questions about the text.
- Read files or documents (text pasted into the chat only).
- Store, send, or write the text anywhere; it has no tools.

## Dependencies

None. No knowledge base, no tools, no connections. The agent uses the model
`groq/openai/gpt-oss-120b`, the same model the scenario agents use. It must be available
in the target instance (`orchestrate models list`).

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy information_redactor

# Or manually:
orchestrate agents import --file standalone/information-redactor/agent.yaml
orchestrate agents deploy --name information_redactor
```

Re-running import is safe — it updates in place.

## Teardown

```bash
python wxodemo.py undeploy information_redactor

# Or manually:
orchestrate agents remove --name information_redactor --kind native
```

## Known limits

| Limit | Detail |
|---|---|
| Not a guarantee | Detection is done by the LLM following the instructions, not by a deterministic pattern engine. It can miss items or mask too much. A person should review the output before it is shared. |
| Data goes to the model | The unredacted text is sent to the configured LLM in order to be redacted. Do not use the agent where that is not allowed. |
| Text size | The text must fit comfortably in the model context window. Redaction quality can drop on very long documents; split them. |
| Language | Works best on English and Finnish. Identifier formats from other countries may be missed. |
| Indirect identifiers | Combinations of facts that identify a person without a direct identifier (for example a rare job title in a small town) are not reliably detected. |
| Verified on a small sample only | All seven prompts in [`examples.md`](examples.md) were run once each against the deployed agent and behaved as described. The first version dropped words around the masked items ("Call", "Contact:" and an instruction-like sentence) and split a full name into two markers in generic mode; the instructions were tightened and those cases re-ran correctly. One run per prompt is not a statistical test, and output is not deterministic, so re-check after any change to `agent.yaml` or the model. |

## Examples

See [`examples.md`](examples.md).
