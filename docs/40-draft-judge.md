# WP · 40 Draft + judge (sub-workflow)

**Job:** write **three variants** of a first message for every contact with a verified channel (A problem first, B insight first, C short and direct), check each one, and let Noah pick the one to send.

**Called by:** WP · 00 once per run, after 30. Can be run alone ("Test workflow").
**Reads:** Contacts with Status *Ready to draft* (verified email → email) or *LinkedIn only* (→ LinkedIn connection note), max 8 per run; the linked Company; active rows in Notion › Offers.
**Writes:** Variant A/B/C, Variants passed, Draft subject/body (= first passing variant as default), Channel, Offer, Draft language, Booking link, Judge result + notes, Status *Draft ready* (≥1 variant passed) or *Check manually* (none passed after the retry). *Chosen variant* is set by Noah (Telegram in 50, or Notion by hand). **Never sends.**

## Flow and reasoning
1. **Config:** models, caps, Cal.com base link, and **Noah's profile**: the canonical facts (Techstars $14M pipeline, Hive 94–99%, Qualas, Sigma Squared). The draft may use nothing else about Noah. Changing a metric = change it here (and in the project instructions).
2. **Build brief (rules, no LLM):**
   - *Channel* from the verified data (30 decides what is verified, 40 never guesses).
   - *Language:* DE for DACH companies, EN otherwise.
   - *Offer by rules:* partnerships/channel signal in the article → Fractional Partnerships Lead; DACH company → GTM Strategy & ICP Sprint; everyone else → Market Entry & Expansion (into DACH). Offer text comes live from Notion › Offers. Prices never appear in a first message.
   - *Facts:* only what 10 extracted and verified (round, amount, summary, verbatim quotes).
   - *Booking link:* `cal.com/book-a-call-with-noah/30min?metadata[contact]=<contact id>` so a booking can be matched to the contact (T-010).
3. **Sales Playbook (Notion page, read live):** principles condensed from SPIN Selling, Gap Selling, The Challenger Sale, Predictable Revenue, Fanatical Prospecting, Never Split the Difference, Influence, To Sell Is Human, The Sales Development Playbook and Founding Sales. Edit the page and the next run follows it. Source in the repo: `prompts/sales-playbook.md`.
4. **Draft (gpt-4o, temp 0.3):** prompt `prompts/draft.md`, three variants in one call. Their world first, "how can we help" framing, the round only as half-sentence context, one proof point, no-oriented question. German = informal *du*. Email 60–110 words, LinkedIn ≤ 280 characters. No prices, ever.
5. **Code check (per variant):** subject length and not about funding, body length, link unchanged, opt-out line, sign-off, first name, *du* not *Sie*, **does not open with the funding round**, no hype or congratulations, and **every number must appear in the brief** (test: an invented "50 startups" is caught).
6. **Judge (gpt-4o-mini, temp 0, per variant):** prompt `prompts/judge.md`. Only yes/no questions and lists (unsupported claims, names, language/du, specific opening, tone, playbook violations); the pass decision is computed in code. Format is NOT judged by the LLM: v1 hallucinated a missing opt-out line that was there.
7. **Decide:** a variant passes if code AND judge find nothing. The contact is ready if at least one variant passes.
8. **One retry only if no variant passed**, with every issue as feedback, then a human decides.

## First live run (15 Oct, v1) and what changed
All 3 drafts (KP Labs, HyLight, Epyr) failed: one variant only, funding-led openings ("Epyr's recent €15M Series A round is a significant step…"), and a judge that wrote "Unsupported: None" as a finding and hallucinated a missing opt-out line. v2: three variants, playbook, funding-headline check in code, du-form, yes/no judge, "none" filtered.

## Why
- **Two different checkers:** code is exact but blind to meaning; an LLM judge understands meaning but can miss arithmetic. Each covers the other's blind spot.
- **Smaller model judges a bigger one:** the judge only compares text against a short brief, which a small model does well and cheaply.
- **Opt-out line in every email:** respectful, lowers spam complaints, and fits GDPR/UWG caution for cold B2B contact.
- **Legal basis:** contacts found via articles carry *None - draft only*; 50 shows that on the approval card and never auto-sends them.

## Second live run (15 Oct, v2) and what changed (v3)
- Every variant showed "Judge returned no verdict": the judge's prompt expression contained real line breaks inside a JavaScript string, so the expression failed before the model was called. Fixed; judge errors now show their message.
- Variant C failed the 60-word minimum by design: C now has its own range (30–60 words). LinkedIn notes are connection requests: max 200 characters.
- Drafts were correct but generic ("I help startups like yours…"). v3 gives the model the **article excerpt and the company homepage** to find a real hook, bans the clichés in code, requires a different ask per variant.
- Models: draft **gpt-5.1**, judge **gpt-5-mini** (see Cost). Fallback: gpt-4o / gpt-4o-mini in the same nodes.

## Cost
Per contact ≈ 6k input + ~3k output/reasoning tokens for the draft (gpt-5.1: $1.25 / $10 per 1M) ≈ $0.04, judge (gpt-5-mini: $0.25 / $2) ≈ $0.01. ≈ $0.05 per contact, up to 2× with a retry. At ~8 contacts per weekday: **≈ $8–15 per month**. gpt-4o for the draft would cost about the same; the gain comes from better instruction following.
