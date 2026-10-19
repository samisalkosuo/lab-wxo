# travel_rules_qa — Finnish State Travel Regulation Q&A Agent

## Purpose

`travel_rules_qa` answers questions about *Valtion matkustussääntö 2026*
(Valtiovarainministeriön julkaisuja 2025:63), the Finnish state collective agreement
on compensation of travel costs. The user writes in English; the agent searches the
Finnish PDF and explains the rules in English with Finnish section citations.

This agent exists because the `travel_request` scenario agent barely uses the PDF
(1 of 24 final answers in evaluation): its instructions steer it toward deterministic
tools for amounts and toward the agency-policy KB for approval levels. A dedicated
Q&A agent removes that competition and gives the document a proper interface.

**What this agent does:**
- Explains rules: what counts as an official trip, per-diem entitlements, meal
  deductions, own-car mileage, accommodation, night travel allowance, travel claim
  deadlines.
- Cites sections in Finnish format: "Valtion matkustussääntö 2026, N §".
- States amounts only when they appear word-for-word in a retrieved passage.

**What this agent does not do:**
- Approve or deny travel requests → use `travel_request` for that.
- Check budgets or employee data.
- Book trips or process expense claims.

## Dependencies

This agent requires the `travel_state_rules` knowledge base to be live in WXO. That
KB is deployed as part of the `travel-request` scenario. If the scenario is deployed,
the KB is already available and you can skip the KB import step below.

If the scenario is **not** deployed (or if you removed it), import the KB first:

```bash
orchestrate knowledge-bases import --file knowledge/travel-request/travel_state_rules.yaml
```

> **Known issue:** updating a knowledge base in place can fail ingestion. If you see
> an ingestion error, remove the KB and re-import:
> ```bash
> orchestrate knowledge-bases remove --name travel_state_rules
> orchestrate knowledge-bases import --file knowledge/travel-request/travel_state_rules.yaml
> ```

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
# 1. Import and deploy this agent
python standalone/manage.py deploy --agent travel_rules_qa

# Or manually:
orchestrate agents import --file standalone/travel-rules-qa/agent.yaml
orchestrate agents deploy --name travel_rules_qa
```

Re-running import is safe — it updates in place.

## Teardown

Remove only this agent. **Do not remove the KB** if `travel_request` is still deployed
(they share it).

```bash
python standalone/manage.py undeploy --agent travel_rules_qa

# Or manually:
orchestrate agents remove --name travel_rules_qa --kind native
```

## Known limits

| Limit | Detail |
|---|---|
| Retrieval accuracy | ~55% in early spike tests (11/20 questions correct). Cross-language retrieval — English question → Finnish search term → Finnish document — is imperfect. The agent is instructed to retry with a synonym on a miss. |
| Amounts | Only stated when present word-for-word in a retrieved passage. Annex tables are indexed but not always retrieved; the agent will say so rather than guess. |
| Section coverage | Sections 3, 5–6, 9–16, 19, 21 are described in the KB metadata. Sections outside this range may not be indexed or may retrieve poorly. |
| No tool access | Employee profiles, budget data, and per-diem rate tables are in tools used by `travel_request`. This agent has no tools. |
| Language | Search queries must be in Finnish. The agent handles this internally, but very unusual topics may not map to a Finnish term the agent knows. |

## Examples

See [`examples.md`](examples.md).

## Document attribution

*Valtion matkustussääntö 2026*, Valtiovarainministeriön julkaisuja 2025:63.
URN: https://urn.fi/URN:ISBN:978-952-367-397-7
License: CC BY-NC-ND 4.0 — no derivative works, non-commercial use only.
