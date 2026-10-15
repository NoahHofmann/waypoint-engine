# WP · 40 Draft + judge (sub-workflow)

> For every contact with a verified channel, writes three draft messages that follow the Notion Sales Playbook. Each draft is checked by code and by a second model, and the contact is handed to WP · 50 for your choice in Telegram. **This workflow never sends anything.**

Chain position: 00 → 10 → 20 → 30 → **40** → 50 / 51. It can also be run on its own ("Test workflow").

## 1. Inputs
| Source | Filter | Fields read |
|---|---|---|
| Notion › Contacts | Status = *Ready to draft* (verified email) or *LinkedIn only*; oldest first; max 8 (Config `maxDraftsPerRun`) | Name, Role, Email, LinkedIn, Status, Draft version, Company |
| Notion › Companies (linked) | – | Company, Country, Domain, Signal summary/source, Round, Amount, Evidence, Qualify reasons |
| Funding article (Signal source) | fetched live | first ~3,500 characters of paragraphs |
| Company homepage (Domain) | fetched live | visible text, capped |
| Notion › Offers | Active = true, by Priority | name, description, who it is for |
| Notion › Sales Playbook | page `3fa64e3c…` (Config `playbookPageId`) | headings, paragraphs and bullets, read on every run |
| Config | – | Noah's canonical profile (the only facts about Noah a draft may use), Cal.com link, models, prompt version |

## 2. How the nodes work together
| # | Section (sticky note) | Nodes | What happens | Why this way |
|---|---|---|---|---|
| 1 | Load context | Config → Notion · active offers → Notion · sales playbook → Notion · contacts to draft | Loads offers, playbook and the queue **once** per run | The playbook is read live, so you change the rules in Notion, not in n8n |
| 2 | Research and brief | Pick contacts → Notion · get company → Fetch article → Fetch homepage → Build brief (rules) | Builds one plain-text BRIEF per contact: channel, language, offer, booking link, facts, profile, playbook | Everything the model may say is in the brief; anything else counts as invented and is caught later |
| 3 | Draft and check | Draft (attempt 1) + Claude · draft 1 + Schema → Check rules 1 | Claude writes variants A, B and C in one call; code checks each one | Counting and exact matching belong in code; models are bad at counting their own words |
| 4 | Judge and decide | Judge (attempt 1) + OpenAI · judge 1 + Schema → Decide 1 → Passed? | GPT-5 mini answers yes/no questions per variant; code combines both checks | A different model family grades the draft, so the drafter doesn't grade itself |
| 5 | Retry and save | Prepare retry → the same chain as attempt 2 → Build draft update → Notion · save draft → Run summary | One retry with concrete feedback, then saves all three variants and the status | One retry fixes most issues; a second retry mostly burns tokens |

**Brief rules (Build brief):**
- **Channel:** Email if the contact has a verified email, otherwise LinkedIn.
- **Language:** DE with informal *du* for DE/AT/CH companies, EN otherwise.
- **Offer:**
  - partnerships, channel or distribution signal → Fractional Partnerships Lead
  - DACH company → GTM Strategy & ICP Sprint
  - all others → Market Entry & Expansion into DACH
- **Booking link:** `…/30min?metadata[contact]=<contact id>`, so a booking can be matched back to the contact.

## 3. Outputs
Written to the contact in Notion:
- Variant A, Variant B and Variant C (failed ones end with "[did not pass review]").
- Variants passed.
- Draft subject and Draft body: the first passing variant, which is the default.
- Draft version +1.
- Judge result and Judge notes: per variant, PASS/FAIL with reasons.
- Channel, Offer, Draft language and Booking link.
- **Status:**
  - *Draft ready* when at least one variant passed. WP · 50 picks it up.
  - *Check manually* when no variant passed after two attempts. It appears in the dashboard.

Run summary to the orchestrator: drafted, passed, passed on the first try, failed.

## 4. Logic and decisions
**Three variants instead of one.** You choose the angle; the engine doesn't guess it.
- A · Problem first.
- B · Insight first.
- C · Short and direct, ≤ 55 words.

**Code checks per variant:**
- Email subject has 3–7 words and doesn't mention funding.
- Body length before the link: A and B 55–120 words; C 25–60 words (the prompt asks for ≤ 55, and code allows a small buffer).
- Booking link unchanged, opt-out line present, sign-off present, first name used.
- German drafts use *du*, never *Sie*.
- The first sentence is not about the funding round.
- No hype, flattery or clichés.
- **Every number must appear in the brief.** This catches invented metrics.
- LinkedIn notes: ≤ 200 characters (the prompt asks for 180), no link, no question.

**What the judge checks:** unsupported claims, names, language and *du*, a specific opening, tone, and playbook violations about content.
- The **pass decision is computed in code**, not by the model.
- Judge remarks about length are dropped, because code owns length. In v3 the judge counted words itself and failed good drafts.
- For LinkedIn, demands for a proof point, a question or an ask are dropped. A connection note deliberately has none of these: the request itself is the ask, and the pitch follows after they accept.

**Models** (preset in the sub-nodes, so after import you only select the credentials):

| Role | Model | Why | Price per 1M tokens (input / output) |
|---|---|---|---|
| Draft | Claude Sonnet 5.5 (`claude-sonnet-5-5`), temperature 0.6 | Most natural German and English prose of the options tested; no reasoning delay | $2 / $10 |
| Judge | GPT-5 mini, reasoning effort low | Different model family from the drafter; cheap; yes/no checking is easy | $0.25 / $2 |

Options considered and rejected for drafting:
- **GPT-5.1:** good, but its reasoning made the run take 6:31, and output costs the same $10.
- **Mistral Large 3:** EU-hosted and cheapest, but stiffer prose.
- **DeepSeek:** processes EU personal data in China, a GDPR problem.
- **Perplexity:** a search product, not a writing model.

**Runtime:** both chains process 4 contacts in parallel (`batching.batchSize = 4`). Expected run time is 2–3 minutes for 8 contacts, down from 6:31 in v3.

**Cost:** about $0.03 per contact per attempt for the draft plus under $0.01 for the judge. That is under $0.50 per run, even with retries.

## 5. Failure modes and recovery
| What breaks | What you see | What the workflow does | What you do |
|---|---|---|---|
| Anthropic/OpenAI API error or timeout | Judge notes: "Judge returned no verdict: …" or empty variants | The node continues; the contact ends in *Check manually* | Set Status back to *Ready to draft* and re-run |
| Credential not selected after import | Red model node | – | Select *Anthropic API* / *OpenAi account* in the two model sub-nodes |
| Playbook page not shared with the integration | Brief says "playbook not loaded" | Drafts still follow the system prompt rules | Share the page with *waypoint-n8n* |
| Article or homepage blocked | Thinner hooks, judge flags "Opening not specific" | Retry with feedback | Add facts to Companies › Evidence by hand |
| Notion save fails | Error in run | Retried 3× after 2 s | Re-run; only contacts still in *Ready to draft* are picked |

Re-running is safe: already drafted contacts have moved to *Draft ready* or later, so they are never drafted twice.

## 6. Settings you can change
| Config key | Default | Notes |
|---|---|---|
| `maxDraftsPerRun` | 8 | Raise once you trust the output; cost scales linearly |
| `profile` | canonical metrics | The ONLY facts about you a draft may use. Keep in sync with the project instructions |
| `calLink` | Cal.com 30 min | Per-contact metadata is appended |
| `playbookPageId` | Sales Playbook | Point to another page to A/B a playbook |
| Batch size (in the Draft/Judge nodes) | 4 | Lower it if Anthropic returns rate-limit errors |

## Changelog
- **v4 · 15 Oct:**
  - Draft model changed to Claude Sonnet 5.5; judge reasoning set to low; 4 contacts processed in parallel.
  - The judge's length remarks and LinkedIn proof/ask demands are dropped.
  - LinkedIn notes: ≤ 180 characters, no question. C: ≤ 55 words.
  - Models are preset by ID.
  - Six sticky notes.
- **v3 · 15 Oct:**
  - The article and homepage are added to the brief as hooks; clichés are banned.
  - Each variant gets a different ask.
  - Fixed the judge expression newline bug (every variant showed "no verdict").
  - Models: GPT-5.1 / GPT-5 mini.
- **v2 · 15 Oct:**
  - Three variants and the Notion playbook.
  - Funding-headline check moved into code; German uses *du*.
  - The judge answers yes/no and "none" items are filtered out.
- **v1 · 15 Oct:**
  - One variant only, and it opened with the funding round.
  - The judge hallucinated a missing opt-out line.
