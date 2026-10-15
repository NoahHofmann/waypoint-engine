# WP · 30 Enrich contacts (sub-workflow)

> For each contact in *Needs email*, finds a verified LinkedIn profile and/or a verified email (and the company website if it's missing), then sets a clear outcome status. Feeds WP · 40.

Chain position: 00 → 10 → 20 → **30** → 40 → 50.

## 1. Inputs
| Source | Filter | Fields read |
|---|---|---|
| Notion › Contacts | Status in the active funnel (one query, max 100) | Name, Role, Status, Company |
| Notion › Companies (linked) | – | Company, Domain, Country, Signal summary, Sector |
| Brave Search API | site:linkedin.com/in queries | title, URL, snippet |
| Company website | candidate homepages and /impressum, /contact, /about, /team | HTML |
| Hunter API | email-finder, email-verifier | email, score, status |
| Workflow static data | monthly counters | Brave and Hunter credits used |

## 2. How the nodes work together
| # | Section (sticky note) | Nodes | What happens | Why this way |
|---|---|---|---|---|
| 1 | Budget and selection | Config + budget → Notion · contacts needing email → Pick contacts | One contact per company per run, max 8. Order: CEO/MD → founder → sales → partnerships. Companies that already have a reachable contact are skipped | The free tiers are small (Brave 300 and Hunter 40 per month, self-capped) |
| 2 | Company context | Notion · get company → Prep search | Company core name (legal forms stripped, Æ→ae …), country TLD, **topic words** from the signal summary, three search queries | Topic words let the website check confirm it's the same business |
| 3 | LinkedIn | Brave attempt 1 → Verify 1 → LinkedIn found? → Brave attempt 2 → Verify 2 | Accepted only when the title has first and last name AND the company appears. Name-only hits go to *LinkedIn candidate* | Same-name collisions are common. A wrong profile is worse than none |
| 4 | Website fail-safe | Has domain? (no) → Website candidates → Fetch candidate homepage → Pick verified website → Notion · save company domain | About 30 likely domains are generated and each homepage is opened. **Accept only if:** not parked/placeholder, name as a whole word, ≥ 1 topic word on the page | Search APIs returned 0 results for company names; opening the sites directly is free |
| 5 | Email | Site pages to scan → Fetch site page → Extract site emails → Hunter finder → Decide verify → Hunter verify → Build contact update → Notion · update contact | First the site's own pages (Impressum etc.), then Hunter. Generic inboxes are saved on the company, never on the person | The Impressum is legally required in DACH; scanning it is free and reliable |
| 6 | Summary | Run summary + budget | Counts, credits used, API errors | Reported to the orchestrator and the Runs DB |

## 3. Outputs
Written to the contact:

| Status | Rule |
|---|---|
| Ready to draft | Hunter says valid (or accept_all with score ≥ 90) |
| LinkedIn only | Verified LinkedIn, no usable email |
| Check manually | Only a name-only LinkedIn candidate, or an unverifiable email |
| Not reachable | Nothing found |
| Needs email (unchanged) | API, auth or rate-limit error. Retried next run at no budget cost |

Also written to the contact: Email, Email source, LinkedIn, LinkedIn candidate, LinkedIn match (a reason trail).

Written to the company:
- **Domain + Domain source:**
  - *Article*: the domain came from the funding article.
  - *Website check*: verified by 30.
  - *Not found*: no candidate passed, so WP · 50 asks you in Telegram.
  - *Manual*: you supplied it.
- **Company inbox:** a generic address (hello@, info@), saved on the company only.

## 4. Logic and decisions
**The website check (v3)** answers three questions before it accepts a domain:
1. **Is it a real site?** It rejects:
   - sale and broker wording: "interested in buying this domain", "contact the seller", "make an offer", "listed by", Sedo, Dan, Afternic, HugeDomains, BrandBucket, Squadhelp…
   - placeholders: "coming soon", "under construction", default server pages
   - pages with fewer than 200 characters of visible text
2. **Is it the same name?** The company name must appear as a whole word, so "holo" does not match "holographic".
3. **Is it the same business?** At least one topic word from the funding article must appear on the page (for Ambio: recycled, plastics, procurement).

Ranking among the domains that pass: name in the title, then more topic words, then candidate order (.com first).

The candidate list includes `try<name>`, `get<name>` and `use<name>` (.com/.ai/.io), `<name>ai.com`, `<name>labs.com` and European ccTLDs. Holo's real site is tryholo.ai.

**Why a wrong domain is worse than none:** Hunter then searches the wrong company, and the "verified" email belongs to a stranger. With *Not found*, the cost is one 5-second Telegram answer.

**Hunter domain sanity check:** if Hunter guessed the domain itself, it must match the company name. A live case returned vexrobotics.com for FLÆ Robotics.

## 5. Failure modes and recovery
| What breaks | What you see | What happens | What you do |
|---|---|---|---|
| Brave/Hunter error or rate limit | LinkedIn match: "API error …" | Contact stays *Needs email*; no budget counted | Nothing; the next run retries |
| Budget used up | Run summary: "budget reached" | No new calls | Wait for the month to reset, or raise the cap in Config |
| No verifiable website | Company Domain source *Not found* | 🌐 question in Telegram (WP · 50) | Reply with the domain; 51 re-queues the contacts |
| Wrong website slipped through | Wrong-company emails | – | Set Domain + *Manual*, and set its contacts back to *Needs email* |

## 6. Settings you can change
| Config key | Default |
|---|---|
| Brave / Hunter monthly caps | 300 / 40 |
| Max contacts per run | 8 |
| Persona order | CEO/MD → founder → sales → partnerships |

## Changelog
- **v3 · 15 Oct:**
  - Website check hardened: broker/seller phrases, whole-word name match, topic-word relevance, try/use/get candidates.
  - *Not found* routes to a Telegram question.
  - Live misses that triggered this: ambio.com (for sale), holo.pl (a hologram sticker shop), miracly.com (coming soon). All three were corrected in Notion.
- **v2 · 15 Oct:** website fail-safe (domain candidates), site-email scan, company inbox, Hunter domain sanity check, API errors kept as *Needs email*.
- **v1 · 14 Oct:** Brave LinkedIn and Hunter only; many contacts ended as "No email found".
