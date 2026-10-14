# Waypoint Engine: documentation

Start here. Every workflow has its own page that explains **what it does, why it is built that way, and how it fails**.

| Doc | What it covers |
|---|---|
| [architecture.md](architecture.md) | The whole system on one page, and the principles every workflow follows |
| [data-model.md](data-model.md) | Notion databases, every status, and what moves a record from one status to the next |
| [00-intake-orchestrator.md](00-intake-orchestrator.md) | Daily trigger, RSS intake, dedupe, calling the sub-workflows |
| [10-qualify-company.md](10-qualify-company.md) | Full-article fetch, fact extraction, icp-v2 scoring, gates |
| [20-find-people.md](20-find-people.md) | Named people from the article, verbatim checks |
| [30-enrich-contacts.md](30-enrich-contacts.md) | LinkedIn, company website, email, outcome statuses, budget |
| [90-error-handler.md](90-error-handler.md) | What happens when anything fails |
| [decision-log.md](decision-log.md) | Dated log of design decisions and the live result that triggered them |

Rule for future changes: **no workflow change without updating its doc and adding a line to the decision log.**
