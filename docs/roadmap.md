# Roadmap

Reordered 20 Oct after the external audit (docs/audit-2026-10-19.md). Rule: engineering gets a fixed block (max ~1 day/week); the rest of the week goes to sending, conversations and proposals.

## H0: Hygiene sprint (one block, this week, ≤1 day total)
Bug fixes only; each is small and has a regression fixture in `tools/`.
- ✅ **Draft-only mode (22 Oct):** 51 always creates a Gmail draft, whatever *Legal basis* says, until an action ledger exists (audit F1 containment). Plus a **Gmail duplicate guard** (no second draft or email to an address already in Drafts/Sent). Fixture `tools/test_51_guard.mjs`.
- **Judge strict (F2):** every verdict field required and non-null; missing, null or duplicate IDs = fail.
- **Verifier errors (F6):** a Hunter verifier error counts as `apiError` (contact stays *Needs email*).
- **Alert wording:** 90 says "send outcome unknown" when the failed workflow is 51, instead of "nothing was sent".
- **Mission backstop:** deterministic fossil/defense/gambling keyword gate in 10, independent of the LLM flag (golden-set #26).
- **Host (22 Oct, mostly done):** ✅ images pinned (n8n 2.43.5, postgres 16.15, cloudflared 2026.10.0); ✅ 169.254.169.254 blocked from Docker (systemd `block-metadata.service`); ✅ tunnel token rotated (it was in cloud-init user data); ✅ first pg_dump in /opt/waypoint/backups. ✅ Cloudflare Access on the editor (One-time PIN, 2 emails, 24 h) with a Bypass app for `webhook/*` + `webhook-test/*`. Open: encryption key in password manager (Noah to confirm); weekly dump off-host.
- **Reporting:** README and STATE show precision/recall with counts (qualify: P 80% · R 57% · n=20), not only "16/20".

## H1: Before ~100 contacts (≈ mid-Nov)
- **Pagination (F3):** 30 queries only pending rows; "company already covered" becomes its own query (by company) with full cursor paging. Same for 50's in-flight check and 00's known-company lookup.
- **Fact evidence (F5):** amount, HQ, round type and B2B need a verbatim span before they feed a hard gate.

## H2: Outcome loop (next feature; prerequisite for everything learning-related)
- **Sent / reply sync (F9):** Gmail history sync on hello@ sets *Sent at* (matched by stored draft/thread ID), *Replied*, opt-out → *Do not contact*. Interim: Noah marks *Sent* by hand.
- **Cal.com webhook** (cut from WBS scope, metadata[contact] already in every link): *Meeting booked*.
- **Analytics agent** (was H2): reply and meeting rate per variant, model, language, offer; n ≥ 20 per arm before calling a winner; human approves any change.
- **Recall work:** only after a month of real outcomes shows which missed segment matters.

## H3: Before auto-send or follow-ups (WP · 60)
- **Action ledger (F1, F10):** one approval = one immutable draft hash + recipient + action; unique key per contact/version/action; `outcome_unknown` never auto-retried.
- **Suppression registry** checked at draft and at dispatch.
- **Follow-up cadence** (from Notion › Sales Playbook): day 0 email · day 1 LinkedIn connect · day 4 email · day 8 LinkedIn message once accepted · day 13 walk-away. Second contacts step in when the first never replies.
- **LinkedIn stack:** approved LinkedIn items queue in one place (third Telegram bot or a daily digest + Notion view "LinkedIn to send") and are worked through in one batch; ✅ per item sets *Sent at*. Notes are optional (free-account cap); the note text becomes the post-acceptance message.
- **Permission model:** manual cold e-mail to DE/AT recipients is allowed since 22 Oct on an informal lawyer OK (targeted, no spam, honour opt-outs). Auto-send and WP · 60 need written legal advice first.

## H4: Only when a client pays for an engine deployment
Per-client n8n instance (no shared tenancy), environment manifest instead of hard-coded IDs, staging + CI, restore drill, n8n licence check for the exact delivery model. Multi-channel sequences and LinkedIn acceptance checks.

## Not on the roadmap
Shared SME SaaS, autonomy levels 3–4, Postgres application layer for the personal pipeline, Kubernetes/queue mode. Revisit only with paying-client evidence.
