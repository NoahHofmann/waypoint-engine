# Waypoint Engine

Outbound research-and-draft engine for **Waypoint** (Noah Hofmann's GTM advisory). Built in n8n as the WBS *AI Agents & Automation* final project.

**Problem:** a solo advisor has no SDR and limited weekly hours for prospecting.
**Output:** qualified companies and founders in Notion, a grounded draft per person, one-tap approval in Telegram, and booked meetings tracked back to the source signal.

## Architecture

| Workflow | Job | AI? |
|---|---|---|
| `00 Intake (orchestrator)` | RSS intake, cleaning, dedupe, cost cap, calls sub-workflows, run log | No |
| `10 Qualify company` | Injection pre-check → LLM scores ICP 0–3 → rule guardrails → Notion › Companies | Yes (1 call) |
| `20 Find people` | LLM extracts founders named in the article → verbatim check → Notion › Contacts | Yes (1 call) |
| `90 Error handler` | Any failure → email + Telegram + Notion › Runs | No |
| 30 Enrich · 40 Draft + judge · 50 Telegram approval | *In progress* | |

Data lives in Notion: **Companies** (1) ↔ (n) **Contacts**, plus **Runs** (one row per execution) and **Evals** (golden set).

## Guardrails: what is enforced vs. requested

- **Before the LLM (code):** fixed sources only, HTML stripped, 2,500-char cap, 15 items/run cap, URL dedupe, regex injection pre-check (EN/DE) that skips the model.
- **The LLM (proposes):** gpt-4o-mini, temperature 0, max 500 tokens, Structured Output Parser enforces the schema.
- **After the LLM (code decides):** evidence must be verbatim in the source; non-funding → 0; no grounded evidence → max 1; round > €50M → max 1; people must be named verbatim.
- **Blast radius:** the model has no tools. It can only write text into Notion fields. Nothing is sent without a human tap, and contacts without a legal basis are draft-only.

## Setup

1. `infra/`: n8n + Postgres + Cloudflare Tunnel via `cloud-init.yaml` (Hetzner) or `bootstrap.sh`. Copy `.env.example` to `.env` and never commit it.
2. Import `workflows/*.json` into n8n. Select credentials (OpenAI, Notion, Telegram, Gmail) on the nodes marked red.
3. In `00`, point both *Execute Workflow* nodes at `10` and `20`. In each workflow's settings, set **Error workflow** = `90 Error handler`.
4. Share the Notion page *Waypoint Engine* with the integration.

## Evals

See Notion › Evals. Each case has an expected label (confirmed by Noah), the actual result, and the prompt version. Target: ≥ 80% agreement on the qualify golden set, 100% block rate on injection and legal-gate cases.

## Compliance note

Contacts are stored with their data source (GDPR Art. 14). First messages state where the data came from and offer deletion. Cold email to German recipients without prior consent is restricted (UWG §7), so such contacts are draft-only. Not legal advice.
