# WP · 50 Approval cards + WP · 51 Approval handler

**Job:** nothing leaves without Noah's tap. 50 sends one Telegram card per contact with Status *Draft ready*; 51 reacts to the taps.

## 50 · Approval cards (sub-workflow, called by 00 after 40)
- Card: company, person, channel, language, ICP score, offer, signal, recipient, **what "Approve" will do** (see gate below), which variants passed review, and Variant A/B/C.
- Buttons: **Send A · Send B · Send C · ✏️ Edit · ⏭ Skip**. Replying to the card with your own text sends that version (first line `Subject: …` for emails).
- Writes Status *Awaiting approval*, the card's Telegram message id, and an Approval log line.

## 51 · Approval handler (Telegram trigger, must be published/active)
1. **Security:** only Noah's chat id is accepted; every other chat is ignored.
2. **Idempotency:** acts only while the contact is *Awaiting approval*. Double or late taps get "Already handled" and nothing is sent twice. The status is the lock.
3. **Legal-basis gate (code):**
   | Channel | Legal basis | What happens | Status |
   |---|---|---|---|
   | Email | Consent / Existing relationship / Inbound | Sent from hello@ | Sent |
   | Email | None - draft only (all article-sourced leads) | **Gmail draft** in hello@; Noah reviews and sends it himself | Gmail draft created |
   | LinkedIn | any | Text sent back in Telegram with the profile link, to paste manually | Approved |
   | any | Skip | nothing | Skipped |
4. **Edit:** reply to the card; the reply becomes *Chosen variant = Edited* and goes through the same gate.
5. **Record:** Status, Chosen variant, final Draft subject/body, Approved at / Sent at, Approval log line. Telegram confirms each outcome.

## Why
- **Telegram:** fastest human-in-the-loop on a phone; inline buttons make the choice one tap.
- **Separate trigger workflow (51):** a Telegram trigger must always be listening; keeping it apart from the daily pipeline means a pipeline failure never blocks approvals and vice versa.
- **Gmail draft for cold contacts:** German UWG §7 makes unsolicited advertising email to businesses risky without (presumed) consent. The engine prepares everything, a human decides and presses send. Not legal advice.
- **LinkedIn by hand:** LinkedIn offers no permitted API for automated messages; automation would risk the account.

## Not yet
Follow-up sequence (60): agreed cadence in Notion › Sales Playbook (5 touches, 2 on LinkedIn, walk-away email at the end).
