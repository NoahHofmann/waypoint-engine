# Roadmap (parked ideas)

## H2: Learning loop (next 1–2 weeks)
**Analytics agent for outreach performance.**
- **Data already captured per contact:**
  - Chosen variant (A/B/C/Edited)
  - Draft model and prompt version (since 16 Oct)
  - Channel, language, offer
  - Approved at / Sent at
- **Missing pieces:**
  - Reply detection: a Gmail trigger on hello@ matches the sender to Contacts and sets Status *Replied* and Replied at.
  - Meeting booked: a Cal.com webhook carries the contact id in its metadata.
- **Dashboard:** reply rate and meeting rate per variant type (A problem-first / B insight-first / C short), per model, per language and per offer. Show a minimum sample size before anything is called a "winner" (n ≥ 20 per arm).
- **Agent:** a weekly review that reads those numbers and proposes changes, e.g. "B outperforms A 2:1 on EN, n=24: make B the default". A human approves. It never auto-changes prompts.
- **Same loop for models:** after the blind bake-off, keep ~20% of drafts on a challenger model to compare reply rates over time.

## H2: Follow-up engine (WP · 60)
Cadence lives in Notion › Sales Playbook:
- day 0: email
- day 1: LinkedIn connect
- day 4: email
- day 8: LinkedIn message, only once the connection is accepted
- day 13: walk-away email

Second contacts become the next step when the first contact never replies.

## H3: Multi-channel
Email and LinkedIn alternating as one sequence; checking whether the LinkedIn connection was accepted.
