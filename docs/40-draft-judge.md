# WP · 40 Draft + judge (sub-workflow)

**Job:** write a first message for every contact with a verified channel, and make sure it is true before a human sees it.

**Called by:** WP · 00 once per run, after 30. Can be run alone ("Test workflow").
**Reads:** Contacts with Status *Ready to draft* (verified email → email) or *LinkedIn only* (→ LinkedIn connection note), max 8 per run; the linked Company; active rows in Notion › Offers.
**Writes:** Draft subject/body/version, Channel, Offer, Draft language, Booking link, Judge result + Judge notes, Status *Draft ready* (pass) or *Check manually* (failed twice). **Never sends.**

## Flow and reasoning
1. **Config:** models, caps, Cal.com base link, and **Noah's profile**: the canonical facts (Techstars $14M pipeline, Hive 94–99%, Qualas, Sigma Squared). The draft may use nothing else about Noah. Changing a metric = change it here (and in the project instructions).
2. **Build brief (rules, no LLM):**
   - *Channel* from the verified data (30 decides what is verified, 40 never guesses).
   - *Language:* DE for DACH companies, EN otherwise.
   - *Offer by rules:* partnerships/channel signal in the article → Fractional Partnerships Lead; DACH company → GTM Strategy & ICP Sprint; everyone else → Market Entry & Expansion (into DACH). Offer text comes live from Notion › Offers. Prices never appear in a first message.
   - *Facts:* only what 10 extracted and verified (round, amount, summary, verbatim quotes).
   - *Booking link:* `cal.com/book-a-call-with-noah/30min?metadata[contact]=<contact id>` so a booking can be matched to the contact (T-010).
3. **Draft (gpt-4o, temp 0.3):** prompt `prompts/draft.md`. Structure: specific observation → relevance to the offer outcome → one proof point → low-friction question → link → opt-out line → sign-off. Email 60–110 words, LinkedIn ≤ 280 characters.
4. **Code check:** subject length, body length, booking link unchanged, opt-out line, sign-off, first name used, no hype/filler, and **every number in the draft must appear in the brief** (test: an invented "50 clients" is caught).
5. **Judge (gpt-4o-mini, temp 0):** prompt `prompts/judge.md`. Lists unsupported claims, correctness and format issues; scores grounded/specific/tone 1–5.
6. **Decide:** pass = no code issues AND judge pass AND no unsupported claims.
7. **One retry** with the concrete issues as feedback, then a human decides. Two attempts keep cost and latency predictable and make the eval metric "first-try pass rate" meaningful.

## Why
- **Two different checkers:** code is exact but blind to meaning; an LLM judge understands meaning but can miss arithmetic. Each covers the other's blind spot.
- **Smaller model judges a bigger one:** the judge only compares text against a short brief, which a small model does well and cheaply.
- **Opt-out line in every email:** respectful, lowers spam complaints, and fits GDPR/UWG caution for cold B2B contact.
- **Legal basis:** contacts found via articles carry *None - draft only*; 50 shows that on the approval card and never auto-sends them.

## Cost
≈ 1,500 tokens draft + 1,200 judge per contact; with gpt-4o + gpt-4o-mini about €0.01 per contact, €0.08 per run at 8 contacts.
