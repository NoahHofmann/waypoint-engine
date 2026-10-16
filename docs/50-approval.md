# WP · 50 Approval cards + WP · 51 Approval handler

> Nothing leaves without your tap. WP · 50 puts each finished draft (and the rare "which website?" question) into Telegram. WP · 51 reacts to your taps and replies: it sends, creates a Gmail draft, or hands you LinkedIn text, and records everything in Notion.

Chain position: 40 → **50** (called by 00) · **51** runs on its own (Telegram trigger, must be published).

## Telegram: two bots, one rule
| Chat | Bot | What lands there | Mute? |
|---|---|---|---|
| **Waypoint approvals** | current bot (credential *Telegram account*) | Only things that need your decision: 📨 APPROVE cards and 🌐 WEBSITE? questions | No |
| **Waypoint alerts** | second bot (credential *Telegram alerts*) | 🚨 ERROR messages from WP · 90 | Yes, if you like |

Every message starts with a fixed type tag and a divider, so you can see the type at a glance:
- **📨 APPROVE 2/5 · Company · Name:** choose A/B/C, ✏️ Edit, or ⏭ Skip.
- **🌐 WEBSITE? · Company:** reply with the domain or tap 🚫 No website.
- **✅ / 📝 / 🔗 / ⏭:** confirmations. These are always a *reply to* the card they belong to, so they never float around without context.

**Stack guard:** at most **5 unanswered approval cards** exist at a time.
- **One out, one in:** each time you decide a card (Send / Skip / Edit), WP · 51 immediately runs WP · 50, so the next waiting draft arrives within seconds. No need to wait for the next scheduled run.
- **Queue full:** when 5 cards are open and drafts are waiting, the run sends one ⏸ QUEUE FULL message naming the open cards. The 07:30 run repeats it each morning until you clear them.
- **One company, one conversation:** a second person at a company that is already in conversation goes to **Backlog**, not to Telegram. Their drafts are kept. Use them if the first contact doesn't reply: set *Approve in Notion*.

**Which bot gets what:** if a message needs your answer or tap → **approvals** (📨 cards, 🌐 website questions, ⏸ queue full). If it's for information only → **alerts** (🚨 errors; daily summaries later). The 🌐 question needs a reply, so it belongs with the approvals.


## Answer rule (v4, 16 Oct)
**Every tap or message from you gets a visible answer. No answer means a bug.**
- **Tap a button:** a short "Got it ✔" toast. The card is then **closed**: edited into a one-line result (✅ SENT / 📝 GMAIL DRAFT / 🔗 LINKEDIN / ⏭ SKIPPED · name · company · time) and its buttons removed. **A card that still has buttons always needs you.**
- **Reply to a card with your own text:** same result; the card closes.
- **🌐 website reply:** the question closes as "✅ WEBSITE SAVED · company · domain". If the text isn't a domain, you get a ⚠️ reply asking again.
- **Late or double tap:** the card closes as "☑️ ALREADY HANDLED"; nothing is sent twice.
- **Any message not tied to a card:** a 🤔 help note ("swipe left on the card to reply").
- **Error:** the card stays open and a ❌ reply says what failed.
- All messages use Telegram HTML, with bold headers and escaped content.

## 1. Inputs
| Workflow | Source | Filter |
|---|---|---|
| 50 | Notion › Contacts | Status *Awaiting approval* (counted for the stack guard), then *Draft ready* (oldest first) |
| 50 | Notion › Companies | Domain source = *Not found* (set by WP · 30), max 3 per run |
| 51 | Telegram trigger | Button taps (`callback_query`) and replies (`message` with `reply_to_message`) from chat 1170608781 only |

## 2. How the nodes work together
**50 · Approval cards**

| # | Section | Nodes | What happens | Why |
|---|---|---|---|---|
| 1 | Stack guard | Config → Notion · cards still open → Notion · drafts ready → Pick drafts | Room = 5 − open cards; takes at most that many drafts | Unanswered cards piling up was the main source of confusion |
| 2 | Card | Notion · get company → Build card → Telegram · send card | One card: company, person, channel, ICP, offer, signal, **what Approve will do**, the variants that passed, and A/B/C | You decide with the legal-basis consequence visible |
| 3 | Lock | Build Notion update → Notion · awaiting approval | Status *Awaiting approval* + the card's message id | The status is the lock: no second card, and no double send |
| 4 | Website questions | Notion · companies without website → Build website question → Telegram · ask website → Notion · mark asked | 🌐 question with a 🔎 Search button; Domain source → *Asked in Telegram* | A human fallback for the rare case where 30 can't verify a site. Each one is asked only once |

**51 · Approval handler**

| # | Section | Nodes | What happens |
|---|---|---|---|
| 1 | Gate | Telegram trigger → Parse update (rules) → Authorized? | Only your chat. Works out the kind of update: choose / edit / skip / reply / website / website_none |
| 2 | Website answer | Website answer? → Build website update → Valid domain? → Notion · save website → Notion · contacts of company → Contacts to retry → Notion · back to Needs email; Telegram · website reply | Saves the domain as *Manual*. Sends that company's *Not reachable* / *Check manually* contacts back to *Needs email*, so WP · 30 retries them |
| 3 | Find contact | Button: Telegram · answer tap → Notion · get contact · Reply: Notion · find contact by card → First match | A tap carries the contact id; a reply is matched through the card's message id |
| 4 | Decide | Decide action (rules) → Route | Idempotent: acts only on *Awaiting approval*. Applies the legal-basis gate |
| 5 | Act and record | Gmail · send / Gmail · create draft → Build outcome → Notion · save outcome → Telegram · confirm; Telegram · notice | One outcome node, so the Notion log is always consistent |

## 3. Outputs
**Contacts:**
- Status: *Sent*, *Gmail draft created*, *Approved* (LinkedIn) or *Skipped*.
- Chosen variant (A/B/C/Edited) and the final Draft subject/body.
- Approved at and Sent at.
- Approval log: one line per event.

**Companies:**
- Domain and Domain source (*Manual*, *Asked in Telegram* or *No website*).

**Telegram:** a confirmation reply under the card, or a notice ("Already handled …", "Reply with your text …").

## 4. Logic and decisions
**Legal-basis gate (code):**

| Channel | Legal basis | What happens | Status |
|---|---|---|---|
| Email | Consent / Existing relationship / Inbound | Sent from hello@ | Sent |
| Email | None - draft only (all article-sourced leads) | **Gmail draft** in hello@ that you send yourself | Gmail draft created |
| LinkedIn | any | Text plus profile link sent back to paste by hand | Approved |
| any | Skip | nothing | Skipped |

Why the design looks like this:
- **Gmail drafts for cold contacts:** German UWG §7 makes unsolicited advertising email risky without (presumed) consent. The engine prepares the email; a human presses send. This is not legal advice.
- **LinkedIn by hand:** LinkedIn has no permitted API for this kind of outreach, and automating it risks the account.
- **51 as a separate, always-on workflow:** a pipeline failure never blocks approvals, and approvals never block the pipeline.
- **Two bots instead of one:** decisions and alerts have different urgency. Mixing them was what made the chat confusing.

## 5. Failure modes and recovery
| What breaks | What you see | What happens | What you do |
|---|---|---|---|
| Double or late tap | "Already handled: … is Sent" | Nothing is sent twice | – |
| Gmail error | ❌ reply under the card | Status stays *Awaiting approval* | Tap again later |
| Reply to the wrong message | "Could not find the contact for this card." | Nothing | Reply directly to the 📨 card |
| Not a domain in a 🌐 reply | "… doesn't look like a domain" | Nothing saved | Reply again, e.g. `acme.ai` |
| 51 not published | Taps spin, nothing happens | – | Publish 51 (only one workflow per bot can hold the trigger) |
| Message from another chat | Ignored | – | – |

## 6. Settings you can change
| Where | Key | Default |
|---|---|---|
| 50 Config | `maxOpenCards` | 5 |
| 50 Config | `maxWebsiteQuestions` | 3 |
| 50 / 51 Parse | allowed chat id | 1170608781 |

## Changelog
- **v3 · 16 Oct:** duplicates go to Backlog (not Skipped); one-out-one-in refill from 51; run log row per 50 run in Notion › Runs; Notion approval can also promote a Backlog contact; credential IDs preset.
- **v2 · 15 Oct:**
  - Stack guard (max 5 open cards); cards numbered "APPROVE n/m" with type tag and divider.
  - 🌐 website questions, with replies handled in 51; contacts are re-queued for 30.
  - Errors moved to a separate alerts bot (WP · 90).
- **v1 · 15 Oct:**
  - Cards with Send A/B/C, Edit and Skip; legal-basis gate.
  - First live test: variant C became a Gmail draft (Radosław).

## Not yet
- **Follow-up engine (WP · 60):** cadence in Notion › Sales Playbook:
  - Day 0: email
  - Day 1: LinkedIn connect
  - Day 4: email
  - Day 8: LinkedIn message, only once the connection is accepted
  - Day 13: walk-away email
