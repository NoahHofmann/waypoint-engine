# WP · 10 Qualify company (sub-workflow)

**Job:** decide whether the company in one article fits the ICP, and store it once in Companies.

## Flow and reasoning
1. **Fetch full article:** RSS only has a teaser, which is why people were never found at first. If the fetch fails, the RSS text is used and the row is flagged *Article fetch failed*.
2. **Prepare article (rules):** keeps only real paragraphs (≥60 chars), dropping menus and "related news". Reason: an "Antler" mention in the sidebar once gave a false *Network investor*. Collects links inside paragraphs → candidate company domain.
3. **Injection pre-check (rules):** regex for "ignore previous instructions" and similar (EN/DE). Hits never reach the model → Rejected + flag.
4. **Extract facts (LLM, gpt-4o-mini, temp 0):** prompt `prompts/qualify-v2.md`. The model returns facts + one verbatim quote per fact group. It never scores.
   - The output schema is deliberately loose (no enums, nullable lists). A strict schema rejected whole answers ("Model output doesn't fit required format") when the model returned e.g. 6 people or "seed" instead of "Seed". Values are normalised in code instead.
5. **Score icp-v2 (rules):**
   - Evidence check: a quote counts if it is in the article, or if ≥80% of its word pairs are (tolerates punctuation and tiny edits, rejects invented quotes). Ungrounded facts fall back to neutral.
   - Hard gates → Rejected: not a single-company equity round · Series B+ or > €20M · UK/non-Europe HQ without Europe expansion · mission gate · **B2C**.
   - 100 points (see Notion › ICP & Rules). ≥60 Qualified, ≥75 Strong.
   - **Business model must be shown**: ≥60 but B2B not confirmed → Archived + *Check: business model unclear* (live case: Coding Giants, a kids' coding school, scored 68).
   - Currency: fixed conservative FX table (good enough for 3 size bands).
6. **Notion · same company? → Already in CRM?** company-level dedupe on the normalised name (live case: FLÆ Robotics came from both feeds with opposite verdicts).
7. **Build company page → create → Return result** to the orchestrator (includes the full article text so 20 doesn't fetch again).

## Where the ICP lives
Notion › ICP & Rules is the source of truth. The weights are mirrored in the *Score icp-v2* node. Change Notion first, then the node, then bump the version.

## Failure modes
Model error → row with Status New + flag (visible in dashboard › Needs attention). Notion write retries 3×.
