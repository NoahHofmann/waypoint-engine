# WP · 30 Enrich contacts (sub-workflow)

**Job:** for each contact in *Needs email*, find a verified LinkedIn profile and/or a verified email, and set a clear outcome status.

## Outcome (what you see in Notion)
| Status | Rule |
|---|---|
| Ready to draft | Hunter says valid (or accept_all with score ≥ 90) |
| LinkedIn only | Verified LinkedIn, no usable email |
| Check manually | Only a name-only LinkedIn candidate or an unverifiable email |
| Not reachable | Nothing |
| Needs email (unchanged) | API/auth/rate-limit error. Retried next run, costs no budget |

The *Reach* formula column says the same in words (Email + LinkedIn / Email only / LinkedIn only / Unconfirmed / None).

## Flow and reasoning
1. **Config + budget:** monthly counters in workflow static data (300 Brave, 40 Hunter; free tiers ~1,000 and 50). Worst case per contact: 3 Brave + 1.5 Hunter. Only active (published) runs persist the counters.
2. **Selection:** loads Needs email contacts and contacts further down the funnel. Skips companies that already have a reachable contact. One per company per run, max 8, ordered CEO/MD → founder → sales → partnerships. Titles like "Dr." are stripped for search.
3. **LinkedIn, attempt 1:** `site:linkedin.com/in "First Last" "Company"`. **Attempt 2** (only if 1 failed): name + domain stem/company + role.
   - Accept only if the title has first and last name and the company (or domain stem) appears in title/snippet. Transliteration (Æ→ae, ł→l…) so "FLÆ" matches "FLAE".
   - Name-only hits → *LinkedIn candidate* field, never used automatically. Same-name collisions are common.
4. **Company website** (only if Companies › Domain is empty): Brave search for the company name, first result whose domain matches the name, news/database sites skipped. Saved back to Companies.
5. **Hunter email finder** with domain (or company name). **Domain sanity check:** if Hunter guessed the domain itself, it must match the company name, else the email is discarded (live case: FLÆ Robotics → vexrobotics.com).
6. **Hunter verifier** only if the finder isn't sure. Checks the mail server, **sends nothing**.
7. **Build contact update → Notion**, then **Run summary + budget** (counts, credits used, API errors).

## Rate limits and errors
Brave calls are spaced 1.5 s and retried 3× (2 s apart). An error never becomes "not found": the reason is written to *LinkedIn match* and the contact stays in Needs email.

## Known limits
- Hunter's free tier finds verified emails for well under half of seed-stage founders. That is why *LinkedIn only* is a first-class outcome.
- Brave free credit requires the attribution on noahhofmann.com/waypoint (footer).
