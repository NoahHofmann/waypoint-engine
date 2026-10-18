# Waypoint Engine: current state (read this first)

Last updated: 18 Oct 2026, 20:30 · Owner: Noah · Repo: NoahHofmann/waypoint-engine (main)

This is the single page a new session (or a new Claude context) reads to continue without losing anything. The details live in `docs/decision-log.md` (every decision and why) and the per-workflow docs.

## Deadlines
- **Mon 19 Oct:** WBS final presentation. Noah builds the deck and video (ElevenLabs).
- **Fri 16 Oct, end of day:** engine stable and tested; only presentation work left.

## What works end to end (verified in live runs)
00 Intake (RSS, weekdays 07:30) → 10 Qualify (gpt-4o-mini, ICP rules) → 20 Find people → 30 Enrich (Brave LinkedIn, website check v3, site scan, Hunter) → 40 Draft + judge (3 variants, code checks + judge, retry once) → 50 Approval cards (Telegram, stack guard 5, backlog, refill) → 51 Approval handler (Gmail draft / send / LinkedIn to-do, closes cards) · 90 Error handler (alerts bot + Notion Runs).

## IDs (n8n)
- **Workflows:**

  | Workflow | ID |
  |---|---|
  | 00 | rBO26s0dO7S1kOn7 |
  | 10 | 4OE5IZv0U12Or4oP |
  | 20 | dufRhYLqpo1JCUpH |
  | 30 | ZOOOloCRp4lfWiJl |
  | 40 | CMf2GVdr4lZ5ruuU |
  | 50 | nKdLZEFyebsDumCl |
  | 51 | iwDMW5Mq4s7mlia4 |
  | 90 | gx1X9dLMg8Hqn5lI |

- **Credentials:**

  | Service | ID |
  |---|---|
  | Notion | qrCZkB1IdXKr7Sp3 |
  | OpenAI | pdSFtuDMCaKd3CHG |
  | Anthropic | GZsdXTaGEKzuDNrl |
  | Gmail | SZBYk0OCrdNe1W56 |
  | Brave (header) | LeyoiGdCQBySGpwl |
  | Hunter (query) | Ijnmypzzm24UpmJD |
  | Telegram approvals | x17tu5yr5xFWMSsZ |
  | Telegram alerts | GH3lzZFd7mdFuTUq |

- All of these are preset by `tools/runlog.py` (`apply_ids`), so imports need no clicks. Telegram chat id: 1170608781 (only this chat is accepted).

## Notion
- Main page "🧭 Waypoint Engine" = dashboard (3fa… views). Databases + rules in sub-page "Databases, rules & evals".
- DB ids:

  | Database | ID |
  |---|---|
  | Companies | 1247998a78a8446993afa06d9811c436 |
  | Contacts | 349e3747aa894088a833ca4a76d6a1b2 |
  | Runs | 84a655097a4449588604e918ae009c1b |
  | Offers | 5618b11e453a4704a41fb530812f110a |
  | Evals | 4bc7f482c57942f293d7fffa01e0323e |

- Sales Playbook page: 3fa64e3c573c81bb9e99da3b6be520c1 (read live by 40).
- Contacts: *Action* formula (to-do text) · *Approve in Notion* (A/B/C/Skip fallback) · *Backlog* status (second person at a company already in conversation) · *Quality score* (own benchmark) · *Draft model* · *Prompt version*.

## Models
- **Draft:** Claude Sonnet 5.5 on attempt 1 (judge GPT-5 mini); GPT-5.1 fallback on attempt 2 (judge Claude Sonnet 5.5). Benchmark = attempt-1 rows (fixed judge).
- **Judge:** GPT-5 mini, reasoning low. **The judge stays fixed**, so *Quality score* stays comparable across draft models: that is our own benchmark. Runs › *Quality avg* + *Model* per run.
- **Qualify / find people:** gpt-4o-mini.

## Noah's standing rules (do not break)
- Nothing is sent without his Telegram tap (or *Approve in Notion*). Cold, article-sourced leads (Legal basis "None - draft only") become **Gmail drafts**, never auto-sent.
- No prices in first emails. German uses informal *du*. The funding round is never the headline.
- Canonical metrics only (Config profile in 40).
- Workflow naming: `WP · NN Name (sub-workflow)`.
- Push every change to GitHub; generators in `tools/` are the source of truth for 30/40/50/51.
- Don't change a workflow before its last version has run (bug fixes excepted).
- Docs follow `docs/_template.md`. Use sticky notes on every workflow (5–6 for long ones).
- Telegram: needs an answer → approvals bot; information only → alerts bot. Every tap or reply gets a visible answer; decided cards close.
- Never raise the Jobcenter topic. No API keys in chat.

## Update protocol (how this page stays current)
Claude rewrites this page and pushes it (repo + Project doc) together with every "Pipeline status / This week / Waiting on" block, i.e. at the end of each working reply where something changed. Noah doesn't need to trigger it; "wrap up" forces it.

## Latest changes (18 Oct evening)
- **Scope:** T-010 (Cal.com booking → Notion) cut from the WBS scope; moved to Notion › Future ideas. Drafts already carry the per-contact booking link with metadata[contact], so only the webhook workflow is missing.
- **T-007 done:** 16/16 drafted contacts judge-passed before approval; draft-v7 4/4 first try (quality 9.4–9.5/10); 11/15 automatic across all draft runs, the 4 others went to Check manually (v6 / first v7 run).
- **Golden set:** `tools/eval_qualify.mjs` runs the 20 qualify + 2 injection cases through the production code read from `workflows/10-qualify-company.json` (only the gpt-4o-mini call is direct). Cases in `docs/evals/golden-set.json`. Evals cases 20 (dedupe, T9) and 22 (legal gate, T2/T5/T8) marked Pass from stress-test evidence; 21 notes partial coverage.
- **README:** models updated (Claude Sonnet 5.5 draft, GPT-5 mini judge), eval/test results table, roadmap pointer. `docs/demo-script.md` = shot list for the recording.
- **Notion › Waypoint Engine › Future ideas** (new database): ICP profiles (= workbook T-015), analytics engine, self-optimising agent, Cal.com booking, follow-ups, LinkedIn acceptance, seniority fallback, sell the engine.

## Open issues (in priority order)
1. **Code freeze until the demo (Mon 19 Oct):** only fix what breaks a live run.
2. Noah: confirm the 20 qualify labels in Notion › Evals, run `OPENAI_API_KEY=… node tools/eval_qualify.mjs`, push `docs/evals/`. Claude then writes results into Notion › Evals and the README table.
3. Record the demo (docs/demo-script.md), then deck + ElevenLabs video.
4. Docs for 00/10/20/90 are not yet in the new template (after the demo).

## Parked (roadmap)
- Analytics agent (reply rates per variant and per model).
- Follow-up engine WP · 60.
- LinkedIn acceptance check.
- Seniority fallback when no decision maker is reachable (e.g. a founding designer at a small company).
- Model bake-off: needs real reply data.
