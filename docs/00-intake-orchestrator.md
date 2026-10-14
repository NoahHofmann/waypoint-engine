# WP · 00 Intake (orchestrator)

**Job:** find fresh funding news once per weekday and hand each article to the sub-workflows. No business logic lives here.

## Flow
1. **Triggers:** schedule 07:30 Mon–Fri (only when published) + manual.
2. **Config:** caps (15 leads/run, 7 days max age), Notion DB IDs, model, prompt versions. One place to change them.
3. **RSS:** EU-Startups funding category + Tech.eu. Merged.
4. **Normalize + funding filter (rules):** strips HTML, drops items older than 7 days, keeps only titles/teasers with funding words, dedupes within the batch.
5. **Notion · known companies → Drop known + cap:** skips articles whose URL is already stored (idempotency across runs), caps at 15 for cost.
6. **Sub · 10** for each article → **Qualified?** → **Sub · 20** for qualified ones.
7. **Build run log → Notion · log run:** counts, tokens, cost, status.
8. **Sub · 30** once at the end (after the run log, so it also processes leftovers from earlier runs).

## Why
- Article-level dedupe here, company-level dedupe in 10: the URL is known before the LLM, the company name only after.
- 30 runs once at the end instead of per company: one budget check, one place where rate limits apply.

## Failure modes
- A feed is down → the other still runs; the run log shows fewer items in.
- A sub-workflow fails → error handler fires; `onError: continue` keeps the other articles going.
