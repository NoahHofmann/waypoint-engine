# Decision log

| Date | Decision | Why (live evidence) |
|---|---|---|
| 13 Oct | Outbound engine on n8n, Notion CRM, human approval via Telegram | Budget €50–100/month, demo Monday |
| 14 Oct | Companies and Contacts as separate databases | One company, several people; dedupe per company |
| 14 Oct | LLM extracts facts, code scores (qualify-v2 / icp-v2) | v1 gave the same FLÆ article "Qualified" and "Archived" from two feeds |
| 14 Oct | Fetch full article in 10 | RSS teaser had no names → 0 contacts |
| 14 Oct | Loose output schema + normalisation in code | Strict schema rejected 4 of 15 answers |
| 14 Oct | Near-verbatim evidence (80% word pairs) | Curly quotes / tiny edits dropped valid evidence, depressing scores |
| 14 Oct | Paragraph-only extraction, investor check on extracted investors | Sidebar "Antler" gave a false Network investor flag |
| 14 Oct | 20 guardrails run once for all items | Per-item mode crashed on 0–3 outputs |
| 14 Oct | B2C hard gate; unconfirmed business model can't qualify | Noah: B2B is the strength; Coding Giants (kids' school) qualified at 68 |
| 14 Oct | Brave + Hunter (free tiers), no Crunchbase scraping | Cost; Crunchbase API is enterprise-only and ToS forbids scraping |
| 14 Oct | API errors keep "Needs email" | Wrong Hunter key marked 5 people "No email found" |
| 14 Oct | One contact per company per run, skip covered companies | 50 Hunter credits/month |
| 14 Oct | Hunter domain guess must match company name | FLÆ Robotics → vexrobotics.com |
| 14 Oct | Outcome statuses: Ready to draft / LinkedIn only / Check manually / Not reachable + Reach formula | "No email found" hid whether a LinkedIn existed |
| 14 Oct | Website search with plain company name | Quoted "official website" query returned 0 results in every live run |
| 15 Oct | Website fail-safe: generate likely domains and verify the homepage shows the company name | Brave website search returned 0 results in every live run; most domains were empty |
| 15 Oct | Scan Impressum/contact/about pages for published addresses; generic inbox stored on the company only | Free second email source; a company inbox is not a person's consent or address |
| 15 Oct | 40: brief built by rules, offer chosen by rules, code check + LLM judge, one retry | Drafts must only use verified facts and canonical metrics; invented numbers are caught in code |
| 15 Oct | Per-contact Cal.com link with metadata | Lets a booking be matched to the contact automatically (T-010) |
| 15 Oct | 30: per-item code nodes that return several items switched to run once for all items | Live error "A 'json' property isn't an object" in Website candidates (same class as the 20 bug) |
| 15 Oct | 40 v2: three variants (problem / insight / short), Noah picks; Sales Playbook in Notion read live | First live run: 3 of 3 drafts failed, all funding-led; Noah wants to choose the message himself |
| 15 Oct | German drafts use "du"; code rejects "Sie" and funding-led openings or subjects | Noah: startup tone, "how can we help" instead of "I saw you raised" |
| 15 Oct | Judge answers yes/no per criterion, pass computed in code, format left to code | v1 judge wrote "Unsupported: None" and hallucinated a missing opt-out line |
| 15 Oct | Follow-up engine planned as separate workflow (60), cadence in the playbook | Noah: sequences matter; kept out of 40 so first touch and follow-ups can be tested separately |
| 15 Oct | 40 v3: article excerpt + homepage in the brief, cliché ban, varied asks, C 30–60 words, LinkedIn ≤ 200 chars | v2 run: drafts correct but generic; judge expression bug ("no verdict" on every variant) |
| 15 Oct | Draft gpt-5.1, judge gpt-5-mini | Same cost range as gpt-4o, better at following many rules at once; fallback kept |
| 15 Oct | Playbook adds $100M Offers and Thinking, Fast and Slow; cadence 5 touches / 2 LinkedIn / walk-away email | Noah's request |
| 15 Oct | 50/51 Telegram approval: 3 variants + Edit + Skip, status as idempotency lock, cold leads become Gmail drafts | Human decides every send; UWG §7 caution for cold B2B email in Germany |
| 15 Oct | 30 v3 website check: broker/placeholder phrases, whole-word name, topic-word relevance; *Not found* → one Telegram question | ambio.com (for sale), holo.pl (hologram stickers), miracly.com (coming soon) were accepted by v2. A wrong domain leads to emails to the wrong people |
| 15 Oct | 40 v4: draft model Claude Sonnet 5.5, judge GPT-5 mini (reasoning low), 4 contacts in parallel | v3 took 6:31 because of GPT-5.1 reasoning. Sonnet 5.5 costs $2/$10 per 1M (same output price as GPT-5.1) and writes more natural DE/EN. Judge from a different family. Rejected: Mistral Large 3 (stiffer prose), DeepSeek (EU personal data to China), Perplexity (search, not writing) |
| 15 Oct | Judge length remarks and LinkedIn proof/ask demands are dropped in code | Code owns length; a connection note deliberately has no pitch |
| 15 Oct | Telegram: approvals bot only for decisions (📨 APPROVE n/m, 🌐 WEBSITE?), second bot for 🚨 errors, max 5 open cards | Stacked, mixed messages lost context |
| 15 Oct | Dashboard moved onto the Waypoint Engine main page; chart views removed | Charts need Notion Plus; six named table/board views instead |
| 15 Oct | Docs follow docs/_template.md (Inputs · nodes · outputs · logic · failure modes · settings · changelog) | Noah: the old docs didn't explain how nodes work together |
| 15 Oct | Draft model decision reopened: GPT-5.1 (reasoning low) stays for now; a blind bake-off via OpenRouter (GPT-5.1 vs Gemini 3.8 Flash vs Claude Sonnet 5.5) decides on Friday | Noah challenged the Sonnet pick. The public writing benchmarks measure fiction, not sales emails, and miss the newest mid-tier models. The cost gap is about $3–5/month, so quality decides |
| 15 Oct | Notion: "Action" formula on Contacts/Companies; "Approve in Notion" fallback (handled by 50 → 51 with the same gate); databases and rules moved into one sub-page | Noah: the dashboard should say what to do, and a missed Telegram card must be actionable in Notion |
| 15 Oct | 50: one company, one conversation (duplicates → Skipped with a reason); ⏸ QUEUE FULL notice instead of silent waiting | Run 3: Dawid (Coding Giants) drafted while Radosław was already in Gmail; 4 drafts waited silently behind 5 unanswered cards |
| 15 Oct | 30: Gmail draft created / LinkedIn only count as "company covered" | Coding Giants was enriched twice |
| 15 Oct | draft-v5: no-oriented question in at most 1 variant; no template self-intro; proof point chosen per situation | Run 3: "Would it be a bad idea/crazy" and "I help funded B2B CEOs…" in nearly every email |
| 16 Oct | Second person at the same company → **Backlog** (not Skipped) | Noah: Skipped implies an error; Backlog = second contact if the first doesn't reply |
| 16 Oct | One out, one in: each decided card triggers WP · 50 immediately | Noah: cards must not wait for the next scheduled run; the pipeline should drain as fast as he answers |
| 16 Oct | Run log rows for 30, 40, 50 (Runs.Duration s added) | System health showed only Intake. Measured: 40 = 46 s (was 6:31), 50 = 6.5 s |
| 16 Oct | Telegram routing rule: needs an answer → approvals bot; info only → alerts bot | Clear rule instead of a per-message call |
| 16 Oct | Contacts store Draft model + Prompt version | Groundwork for the response-rate analytics agent (docs/roadmap.md) |
| 16 Oct | 51 v4: every tap/reply answered; decided cards are edited closed (buttons removed); unmatched messages get a help note; HTML bold formatting | Noah: no response left him unsure whether a tap was recorded; open vs. done must be visible at a glance |
| 16 Oct | Run log is an upsert per execution ($execution.customData) | v1 wrote 2–3 rows per run, because 30/40 summaries run once per arriving branch |
| 16 Oct | All credential + workflow IDs preset in the generators (tools/runlog.py) | Zero-click imports |
| 16 Oct | Orchestrator: Always Output Data on Sub · 30/40/50 | A sub-workflow with nothing to do returns 0 items and n8n stops the chain: 40 and 50 never ran at 12:46 |
| 16 Oct | 30: only decision-maker roles are enriched (CEO/MD, founder, sales, partnerships); a missing role is skipped | Holo's "Founding UX Designer" got a Gmail draft when the CEO was unreachable |
| 16 Oct | LinkedIn approvals become an open "🔗 LINKEDIN TO SEND" message with Open profile + ✅ Sent on LinkedIn buttons | Noah: "copy and send" texts get lost in the chat; the to-do must stay visibly open until done |
| 16 Oct | Draft model → Claude Sonnet 5.5; judge-v5 adds a 10-point quality rubric (own benchmark); judge stays GPT-5 mini | Noah added Anthropic; wants good emails without overpaying and a way to compare models over time |
| 16 Oct | All workflows: credential + workflow IDs preset, Error workflow = WP · 90 | Zero-click imports; every crash reaches the alerts bot |
| 16 Oct | docs/STATE.md (+ Project doc) is the handover page for new sessions; decision-log keeps the why | Context compaction can drop details; one page restores the state |
| 16 Oct | Status "Backlog" renamed to **Second contact**; card tag 📥 BACKLOG = came from the queue | The same word was used for two things |
| 16 Oct | 3 more RSS feeds (Tech Funding News, Silicon Canals, Trending Topics) with a source priority 1–5 before the per-run cap | Need more fresh funded companies; the best-fit, non-paywalled sources come first. Sifted/Gründerszene excluded (paywall breaks hooks and link extraction) |
| 16 Oct | 40: draft output parsed in code (tolerant JSON), n8n structured parser removed for the draft | First Claude run: both emails came back empty. Claude writes real line breaks inside JSON strings, the parser rejected them, and every email variant counted as "missing" (LinkedIn notes have one line, so they passed at 9.7/10) |
| 16 Oct | Missing variants are not scored | The empty drafts pulled Quality avg down to 3.2; only real drafts count |

## 16 Oct, 18:15 · Code freeze after 14/14 stress tests
All tests passed after three real fixes (double-tap lock, Claude output budget + GPT fallback, alerts-bot setup). No further fixes before Monday: every change now risks the demo more than it improves it. Open items stay parked in the roadmap (analytics agent, WP · 60, seniority fallback, model bake-off, Tech Funding News 403, docs 00/10/20/90 in the template).

## 20 Oct · External audit integrated
| Date | Decision | Why |
|---|---|---|
| 20 Oct | Accept audit code findings F2, F3, F6, alert wording, backups, image pinning, editor access; fix in one H0 block | Confirmed in the generators at 61787d1; each is under an hour |
| 20 Oct | Re-rate F1/F10 (duplicate send, approval binding) to Low while 51 is forced to draft-only | Every cold lead is a Gmail draft; worst case is a duplicate draft. Re-rated High before auto-send or WP · 60 |
| 20 Oct | Outcome sync (sent/reply/booking) becomes the next feature, ahead of follow-ups and analytics | 12 drafts have no recorded send; no reply data means no analytics, no bake-off, no safe follow-up stop |
| 20 Oct | No SaaS, tenancy or Postgres application layer on the roadmap | Audit's own cost model: 7.6% contribution at 5 × €299. Offer 5 is a service on per-client instances |
| 20 Oct | DE/AT recipients: LinkedIn or warm intro, not cold e-mail, pending legal advice | UWG §7(2) Nr. 2 requires prior consent for advertising e-mail, B2B included; manual sending doesn't change it |
| 20 Oct | Eval reporting shows precision/recall with counts | "80%" accuracy hid 57% recall against a 65% majority baseline |

## 22 Oct · Legal stance, Gmail/Notion reconciliation
| Date | Decision | Why |
|---|---|---|
| 22 Oct | DE/AT recipients may receive a manual cold e-mail again, with a concrete, researched reason to contact them. The 20 Oct "LinkedIn or warm intro only" rule is withdrawn for now. The engine gate stays: Legal basis "None - draft only", Gmail draft, Noah sends by hand | Noah spoke informally with a lawyer friend: fine as long as it is targeted and not spam (no bulk or generic blasts, remove and delete anyone who asks to stop). **Informal and verbal, not written advice, and no formal sign-off.** It differs from the 19 Oct audit reading of UWG §7(2) Nr. 2 (prior consent, B2B included; Austria stricter under TKG §174). Residual risk (cease-and-desist letter) is accepted by Noah. Re-check with written advice before auto-send, WP · 60, or selling offer 5 to a client |
| 22 Oct | Opt-out handling: on any "stop" reply set Status = Do not contact, delete the e-mail address, never contact again | Conditions of the informal go-ahead |
| 22 Oct | Gmail drafts reconciled with Notion: 6 stale or duplicate drafts deleted (5 from an earlier 10:16 run on 16 Oct for Solvera, Epyr, Hylight, Causa Prima, KP Labs; Dawid at Coding Giants). Dawid set to **Second contact**. Holo draft (lost, no trace in Gmail or Sent) recreated from Notion. Ambio: Noah's hand-edited Gmail text adopted, Notion synced (Chosen variant = Edited) | Rule: no discrepancy between Notion and Gmail before sending. Observation for H0: 5 recipients had two Gmail drafts and one draft vanished, so draft creation in 51 is not idempotent and not verified against Gmail |

