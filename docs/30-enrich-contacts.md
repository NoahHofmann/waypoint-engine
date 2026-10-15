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
4. **Website fail-safe** (only if Companies › Domain is empty). Search APIs returned 0 results for company names in every live run, so we check the web directly: up to 24 likely domains are generated from the name (name.com/.ai/.io/.co/.eu/.de/.tech/.app, the HQ country TLD, hyphenated and first-word variants, get<name>.com, <name>hq.com, other European ccTLDs). Each homepage is opened; a candidate counts only if it loads, is not a parked/for-sale page, and shows the company name in title, meta or visible text. Name-in-title wins, then .com. Saved to Companies › Domain with *Domain source* = Website check. Free, no API credits.
5. **Site scan for emails (free):** homepage, /impressum, /imprint, /legal-notice, /contact, /kontakt, /about, /team. Addresses on the company's own domain are collected (obfuscations like [at] decoded). A personal address matching the contact's name becomes a fallback email (*Email source* = Website, always verified by Hunter). A generic inbox (hello@, info@ …) is saved on the **company** as *Company inbox*, never as the person's email.
6. **Hunter email finder** with domain (or company name). **Domain sanity check:** if Hunter guessed the domain itself, it must match the company name, else the email is discarded (live case: FLÆ Robotics → vexrobotics.com).
7. **Hunter verifier** only if the finder isn't sure. Checks the mail server, **sends nothing**.
8. **Build contact update → Notion**, then **Run summary + budget** (counts, credits used, API errors).

## Rate limits and errors
Brave calls are spaced 1.5 s and retried 3× (2 s apart). An error never becomes "not found": the reason is written to *LinkedIn match* and the contact stays in Needs email.

## Known limits
- Hunter's free tier finds verified emails for well under half of seed-stage founders. That is why *LinkedIn only* is a first-class outcome.
- Brave free credit requires the attribution on noahhofmann.com/waypoint (footer).
