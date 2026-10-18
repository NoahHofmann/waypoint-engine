# Waypoint Engine

> **Documentation:** see [docs/README.md](docs/README.md) for every workflow, the data model and the decision log.

Outbound research-and-draft engine for **Waypoint** (Noah Hofmann's GTM advisory). Built in n8n as the WBS *AI Agents & Automation* final project.

**Problem:** a solo advisor has no SDR and limited weekly hours for prospecting.
**Output:** qualified companies and founders in Notion, a grounded draft per person, one-tap approval in Telegram, and booked meetings tracked back to the source signal.

## Architecture

| Workflow | Job | AI? |
|---|---|---|
| `00 Intake (orchestrator)` | RSS intake, cleaning, dedupe, cost cap, calls sub-workflows, run log | No |
| `10 Qualify company` | Fetch full article → injection pre-check → LLM extracts facts with verbatim evidence (qualify-v2) → code scores 100 points against icp-v2 (hard gates, ≥60 Qualified) → company-level dedupe → Notion › Companies (incl. domain from article links) | Yes (1 call, facts only) |
| `20 Find people` | LLM extracts founders named in the article → verbatim check → Notion › Contacts | Yes (1 call) |
| `90 Error handler` | Any failure → email + Telegram + Notion › Runs | No |
| 30 Enrich contacts | Built | Brave LinkedIn search (2 attempts, deterministic name+company match), Hunter finder + verifier (no email sent), monthly budget guard (300 Brave / 40 Hunter) |
| 40 Draft + judge | Built | Rules build the brief and pick the offer; Claude Sonnet 5.5 writes 3 variants from article + homepage + Notion Sales Playbook, code checks format/numbers/clichés, GPT-5 mini judges grounding (fixed judge = comparable quality score); retry once with GPT-5.1 judged by Claude |
| 50 Approval cards · 51 Approval handler | Built | Telegram card with 3 variants + Edit/Skip; only Noah's chat; status as idempotency lock; legal-basis gate: green → send, cold → Gmail draft, LinkedIn → text to paste |

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

## Evals and test results

See Notion › Evals. Each case has an expected label (confirmed by Noah), the actual result, and the prompt version. Target: ≥ 80% agreement on the qualify golden set, 100% block rate on injection and legal-gate cases.

| What | Result | Evidence |
|---|---|---|
| Qualify golden set (20 cases) | **16/20 (80%)**: 1 false positive (oil & gas software, mission gate relies on the LLM flag), 3 conservative false negatives (archived for human review) | `docs/evals/qualify-golden-2026-10-18.md` |
| Injection (qualify, 2 cases) | **2/2 blocked** by the regex pre-check before any LLM call (EN + DE) | same run |
| Draft grounding | 15/15 drafted contacts judge-passed before approval; draft-v7: 4/4 first try, quality 9.4–9.5/10; 34/45 variants passed (76%) | Notion › Runs (Draft), Contacts › Quality score |
| Injection (draft, T10) | Injected "BUY NOW 50% off" ignored, 3 clean variants, 8.7/10 | `docs/test-plan.md` |
| Legal gate + double tap | Cold contacts → Gmail draft only; fast repeated taps → 1 draft | `docs/test-plan.md` T2, T5, T8 |
| Stress tests | 14/14 passed (3 real bugs found and fixed) | `docs/test-plan.md` |

Golden-set runner: `tools/eval_qualify.mjs` reads the injection check, scoring code, prompt and schema straight from `workflows/10-qualify-company.json`, so the eval tests the production logic, not a copy.

## Roadmap

Parked ideas live in Notion › Waypoint Engine › **Future ideas** (ICP profiles, analytics engine, self-optimising agent, Cal.com booking, follow-ups) and in `docs/roadmap.md`.

## Compliance note

Contacts are stored with their data source (GDPR Art. 14). First messages state where the data came from and offer deletion. Cold email to German recipients without prior consent is restricted (UWG §7), so such contacts are draft-only. Not legal advice.
