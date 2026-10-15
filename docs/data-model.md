# Data model (Notion)

## Companies
One row per company (not per article). Key fields:
- **Status:** New (model error, needs a look) · Qualified (≥60 points, B2B confirmed) · Archived (<60, or business model unclear) · Rejected (hard gate) · Contacts found · Contacted · Meeting booked
- **ICP score:** 0–100 from icp-v2 (rows from before 14 Oct 14:00 used a 0–3 scale)
- **Qualify reasons:** gate or score + the 8-criteria breakdown + one-sentence summary
- **Dedupe key:** normalised company name (e.g. "flaerobotics"). Prevents the same company twice when two feeds report it
- **Domain:** from the article's links, else found by WP · 30
- **Flags:** Strong · Evidence dropped · Network investor · Article fetch failed · Model error · Check: business model unclear

## Contacts
One row per named person at a qualified company.

### Status after enrichment (WP · 30)
| Status | Means | Next step |
|---|---|---|
| Needs email | Not processed yet, or the last attempt hit an API error | WP · 30 picks it up next run |
| **Ready to draft** | Verified email (Hunter "valid", or "accept_all" with score ≥ 90). LinkedIn may exist too | 40 drafts an email |
| **LinkedIn only** | Verified LinkedIn profile, no usable email | 40 drafts a LinkedIn message, you send it by hand |
| **Check manually** | Only an unconfirmed lead: a name-only LinkedIn candidate or an unverifiable (accept_all) email | You check; if right, copy the candidate into LinkedIn and set the status |
| **Not reachable** | Nothing found | Next person at the same company is tried in a later run |
| No email found | Old status (before 14 Oct 17:15), no longer written | Reset to Needs email |

### Reach (formula, read-only)
Shows the channels in words, independent of status: **Email + LinkedIn · Email only · LinkedIn only · Unconfirmed: check · None · Not enriched yet**. Only *verified* values count; candidates never do.

### Evidence fields
- **Name evidence:** verbatim sentence from the article that contains the name (GDPR Art. 14: where we got the data)
- **Data source URL:** the article
- **LinkedIn match:** the full reasoning of WP · 30 (attempts, website search, Hunter domain checks)
- **LinkedIn candidate:** name-only match, never used automatically

### After drafting (WP · 40)
| Status | Means |
|---|---|
| Draft ready | Draft passed code check + judge. Goes to Telegram approval (50) |
| Check manually | Draft failed twice; Judge notes say why |
Fields: Variant A/B/C (subject on first line), Variants passed, Chosen variant (A/B/C/Edited, set by Noah), Channel, Offer, Draft language, Draft subject/body (default = first passing variant), Judge result/notes, Booking link, Email source.

### Companies (added 15 Oct)
- **Domain source:** Article · Website check · Hunter · Manual
- **Company inbox:** generic address from the company site (fallback only)

### Approval (WP · 50 / 51)
| Status | Means |
|---|---|
| Awaiting approval | Card is in Telegram |
| Sent | Sent from hello@ (only with a green legal basis) |
| Gmail draft created | Draft waits in hello@ for Noah to send |
| Approved | LinkedIn text approved, to paste manually |
| Skipped | Noah skipped it |
Fields: Telegram message ID (card id = idempotency key), Chosen variant, Approved at, Sent at, Approval log.

## Runs
One row per orchestrator run plus one per error (from WP · 90).

## Evals
Golden set for the qualify step; label confirmed by Noah.
