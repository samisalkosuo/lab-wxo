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

Run the evaluation locally with the ADK (needs the optional evaluation framework, see the
root README). Results go to `standalone/entity-extractor/results/`, a generated folder:

```bash
orchestrate evaluations evaluate --config standalone/entity-extractor/eval_config.yaml
```

`python wxodemo.py eval` only accepts scenarios, so it does not work for this agent.
`python wxodemo.py test-upload entity-extractor` uploads the test prompts to the Tests tab,
but the SaaS gateway does not expose that API; on SaaS create tests from Draft Preview
(`Save as test`) instead.

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
| Evaluation is simulated | The ADK evaluation uses an LLM-simulated user, so multi-turn behaviour after the first reply can vary between runs. See the results folder for the latest run. |
| Regex tool is heuristic | Phone numbers, labelled identifiers and dates in unusual formats can be missed or over-matched. Slash dates such as `03/04/2025` are returned without a `normalized` value because day/month order is ambiguous. |
| Currency coverage | Symbols `$ € £ ¥`, a short list of ISO codes (EUR, USD, GBP, SEK, NOK, DKK, CHF, JPY, CNY, INR, CAD, AUD) and the words euro/dollar/pound are recognised. |
| Semantic entities are model-based | `person`, `organization`, `location`, `product`, `job_title`, `event` and custom entities depend on the model; ambiguous names (e.g. a company that is also a place) may be mislabelled. |
| Tool routing is prompt-based | Whether the tool is called for the right entity types, and with the exact source text, is enforced by the instructions, not by code. The test cases (tc_01, tc_03, tc_08) check only the final JSON, not the tool-call arguments. Local ADK runs of the 8 cases vary: one run passed 8 of 8, the next 6 of 8. The recurring fault is the model mis-copying the surname "Virtanen" from the user's message (seen as `Virtuunen`, `Virtuen`, `virtunen`, `virtonen`), both in the tool-call `text` and, in tc_02, in a reply with no tool call at all. The model also sometimes leaves the request phrase "Extract entities:" in the tool-call `text` or omits `url`/`percentage` from `entity_types`. Check extracted values against the source text before relying on them. |
| Draft agents | On Developer Edition `orchestrate agents deploy` may fail; the agent then stays a draft. |

## Examples

See [`examples.md`](examples.md).
