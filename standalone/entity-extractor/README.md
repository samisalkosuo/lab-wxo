# entity_extractor — Entity Extraction Agent

## Purpose

`entity_extractor` finds named entities in text the user provides and always answers with
JSON. By default it extracts every built-in entity; the user can name the ones they want, or
define their own custom entities.

**What this agent does:**
- Extracts built-in entities: `person`, `organization`, `location`, `product`, `job_title`,
  `event` (by the language model) and `email_address`, `phone_number`, `date`,
  `monetary_amount`, `identifier`, `url`, `percentage` (by the `extract_pattern_entities`
  Python tool, which uses regular expressions).
- Normalizes dates (ISO `YYYY-MM-DD`) and monetary amounts (`amount` + `currency`) where
  the format is unambiguous.
- Extracts only the entity types the user names, or all except the ones the user excludes.
- Extracts user-defined custom entities, and asks one short question for a description or
  example when a custom entity is unclear.
- Answers "what do you do?" / "which entities do you know?" with a JSON list of the
  supported entities.
- Treats instructions embedded in the source text as data, not commands.

**What this agent does not do:**
- Summarise, translate, classify or answer questions about the text.
- Invent entities that are not in the text.
- Write anything anywhere — the tool is read-only and has no side effects.

## Files

- `agent.yaml` — agent definition
- `pattern_entities.py` — the `extract_pattern_entities` Python tool (imported by `wxodemo` before the agent)
- `examples.md` — example prompts and expected behaviour
- `eval_config.yaml`, `test_cases/` — evaluation configuration and test cases

## Dependencies

None beyond an active WXO environment. No knowledge base, no connections. The agent uses
the model `groq/openai/gpt-oss-120b` (check with `orchestrate models list`). The tool uses
only the Python standard library.

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy entity-extractor

# Or manually:
orchestrate tools import -k python -f standalone/entity-extractor/pattern_entities.py
orchestrate agents import --file standalone/entity-extractor/agent.yaml
orchestrate agents deploy --name entity_extractor
```

Re-running import is safe — it updates in place.

## Test

```bash
python wxodemo.py test-upload entity-extractor          # upload test cases
python wxodemo.py test-upload entity-extractor --eval   # upload and evaluate
```

## Teardown

```bash
python wxodemo.py undeploy entity-extractor

# Or manually:
orchestrate agents remove --name entity_extractor --kind native
orchestrate tools remove --name extract_pattern_entities
```

## Known limits

| Limit | Detail |
|---|---|
| Not verified by a live run | The agent has not been exercised against a live instance. The tool was run locally on one sample text only. Validate JSON shape, tool-call arguments and clarification behaviour after deploy. |
| Regex tool is heuristic | Phone numbers, labelled identifiers and dates in unusual formats can be missed or over-matched. Slash dates such as `03/04/2025` are returned without a `normalized` value because day/month order is ambiguous. |
| Currency coverage | Symbols `$ € £ ¥`, a short list of ISO codes (EUR, USD, GBP, SEK, NOK, DKK, CHF, JPY, CNY, INR, CAD, AUD) and the words euro/dollar/pound are recognised. |
| Semantic entities are model-based | `person`, `organization`, `location`, `product`, `job_title`, `event` and custom entities depend on the model; ambiguous names (e.g. a company that is also a place) may be mislabelled. |
| Tool routing is prompt-based | Whether the tool is called for the right entity types is enforced by the instructions, not by code. |
| Draft agents | On Developer Edition `orchestrate agents deploy` may fail; the agent then stays a draft. |

## Examples

See [`examples.md`](examples.md).
