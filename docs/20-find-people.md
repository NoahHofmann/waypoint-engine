# WP · 20 Find people (sub-workflow)

**Job:** for a qualified company, create up to 3 Contacts from people named in the article.

## Flow and reasoning
1. **Extract people (LLM):** only people who work at the company (founders, C-level), with one verbatim sentence each. Not investors, not journalists.
2. **Guardrails (rules, runs once for all items):** full name (2+ words), name and evidence must both appear in the article (punctuation-insensitive), no duplicates, max 3.
   - Runs "once for all items" because it returns 0–3 contacts. Per-item mode crashed with "A 'json' property isn't an object".
3. **Build contact page → Notion:** Status *Needs email*, Legal basis *None - draft only*, Name evidence + Data source URL (GDPR Art. 14).
4. **Company → Contacts found** only if at least one contact was created.

## Why not search LinkedIn here?
Separation: 20 only uses the article (free, deterministic). Paid lookups live in 30, behind the budget guard.
