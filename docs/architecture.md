# Architecture

## The pipeline

```
07:30 weekdays
WP · 00 Intake (orchestrator)
  ├─ RSS: EU-Startups funding + Tech.eu      → normalise, keep funding news ≤ 7 days
  ├─ Notion: drop articles already processed  → idempotency
  ├─ for each article (max 15):
  │    WP · 10 Qualify company   → Companies row (Qualified / Archived / Rejected)
  │    if Qualified: WP · 20 Find people → Contacts rows (Needs email)
  ├─ Runs row (counts, tokens, cost)
  └─ WP · 30 Enrich contacts (once)  → LinkedIn + email → outcome status
Any failure anywhere → WP · 90 Error handler → Telegram + email + Runs row
Next (Thu): 40 Draft + judge → 50 Telegram approval → send / booking
```

## Principles (and why)

1. **The LLM extracts, code decides.** The model reads messy text well but is not reproducible. So the model only returns facts with verbatim quotes; scores, gates and statuses are computed in code. Same input → same decision. This is what makes the evals meaningful.
2. **Every fact needs evidence.** A fact without a quote that appears in the source falls back to a neutral value. This blocks hallucinated names, amounts and countries.
3. **Every decision leaves a reason in Notion.** Qualify reasons (score breakdown), LinkedIn match (why a profile was accepted or not), Flags. You should never have to open n8n to understand a row.
4. **Fail loud, never silent.** API errors are not "no result". Errors go to the error handler; contacts hit by an API error stay in their status and are retried.
5. **Budget before calls.** Free tiers (Brave ~1,000 searches/month, Hunter 50 credits/month) are protected by caps inside the workflows, not by trust.
6. **Human approval before anything leaves.** Nothing is sent without a Telegram approval; cold contacts carry Legal basis = "None - draft only".
7. **Modular sub-workflows with small contracts.** Each workflow has one job and can be tested alone with pinned data. The orchestrator only does plumbing.
8. **Notion is the source of truth.** ICP & Rules and Offers live in Notion; the workflows mirror them (ICP weights are copied into WP · 10, see that doc).

## Cost per run (measured 14 Oct)
gpt-4o-mini, ~15 articles: €0.004–0.009 per run. Brave + Hunter: within free tiers at ≤8 contacts/run.
