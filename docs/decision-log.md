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
