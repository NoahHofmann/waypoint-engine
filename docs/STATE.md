# Waypoint Engine: current state (read this first)

Last updated: 22 Oct 2026, 18:20 · Owner: Noah · Repo: NoahHofmann/waypoint-engine (main)

This is the single page a new session (or a new Claude context) reads to continue without losing anything. The details live in `docs/decision-log.md` (every decision and why) and the per-workflow docs.

## Deadlines
- **Mon 19 Oct:** WBS final presentation (past). Code freeze lifted for bug fixes.
- **Next:** H0 hygiene sprint (docs/roadmap.md), one engineering block this week, max ~1 day.

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

## Latest changes (20 Oct)
- **External audit (Codex, 19 Oct)** reviewed at commit 61787d1. Verdict per finding in `docs/audit-2026-10-19.md`. Code findings confirmed (judge accepts incomplete verdicts, 100-row Notion queries, verifier errors ignored, unconditional "nothing sent" alert, no backups, unpinned images). Severities re-rated for one operator in draft-only mode; SaaS/tenancy work dropped.
- **Qualify eval, honest numbers:** precision 80% (4/5), recall 57% (4/7), n=20; majority baseline 65%. The miss that matters is #26 (mission gate).
- **Roadmap reordered** (docs/roadmap.md): H0 hygiene → H1 before 100 contacts → H2 outcome loop (sent/reply/booking sync) → H3 ledger + suppression before auto-send or WP · 60 → H4 only for a paying engine client.
- **Live state 20 Oct:** 38 contacts. 12 Gmail drafts created (since 16 Oct), none with *Sent at*; 3 awaiting approval; 16 need email.
- **Legal (22 Oct):** German/Austrian recipients may get a targeted manual cold e-mail. Informal OK from a lawyer friend (verbal, not written advice) on the conditions: researched reason, no spam, honour opt-outs (Do not contact + delete e-mail). Residual UWG §7(2) Nr. 2 / TKG §174 risk accepted by Noah. Get written advice before auto-send, WP · 60 or selling offer 5.
- **22 Oct, 15:30 · Live state:** 27 contacts Sent with *Sent at* from Gmail Sent (23 e-mails at 14:47–15:19, 3 LinkedIn requests at 15:23, Victor Canivell on 16 Oct). 0 open Gmail drafts, 0 open approvals. 3 Second contact (Dawid, Marta, +1), 27 Needs email, 2 Check manually. Michał Zachara (KP Labs) is OOO; Noah forwarded by hand to Tomàsz (tpozniak@kplabs.pl), who is not yet in Notion. Bjorn Bergstrom got a connection request **without** a note (free LinkedIn note limit).

## Open issues (in priority order)
1. H0 rest: F2 judge strict, F6 Hunter verifier error, 90 alert wording, mission keyword backstop, weekly off-host dump, P/R reporting. Done 22 Oct: 51 draft-only + Gmail duplicate guard; host (metadata block, token rotation, pinned images, Cloudflare Access). Keep marking *Sent* by hand until H2 exists.
3. Docs for 00/10/20/90 into the template.
4. H0 addition: make Gmail draft creation in 51 idempotent and verify it against Gmail (22 Oct: 5 recipients had two drafts, one draft disappeared).

## Parked (roadmap)
- Analytics agent (reply rates per variant and per model).
- Follow-up engine WP · 60.
- LinkedIn acceptance check.
- Seniority fallback when no decision maker is reachable (e.g. a founding designer at a small company).
- Model bake-off: needs real reply data.
