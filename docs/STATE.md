# Waypoint Engine: current state (read this first)

Last updated: 16 Oct 2026, 16:35 · Owner: Noah · Repo: NoahHofmann/waypoint-engine (main)

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

## Latest changes (16 Oct afternoon)
- **Cards:**
  - Header: 📨 APPROVE (first batch) or 📥 BACKLOG (came from the queue).
  - Lines: 🏢 What they do, ICP fit %, Quality x/10, Queue count.
  - Each variant that didn't pass shows "⚠️ Not recommended: <category> · reason". The 6 categories: claim not backed, too generic, tone/hype, length/format, playbook rule, other.
- **40 (draft-v6):** a formatting check (blank lines between paragraphs) and a company one-liner.
- **30:** website candidates now start with the company's link inside the funding article.
- **Dawid:** not a bug. The old 50 v2 had set him to Skipped; moved to Backlog by hand.
- Tommi, Filip and Victor were re-queued for re-drafting with Claude. Their GPT-5.1 baseline is in `docs/evals/gpt51-baseline-16oct.md`.

## Open issues (in priority order)
1. **Drafting fixed** (40 v6/v7): Claude cards arrived at 16:10. Claude max tokens 8000; attempt 2 = GPT-5.1 draft judged by Claude (cross-family both ways).
2. **T2 failed** (3 Gmail drafts from fast taps) → 51 v5 Notion lock (Contacts › Lock). Retest on Filip's card. T3 passed. Tommi re-queued as Draft ready for T5.
1b. Intake: Normalize 71 → 20, all 20 already known. Tech Funding News returns 403 (blocks n8n). Planned: TFN via HTTP Request with a browser User-Agent, maxAgeDays 7 → 14, German funding terms.
2. Stress tests not yet run (`docs/test-plan.md`).
3. README, architecture diagram and demo script for Monday.
4. Docs for 00/10/20/90 are not yet in the new template.

## Parked (roadmap)
- Analytics agent (reply rates per variant and per model).
- Follow-up engine WP · 60.
- LinkedIn acceptance check.
- Seniority fallback when no decision maker is reachable (e.g. a founding designer at a small company).
- Model bake-off: needs real reply data.
