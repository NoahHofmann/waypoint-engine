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
