# Generators

The workflow JSONs in `/workflows` are generated, not hand-edited. Each script rebuilds its files from scratch: node code, prompts (read from `/prompts`) and sticky notes.

```
python3 tools/gen30.py   # → workflows/30-enrich-contacts.json
python3 tools/gen40.py   # → workflows/40-draft-judge.json (reads prompts/draft.md, judge.md)
python3 tools/gen50.py   # → workflows/50-approval-cards.json + 51-approval-handler.json
```

Why: one place per workflow to read the whole logic, to diff changes in git, and to regenerate after a prompt edit. To import, use n8n › Workflow › Import from file (replace the existing workflow).
